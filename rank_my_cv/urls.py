from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.analyzer.urls')),
    path('auth/', include('apps.accounts.urls')),
    path('jobs/', include('apps.jobs.urls')),
]
