from django.db import models
from django.utils import timezone
import uuid


class Conversation(models.Model):
	"""A chat session tracking device selection and context across turns."""
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	# Last resolved device alias (e.g., UKLONB1SW2) & host snapshot
	device_alias = models.CharField(max_length=64, blank=True, null=True)
	device_host = models.CharField(max_length=64, blank=True, null=True)
	# Last executed CLI command (normalized)
	last_command = models.TextField(blank=True, null=True)
	# Arbitrary JSON-ish context (store compact serialized dict)
	context_blob = models.TextField(blank=True, null=True)

	def __str__(self):  # pragma: no cover
		return f"Conversation {self.id} ({self.device_alias or 'no-device'})"


class Message(models.Model):
	ROLE_USER = "user"
	ROLE_ASSISTANT = "assistant"
	ROLE_SYSTEM = "system"
	ROLE_CHOICES = [
		(ROLE_USER, "User"),
		(ROLE_ASSISTANT, "Assistant"),
		(ROLE_SYSTEM, "System"),
	]

	id = models.BigAutoField(primary_key=True)
	conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
	role = models.CharField(max_length=16, choices=ROLE_CHOICES)
	content = models.TextField()
	# Optional structured attachments (e.g., raw CLI output) stored serialized
	meta = models.TextField(blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["created_at", "id"]

	def __str__(self):  # pragma: no cover
		return f"Msg[{self.role}] {self.content[:40]}"


class DeviceHealth(models.Model):
	"""Stores CPU samples and optional topology metadata per device alias."""
	id = models.BigAutoField(primary_key=True)
	alias = models.CharField(max_length=64, db_index=True)
	cpu_pct = models.FloatField()
	raw = models.TextField(blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		indexes = [models.Index(fields=["alias", "created_at"])]
		ordering = ["-created_at", "-id"]


class HealthAlert(models.Model):
	"""Alert records for CPU spikes or loop detection."""
	SEVERITY_CHOICES = (
		("info", "Info"),
		("warn", "Warn"),
		("crit", "Critical"),
	)
	CATEGORY_CHOICES = (
		("cpu", "CPU"),
		("loop", "Loop"),
	)

	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	alias = models.CharField(max_length=64, db_index=True)
	category = models.CharField(max_length=16, choices=CATEGORY_CHOICES)
	severity = models.CharField(max_length=8, choices=SEVERITY_CHOICES, default="warn")
	message = models.TextField()
	meta = models.TextField(blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	cleared_at = models.DateTimeField(blank=True, null=True)

	class Meta:
		indexes = [models.Index(fields=["alias", "category", "created_at"])]
		ordering = ["-created_at"]
