from django.urls import path
from .views import (
    NetworkCommandAPIView,
    MeAPIView,
    DeviceLocationAPIView,
    DeviceStatusAPIView,
    DeviceHealthAPIView,
    HealthzAPIView,
    MemoryStatsAPIView,
    DeviceListAPIView,
    VLANQuickCreateAPIView,
    DeviceBackupAPIView,
    BackupDetailsAPIView,
    DeviceManagementAPIView,
)

urlpatterns = [
    path("network-command/", NetworkCommandAPIView.as_view(), name="network-command"),
    path("auth/me/", MeAPIView.as_view(), name="me"),
    path("device-locations/", DeviceLocationAPIView.as_view(), name="device-locations"),
    path("device-status/", DeviceStatusAPIView.as_view(), name="device-status"),
    path("device-health/", DeviceHealthAPIView.as_view(), name="device-health"),
    path("devices/", DeviceListAPIView.as_view(), name="devices"),
    path("vlan/create/", VLANQuickCreateAPIView.as_view(), name="vlan-quick-create"),
    path("healthz/", HealthzAPIView.as_view(), name="healthz"),
    path("memory/stats/", MemoryStatsAPIView.as_view(), name="memory-stats"),
    # Device Backup & Management
    path("backup/", DeviceBackupAPIView.as_view(), name="device-backup"),
    path("backup/<str:backup_file>/", BackupDetailsAPIView.as_view(), name="backup-details"),
    path("device-management/", DeviceManagementAPIView.as_view(), name="device-management"),
]
