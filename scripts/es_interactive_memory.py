#!/usr/bin/env python
"""
Interactive command-line utility for creating memory JSON files for Luna's Elasticsearch.
This script walks users through creating different types of memories and saves them to JSON files.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from domain.models.emotion import EmotionalState
from domain.models.memory import EmotionalMemory, EpisodicMemory, RelationshipMemory, SemanticMemory


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Interactive memory creation for Luna.")
    parser.add_argument(
        "--output", default=None, help="Output file path (default: memory_TIMESTAMP.json)"
    )
    parser.add_argument(
        "--insert",
        action="store_true",
        help="Insert the created memory into Elasticsearch after creation",
    )
    parser.add_argument(
        "--host",
        default="http://localhost:9200",
        help="Elasticsearch host URL (when using --insert)",
    )
    parser.add_argument(
        "--index", default=None, help="Override the default index name (when using --insert)"
    )

    return parser.parse_args()


def get_input(prompt, default=None, required=False, validator=None, type_converter=None):
    """
    Get user input with validation and default values.

    Args:
        prompt: The prompt to display
        default: Default value if user enters nothing
        required: Whether this field is required
        validator: Function to validate input
        type_converter: Function to convert input to desired type

    Returns:
        The validated, converted input value
    """
    default_display = f" [{default}]" if default is not None else ""
    required_marker = " (required)" if required else ""

    while True:
        user_input = input(f"{prompt}{default_display}{required_marker}: ").strip()

        # Use default if input is empty
        if not user_input and default is not None:
            user_input = default

        # Check if required field is empty
        if required and not user_input:
            print("This field is required. Please enter a value.")
            continue

        # Return None for empty optional fields
        if not user_input and not required:
            return None

        # Apply type conversion if provided
        if type_converter and user_input:
            try:
                user_input = type_converter(user_input)
            except Exception:
                print(f"Invalid input. Expected {type_converter.__name__} type.")
                continue

        # Apply validation if provided
        if validator and user_input:
            valid, message = validator(user_input)
            if not valid:
                print(message)
                continue

        return user_input


def get_yes_no(prompt, default=None):
    """Get a yes/no response from the user."""
    default_display = ""
    if default is not None:
        default_display = " [Y/n]" if default else " [y/N]"

    while True:
        response = input(f"{prompt}{default_display}: ").strip().lower()

        if not response and default is not None:
            return default

        if response in ["y", "yes"]:
            return True
        if response in ["n", "no"]:
            return False

        print("Please enter 'y' or 'n'.")


def get_list_input(prompt, default=None):
    """Get a list of items from the user."""
    default_str = ", ".join(default) if default else ""
    input_str = get_input(f"{prompt} (comma-separated)", default=default_str)

    if not input_str:
        return []

    return [item.strip() for item in input_str.split(",") if item.strip()]


def get_float_in_range(prompt, min_val, max_val, default=None):
    """Get a float value within a specific range."""

    def validator(value):
        if min_val <= value <= max_val:
            return True, ""
        return False, f"Value must be between {min_val} and {max_val}."

    return get_input(
        f"{prompt} ({min_val}-{max_val})",
        default=default,
        validator=validator,
        type_converter=float,
    )


def get_memory_type():
    """Get the memory type from the user."""
    memory_types = {
        "1": ("episodic", "Events or experiences (conversations, interactions)"),
        "2": ("semantic", "Facts or knowledge"),
        "3": ("emotional", "Feelings or emotional responses"),
        "4": ("relationship", "Relationship dynamics or patterns"),
    }

    print("\n=== Memory Type ===")
    for key, (type_name, description) in memory_types.items():
        print(f"{key}. {type_name.capitalize()}: {description}")

    while True:
        choice = input("\nSelect memory type (1-4): ").strip()
        if choice in memory_types:
            memory_type = memory_types[choice][0]
            print(f"Selected: {memory_type.capitalize()}")
            return memory_type
        print("Invalid choice. Please enter a number between 1 and 4.")


def get_common_memory_data():
    """Get common memory data fields."""
    print("\n=== Basic Memory Information ===")

    data = {}
    data["content"] = get_input("Memory content", required=True)
    data["importance"] = get_input(
        "Importance",
        default="5",
        validator=lambda x: (1 <= x <= 10, "Value must be between 1 and 10."),
        type_converter=int,
    )
    data["user_id"] = get_input("User ID")
    data["keywords"] = get_list_input("Keywords")

    # Get emotional data
    if get_yes_no("Add emotional context?", default=False):
        print("\n=== Emotional Context ===")
        print("Values range from 0.0 (low) to 1.0 (high)")

        data["emotion"] = {}
        data["emotion"]["pleasure"] = get_float_in_range("Pleasure level", 0.0, 1.0, default="0.5")
        data["emotion"]["arousal"] = get_float_in_range("Arousal level", 0.0, 1.0, default="0.5")
        data["emotion"]["dominance"] = get_float_in_range(
            "Dominance level", 0.0, 1.0, default="0.5"
        )

    return data


def get_episodic_memory_data():
    """Get episodic memory specific data."""
    print("\n=== Episodic Memory Details ===")

    data = {}
    data["participants"] = get_list_input("Participants", default=["Luna"])
    data["context"] = get_input("Context (setting, situation)")

    return data


def get_semantic_memory_data():
    """Get semantic memory specific data."""
    print("\n=== Semantic Memory Details ===")

    data = {}
    data["certainty"] = get_float_in_range("Certainty level", 0.0, 1.0, default="0.8")
    data["verifiability"] = get_float_in_range("Verifiability level", 0.0, 1.0, default="0.7")
    data["domain"] = get_input("Knowledge domain")
    data["source"] = get_input("Source of information")
    data["source_reliability"] = get_float_in_range("Source reliability", 0.0, 1.0, default="0.8")

    return data


def get_emotional_memory_data():
    """Get emotional memory specific data."""
    print("\n=== Emotional Memory Details ===")

    data = {}
    data["trigger"] = get_input("Emotional trigger")

    print("\nEvent emotional impact (how the event made Luna feel):")
    data["event_pleasure"] = get_float_in_range("Event pleasure impact", 0.0, 1.0, default="0.5")
    data["event_arousal"] = get_float_in_range("Event arousal impact", 0.0, 1.0, default="0.5")
    data["event_dominance"] = get_float_in_range("Event dominance impact", 0.0, 1.0, default="0.5")

    return data


def get_relationship_memory_data():
    """Get relationship memory specific data."""
    print("\n=== Relationship Memory Details ===")

    data = {}
    data["relationship_type"] = get_input("Relationship type")
    data["closeness"] = get_float_in_range("Closeness level", 0.0, 1.0, default="0.5")
    data["trust"] = get_float_in_range("Trust level", 0.0, 1.0, default="0.5")
    data["apprehension"] = get_float_in_range("Apprehension level", 0.0, 1.0, default="0.2")
    data["shared_experiences"] = get_list_input("Shared experiences")
    data["connection_points"] = get_list_input("Connection points")
    data["inside_references"] = get_list_input("Inside references")

    return data


def validate_memory_data(memory_data):
    """Convert memory data to a Memory object to validate it."""
    try:
        memory_type = memory_data.get("type")

        # Create emotional state if provided
        emotion = None
        if "emotion" in memory_data:
            emotion = EmotionalState(
                pleasure=memory_data["emotion"].get("pleasure"),
                arousal=memory_data["emotion"].get("arousal"),
                dominance=memory_data["emotion"].get("dominance"),
            )

        # Common parameters
        common_args = {
            "content": memory_data.get("content", ""),
            "importance": memory_data.get("importance", 5),
            "user_id": memory_data.get("user_id"),
            "keywords": memory_data.get("keywords", []),
            "emotion": emotion,
        }

        # Create the appropriate memory type
        if memory_type == "episodic":
            memory = EpisodicMemory(
                **common_args,
                participants=memory_data.get("participants", []),
                context=memory_data.get("context", ""),
            )
        elif memory_type == "semantic":
            memory = SemanticMemory(
                **common_args,
                certainty=memory_data.get("certainty", 0.5),
                verifiability=memory_data.get("verifiability", 0.5),
                domain=memory_data.get("domain", ""),
                source=memory_data.get("source", ""),
                source_reliability=memory_data.get("source_reliability", 0.5),
            )
        elif memory_type == "emotional":
            memory = EmotionalMemory(
                **common_args,
                trigger=memory_data.get("trigger", ""),
                event_pleasure=memory_data.get("event_pleasure", 0.5),
                event_arousal=memory_data.get("event_arousal", 0.5),
                event_dominance=memory_data.get("event_dominance", 0.5),
            )
        elif memory_type == "relationship":
            memory = RelationshipMemory(
                **common_args,
                relationship_type=memory_data.get("relationship_type", ""),
                closeness=memory_data.get("closeness", 0.5),
                trust=memory_data.get("trust", 0.5),
                apprehension=memory_data.get("apprehension", 0.5),
                shared_experiences=memory_data.get("shared_experiences", []),
                connection_points=memory_data.get("connection_points", []),
                inside_references=memory_data.get("inside_references", []),
            )
        else:
            raise ValueError(f"Invalid memory type: {memory_type}")

        # Successful validation
        return True, memory

    except Exception as e:
        return False, str(e)


def save_memory_to_file(memory_data, output_path):
    """Save memory data to a JSON file."""
    try:
        with open(output_path, "w") as f:
            json.dump(memory_data, f, indent=2)
        return True, output_path
    except Exception as e:
        return False, str(e)


def insert_memory_to_elasticsearch(memory_data, host, index):
    """Insert memory data to Elasticsearch."""
    try:
        # Import here to avoid circular imports
        from adapters.elasticsearch_adapter import ElasticsearchAdapter
        from scripts.es_insert_memory import create_memory_from_json

        # Create a temporary file
        temp_file = "temp_memory.json"
        with open(temp_file, "w") as f:
            json.dump(memory_data, f)

        # Create memory object
        memory = create_memory_from_json(temp_file)

        # Create the Elasticsearch adapter
        es_adapter = ElasticsearchAdapter(
            host=host, memory_index_name=index or ElasticsearchAdapter.DEFAULT_MEMORY_INDEX
        )

        # Store the memory
        response = es_adapter.store_memory(memory)

        # Clean up temp file
        os.remove(temp_file)

        if response and "_id" in response:
            memory_id = response["_id"]
            return True, memory_id
        else:
            return False, f"No ID returned: {response}"

    except Exception as e:
        return False, str(e)


def main():
    """Main entry point."""
    print("===== Luna Memory Creator =====")
    print("This tool will help you create memory JSON files for Luna's Elasticsearch.")

    args = parse_arguments()

    try:
        # Get memory type
        memory_type = get_memory_type()

        # Get common memory data
        memory_data = get_common_memory_data()
        memory_data["type"] = memory_type

        # Get memory type specific data
        if memory_type == "episodic":
            memory_data.update(get_episodic_memory_data())
        elif memory_type == "semantic":
            memory_data.update(get_semantic_memory_data())
        elif memory_type == "emotional":
            memory_data.update(get_emotional_memory_data())
        elif memory_type == "relationship":
            memory_data.update(get_relationship_memory_data())

        # Validate memory data
        valid, result = validate_memory_data(memory_data)
        if not valid:
            print(f"\nERROR: Memory validation failed: {result}")
            return 1

        # Generate output file path if not provided
        if not args.output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            args.output = f"memory_{memory_type}_{timestamp}.json"

        # Save memory data to file
        print(f"\nSaving memory to file: {args.output}")
        success, result = save_memory_to_file(memory_data, args.output)

        if not success:
            print(f"ERROR: Failed to save memory: {result}")
            return 1

        print(f"Memory saved successfully to: {result}")

        # Insert memory into Elasticsearch if requested
        if args.insert:
            print(f"\nInserting memory into Elasticsearch at {args.host}")
            success, result = insert_memory_to_elasticsearch(memory_data, args.host, args.index)

            if success:
                print(f"Memory inserted successfully with ID: {result}")
            else:
                print(f"ERROR: Failed to insert memory: {result}")
                return 1

        return 0

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 0
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
