from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
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
            created_by=request.user
        )
        agreement.save()

        # Add services
        service_names = request.POST.getlist('service_name[]')
        service_types = request.POST.getlist('service_type[]')
        service_charges = request.POST.getlist('service_charge[]')
        service_descs = request.POST.getlist('service_description[]')

        for i in range(len(service_names)):
            if service_names[i]:
                Service.objects.create(
                    agreement=agreement,
                    name=service_names[i],
                    service_type=service_types[i] if i < len(service_types) else 'monthly',
                    charge=service_charges[i] if i < len(service_charges) else 0,
                    description=service_descs[i] if i < len(service_descs) else '',
                )

        messages.success(request, 'Agreement added successfully.')
        return redirect('client_detail', pk=client_pk)

    return render(request, 'clients/agreement_form.html', {
        'client': client,
        'profile': profile,
        'service_types': Service._meta.get_field('service_type').choices
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
        agreement.save()

        # Update services
        agreement.services.all().delete()
        service_names = request.POST.getlist('service_name[]')
        service_types = request.POST.getlist('service_type[]')
        service_charges = request.POST.getlist('service_charge[]')
        service_descs = request.POST.getlist('service_description[]')

        for i in range(len(service_names)):
            if service_names[i]:
                Service.objects.create(
                    agreement=agreement,
                    name=service_names[i],
                    service_type=service_types[i] if i < len(service_types) else 'monthly',
                    charge=service_charges[i] if i < len(service_charges) else 0,
                    description=service_descs[i] if i < len(service_descs) else '',
                )

        messages.success(request, 'Agreement updated successfully.')
        return redirect('client_detail', pk=client.pk)

    return render(request, 'clients/agreement_form.html', {
        'client': client,
        'agreement': agreement,
        'profile': profile,
        'service_types': Service._meta.get_field('service_type').choices
    })
