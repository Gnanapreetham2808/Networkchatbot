# Memory Management Quick Reference

## Installation

```powershell
# Option 1: Use installation script
cd C:\Networkchatbot\Backend
.\install_memory.ps1

# Option 2: Manual installation
pip install langchain==0.3.7 langchain-huggingface==0.1.2 langchain-community==0.3.7 sentence-transformers==3.3.1
```

## Configuration (.env)

```bash
# Memory Type: buffer | window | summary
CHATBOT_MEMORY_TYPE=window

# Window Size (for window mode)
CHATBOT_MEMORY_WINDOW_SIZE=10

# Max tokens (for summary mode)
CHATBOT_MEMORY_MAX_TOKEN_LIMIT=2000
```

## Management Commands

### Test Memory Functionality
```bash
# Run default tests
python manage.py memory_test

# Test specific session
python manage.py memory_test --session-id abc-123-def-456

# Show stats for all sessions
python manage.py memory_test --stats

# Create test conversation
python manage.py memory_test --create-test

# Clear all memory caches
python manage.py memory_test --clear-all
```

## API Endpoints

### Get Memory Statistics
```bash
GET /api/nlp/memory/stats/?session_id=abc-123-def-456
```

**Response:**
```json
{
  "enabled": true,
  "memory_type": "window",
  "message_count": 8,
  "window_size": 10,
  "conversation_id": "abc-123-def-456",
  "db_message_count": 15,
  "device_alias": "UKLONB10C01",
  "device_host": "192.168.30.1",
  "last_command": "show interfaces",
  "updated_at": "2025-10-29T10:30:00Z",
  "last_messages": [
    {"role": "user", "content": "Show interfaces"},
    {"role": "assistant", "content": "Executed: show interfaces"}
  ]
}
```

### Clear Session Memory
```bash
DELETE /api/nlp/memory/stats/?session_id=abc-123-def-456
```

**Response:**
```json
{
  "message": "Memory cleared",
  "session_id": "abc-123-def-456"
}
```

## Python API Usage

### Get Memory Manager
```python
from chatbot.memory_manager import get_memory_manager

# Get manager for a session
memory_mgr = get_memory_manager(session_id)

# Check if enabled
if memory_mgr.is_enabled():
    print("Memory is enabled")
```

### Add Messages
```python
# Add user message
memory_mgr.add_user_message("Show interfaces on London switch")

# Add AI response
memory_mgr.add_ai_message("Executed: show interfaces")
```

### Get Context
```python
# Get formatted conversation history
context = memory_mgr.get_context()
print(context)
# Output:
# User: Show interfaces on London switch
# Assistant: Executed: show interfaces
# User: What's the status?
# Assistant: Executed: show interface status
```

### Get Last Messages
```python
# Get last 5 messages
messages = memory_mgr.get_last_n_messages(5)

for msg in messages:
    print(f"{msg['role']}: {msg['content']}")
```

### Get Statistics
```python
stats = memory_mgr.get_memory_stats()
print(stats)
# {
#   'enabled': True,
#   'memory_type': 'window',
#   'message_count': 8,
#   'window_size': 10,
#   'conversation_id': 'abc-123'
# }
```

### Clear Memory
```python
memory_mgr.clear()
```

### Load from Django
```python
from chatbot.models import Conversation

conv = Conversation.objects.get(id=session_id)
messages = conv.messages.all()

# Load into memory
memory_mgr.load_from_django_messages(messages)
```

## Testing Examples

### Test 1: Basic Context
```python
# Create conversation
conv = Conversation.objects.create()
session_id = str(conv.id)

# Add messages
Message.objects.create(
    conversation=conv,
    role="user",
    content="Show interfaces on Aruba switch"
)
Message.objects.create(
    conversation=conv,
    role="assistant",
    content="Executed: show interfaces"
)

# Test memory
memory_mgr = get_memory_manager(session_id)
memory_mgr.load_from_django_messages(conv.messages.all())

# Verify
assert memory_mgr.get_memory_stats()['message_count'] == 2
print("✓ Context test passed")
```

