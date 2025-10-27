from django.apps import AppConfig


class VlanAgentConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "netops_backend.vlan_agent"
    verbose_name = "VLAN Agent"
