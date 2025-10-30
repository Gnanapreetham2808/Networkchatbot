"""
Django management command to test and manage chatbot memory.

Usage:
    python manage.py memory_test
    python manage.py memory_test --session-id abc-123
    python manage.py memory_test --clear-all
    python manage.py memory_test --stats
"""
from django.core.management.base import BaseCommand
from chatbot.models import Conversation, Message
from chatbot.memory_manager import get_memory_manager, clear_memory_cache
import uuid


class Command(BaseCommand):
    help = 'Test and manage chatbot memory functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--session-id',
            type=str,
            help='Test specific session ID',
        )
        parser.add_argument(
            '--clear-all',
            action='store_true',
            help='Clear all memory caches',
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Show memory statistics for all sessions',
        )
        parser.add_argument(
            '--create-test',
            action='store_true',
            help='Create a test conversation',
        )

    def handle(self, *args, **options):
        if options['clear_all']:
            self.clear_all_memory()
        elif options['stats']:
            self.show_stats()
        elif options['create_test']:
            self.create_test_conversation()
        elif options['session_id']:
            self.test_session(options['session_id'])
        else:
            self.run_default_test()

    def clear_all_memory(self):
        """Clear all memory caches."""
        clear_memory_cache()
        self.stdout.write(self.style.SUCCESS('✓ All memory caches cleared'))

    def show_stats(self):
        """Show memory statistics for all active conversations."""
        self.stdout.write(self.style.HTTP_INFO('\n=== Memory Statistics ===\n'))
        
        conversations = Conversation.objects.all().order_by('-updated_at')[:10]
        
        if not conversations:
            self.stdout.write(self.style.WARNING('No conversations found'))
            return
        
        self.stdout.write(f"{'Session ID':<40} {'Messages':<10} {'Device':<15} {'Last Active'}")
        self.stdout.write('-' * 90)
        
        for conv in conversations:
            msg_count = conv.messages.count()
            device = conv.device_alias or 'N/A'
            last_active = conv.updated_at.strftime('%Y-%m-%d %H:%M')
            
            # Get memory stats
            memory_mgr = get_memory_manager(str(conv.id))
            mem_stats = memory_mgr.get_memory_stats()
            mem_count = mem_stats.get('message_count', 0)
            
            status = '✓' if mem_stats.get('enabled') else '✗'
            
            self.stdout.write(
                f"{str(conv.id):<40} {msg_count:<10} {device:<15} {last_active} {status} (mem:{mem_count})"
            )
        
        self.stdout.write(f"\nTotal conversations: {conversations.count()}")

    def create_test_conversation(self):
        """Create a test conversation with sample messages."""
        conv = Conversation.objects.create()
        session_id = str(conv.id)
        
        # Create sample messages
        sample_messages = [
            ("user", "Show interfaces on London switch"),
            ("assistant", "Executed: show interfaces"),
            ("user", "What's the status?"),
            ("assistant", "Executed: show interface status"),
            ("user", "Show VLANs"),
            ("assistant", "Executed: show vlan"),
        ]
        
        for role, content in sample_messages:
            Message.objects.create(
                conversation=conv,
                role=role,
                content=content
            )
        
        # Update conversation
        conv.device_alias = "UKLONB10C01"
        conv.device_host = "192.168.30.1"
        conv.save()
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Test conversation created'))
        self.stdout.write(f"Session ID: {session_id}")
        self.stdout.write(f"Messages: {len(sample_messages)}")
        
        # Test memory loading
        memory_mgr = get_memory_manager(session_id)
        memory_mgr.load_from_django_messages(conv.messages.all())
        
        stats = memory_mgr.get_memory_stats()
        self.stdout.write(f"Memory loaded: {stats.get('message_count')} messages")
        self.stdout.write(f"Memory type: {stats.get('memory_type')}")

    def test_session(self, session_id):
        """Test memory functionality for a specific session."""
        self.stdout.write(self.style.HTTP_INFO(f'\n=== Testing Session: {session_id} ===\n'))
        
        try:
            conv = Conversation.objects.get(id=session_id)
        except Conversation.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'✗ Session {session_id} not found'))
            return
        
        # Show conversation details
        self.stdout.write(f"Device: {conv.device_alias or 'N/A'}")
        self.stdout.write(f"Host: {conv.device_host or 'N/A'}")
        self.stdout.write(f"Last command: {conv.last_command or 'N/A'}")
        self.stdout.write(f"Updated: {conv.updated_at}")
        
        # Show messages
        messages = conv.messages.all()
        self.stdout.write(f"\nMessages in DB: {messages.count()}")
        
        for i, msg in enumerate(messages[:5], 1):
            role_emoji = "👤" if msg.role == "user" else "🤖"
            self.stdout.write(f"  {i}. {role_emoji} {msg.role}: {msg.content[:60]}...")
        
        if messages.count() > 5:
            self.stdout.write(f"  ... and {messages.count() - 5} more")
        
        # Test memory manager
        self.stdout.write(self.style.HTTP_INFO('\n--- Memory Manager ---'))
        
        memory_mgr = get_memory_manager(session_id)
        
        if not memory_mgr.is_enabled():
            self.stdout.write(self.style.WARNING('✗ Memory manager not enabled (LangChain not installed?)'))
            return
        
        # Load messages
        memory_mgr.load_from_django_messages(messages)
        
        # Show stats
        stats = memory_mgr.get_memory_stats()
        self.stdout.write(f"Enabled: {stats.get('enabled')}")
        self.stdout.write(f"Type: {stats.get('memory_type')}")
        self.stdout.write(f"Messages in memory: {stats.get('message_count')}")
        self.stdout.write(f"Window size: {stats.get('window_size') or 'N/A'}")
        
        # Show context
        context = memory_mgr.get_context()
        if context:
            self.stdout.write(self.style.HTTP_INFO('\n--- Context Preview ---'))
            lines = context.split('\n')[:6]
            for line in lines:
                self.stdout.write(f"  {line}")
            if len(context.split('\n')) > 6:
                self.stdout.write("  ...")
        
        self.stdout.write(self.style.SUCCESS('\n✓ Memory test completed'))

    def run_default_test(self):
        """Run default memory functionality test."""
        self.stdout.write(self.style.HTTP_INFO('\n=== Chatbot Memory Test ===\n'))
        
        # Check if LangChain is available
        try:
            from langchain.memory import ConversationBufferMemory
            self.stdout.write(self.style.SUCCESS('✓ LangChain installed'))
        except ImportError:
            self.stdout.write(self.style.ERROR('✗ LangChain not installed'))
            self.stdout.write('\nInstall with: pip install langchain langchain-huggingface')
            return
        
        # Create test session
        self.stdout.write('\n1. Creating test conversation...')
        conv = Conversation.objects.create()
        session_id = str(conv.id)
        self.stdout.write(self.style.SUCCESS(f'   ✓ Session: {session_id}'))
        
        # Add test messages
        self.stdout.write('\n2. Adding test messages...')
        test_messages = [
            ("user", "Show interfaces on Aruba switch"),
            ("assistant", "Executed: show interfaces"),
            ("user", "What about VLANs?"),
            ("assistant", "Executed: show vlan"),
        ]
        
        for role, content in test_messages:
            Message.objects.create(conversation=conv, role=role, content=content)
        
        self.stdout.write(self.style.SUCCESS(f'   ✓ Added {len(test_messages)} messages'))
        
        # Test memory manager
        self.stdout.write('\n3. Testing memory manager...')
        memory_mgr = get_memory_manager(session_id)
        
        if not memory_mgr.is_enabled():
            self.stdout.write(self.style.ERROR('   ✗ Memory manager failed to initialize'))
            return
        
        self.stdout.write(self.style.SUCCESS('   ✓ Memory manager initialized'))
        
        # Load messages
        self.stdout.write('\n4. Loading messages into memory...')
        memory_mgr.load_from_django_messages(conv.messages.all())
        
        stats = memory_mgr.get_memory_stats()
        self.stdout.write(self.style.SUCCESS(f'   ✓ Loaded {stats["message_count"]} messages'))
        self.stdout.write(f'   Memory type: {stats["memory_type"]}')
        
        # Show context
        self.stdout.write('\n5. Retrieving context...')
        context = memory_mgr.get_context()
        if context:
            self.stdout.write(self.style.SUCCESS('   ✓ Context retrieved:'))
            for line in context.split('\n'):
                self.stdout.write(f'      {line}')
        
        # Test adding new messages
        self.stdout.write('\n6. Testing add message...')
        memory_mgr.add_user_message("Show running config")
        memory_mgr.add_ai_message("Executed: show running-config")
        
        new_stats = memory_mgr.get_memory_stats()
        self.stdout.write(self.style.SUCCESS(f'   ✓ Memory now has {new_stats["message_count"]} messages'))
        
        # Cleanup
        self.stdout.write('\n7. Cleaning up test data...')
        conv.delete()
        clear_memory_cache()
        self.stdout.write(self.style.SUCCESS('   ✓ Test data removed'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ All tests passed! Memory management is working.\n'))