### Test 2: Window Size
```python
# Create conversation with 20 messages
conv = Conversation.objects.create()

for i in range(10):
    Message.objects.create(conv=conv, role="user", content=f"Query {i}")
    Message.objects.create(conv=conv, role="assistant", content=f"Response {i}")

# Load with window size = 10
memory_mgr = get_memory_manager(str(conv.id))
memory_mgr.load_from_django_messages(conv.messages.all())

# Should only keep last 10
stats = memory_mgr.get_memory_stats()
assert stats['message_count'] == 10
print(f"✓ Window test passed (kept {stats['message_count']} of 20)")
```

### Test 3: Session Persistence
```python
# Session 1: Create and store messages
session_id = str(uuid.uuid4())
conv = Conversation.objects.create(id=session_id)

Message.objects.create(conv=conv, role="user", content="Test 1")
Message.objects.create(conv=conv, role="assistant", content="Response 1")

# Session 2: Reconnect and load
memory_mgr = get_memory_manager(session_id)
memory_mgr.load_from_django_messages(conv.messages.all())

# Should have loaded messages
assert memory_mgr.get_memory_stats()['message_count'] > 0
print("✓ Persistence test passed")
```

## Troubleshooting

### Check if LangChain is installed
```python
python -c "import langchain; print(langchain.__version__)"
```

### Verify memory is working
```bash
python manage.py memory_test
```

### Check session memory
```bash
curl "http://localhost:8000/api/nlp/memory/stats/?session_id=YOUR_SESSION_ID"
```

### View all conversations
```bash
python manage.py memory_test --stats
```

### Clear stuck memory
```bash
python manage.py memory_test --clear-all
```

## Performance Tips

### Optimize Window Size
```bash
# Small (faster, less context)
CHATBOT_MEMORY_WINDOW_SIZE=5

# Medium (balanced) - Recommended
CHATBOT_MEMORY_WINDOW_SIZE=10

# Large (slower, more context)
CHATBOT_MEMORY_WINDOW_SIZE=20
```

### Choose Right Memory Type
```bash
# For short chats
CHATBOT_MEMORY_TYPE=buffer

# For production (recommended)
CHATBOT_MEMORY_TYPE=window

# For very long sessions
CHATBOT_MEMORY_TYPE=summary  # (future feature)
```

### Limit Message Loading
```python
# Load only last 50 messages
messages = conv.messages.all()[:50]
memory_mgr.load_from_django_messages(messages)
```

## Common Issues

### Issue: Memory not persisting
**Solution:** Check if messages are being saved to DB
```python
conv = Conversation.objects.get(id=session_id)
print(f"Messages in DB: {conv.messages.count()}")
```

### Issue: LangChain import errors
**Solution:** Reinstall dependencies
```bash
pip install --upgrade langchain langchain-huggingface
```

### Issue: High memory usage
**Solution:** Reduce window size or clear old sessions
```bash
# Reduce window
CHATBOT_MEMORY_WINDOW_SIZE=5

# Or clear old sessions
python manage.py shell
>>> from chatbot.models import Conversation
>>> old = Conversation.objects.filter(updated_at__lt=datetime.now()-timedelta(days=7))
>>> old.delete()
```

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `CHATBOT_MEMORY_TYPE` | `window` | Memory type (buffer/window/summary) |
| `CHATBOT_MEMORY_WINDOW_SIZE` | `10` | Messages to keep in window mode |
| `CHATBOT_MEMORY_MAX_TOKEN_LIMIT` | `2000` | Max tokens for summary mode |

## Quick Start Checklist

- [ ] Install dependencies (`.\install_memory.ps1`)
- [ ] Configure `.env` file
- [ ] Restart backend server
- [ ] Run `python manage.py memory_test`
- [ ] Test with actual conversation
- [ ] Check memory stats API
- [ ] Monitor performance

## Next Steps

1. **Run Tests:** `python manage.py memory_test`
2. **Create Test Conversation:** `python manage.py memory_test --create-test`
3. **Check Stats:** `python manage.py memory_test --stats`
4. **Test API:** `curl http://localhost:8000/api/nlp/memory/stats/?session_id=SESSION_ID`

---

**For full documentation, see:** `MEMORY_MANAGEMENT.md`
