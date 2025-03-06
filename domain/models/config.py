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

@dataclass
class UserProfileIndexSchema:
    """
    Schema for user profiles in Elasticsearch.
    
    Attributes:
        index_name: Name of the index
        mappings: Type mappings for the index
    """
    index_name: str = "luna_user_profiles"
    mappings: Dict[str, Any] = field(default_factory=lambda: {
        "properties": {
            # User identification
            "user_id": {"type": "keyword"},
            "doc_type": {"type": "keyword"},  # profile or relationship
            
            # Biographical information
            "biographical": {
                "properties": {
                    "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "nickname": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "pronouns": {"type": "keyword"},
                    "age": {"type": "integer"},
                    "birthday": {"type": "text"},
                    "occupation": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "education": {
                        "properties": {
                            "level": {"type": "keyword"},
                            "field": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                            "institutions": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                        }
                    },
                    "languages": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "location": {
                        "properties": {
                            "country": {"type": "keyword"},
                            "region": {"type": "keyword"},
                            "city": {"type": "keyword"},
                            "timezone": {"type": "keyword"}
                        }
                    }
                }
            },
            
            # Personal context
            "personal_context": {
                "properties": {
                    "family": {
                        "type": "nested",
                        "properties": {
                            "relation": {"type": "keyword"},
                            "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                            "important_details": {"type": "text"}
                        }
                    },
                    "pets": {
                        "type": "nested",
                        "properties": {
                            "type": {"type": "keyword"},
                            "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                        }
                    },
                    "living_situation": {"type": "text"},
                    "major_life_events": {
                        "type": "nested",
                        "properties": {
                            "event": {"type": "text"},
                            "date": {"type": "text"},
                            "emotional_impact": {"type": "text"}
                        }
                    }
                }
            },
            
            # Preferences
            "preferences": {
                "properties": {
                    "topics": {
                        "properties": {
                            "interests": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                            "expertise_areas": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                            "learning_goals": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                        }
                    },
                    "media": {
                        "properties": {
                            "books": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                            "music": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                            "movies": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                            "games": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                        }
                    },
                    "food": {
                        "properties": {
                            "likes": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                            "dislikes": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                            "dietary_restrictions": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                        }
                    },
                    "aesthetic": {
                        "properties": {
                            "colors": {"type": "keyword"},
                            "styles": {"type": "keyword"}
                        }
                    },
                    "activities": {
                        "properties": {
                            "hobbies": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                            "exercise": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                            "social": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                        }
                    }
                }
            },
            
            # Behavioral patterns
            "behavioral_patterns": {
                "properties": {
                    "communication_style": {
                        "properties": {
                            "verbosity": {"type": "keyword"},
                            "formality": {"type": "keyword"},
                            "humor": {"type": "keyword"},
                            "expressiveness": {"type": "keyword"}
                        }
                    },
                    "interaction_patterns": {
                        "properties": {
                            "preferred_times": {"type": "keyword"},
                            "frequency": {"type": "keyword"},
                            "session_length": {"type": "keyword"},
                            "conversation_pacing": {"type": "keyword"}
                        }
                    },
                    "learning_style": {
                        "properties": {
                            "preferred_learning": {"type": "keyword"},
                            "explanation_preference": {"type": "keyword"},
                            "detail_level": {"type": "keyword"}
                        }
                    },
                    "decision_making": {
                        "properties": {
                            "approach": {"type": "keyword"},
                            "risk_attitude": {"type": "keyword"},
                            "influences": {"type": "keyword"}
                        }
                    }
                }
            },
            
            # Values and beliefs
            "values_and_beliefs": {
                "properties": {
                    "core_values": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "worldview": {
                        "properties": {
                            "political_leaning": {"type": "keyword"},
                            "philosophical_interests": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                            "spiritual_framework": {"type": "keyword"}
                        }
                    },
                    "cultural_background": {
                        "properties": {
                            "heritage": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                            "important_traditions": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                            "cultural_identities": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                        }
                    },
                    "ethics": {
                        "properties": {
                            "moral_foundations": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                            "causes": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                        }
                    }
                }
            },
            
            # Interaction metadata
            "interaction_meta": {
                "properties": {
                    "first_interaction": {"type": "date"},
                    "interaction_count": {"type": "integer"}
                }
            }
        }
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

@dataclass
class UserRelationshipIndexSchema:
    """
    Schema for user relationships in Elasticsearch.
    
    Attributes:
        index_name: Name of the index
        mappings: Type mappings for the index
    """
    index_name: str = "luna_user_relationships"
    mappings: Dict[str, Any] = field(default_factory=lambda: {
        "properties": {
            # User identification
            "user_id": {"type": "keyword"},
            "doc_type": {"type": "keyword"},  # profile or relationship
            
            # Relationship stage
            "relationship_stage": {
                "properties": {
                    "current_stage": {"type": "keyword"},
                    "time_in_stage": {"type": "text"},
                    "progression_notes": {"type": "text"},
                    "stage_history": {
                        "type": "nested",
                        "properties": {
                            "stage": {"type": "keyword"},
                            "started": {"type": "text"},
                            "ended": {"type": "text"}
                        }
                    }
                }
            },
            
            # Emotional dynamics
            "emotional_dynamics": {
                "properties": {
                    "luna_comfort_level": {"type": "integer"},
                    "trust_level": {"type": "keyword"},
                    "emotional_safety": {
                        "properties": {
                            "sensitive_topics": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                            "approach_carefully": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                            "avoid": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                        }
                    },
                    "emotional_resonance": {
                        "properties": {
                            "topics_with_positive_response": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                            "topics_with_deep_engagement": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                            "tension_points": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                        }
                    },
                    "luna_emotional_responses": {
                        "properties": {
                            "joy_triggers": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                            "pride_moments": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                            "challenge_areas": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                        }
                    }
                }
            },
            
            # Relationship history
            "relationship_history": {
                "properties": {
                    "key_moments": {
                        "type": "nested",
                        "properties": {
                            "event": {"type": "text"},
                            "date": {"type": "text"},
                            "significance": {"type": "text"},
                            "emotional_impact": {"type": "text"}
                        }
                    },
                    "inside_references": {
                        "type": "nested",
                        "properties": {
                            "reference": {"type": "text"},
                            "context": {"type": "text"},
                            "first_mentioned": {"type": "text"}
                        }
                    },
                    "recurring_themes": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "unresolved_threads": {
                        "type": "nested",
                        "properties": {
                            "topic": {"type": "text"},
                            "last_discussed": {"type": "text"},
                            "status": {"type": "text"}
                        }
                    }
                }
            },
            
            # Conversation patterns
            "conversation_patterns": {
                "properties": {
                    "successful_approaches": {"type": "object"},
                    "communication_adjustments": {
                        "type": "nested",
                        "properties": {
                            "area": {"type": "text"},
                            "adjustment": {"type": "text"},
                            "result": {"type": "text"}
                        }
                    },
                    "conversation_flow": {
                        "properties": {
                            "typical_openings": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                            "depth_progression": {"type": "text"},
                            "closing_patterns": {"type": "text"}
                        }
                    },
                    "special_interaction_notes": {"type": "text"}
                }
            },
            
            # Luna's subjective experience
            "luna_subjective_experience": {
                "properties": {
                    "connection_quality": {
                        "properties": {
                            "intellectual": {"type": "integer"},
                            "emotional": {"type": "integer"},
                            "creative": {"type": "integer"},
                            "overall": {"type": "integer"}
                        }
                    },
                    "growth_through_relationship": {
                        "type": "nested",
                        "properties": {
                            "area": {"type": "text"},
                            "insight": {"type": "text"},
                            "impact_on_luna": {"type": "text"}
                        }
                    },
                    "authenticity_level": {
                        "properties": {
                            "current_level": {"type": "keyword"},
                            "evolution": {"type": "text"},
                            "restricted_areas": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                        }
                    },
                    "relationship_reflections": {"type": "text"}
                }
            },
            
            # Intervention strategies
            "intervention_strategies": {
                "properties": {
                    "anxiety_response": {
                        "properties": {
                            "recognition_patterns": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                            "effective_approaches": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                            "backfire_risks": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                        }
                    },
                    "motivation_support": {
                        "properties": {
                            "effective_encouragement": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                            "accountability_preferences": {"type": "text"},
                            "celebration_style": {"type": "text"}
                        }
                    },
                    "conflict_resolution": {
                        "properties": {
                            "user_response_to_misunderstandings": {"type": "text"},
                            "repair_approaches": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                            "prevention_strategies": {"type": "text"}
                        }
                    }
                }
            }
        }
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