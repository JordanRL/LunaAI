#!/usr/bin/env python
"""
Command-line utility for deleting Elasticsearch indices in Luna's system.
"""

import argparse
import sys
import traceback
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from elasticsearch import Elasticsearch


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Delete Elasticsearch indices in Luna's system.")

    # Required arguments - either a specific index or a pattern
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--index", help="Specific index name to delete")
    group.add_argument("--pattern", help='Index pattern to delete (e.g., "test-*")')

    # Optional arguments
    parser.add_argument(
        "--host",
        default="http://localhost:9200",
        help="Elasticsearch host URL (default: http://localhost:9200)",
    )
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")

    return parser.parse_args()


def confirm_deletion(indices, pattern=None):
    """Ask user to confirm deletion of indices."""
    if not indices:
        print(
            f"No indices found matching {'pattern: ' + pattern if pattern else 'the specified index'}"
        )
        return False

    print("The following indices will be PERMANENTLY DELETED:")
    for index in sorted(indices):
        print(f"  - {index}")

    print("\nWARNING: This action cannot be undone and all data will be lost!")
    confirm = input("Type 'DELETE' to confirm: ")

    return confirm == "DELETE"


def main():
    """Main entry point."""
    args = parse_arguments()

    try:
        # Create the Elasticsearch client
        es = Elasticsearch(hosts=args.host)

        # Check connection
        if not es.ping():
            print(f"ERROR: Could not connect to Elasticsearch at {args.host}")
            return 1

        # Get indices information based on input
        if args.index:
            # Check if specific index exists
            if not es.indices.exists(index=args.index):
                print(f"ERROR: Index '{args.index}' does not exist.")
                return 1
            indices = [args.index]
        else:  # args.pattern
            # Get all indices matching the pattern
            try:
                matching_indices = es.indices.get(index=args.pattern)
                indices = list(matching_indices.keys())
            except Exception as e:
                print(
                    f"ERROR: Failed to retrieve indices matching pattern '{args.pattern}': {str(e)}"
                )
                return 1

        # Ask for confirmation unless --force is specified
        if not args.force and not confirm_deletion(indices, args.pattern if args.pattern else None):
            print("Operation cancelled.")
            return 0

        # Delete the indices
        success_count = 0
        for index in indices:
            try:
                response = es.indices.delete(index=index)
                if response.get("acknowledged", False):
                    print(f"Deleted index: {index}")
                    success_count += 1
                else:
                    print(f"Failed to delete index: {index} - Not acknowledged by server")
            except Exception as e:
                print(f"Error deleting index {index}: {str(e)}")

        # Print summary
        if success_count == len(indices):
            print(f"SUCCESS: All {success_count} indices deleted.")
        else:
            print(f"WARNING: {success_count} out of {len(indices)} indices deleted.")
            if success_count < len(indices):
                print("Some indices could not be deleted. Check error messages above.")

        return 0 if success_count > 0 else 1

    except Exception as e:
        print(f"ERROR: {str(e)}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
