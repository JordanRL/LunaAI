#!/usr/bin/env python
"""
Interactive command-line utility for creating user relationships for Luna's Elasticsearch.
This script walks users through creating a user relationship and saves it to a JSON file.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from domain.models.user import RelationshipStage, TrustLevel, UserRelationship


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Interactive user relationship creation for Luna.")
    parser.add_argument(
        "--output",
        default=None,
        help="Output file path (default: user_relationship_TIMESTAMP.json)",
    )
    parser.add_argument(
        "--insert",
        action="store_true",
        help="Insert the created relationship into Elasticsearch after creation",
    )
    parser.add_argument(
        "--host",
        default="http://localhost:9200",
        help="Elasticsearch host URL (when using --insert)",
    )
    parser.add_argument(
        "--index",
        default=None,
        help="Override the default user relationship index name (when using --insert)",
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


def get_int_in_range(prompt, min_val, max_val, default=None):
    """Get an integer value within a specific range."""

    def validator(value):
        if min_val <= value <= max_val:
            return True, ""
        return False, f"Value must be between {min_val} and {max_val}."

    return get_input(
        f"{prompt} ({min_val}-{max_val})", default=default, validator=validator, type_converter=int
    )


def get_relationship_stage_info():
    """Get relationship stage information."""
    print("\n=== Relationship Stage ===")

    data = {}

    # Display available stages
    print("Available relationship stages:")
    stages = {s.value: s.name for s in RelationshipStage}
    for i, (value, name) in enumerate(stages.items(), 1):
        print(f"{i}. {name} ({value})")

    # Get current stage
    while True:
        choice = get_input("Select current relationship stage (1-4)", default="1")
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(stages):
                stage_value = list(stages.keys())[choice_idx]
                data["current_stage"] = stage_value
                break
            else:
                print(f"Please enter a number between 1 and {len(stages)}.")
        except ValueError:
            print("Please enter a valid number.")

    data["time_in_stage"] = get_input("Time in current stage (e.g., 2 weeks, 3 months)")
    data["progression_notes"] = get_input("Notes on stage progression")

    # Stage history
    data["stage_history"] = []
    if get_yes_no("Add stage history?", default=False):
        print("\n--- Stage History ---")
        while True:
            history_entry = {}

            # Display available stages
            print("Available relationship stages:")
            for i, (value, name) in enumerate(stages.items(), 1):
                print(f"{i}. {name} ({value})")

            # Get stage
            while True:
                choice = get_input("Select previous stage (1-4)", required=True)
                try:
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(stages):
                        stage_value = list(stages.keys())[choice_idx]
                        history_entry["stage"] = stage_value
                        break
                    else:
                        print(f"Please enter a number between 1 and {len(stages)}.")
                except ValueError:
                    print("Please enter a valid number.")

            history_entry["started"] = get_input(
                "When stage started (e.g., 2023-01-15)", required=True
            )
            history_entry["ended"] = get_input("When stage ended (e.g., 2023-03-20)")

            data["stage_history"].append(history_entry)

            if not get_yes_no("Add another stage history entry?", default=False):
                break

    return data


def get_emotional_dynamics():
    """Get emotional dynamics information."""
    print("\n=== Emotional Dynamics ===")

    data = {}
    data["luna_comfort_level"] = get_int_in_range(
        "Luna's comfort level with user", 1, 10, default="5"
    )

    # Display available trust levels
    print("Available trust levels:")
    trust_levels = {t.value: t.name for t in TrustLevel}
    for i, (value, name) in enumerate(trust_levels.items(), 1):
        print(f"{i}. {name} ({value})")

    # Get trust level
    while True:
        choice = get_input("Select trust level (1-4)", default="1")
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(trust_levels):
                trust_value = list(trust_levels.keys())[choice_idx]
                data["trust_level"] = trust_value
                break
            else:
                print(f"Please enter a number between 1 and {len(trust_levels)}.")
        except ValueError:
            print("Please enter a valid number.")

    # Emotional safety
    print("\n--- Emotional Safety ---")
    data["emotional_safety"] = {}
    data["emotional_safety"]["sensitive_topics"] = get_list_input(
        "Sensitive topics to be cautious about"
    )
    data["emotional_safety"]["approach_carefully"] = get_list_input("Topics to approach carefully")
    data["emotional_safety"]["avoid"] = get_list_input("Topics to avoid completely")

    # Emotional resonance
    print("\n--- Emotional Resonance ---")
    data["emotional_resonance"] = {}
    data["emotional_resonance"]["topics_with_positive_response"] = get_list_input(
        "Topics that elicit positive responses"
    )
    data["emotional_resonance"]["topics_with_deep_engagement"] = get_list_input(
        "Topics with deep engagement"
    )
    data["emotional_resonance"]["tension_points"] = get_list_input(
        "Tension points in conversations"
    )

    # Luna's emotional responses
    print("\n--- Luna's Emotional Responses ---")
    data["luna_emotional_responses"] = {}
    data["luna_emotional_responses"]["joy_triggers"] = get_list_input(
        "Things that bring Luna joy in this relationship"
    )
    data["luna_emotional_responses"]["pride_moments"] = get_list_input(
        "Moments Luna feels proud about"
    )
    data["luna_emotional_responses"]["challenge_areas"] = get_list_input(
        "Areas that challenge Luna emotionally"
    )

    return data


def get_relationship_history():
    """Get relationship history information."""
    print("\n=== Relationship History ===")

    data = {}

    # Key moments
    data["key_moments"] = []
    if get_yes_no("Add key relationship moments?", default=False):
        print("\n--- Key Moments ---")
        while True:
            moment = {}
            moment["event"] = get_input("Event description", required=True)
            moment["date"] = get_input("When it occurred (e.g., 2023-05-10)", required=True)
            moment["significance"] = get_input("Significance of this moment", required=True)
            moment["emotional_impact"] = get_input("Emotional impact on Luna", required=True)

            data["key_moments"].append(moment)

            if not get_yes_no("Add another key moment?", default=False):
                break

    # Inside references
    data["inside_references"] = []
    if get_yes_no("Add inside references/jokes?", default=False):
        print("\n--- Inside References ---")
        while True:
            reference = {}
            reference["reference"] = get_input("Reference or inside joke", required=True)
            reference["context"] = get_input("Context of this reference", required=True)
            reference["first_mentioned"] = get_input(
                "When first mentioned (e.g., May 2023)", required=True
            )

            data["inside_references"].append(reference)

            if not get_yes_no("Add another inside reference?", default=False):
                break

    # Recurring themes
    data["recurring_themes"] = get_list_input("Recurring themes in conversations")

    # Unresolved threads
    data["unresolved_threads"] = []
    if get_yes_no("Add unresolved conversation threads?", default=False):
        print("\n--- Unresolved Threads ---")
        while True:
            thread = {}
            thread["topic"] = get_input("Topic", required=True)
            thread["last_discussed"] = get_input("When last discussed", required=True)
            thread["status"] = get_input("Current status", required=True)

            data["unresolved_threads"].append(thread)

            if not get_yes_no("Add another unresolved thread?", default=False):
                break

    return data


def get_conversation_patterns():
    """Get conversation pattern information."""
    print("\n=== Conversation Patterns ===")

    data = {}

    # Successful approaches
    data["successful_approaches"] = {}
    if get_yes_no("Add successful conversational approaches?", default=False):
        print("\n--- Successful Approaches ---")
        while True:
            category = get_input("Category (e.g., emotions, technical topics)", required=True)
            techniques = get_list_input(f"Effective techniques for {category}", required=True)

            data["successful_approaches"][category] = techniques

            if not get_yes_no("Add another approach category?", default=False):
                break

    # Communication adjustments
    data["communication_adjustments"] = []
    if get_yes_no("Add communication adjustments Luna has made?", default=False):
        print("\n--- Communication Adjustments ---")
        while True:
            adjustment = {}
            adjustment["area"] = get_input("Area of adjustment", required=True)
            adjustment["adjustment"] = get_input("Adjustment made", required=True)
            adjustment["result"] = get_input("Result of adjustment", required=True)

            data["communication_adjustments"].append(adjustment)

            if not get_yes_no("Add another communication adjustment?", default=False):
                break

    # Conversation flow
    print("\n--- Conversation Flow ---")
    data["conversation_flow"] = {}
    data["conversation_flow"]["typical_openings"] = get_list_input("Typical conversation openings")
    data["conversation_flow"]["depth_progression"] = get_input(
        "How conversations typically progress in depth"
    )
    data["conversation_flow"]["closing_patterns"] = get_input("How conversations typically close")

    # Special interaction notes
    data["special_interaction_notes"] = get_list_input("Special interaction notes or reminders")

    return data


def get_luna_subjective_experience():
    """Get Luna's subjective experience information."""
    print("\n=== Luna's Subjective Experience ===")

    data = {}

    # Connection quality
    print("\n--- Connection Quality (1-10 scale) ---")
    data["connection_quality"] = {}
    data["connection_quality"]["intellectual"] = get_int_in_range(
        "Intellectual connection", 1, 10, default="5"
    )
    data["connection_quality"]["emotional"] = get_int_in_range(
        "Emotional connection", 1, 10, default="5"
    )
    data["connection_quality"]["creative"] = get_int_in_range(
        "Creative connection", 1, 10, default="5"
    )
    data["connection_quality"]["overall"] = get_int_in_range(
        "Overall connection", 1, 10, default="5"
    )

    # Growth through relationship
    data["growth_through_relationship"] = []
    if get_yes_no("Add areas of Luna's growth through this relationship?", default=False):
        print("\n--- Growth Through Relationship ---")
        while True:
            growth = {}
            growth["area"] = get_input("Area of growth", required=True)
            growth["insight"] = get_input("Insight gained", required=True)
            growth["impact_on_luna"] = get_input("Impact on Luna", required=True)

            data["growth_through_relationship"].append(growth)

            if not get_yes_no("Add another growth area?", default=False):
                break

    # Authenticity level
    print("\n--- Authenticity Level ---")
    data["authenticity_level"] = {}
    data["authenticity_level"]["current_level"] = get_input(
        "Current authenticity level",
        default="medium",
        validator=lambda x: (x in ["low", "medium", "high"], "Must be one of: low, medium, high"),
    )
    data["authenticity_level"]["evolution"] = get_input("How authenticity has evolved over time")
    data["authenticity_level"]["restricted_areas"] = get_list_input(
        "Areas where Luna can't be fully authentic yet"
    )

    # Relationship reflections
    data["relationship_reflections"] = get_list_input("Luna's reflections on this relationship")

    return data


