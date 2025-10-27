"""ViewSets for vlan_agent with an apply_intents action."""
from __future__ import annotations

from typing import Any, Dict, List

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import VLANIntent
from .serializers import VLANIntentSerializer
from .utils import validate_vlan_id_uniqueness, log_event, generate_vlan_intent_from_text
from .nornir_driver import deploy_vlan_to_switches, validate_vlan_propagation


class VLANIntentViewSet(viewsets.ModelViewSet):
    queryset = VLANIntent.objects.all()
    serializer_class = VLANIntentSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=["post"], url_path="apply-intents")
    def apply_intents(self, request, *args, **kwargs):
        """Apply all PENDING VLAN intents by deploying to switches.

        For each PENDING intent:
          - Build vlan_plan = {vlan_id, name, scope}
          - Call deploy_vlan_to_switches(vlan_plan)
          - If any device failed -> mark FAILED; if any created -> APPLIED;
            if all skipped -> APPLIED but include in "skipped" summary
        Returns JSON summary: {applied: [ids], failed: {id: reason}, skipped: [ids]}
        """
        pending = list(VLANIntent.objects.filter(status="PENDING").order_by("id"))
        if not pending:
            return Response({"applied": [], "failed": {}, "skipped": []}, status=status.HTTP_200_OK)

        # Optional: pre-validate uniqueness inside this batch for clearer errors
        _, uniqueness_errors = validate_vlan_id_uniqueness(pending)

        applied_ids: List[int] = []
        skipped_ids: List[int] = []
        failed_map: Dict[int, str] = {}

        for intent in pending:
            if intent.id in uniqueness_errors:
                failed_map[intent.vlan_id] = uniqueness_errors[intent.id]
                intent.status = "FAILED"
                intent.save(update_fields=["status", "updated_at"])
                log_event(
                    level=20,  # INFO
                    msg="VLAN intent failed uniqueness",
                    vlan_id=intent.vlan_id,
                    scope=intent.scope,
                    reason=uniqueness_errors[intent.id],
                )
                continue

            vlan_plan = {"vlan_id": intent.vlan_id, "name": intent.name, "scope": intent.scope}
            log_event(20, "Deploying VLAN plan", vlan_id=intent.vlan_id, scope=intent.scope)
            try:
                summary = deploy_vlan_to_switches(vlan_plan)
            except Exception as e:  # pragma: no cover
                failed_map[intent.vlan_id] = f"deployment error: {e}"
                intent.status = "FAILED"
                intent.save(update_fields=["status", "updated_at"])
                log_event(40, f"Deployment exception: {e}", vlan_id=intent.vlan_id, scope=intent.scope)
                continue

            vals = list(summary.values())
            any_failed = any(v == "failed" for v in vals)
            any_created = any(v == "created" for v in vals)
            all_skipped = vals and all(v == "skipped" for v in vals)

            if any_failed and not any_created:
                # Pure failure (or partial with no creation)
                reason = ", ".join(f"{k}:{v}" for k, v in summary.items() if v == "failed") or "failed"
                failed_map[intent.vlan_id] = reason
                intent.status = "FAILED"
                intent.save(update_fields=["status", "updated_at"])
                log_event(40, "VLAN deployment failed", vlan_id=intent.vlan_id, scope=intent.scope, summary=summary)
            else:
                # Treat created or all skipped as success
                if all_skipped:
                    skipped_ids.append(intent.vlan_id)
                    log_event(20, "VLAN already present on all devices (skipped)", vlan_id=intent.vlan_id, scope=intent.scope)
                else:
                    applied_ids.append(intent.vlan_id)
                    log_event(20, "VLAN created on one or more devices", vlan_id=intent.vlan_id, scope=intent.scope, summary=summary)
                intent.status = "APPLIED"
                intent.save(update_fields=["status", "updated_at"])

        return Response({
            "applied": applied_ids,
            "failed": failed_map,
            "skipped": skipped_ids,
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="validate")
    def validate(self, request, *args, **kwargs):
        """Validate VLAN propagation for this intent's vlan_id across devices."""
        intent = self.get_object()
        vlan_id = int(intent.vlan_id)

        # Start validation
        log_event(20, "Starting VLAN propagation validation", vlan_id=vlan_id, scope=intent.scope)
        try:
            results = validate_vlan_propagation(vlan_id)
        except Exception as e:  # pragma: no cover
            log_event(40, f"Validation exception: {e}", vlan_id=vlan_id, scope=intent.scope)
            return Response({"vlan_id": vlan_id, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        total = len(results)
        ok_count = sum(1 for v in results.values() if v == "ok")
        consistent = total > 0 and ok_count == total
        summary = f"{ok_count}/{total} devices consistent"

        if not consistent:
            log_event(40, "VLAN propagation inconsistent", vlan_id=vlan_id, scope=intent.scope, results=results)
        else:
            log_event(20, "VLAN propagation consistent", vlan_id=vlan_id, scope=intent.scope)

        return Response({
            "vlan_id": vlan_id,
            "results": results,
            "summary": summary,
            "consistent": consistent,
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="nlp")
    def nlp(self, request, *args, **kwargs):
        """Parse natural language to VLAN intent and create/update as PENDING.

        Body: {"command": "<text>"}
        Optional query param apply=1 to immediately deploy only this intent.
        """
        payload = request.data or {}
        cmd = str(payload.get("command", "")).strip()
        if not cmd:
            return Response({"error": "Missing 'command'"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            parsed = generate_vlan_intent_from_text(cmd)
        except Exception as e:
            log_event(40, f"NLP parse error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        vlan_id = parsed["vlan_id"]
        name = parsed["name"]
        scope = parsed.get("scope", "access")

        # Create or update intent
        obj, created = VLANIntent.objects.update_or_create(
            vlan_id=vlan_id,
            scope=scope,
            defaults={"name": name, "status": "PENDING"},
        )
        log_event(20, "VLAN intent upserted from NLP", vlan_id=vlan_id, scope=scope, status="PENDING")

        # Optional immediate apply: apply=1|true|yes
        apply_flag = str(request.query_params.get("apply", "0")).lower() in {"1", "true", "yes"}
        if apply_flag:
            try:
                summary = deploy_vlan_to_switches({"vlan_id": vlan_id, "name": name, "scope": scope})
                vals = list(summary.values())
                any_failed = any(v == "failed" for v in vals)
                any_created = any(v == "created" for v in vals)
                all_skipped = vals and all(v == "skipped" for v in vals)

                if any_failed and not any_created:
                    obj.status = "FAILED"
                    obj.save(update_fields=["status", "updated_at"])
                    log_event(40, "NLP-deploy failed", vlan_id=vlan_id, scope=scope, summary=summary)
                else:
                    obj.status = "APPLIED"
                    obj.save(update_fields=["status", "updated_at"])
                    log_event(20, "NLP-deploy success", vlan_id=vlan_id, scope=scope, summary=summary)
            except Exception as e:  # pragma: no cover
                obj.status = "FAILED"
                obj.save(update_fields=["status", "updated_at"])
                log_event(40, f"NLP-deploy exception: {e}", vlan_id=vlan_id, scope=scope)

        return Response({
            "parsed": {"vlan_id": vlan_id, "name": name, "scope": scope},
            "intent_id": obj.id,
            "status": "created" if created else "updated",
            "applied": obj.status == "APPLIED",
        }, status=status.HTTP_200_OK)
