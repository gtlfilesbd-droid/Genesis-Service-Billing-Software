from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
import json
from .models import Client, Agreement, Service
from accounts.models import UserProfile


def get_user_profile(user):
    try:
        return user.profile
    except UserProfile.DoesNotExist:
        return UserProfile.objects.create(user=user)


@login_required
def client_list(request):
    clients = Client.objects.all()
    search = request.GET.get('search', '')
    if search:
        clients = clients.filter(name__icontains=search) | clients.filter(company__icontains=search)
    paginator = Paginator(clients, 10)
    page = request.GET.get('page')
    clients = paginator.get_page(page)
    profile = get_user_profile(request.user)
    return render(request, 'clients/client_list.html', {'clients': clients, 'search': search, 'profile': profile})


@login_required
def client_add(request):
    profile = get_user_profile(request.user)
    if not profile.can_add_client and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to add clients.')
        return redirect('client_list')

    if request.method == 'POST':
        client = Client(
            name=request.POST.get('name'),
            company=request.POST.get('company'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address'),
            city=request.POST.get('city'),
            country=request.POST.get('country', 'Bangladesh'),
            created_by=request.user
        )
        client.save()
        messages.success(request, f'Client "{client.name}" added successfully.')
        return redirect('client_detail', pk=client.pk)

    return render(request, 'clients/client_form.html', {'action': 'Add', 'profile': profile})


@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    profile = get_user_profile(request.user)
    agreements = client.agreements.prefetch_related('services').all()
    service_type_choices = dict(Service._meta.get_field('service_type').choices)
    # Each Service row may contain multiple names (one per line).
    for ag in agreements:
        months = Agreement._months_in_period(ag.start_date, ag.end_date) if ag.end_date else 0
        years = Agreement._years_in_period(ag.start_date, ag.end_date) if ag.end_date else 0
        ag.grouped_services = []
        ag.total_monthly_amount = 0
        ag.total_yearly_amount = 0
        for s in ag.services.all():
            from decimal import Decimal, InvalidOperation
            names = [n.strip() for n in (s.name or '').splitlines() if n.strip()]
            try:
                charge = Decimal(str(s.charge or 0))
            except (InvalidOperation, TypeError, ValueError):
                charge = Decimal('0')

            st = (s.service_type or '').lower()
            if st == 'monthly':
                monthly_amount = charge
                yearly_amount = charge * Decimal('12')
            elif st in ('annual', 'yearly'):
                # charge is treated as yearly
                monthly_amount = charge / Decimal('12') if charge else Decimal('0')
                yearly_amount = charge
            elif st == 'quarterly':
                monthly_amount = charge / Decimal('3') if charge else Decimal('0')
                yearly_amount = charge * Decimal('4')
            elif st == 'semi_annual':
                monthly_amount = charge / Decimal('6') if charge else Decimal('0')
                yearly_amount = charge * Decimal('2')
            elif st == 'one_time':
                monthly_amount = charge
                yearly_amount = charge
            else:
                monthly_amount = charge
                yearly_amount = charge * Decimal('12')

            if st in ('annual', 'yearly'):
                total_amc = charge * Decimal(years or 0)
            elif st == 'monthly':
                total_amc = monthly_amount * Decimal(months or 0)
            elif st == 'quarterly':
                periods = (months + 2) // 3 if months else 0
                total_amc = charge * Decimal(periods)
            elif st == 'semi_annual':
                periods = (months + 5) // 6 if months else 0
                total_amc = charge * Decimal(periods)
            elif st == 'one_time':
                total_amc = charge
            else:
                total_amc = charge

            ag.total_monthly_amount += monthly_amount
            ag.total_yearly_amount += yearly_amount
            ag.grouped_services.append({
                'names': names if names else ['—'],
                'service_type': s.service_type,
                'service_type_label': service_type_choices.get(s.service_type, s.service_type),
                'charge': charge,
                'monthly_amount': monthly_amount,
                'yearly_amount': yearly_amount,
                'total_amc_amount': total_amc,
                'description': s.description or '',
            })
    return render(request, 'clients/client_detail.html', {
        'client': client,
        'agreements': agreements,
        'profile': profile
    })


@login_required
def client_edit(request, pk):
    profile = get_user_profile(request.user)
    if not profile.can_edit_client and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to edit clients.')
        return redirect('client_detail', pk=pk)

    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        client.name = request.POST.get('name')
        client.company = request.POST.get('company')
        client.email = request.POST.get('email')
        client.phone = request.POST.get('phone')
        client.address = request.POST.get('address')
        client.city = request.POST.get('city')
        client.country = request.POST.get('country', 'Bangladesh')
        client.is_active = request.POST.get('is_active') == 'on'
        client.save()
        messages.success(request, 'Client updated successfully.')
        return redirect('client_detail', pk=pk)

    return render(request, 'clients/client_form.html', {'action': 'Edit', 'client': client, 'profile': profile})


@login_required
def agreement_add(request, client_pk):
    profile = get_user_profile(request.user)
    if not profile.can_add_client and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to add agreements.')
        return redirect('client_detail', pk=client_pk)

    client = get_object_or_404(Client, pk=client_pk)
    if request.method == 'POST':
        agreement = Agreement(
            client=client,
            title=request.POST.get('title'),
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date') or None,
            notes=request.POST.get('notes'),
            attachment=request.FILES.get('attachment'),
            created_by=request.user
        )
        agreement.save()

        # Add services
        service_names_json = request.POST.getlist('service_names_json[]')
        service_types = request.POST.getlist('service_type[]')
        service_charges = request.POST.getlist('service_charge[]')
        service_descs = request.POST.getlist('service_description[]')

        # Backward compatibility: if older template posts flat service_name[]
        if not service_names_json:
            service_names = request.POST.getlist('service_name[]')
            for i in range(len(service_names)):
                if service_names[i]:
                    Service.objects.create(
                        agreement=agreement,
                        name=service_names[i],
                        service_type=service_types[i] if i < len(service_types) else 'monthly',
                        charge=service_charges[i] if i < len(service_charges) else 0,
                        description=service_descs[i] if i < len(service_descs) else '',
                    )
        else:
            for i in range(len(service_names_json)):
                raw = service_names_json[i]
                try:
                    names = json.loads(raw) if raw else []
                except json.JSONDecodeError:
                    names = []
                cleaned = [n.strip() for n in names if isinstance(n, str) and n.strip()]
                if not cleaned:
                    continue
                # One row = one charge. Store multiple names in one Service (one per line).
                Service.objects.create(
                    agreement=agreement,
                    name="\n".join(cleaned),
                    service_type=service_types[i] if i < len(service_types) else 'monthly',
                    charge=service_charges[i] if i < len(service_charges) else 0,
                    description=service_descs[i] if i < len(service_descs) else '',
                )

        messages.success(request, 'Agreement added successfully.')
        return redirect('client_detail', pk=client_pk)

    return render(request, 'clients/agreement_form.html', {
        'client': client,
        'profile': profile,
        'service_types': Service._meta.get_field('service_type').choices,
    })


@login_required
def agreement_edit(request, pk):
    profile = get_user_profile(request.user)
    agreement = get_object_or_404(Agreement, pk=pk)
    client = agreement.client

    if not profile.can_edit_client and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to edit agreements.')
        return redirect('client_detail', pk=client.pk)

    if request.method == 'POST':
        agreement.title = request.POST.get('title')
        agreement.start_date = request.POST.get('start_date')
        agreement.end_date = request.POST.get('end_date') or None
        agreement.notes = request.POST.get('notes')
        agreement.is_active = request.POST.get('is_active') == 'on'
        if request.FILES.get('attachment'):
            agreement.attachment = request.FILES.get('attachment')
        agreement.save()

        # Update services
        agreement.services.all().delete()
        service_names_json = request.POST.getlist('service_names_json[]')
        service_types = request.POST.getlist('service_type[]')
        service_charges = request.POST.getlist('service_charge[]')
        service_descs = request.POST.getlist('service_description[]')

        # Backward compatibility: if older template posts flat service_name[]
        if not service_names_json:
            service_names = request.POST.getlist('service_name[]')
            for i in range(len(service_names)):
                if service_names[i]:
                    Service.objects.create(
                        agreement=agreement,
                        name=service_names[i],
                        service_type=service_types[i] if i < len(service_types) else 'monthly',
                        charge=service_charges[i] if i < len(service_charges) else 0,
                        description=service_descs[i] if i < len(service_descs) else '',
                    )
        else:
            for i in range(len(service_names_json)):
                raw = service_names_json[i]
                try:
                    names = json.loads(raw) if raw else []
                except json.JSONDecodeError:
                    names = []
                cleaned = [n.strip() for n in names if isinstance(n, str) and n.strip()]
                if not cleaned:
                    continue
                Service.objects.create(
                    agreement=agreement,
                    name="\n".join(cleaned),
                    service_type=service_types[i] if i < len(service_types) else 'monthly',
                    charge=service_charges[i] if i < len(service_charges) else 0,
                    description=service_descs[i] if i < len(service_descs) else '',
                )

        messages.success(request, 'Agreement updated successfully.')
        return redirect('client_detail', pk=client.pk)

    # Each Service row may contain multiple names (one per line)
    service_groups = []
    if agreement:
        for s in agreement.services.all():
            names = [n.strip() for n in (s.name or '').splitlines() if n.strip()]
            service_groups.append({
                'names': names if names else [''],
                'service_type': s.service_type,
                'charge': s.charge,
                'description': s.description or '',
            })

    return render(request, 'clients/agreement_form.html', {
        'client': client,
        'agreement': agreement,
        'profile': profile,
        'service_types': Service._meta.get_field('service_type').choices,
        'service_groups': service_groups,
    })


@login_required
def agreement_delete(request, pk):
    profile = get_user_profile(request.user)
    agreement = get_object_or_404(Agreement, pk=pk)
    client = agreement.client

    if not profile.can_edit_client and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to delete agreements.')
        return redirect('client_detail', pk=client.pk)

    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('client_detail', pk=client.pk)

    title = agreement.title
    agreement.delete()
    messages.success(request, f'Agreement "{title}" deleted successfully.')
    return redirect('client_detail', pk=client.pk)
