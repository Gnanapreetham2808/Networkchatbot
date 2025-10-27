"""DRF serializers for vlan_agent (as specified)."""
from __future__ import annotations

from rest_framework import serializers
from .models import VLANIntent


class VLANIntentSerializer(serializers.ModelSerializer):
    class Meta:
        model = VLANIntent
        fields = "__all__"
