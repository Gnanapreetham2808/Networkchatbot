"""Django models for vlan_agent (as specified)."""
from __future__ import annotations

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class VLANIntent(models.Model):
    vlan_id = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(4094)])
    name = models.CharField(max_length=64)
    scope = models.CharField(max_length=32, default="access")
    status = models.CharField(max_length=32, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("vlan_id", "scope")

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"VLAN {self.vlan_id} {self.name} @{self.scope} [{self.status}]"
