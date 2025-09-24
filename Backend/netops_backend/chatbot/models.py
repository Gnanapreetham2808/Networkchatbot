from django.db import models
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
