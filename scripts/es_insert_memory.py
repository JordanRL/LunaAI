#!/usr/bin/env python
"""
Command-line utility for inserting a memory from a JSON file into Luna's Elasticsearch memory index.
"""

import argparse
import json
import sys
import traceback
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from adapters.elasticsearch_adapter import ElasticsearchAdapter
from domain.models.emotion import EmotionalState
from domain.models.memory import EmotionalMemory, EpisodicMemory, RelationshipMemory, SemanticMemory


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Insert a memory from a JSON file into Luna's Elasticsearch."
    )

    # Required arguments
    parser.add_argument("file", help="JSON file containing the memory data")

    # Optional arguments
    parser.add_argument(
        "--host",
        default="http://localhost:9200",
        help="Elasticsearch host URL (default: http://localhost:9200)",
    )
    parser.add_argument(
        "--index", default=None, help="Override the default Elasticsearch index name"
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild the index before inserting (WARNING: deletes existing memories)",
    )

    return parser.parse_args()


def create_memory_from_json(json_file):
    """Create a memory object from a JSON file."""
    try:
        with open(json_file, "r") as f:
            data = json.load(f)

        # Extract type
        memory_type = data.get("type") or data.get("memory_type", "episodic")

        # Create emotional state if provided
        emotion = None
        if "emotion" in data:
            emotion = EmotionalState(
                pleasure=data["emotion"].get("pleasure"),
                arousal=data["emotion"].get("arousal"),
                dominance=data["emotion"].get("dominance"),
            )

        # Common parameters
        common_args = {
            "content": data.get("content", ""),
            "importance": data.get("importance", 5),
            "user_id": data.get("user_id"),
            "keywords": data.get("keywords", []),
            "emotion": emotion,
        }

        # Create the appropriate memory type
        if memory_type == "episodic":
            return EpisodicMemory(
                **common_args,
                participants=data.get("participants", []),
                context=data.get("context", ""),
            )

        elif memory_type == "semantic":
            return SemanticMemory(
                **common_args,
                certainty=data.get("certainty", 0.5),
                verifiability=data.get("verifiability", 0.5),
                domain=data.get("domain", ""),
                source=data.get("source", ""),
            )

        elif memory_type == "emotional":
            # Use the provided emotion or default values
            if emotion:
                event_pleasure = emotion.pleasure if emotion.pleasure is not None else 0.0
                event_arousal = emotion.arousal if emotion.arousal is not None else 0.0
                event_dominance = emotion.dominance if emotion.dominance is not None else 0.0
            else:
                event_pleasure = data.get("event_pleasure", 0.0)
                event_arousal = data.get("event_arousal", 0.0)
                event_dominance = data.get("event_dominance", 0.0)

            return EmotionalMemory(
                **common_args,
                trigger=data.get("trigger", ""),
                event_pleasure=event_pleasure,
                event_arousal=event_arousal,
                event_dominance=event_dominance,
            )

        elif memory_type == "relationship":
            return RelationshipMemory(
                **common_args,
                relationship_type=data.get("relationship_type", ""),
                closeness=data.get("closeness", 0.5),
                trust=data.get("trust", 0.5),
                shared_experiences=data.get("shared_experiences", []),
            )

        else:
            raise ValueError(f"Invalid memory type: {memory_type}")

    except Exception as e:
        print(f"Error loading JSON file: {e}")
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point."""
    args = parse_arguments()

    try:
        # Create the Elasticsearch adapter
        es_adapter = ElasticsearchAdapter(
            host=args.host,
            memory_index_name=args.index or ElasticsearchAdapter.DEFAULT_MEMORY_INDEX,
            rebuild_indices=args.rebuild,
        )

        # Create memory object from JSON file
        memory = create_memory_from_json(args.file)

        # Store the memory
        response = es_adapter.store_memory(memory)

        if response and "_id" in response:
            memory_id = response["_id"]
            print(f"SUCCESS: Stored {memory.memory_type} memory with ID {memory_id}")
            print(f"Content: {memory.content[:100]}{'...' if len(memory.content) > 100 else ''}")
            print(f"Index: {es_adapter.memory_index_name}")
            return 0
        else:
            print(f"ERROR: Failed to store memory. Response: {response}")
            return 1

    except Exception as e:
        print(f"ERROR: {str(e)}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