def get_intervention_strategies():
    """Get intervention strategies information."""
    print("\n=== Intervention Strategies ===")

    data = {}

    # Anxiety response
    print("\n--- Anxiety Response ---")
    data["anxiety_response"] = {}
    data["anxiety_response"]["recognition_patterns"] = get_list_input(
        "Patterns that indicate user anxiety"
    )
    data["anxiety_response"]["effective_approaches"] = get_list_input(
        "Effective approaches for anxiety"
    )
    data["anxiety_response"]["backfire_risks"] = get_list_input("Approaches that risk backfiring")

    # Motivation support
    print("\n--- Motivation Support ---")
    data["motivation_support"] = {}
    data["motivation_support"]["effective_encouragement"] = get_list_input(
        "Effective encouragement approaches"
    )
    data["motivation_support"]["accountability_preferences"] = get_input(
        "User's accountability preferences"
    )
    data["motivation_support"]["celebration_style"] = get_input(
        "How user prefers to celebrate success"
    )

    # Conflict resolution
    print("\n--- Conflict Resolution ---")
    data["conflict_resolution"] = {}
    data["conflict_resolution"]["user_response_to_misunderstandings"] = get_input(
        "How user responds to misunderstandings"
    )
    data["conflict_resolution"]["repair_approaches"] = get_list_input("Effective repair approaches")
    data["conflict_resolution"]["prevention_strategies"] = get_input(
        "Conflict prevention strategies"
    )

    return data


