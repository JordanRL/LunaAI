#!/usr/bin/env python
"""
Command-line utility for rebuilding Elasticsearch indices in Luna's system.
This script uses the ElasticsearchAdapter to recreate indices with proper mappings and settings.
"""

import argparse
import sys
import traceback
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from adapters.elasticsearch_adapter import ElasticsearchAdapter


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Rebuild Elasticsearch indices for Luna.")

    # Optional arguments
    parser.add_argument(
        "--host",
        default="http://localhost:9200",
        help="Elasticsearch host URL (default: http://localhost:9200)",
    )
    parser.add_argument(
        "--index-type",
        choices=["all", "memories", "profiles", "relationships"],
        default="all",
        help="Type of index to rebuild (default: all)",
    )
    parser.add_argument(
        "--memory-index",
        help=f"Override the default memory index name (default: {ElasticsearchAdapter.DEFAULT_MEMORY_INDEX})",
    )
    parser.add_argument(
        "--profile-index",
        help=f"Override the default user profile index name (default: {ElasticsearchAdapter.DEFAULT_USER_PROFILE_INDEX})",
    )
    parser.add_argument(
        "--relationship-index",
        help=f"Override the default user relationship index name (default: {ElasticsearchAdapter.DEFAULT_USER_RELATIONSHIP_INDEX})",
    )
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")

    return parser.parse_args()


def confirm_rebuild(index_names):
    """Ask user to confirm rebuilding of indices."""
    print("The following indices will be DELETED and REBUILT:")
    for index in index_names:
        print(f"  - {index}")

    print("\nWARNING: This action will DELETE ALL DATA in these indices!")
    confirm = input("Type 'REBUILD' to confirm: ")

    return confirm == "REBUILD"


def main():
    """Main entry point."""
    args = parse_arguments()

    try:
        # Create the indices list based on the index type argument
        indices_to_rebuild = []
        memory_index = args.memory_index or ElasticsearchAdapter.DEFAULT_MEMORY_INDEX
        profile_index = args.profile_index or ElasticsearchAdapter.DEFAULT_USER_PROFILE_INDEX
        relationship_index = (
            args.relationship_index or ElasticsearchAdapter.DEFAULT_USER_RELATIONSHIP_INDEX
        )

        if args.index_type in ["all", "memories"]:
            indices_to_rebuild.append(memory_index)

        if args.index_type in ["all", "profiles"]:
            indices_to_rebuild.append(profile_index)

        if args.index_type in ["all", "relationships"]:
            indices_to_rebuild.append(relationship_index)

        # Ask for confirmation unless --force is specified
        if not args.force and not confirm_rebuild(indices_to_rebuild):
            print("Operation cancelled.")
            return 0

        # Create the Elasticsearch adapter with rebuild_indices=True
        print(f"Connecting to Elasticsearch at {args.host}...")
        es_adapter = ElasticsearchAdapter(
            host=args.host,
            memory_index_name=memory_index,
            user_profile_index_name=profile_index,
            user_relationship_index_name=relationship_index,
            rebuild_indices=False,  # We'll handle rebuilding manually
        )

        # Rebuild only the selected indices
        success_count = 0

        if args.index_type in ["all", "memories"]:
            print(f"Rebuilding memory index: {memory_index}...")
            try:
                es_adapter.delete_index(memory_index)
                es_adapter._initialize_memory_index()
                print("✓ Memory index rebuilt successfully")
                success_count += 1
            except Exception as e:
                print(f"✗ Failed to rebuild memory index: {str(e)}")
                traceback.print_exc()

        if args.index_type in ["all", "profiles"]:
            print(f"Rebuilding user profile index: {profile_index}...")
            try:
                es_adapter.delete_index(profile_index)
                es_adapter._initialize_user_profile_index()
                print("✓ User profile index rebuilt successfully")
                success_count += 1
            except Exception as e:
                print(f"✗ Failed to rebuild user profile index: {str(e)}")
                traceback.print_exc()

        if args.index_type in ["all", "relationships"]:
            print(f"Rebuilding user relationship index: {relationship_index}...")
            try:
                es_adapter.delete_index(relationship_index)
                es_adapter._initialize_user_relationship_index()
                print("✓ User relationship index rebuilt successfully")
                success_count += 1
            except Exception as e:
                print(f"✗ Failed to rebuild user relationship index: {str(e)}")
                traceback.print_exc()

        # Print summary
        if success_count == len(indices_to_rebuild):
            print(f"SUCCESS: All {success_count} indices rebuilt successfully.")
        else:
            print(
                f"WARNING: {success_count} out of {len(indices_to_rebuild)} indices rebuilt successfully."
            )
            if success_count < len(indices_to_rebuild):
                print("Some indices could not be rebuilt. Check error messages above.")

        return 0 if success_count > 0 else 1

    except Exception as e:
        print(f"ERROR: {str(e)}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
