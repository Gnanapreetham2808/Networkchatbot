"""
Intent Recognition System for Network Automation

Provides a scalable pattern-matching system for detecting configuration intents
in natural language queries. Supports multiple automation workflows beyond just VLANs.

Architecture:
- Intent patterns defined in configuration
- Priority-based matching
- Extensible for future features
- Backend validation before execution
"""
from __future__ import annotations

import re
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Intent:
    """Represents a detected user intent for network automation."""
    name: str
    category: str
    confidence: float
    params: Dict[str, Any]
    requires_approval: bool
    description: str


class IntentRecognizer:
    """
    Recognizes configuration intents from natural language queries.
    
    Supports multiple automation workflows:
    - VLAN management (create, modify, delete)
    - Interface configuration
    - Routing configuration  
    - ACL management
    - QoS policies
    - And more...
    """
    
    # Intent patterns organized by category
    INTENT_PATTERNS = {
        # VLAN Management
        'vlan_create': {
            'category': 'vlan',
            'patterns': [
                r'\b(create|add|new|make)\s+(a\s+)?vlan\b',
                r'\bvlan\s+(create|add|new)\b',
                r'\bconfigure\s+vlan\b',
            ],
            'requires_approval': True,
            'description': 'Create or configure VLANs',
            'param_extractors': {
                'vlan_id': r'vlan\s+(\d+)',
                'vlan_name': r'(?:name|called)\s+(["\']?)(\w+)\1',
            }
        },
        'vlan_delete': {
            'category': 'vlan',
            'patterns': [
                r'\b(delete|remove|destroy)\s+(the\s+)?vlan\b',
                r'\bvlan\s+(delete|remove)\b',
                r'\bno\s+vlan\b',
            ],
            'requires_approval': True,
            'description': 'Delete VLAN',
            'param_extractors': {
                'vlan_id': r'vlan\s+(\d+)',
            }
        },
        'vlan_modify': {
            'category': 'vlan',
            'patterns': [
                r'\b(modify|change|update|edit)\s+(the\s+)?vlan\b',
                r'\bvlan\s+(modify|change|update)\b',
            ],
            'requires_approval': True,
            'description': 'Modify VLAN configuration',
            'param_extractors': {
                'vlan_id': r'vlan\s+(\d+)',
                'new_name': r'(?:to|name)\s+(["\']?)(\w+)\1',
            }
        },
        
        # Interface Configuration
        'interface_configure': {
            'category': 'interface',
            'patterns': [
                r'\b(configure|set up|setup)\s+(the\s+)?(interface|port)\b',
                r'\binterface\s+(configure|config|setup)\b',
                r'\b(enable|disable|shutdown|no shutdown)\s+(interface|port)\b',
            ],
            'requires_approval': True,
            'description': 'Configure network interface',
            'param_extractors': {
                'interface_name': r'(?:interface|port)\s+([\w/\.-]+)',
                'action': r'\b(enable|disable|shutdown|no shutdown)\b',
                'description': r'description\s+(["\']?)([^"\'"]+)\1',
            }
        },
        'interface_assign_vlan': {
            'category': 'interface',
            'patterns': [
                r'\b(assign|add|put|place)\s+(?:interface|port).*?\bto\s+vlan\b',
                r'\bvlan\s+\d+.*?(?:interface|port)\b',
                r'\b(access|trunk)\s+vlan\b',
            ],
            'requires_approval': True,
            'description': 'Assign interface to VLAN',
            'param_extractors': {
                'interface_name': r'(?:interface|port)\s+([\w/\.-]+)',
                'vlan_id': r'vlan\s+(\d+)',
                'mode': r'\b(access|trunk)\b',
            }
        },
        
        # Routing Configuration
        'route_add': {
            'category': 'routing',
            'patterns': [
                r'\b(add|create|configure)\s+(a\s+)?(?:static\s+)?route\b',
                r'\broute\s+(add|create)\b',
                r'\bip\s+route\b',
            ],
            'requires_approval': True,
            'description': 'Add static route',
            'param_extractors': {
                'destination': r'(?:to|destination)\s+([\d\.\/]+)',
                'next_hop': r'(?:via|gateway|next-hop)\s+([\d\.]+)',
            }
        },
        'route_delete': {
            'category': 'routing',
            'patterns': [
                r'\b(remove|delete)\s+(the\s+)?route\b',
                r'\bno\s+ip\s+route\b',
            ],
            'requires_approval': True,
            'description': 'Delete static route',
            'param_extractors': {
                'destination': r'(?:to|destination)\s+([\d\.\/]+)',
            }
        },
        
        # ACL Management
        'acl_create': {
            'category': 'acl',
            'patterns': [
                r'\b(create|add|configure)\s+(?:an?\s+)?(?:access\s+)?(?:list|acl)\b',
                r'\bacl\s+(create|add|new)\b',
                r'\baccess-list\b',
            ],
            'requires_approval': True,
            'description': 'Create access control list',
            'param_extractors': {
                'acl_number': r'(?:acl|list)\s+(\d+)',
                'acl_name': r'(?:acl|list)\s+(?:named?\s+)?(["\']?)(\w+)\1',
            }
        },
        'acl_apply': {
            'category': 'acl',
            'patterns': [
                r'\b(apply|attach|bind)\s+acl\b',
                r'\bacl.*?(?:to|on)\s+(?:interface|port)\b',
            ],
            'requires_approval': True,
            'description': 'Apply ACL to interface',
            'param_extractors': {
                'acl_name': r'acl\s+(["\']?)(\w+)\1',
                'interface': r'(?:interface|port)\s+([\w/\.-]+)',
                'direction': r'\b(in|out|inbound|outbound)\b',
            }
        },
        
        # Device Management
        'device_backup': {
            'category': 'management',
            'patterns': [
                r'\b(backup|save|export)\s+(?:the\s+)?(?:config|configuration)\b',
                r'\bcopy\s+running-config\b',
            ],
            'requires_approval': False,  # Read operation
            'description': 'Backup device configuration',
            'param_extractors': {}
        },
        'device_reboot': {
            'category': 'management',
            'patterns': [
                r'\b(reboot|restart|reload)\s+(?:the\s+)?(?:device|switch|router)\b',
            ],
            'requires_approval': True,
            'description': 'Reboot network device',
            'param_extractors': {
                'confirm': r'\bconfirm(?:ed)?\b',
            }
        },
    }
    
    def __init__(self):
        """Initialize the intent recognizer with compiled patterns."""
        self._compiled_patterns = {}
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Pre-compile all regex patterns for performance."""
        for intent_name, intent_config in self.INTENT_PATTERNS.items():
            compiled = []
            for pattern in intent_config['patterns']:
                try:
                    compiled.append(re.compile(pattern, re.IGNORECASE))
                except re.error as e:
                    logger.error(f"Invalid regex pattern for {intent_name}: {pattern} - {e}")
            self._compiled_patterns[intent_name] = compiled
    
    def recognize(self, query: str) -> Optional[Intent]:
        """
        Recognize intent from natural language query.
        
        Args:
            query: User's natural language query
            
        Returns:
            Intent object if matched, None otherwise
        """
        if not query or not query.strip():
            return None
        
        query = query.strip()
        best_match = None
        best_confidence = 0.0
        
        # Try to match against all intent patterns
        for intent_name, compiled_patterns in self._compiled_patterns.items():
            for pattern in compiled_patterns:
                match = pattern.search(query)
                if match:
                    # Calculate confidence based on match quality
                    confidence = self._calculate_confidence(query, match)
                    
                    if confidence > best_confidence:
                        config = self.INTENT_PATTERNS[intent_name]
                        
                        # Extract parameters
                        params = self._extract_params(query, config.get('param_extractors', {}))
                        
                        best_match = Intent(
                            name=intent_name,
                            category=config['category'],
                            confidence=confidence,
                            params=params,
                            requires_approval=config['requires_approval'],
                            description=config['description']
                        )
                        best_confidence = confidence
        
        return best_match
    
    def _calculate_confidence(self, query: str, match: re.Match) -> float:
        """
        Calculate confidence score for a pattern match.
        
        Factors:
        - Match coverage (how much of query is matched)
        - Match position (earlier is better)
        - Exact keyword matches
        """
        # Base confidence
        confidence = 0.7
        
        # Boost if match covers significant portion of query
        match_length = len(match.group(0))
        query_length = len(query)
        coverage = match_length / query_length
        confidence += coverage * 0.2
        
        # Boost if match is at beginning of query
        if match.start() == 0:
            confidence += 0.1
        
        # Cap at 1.0
        return min(confidence, 1.0)
    
    def _extract_params(self, query: str, extractors: Dict[str, str]) -> Dict[str, Any]:
        """
        Extract parameters from query using configured extractors.
        
        Args:
            query: User's query
            extractors: Dict of param_name -> regex_pattern
            
        Returns:
            Dict of extracted parameters
        """
        params = {}
        
        for param_name, pattern in extractors.items():
            try:
                regex = re.compile(pattern, re.IGNORECASE)
                match = regex.search(query)
                if match:
                    # Get the last captured group (most specific)
                    value = match.group(match.lastindex or 1)
                    params[param_name] = value.strip()
            except (re.error, IndexError) as e:
                logger.debug(f"Failed to extract {param_name}: {e}")
        
        return params
    
    def get_intents_by_category(self, category: str) -> List[str]:
        """Get all intent names for a specific category."""
        return [
            name for name, config in self.INTENT_PATTERNS.items()
            if config['category'] == category
        ]
    
    def get_categories(self) -> List[str]:
        """Get all available intent categories."""
        categories = set()
        for config in self.INTENT_PATTERNS.values():
            categories.add(config['category'])
        return sorted(categories)
    
    def is_configuration_intent(self, intent_name: str) -> bool:
        """Check if an intent requires configuration changes."""
        config = self.INTENT_PATTERNS.get(intent_name)
        return config['requires_approval'] if config else False


# Singleton instance
_recognizer_instance: Optional[IntentRecognizer] = None


def get_intent_recognizer() -> IntentRecognizer:
    """Get or create the global intent recognizer instance."""
    global _recognizer_instance
    if _recognizer_instance is None:
        _recognizer_instance = IntentRecognizer()
    return _recognizer_instance


def recognize_intent(query: str) -> Optional[Intent]:
    """
    Convenience function to recognize intent from query.
    
    Usage:
        intent = recognize_intent("create vlan 100 named engineering")
        if intent:
            print(f"Intent: {intent.name}")
            print(f"Category: {intent.category}")
            print(f"Params: {intent.params}")
    """
    recognizer = get_intent_recognizer()
    return recognizer.recognize(query)
