#!/usr/bin/env python
"""
Interactive command-line utility for creating user profiles for Luna's Elasticsearch.
This script walks users through creating a user profile and saves it to a JSON file.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from domain.models.user import UserProfile


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Interactive user profile creation for Luna.")
    parser.add_argument(
        "--output", default=None, help="Output file path (default: user_profile_TIMESTAMP.json)"
    )
    parser.add_argument(
        "--insert",
        action="store_true",
        help="Insert the created profile into Elasticsearch after creation",
    )
    parser.add_argument(
        "--host",
        default="http://localhost:9200",
        help="Elasticsearch host URL (when using --insert)",
    )
    parser.add_argument(
        "--index",
        default=None,
        help="Override the default user profile index name (when using --insert)",
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


def get_biographical_info():
    """Get biographical information for the user profile."""
    print("\n=== Biographical Information ===")

    data = {}
    data["name"] = get_input("Full name")
    data["nickname"] = get_input("Nickname or preferred name")
    data["pronouns"] = get_input("Pronouns (e.g., he/him, she/her, they/them)")
    data["age"] = get_input("Age", type_converter=int)
    data["birthday"] = get_input("Birthday (format: MM-DD)")
    data["occupation"] = get_input("Occupation")

    # Education
    print("\n--- Education ---")
    data["education"] = {}
    data["education"]["level"] = get_input(
        "Education level (e.g., high school, bachelor's, master's)"
    )
    data["education"]["field"] = get_input("Field of study")
    data["education"]["institutions"] = get_list_input("Educational institutions")

    # Languages
    data["languages"] = get_list_input("Languages spoken")

    # Location
    print("\n--- Location ---")
    data["location"] = {}
    data["location"]["country"] = get_input("Country")
    data["location"]["region"] = get_input("Region/State/Province")
    data["location"]["city"] = get_input("City")
    data["location"]["timezone"] = get_input("Timezone (e.g., UTC-5, EST)")

    return data


def get_personal_context():
    """Get personal context information for the user profile."""
    print("\n=== Personal Context ===")

    data = {}

    # Family members
    data["family"] = []
    if get_yes_no("Add family members?", default=False):
        print("\n--- Family Members ---")
        while True:
            family_member = {}
            family_member["relation"] = get_input("Relation (e.g., mother, brother)", required=True)
            family_member["name"] = get_input("Name", required=True)
            family_member["important_details"] = get_input("Important details")

            data["family"].append(family_member)

            if not get_yes_no("Add another family member?", default=False):
                break

    # Pets
    data["pets"] = []
    if get_yes_no("Add pets?", default=False):
        print("\n--- Pets ---")
        while True:
            pet = {}
            pet["type"] = get_input("Type (e.g., dog, cat)", required=True)
            pet["name"] = get_input("Name", required=True)

            data["pets"].append(pet)

            if not get_yes_no("Add another pet?", default=False):
                break

    # Living situation
    data["living_situation"] = get_input("Living situation (e.g., apartment, house, with family)")

    # Major life events
    data["major_life_events"] = []
    if get_yes_no("Add major life events?", default=False):
        print("\n--- Major Life Events ---")
        while True:
            event = {}
            event["event"] = get_input("Event description", required=True)
            event["date"] = get_input("When it occurred (e.g., 2019, last summer)", required=True)
            event["emotional_impact"] = get_input("Emotional impact")

            data["major_life_events"].append(event)

            if not get_yes_no("Add another life event?", default=False):
                break

    return data


def get_preferences():
    """Get preference information for the user profile."""
    print("\n=== Preferences ===")

    data = {}

    # Topics
    print("\n--- Topic Preferences ---")
    data["topics"] = {}
    data["topics"]["interests"] = get_list_input("General interests")
    data["topics"]["expertise_areas"] = get_list_input("Areas of expertise")
    data["topics"]["learning_goals"] = get_list_input("Learning goals")

    # Media
    print("\n--- Media Preferences ---")
    data["media"] = {}
    data["media"]["books"] = get_list_input("Favorite books or authors")
    data["media"]["music"] = get_list_input("Favorite music or artists")
    data["media"]["movies"] = get_list_input("Favorite movies or shows")
    data["media"]["games"] = get_list_input("Favorite games")

    # Food
    print("\n--- Food Preferences ---")
    data["food"] = {}
    data["food"]["likes"] = get_list_input("Food likes")
    data["food"]["dislikes"] = get_list_input("Food dislikes")
    data["food"]["dietary_restrictions"] = get_list_input("Dietary restrictions")

    # Aesthetic
    print("\n--- Aesthetic Preferences ---")
    data["aesthetic"] = {}
    data["aesthetic"]["colors"] = get_list_input("Favorite colors")
    data["aesthetic"]["styles"] = get_list_input("Preferred styles")

    # Activities
    print("\n--- Activity Preferences ---")
    data["activities"] = {}
    data["activities"]["hobbies"] = get_list_input("Hobbies")
    data["activities"]["exercise"] = get_list_input("Exercise activities")
    data["activities"]["social"] = get_list_input("Social activities")

    return data


def get_behavioral_patterns():
    """Get behavioral pattern information for the user profile."""
    print("\n=== Behavioral Patterns ===")

    data = {}

    # Communication style
    print("\n--- Communication Style ---")
    data["communication_style"] = {}
    data["communication_style"]["verbosity"] = get_input(
        "Verbosity",
        default="balanced",
        validator=lambda x: (
            x in ["concise", "balanced", "detailed", "verbose"],
            "Must be one of: concise, balanced, detailed, verbose",
        ),
    )
    data["communication_style"]["formality"] = get_input(
        "Formality",
        default="casual",
        validator=lambda x: (
            x in ["formal", "casual", "varies"],
            "Must be one of: formal, casual, varies",
        ),
    )
    data["communication_style"]["humor"] = get_input(
        "Humor style (e.g., sarcastic, silly, dry, wit)"
    )
    data["communication_style"]["expressiveness"] = get_input(
        "Expressiveness style (e.g., emoji_user, descriptive, reserved)"
    )

    # Interaction patterns
    print("\n--- Interaction Patterns ---")
    data["interaction_patterns"] = {}
    data["interaction_patterns"]["preferred_times"] = get_list_input(
        "Preferred times for interaction"
    )
    data["interaction_patterns"]["frequency"] = get_input(
        "Interaction frequency (e.g., daily, weekly)"
    )
    data["interaction_patterns"]["session_length"] = get_input(
        "Session length",
        default="medium",
        validator=lambda x: (
            x in ["brief", "medium", "extended"],
            "Must be one of: brief, medium, extended",
        ),
    )
    data["interaction_patterns"]["conversation_pacing"] = get_input(
        "Conversation pacing",
        default="balanced",
        validator=lambda x: (
            x in ["rapid", "balanced", "thoughtful"],
            "Must be one of: rapid, balanced, thoughtful",
        ),
    )

    # Learning style
    print("\n--- Learning Style ---")
    data["learning_style"] = {}
    data["learning_style"]["preferred_learning"] = get_input(
        "Preferred learning method",
        default="balanced",
        validator=lambda x: (
            x in ["visual", "auditory", "reading", "doing", "balanced"],
            "Must be one of: visual, auditory, reading, doing, balanced",
        ),
    )
    data["learning_style"]["explanation_preference"] = get_input(
        "Explanation preference",
        default="balanced",
        validator=lambda x: (
            x in ["theory_first", "examples_first", "step_by_step", "balanced"],
            "Must be one of: theory_first, examples_first, step_by_step, balanced",
        ),
    )
    data["learning_style"]["detail_level"] = get_input(
        "Detail level",
        default="balanced",
        validator=lambda x: (
            x in ["overview", "balanced", "deep_dives"],
            "Must be one of: overview, balanced, deep_dives",
        ),
    )

    # Decision making
    print("\n--- Decision Making ---")
    data["decision_making"] = {}
    data["decision_making"]["approach"] = get_input(
        "Decision-making approach",
        default="balanced",
        validator=lambda x: (
            x in ["intuitive", "analytical", "deliberative", "balanced"],
            "Must be one of: intuitive, analytical, deliberative, balanced",
        ),
    )
    data["decision_making"]["risk_attitude"] = get_input(
        "Risk attitude",
        default="balanced",
        validator=lambda x: (
            x in ["adventurous", "balanced", "cautious"],
            "Must be one of: adventurous, balanced, cautious",
        ),
    )
    data["decision_making"]["influences"] = get_list_input("Decision influences")

    return data


def get_values_and_beliefs():
    """Get values and beliefs information for the user profile."""
    print("\n=== Values and Beliefs ===")

    data = {}
    data["core_values"] = get_list_input("Core values")

    # Worldview
    print("\n--- Worldview ---")
    data["worldview"] = {}
    data["worldview"]["political_leaning"] = get_input("Political leaning (if comfortable sharing)")
    data["worldview"]["philosophical_interests"] = get_list_input("Philosophical interests")
    data["worldview"]["spiritual_framework"] = get_input(
        "Spiritual framework (if comfortable sharing)"
    )

    # Cultural background
    print("\n--- Cultural Background ---")
    data["cultural_background"] = {}
    data["cultural_background"]["heritage"] = get_list_input("Cultural heritage")
    data["cultural_background"]["important_traditions"] = get_list_input("Important traditions")
    data["cultural_background"]["cultural_identities"] = get_list_input("Cultural identities")

    # Ethics
    print("\n--- Ethics ---")
    data["ethics"] = {}
    data["ethics"]["moral_foundations"] = get_list_input("Moral foundations")
    data["ethics"]["causes"] = get_list_input("Important causes")

    return data


def validate_profile_data(profile_data):
    """Convert profile data to a UserProfile object to validate it."""
    try:
        # Create a UserProfile instance
        profile = UserProfile(**profile_data)
        return True, profile
    except Exception as e:
        return False, str(e)


def save_profile_to_file(profile_data, output_path):
    """Save profile data to a JSON file."""
    try:
        with open(output_path, "w") as f:
            json.dump(profile_data, f, indent=2)
        return True, output_path
    except Exception as e:
        return False, str(e)


def insert_profile_to_elasticsearch(profile_data, host, index):
    """Insert profile data to Elasticsearch."""
    try:
        # Import here to avoid circular imports
        from adapters.elasticsearch_adapter import ElasticsearchAdapter
        from domain.models.user import UserProfile

        # Create a UserProfile object
        profile = UserProfile(**profile_data)

        # Create the Elasticsearch adapter
        es_adapter = ElasticsearchAdapter(
            host=host,
            user_profile_index_name=index or ElasticsearchAdapter.DEFAULT_USER_PROFILE_INDEX,
        )

        # Store the profile
        response = es_adapter.store_user_profile(profile)

        if response and "_id" in response:
            profile_id = response["_id"]
            return True, profile_id
        else:
            return False, f"No ID returned: {response}"

    except Exception as e:
        return False, str(e)


def main():
    """Main entry point."""
    print("===== Luna User Profile Creator =====")
    print("This tool will help you create a user profile for Luna's system.")

    args = parse_arguments()

    try:
        # Get user ID (required)
        print("\n=== User Identification ===")
        user_id = get_input("User ID", required=True)

        # Create profile data structure
        profile_data = {
            "user_id": user_id,
            "biographical": get_biographical_info(),
            "personal_context": get_personal_context(),
            "preferences": get_preferences(),
            "behavioral_patterns": get_behavioral_patterns(),
            "values_and_beliefs": get_values_and_beliefs(),
            "interaction_meta": {
                "first_interaction": datetime.now().isoformat(),
                "interaction_count": 0,
            },
        }

        # Validate profile data
        valid, result = validate_profile_data(profile_data)
        if not valid:
            print(f"\nERROR: Profile validation failed: {result}")
            return 1

        # Generate output file path if not provided
        if not args.output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            args.output = f"user_profile_{user_id}_{timestamp}.json"

        # Save profile data to file
        print(f"\nSaving profile to file: {args.output}")
        success, result = save_profile_to_file(profile_data, args.output)

        if not success:
            print(f"ERROR: Failed to save profile: {result}")
            return 1

        print(f"Profile saved successfully to: {result}")

        # Insert profile into Elasticsearch if requested
        if args.insert:
            print(f"\nInserting profile into Elasticsearch at {args.host}")
            success, result = insert_profile_to_elasticsearch(profile_data, args.host, args.index)

            if success:
                print(f"Profile inserted successfully with ID: {result}")
            else:
                print(f"ERROR: Failed to insert profile: {result}")
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
