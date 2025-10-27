"""Tasks for vlan_agent.

No Celery dependency by default. If Celery is later added, these can be
refactored to @shared_task. For now, plain callables are provided.
"""
from __future__ import annotations

from typing import Any, Dict
from django.db import transaction
from .models import VLANIntent
from .nornir_driver import VLANOrchestrator


def plan_and_apply_vlan_intent(intent_id: int) -> Dict[str, Any]:
    """Plan and (stub) apply a VLAN intent.

    Returns a dict with status and notes. Replace with orchestration calls.
    """
    with transaction.atomic():
        intent = VLANIntent.objects.select_for_update().get(id=intent_id)
        orch = VLANOrchestrator()
        plan = orch.plan(intent)
        # In a real flow, require approval. For scaffold, we mark approved->applied.
        try:
            orch.apply(plan)
            intent.status = "APPLIED"
            intent.save(update_fields=["status", "updated_at"])
            return {"ok": True, "status": intent.status, "plan": plan}
        except Exception as e:  # pragma: no cover - placeholder
            intent.status = "FAILED"
            intent.save(update_fields=["status", "updated_at"])
            return {"ok": False, "error": str(e)}
