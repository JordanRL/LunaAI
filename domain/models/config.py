from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class DebugLevel(Enum):
    """
    Debug verbosity levels.
    """
    NONE = "none"           # No debug output
    MINIMAL = "minimal"     # Basic info only (agent transitions, errors)
    STANDARD = "standard"   # Normal debug info (content snippets, stats)
    VERBOSE = "verbose"     # Detailed output (routing paths, content previews)
    TRACE = "trace"         # Full trace (message contents, execution flow)

@dataclass
class AppConfig:
    """
    Application configuration.
    
    Attributes:
        default_model: Default model to use
        chroma_db_path: Path to ChromaDB storage
        show_inner_thoughts: Whether to display Luna's inner thoughts
        log_inner_thoughts: Whether to log inner thoughts to file
        inner_thoughts_log_path: Path for logging inner thoughts
        debug_level: Current debug level
    """
    default_model: str = "claude-3-7-sonnet-latest" 
    chroma_db_path: str = "chroma_db"
    show_inner_thoughts: bool = True
    log_inner_thoughts: bool = False
    inner_thoughts_log_path: str = "logs/luna_debug.log"
    debug_level: DebugLevel = DebugLevel.NONE

@dataclass
class APIKeys:
    """
    API keys for external services.
    
    Attributes:
        anthropic_api_key: Anthropic API key
        openrouter_api_key: OpenRouter API key
    """
    anthropic_api_key: str = ""
    openrouter_api_key: str = ""

@dataclass
class EmotionalDefaults:
    """
    Default emotional state configuration.
    
    Attributes:
        baseline_pleasure: Baseline pleasure level (0.0-1.0)
        baseline_arousal: Baseline arousal level (0.0-1.0)
        baseline_dominance: Baseline dominance level (0.0-1.0)
        decay_rate: Rate of emotional decay per interaction
    """
    baseline_pleasure: float = 0.60
    baseline_arousal: float = 0.55
    baseline_dominance: float = 0.65
    decay_rate: float = 0.10

@dataclass
class ConversationDefaults:
    """
    Default conversation configuration.
    
    Attributes:
        max_history: Maximum messages to keep in history
        min_intact_messages: Minimum number of recent messages to keep intact
        summarize_after_messages: Create summaries after this many new messages
        summary_token_budget: Maximum tokens to use for summary generation
        auto_summarize: Whether to automatically summarize during message addition
    """
    max_history: int = 50
    min_intact_messages: int = 16
    summarize_after_messages: int = 10
    summary_token_budget: int = 4000
    auto_summarize: bool = True

@dataclass
class LunaMemoriesIndexSchema:
    """
    Default schema for Luna's memory elastic search index.

    Attributes:
        index_name: Name of the index
        mappings: Type mappings for the index
    """
    index_name: str = "luna_memories"
    mappings: Dict[str, Any] = field(default_factory=lambda: {
        "properties": {
            # Common Fields
            "content": {
                "type": "text",
                "analyzer": "memory_analyzer",
                "fields": {
                    "keyword": {"type": "keyword", "ignore_above": 256},
                }
            },
            "memory_type": {"type": "keyword"},
            "importance": {"type": "integer"},
            "timestamp": {"type": "date"},
            "last_accessed": {"type": "date"},
            "user_id": {"type": "keyword"},
            "keywords": {"type": "text", "analyzer": "memory_analyzer", "fields": {"raw": {"type": "keyword"}}},

            ## Common Fields - Emotion Fields
            "emotion_pleasure": {"type": "float"},
            "emotion_arousal": {"type": "float"},
            "emotion_dominance": {"type": "float"},

            # Episodic Fields
            "context": {
                "type": "text",
                "analyzer": "memory_analyzer",
                "fields": {
                    "keyword": {"type": "keyword", "ignore_above": 256},
                }
            },
            "participants": {
                "type": "text",
                "analyzer": "memory_analyzer",
                "fields": {
                    "keyword": {"type": "keyword", "ignore_above": 256},
                }
            },

            # Semantic Fields
            "certainty": {"type": "float"},
            "verifiability": {"type": "float"},
            "domain": {"type": "keyword"},
            "source": {"type": "keyword"},
            "source_reliability": {"type": "float"},

            # Emotional Fields
            "trigger": {"type": "text", "analyzer": "memory_analyzer", "fields": {"raw": {"type": "keyword"}}},
            "event_pleasure": {"type": "float"},
            "event_arousal": {"type": "float"},
            "event_dominance": {"type": "float"},

            # Relationship Fields
            "relationship_type": {"type": "keyword"},
            "closeness": {"type": "float"},
            "trust": {"type": "float"},
            "appreciation": {"type": "float"},
            "shared_experiences": {"type": "text", "analyzer": "memory_analyzer"},
            "connection_points": {"type": "text", "analyzer": "memory_analyzer"},
            "inside_references": {"type": "text", "analyzer": "memory_analyzer"},
        },
        "dynamic_templates": [
            {
                "strings_as_keywords": {
                    "match_mapping_type": "string",
                    "mapping": {
                        "type": "text",
                        "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}
                    }
                }
            }
        ]
    })
    settings: Dict[str, Any] = field(default_factory=lambda: {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "memory_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "stop", "snowball"]
                }
            }
        }
    })