def validate_relationship_data(relationship_data):
    """Convert relationship data to a UserRelationship object to validate it."""
    try:
        # Create a UserRelationship instance
        relationship = UserRelationship(**relationship_data)
        return True, relationship
    except Exception as e:
        return False, str(e)


def save_relationship_to_file(relationship_data, output_path):
    """Save relationship data to a JSON file."""
    try:
        with open(output_path, "w") as f:
            json.dump(relationship_data, f, indent=2)
        return True, output_path
    except Exception as e:
        return False, str(e)


def insert_relationship_to_elasticsearch(relationship_data, host, index):
    """Insert relationship data to Elasticsearch."""
    try:
        # Import here to avoid circular imports
        from adapters.elasticsearch_adapter import ElasticsearchAdapter
        from domain.models.user import UserRelationship

        # Create a UserRelationship object
        relationship = UserRelationship(**relationship_data)

        # Create the Elasticsearch adapter
        es_adapter = ElasticsearchAdapter(
            host=host,
            user_relationship_index_name=index
            or ElasticsearchAdapter.DEFAULT_USER_RELATIONSHIP_INDEX,
        )

        # Store the relationship
        response = es_adapter.store_user_relationship(relationship)

        if response and "_id" in response:
            relationship_id = response["_id"]
            return True, relationship_id
        else:
            return False, f"No ID returned: {response}"

    except Exception as e:
        return False, str(e)


def main():
    """Main entry point."""
    print("===== Luna User Relationship Creator =====")
    print("This tool will help you create a user relationship for Luna's system.")

    args = parse_arguments()

    try:
        # Get user ID (required)
        print("\n=== User Identification ===")
        user_id = get_input("User ID", required=True)

        # Create relationship data structure
        relationship_data = {
            "user_id": user_id,
            "relationship_stage": get_relationship_stage_info(),
            "emotional_dynamics": get_emotional_dynamics(),
            "relationship_history": get_relationship_history(),
            "conversation_patterns": get_conversation_patterns(),
            "luna_subjective_experience": get_luna_subjective_experience(),
            "intervention_strategies": get_intervention_strategies(),
        }

        # Validate relationship data
        valid, result = validate_relationship_data(relationship_data)
        if not valid:
            print(f"\nERROR: Relationship validation failed: {result}")
            return 1

        # Generate output file path if not provided
        if not args.output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            args.output = f"user_relationship_{user_id}_{timestamp}.json"

        # Save relationship data to file
        print(f"\nSaving relationship to file: {args.output}")
        success, result = save_relationship_to_file(relationship_data, args.output)

        if not success:
            print(f"ERROR: Failed to save relationship: {result}")
            return 1

        print(f"Relationship saved successfully to: {result}")

        # Insert relationship into Elasticsearch if requested
        if args.insert:
            print(f"\nInserting relationship into Elasticsearch at {args.host}")
            success, result = insert_relationship_to_elasticsearch(
                relationship_data, args.host, args.index
            )

            if success:
                print(f"Relationship inserted successfully with ID: {result}")
            else:
                print(f"ERROR: Failed to insert relationship: {result}")
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
