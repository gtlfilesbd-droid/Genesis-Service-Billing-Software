from django.core.management.base import BaseCommand

from billing.sync_auto_bills import sync_billing_queues


class Command(BaseCommand):
    help = 'Create missing bills for mature agreement periods and refresh auto-generated pending invoice dates.'

    def handle(self, *args, **options):
        sync_billing_queues()
        self.stdout.write(self.style.SUCCESS('Billing sync completed.'))
