from django.contrib import admin
from django.urls import path, include

admin.site.site_header = "Genesis BillSoft Administration"
admin.site.site_title = "Genesis BillSoft Administration"
admin.site.index_title = "Genesis BillSoft Administration"
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('clients/', include('clients.urls')),
    path('billing/', include('billing.urls')),
    path('reports/', include('reports.urls')),
    path('dashboard/', include('billing_system.dashboard_urls')),
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
