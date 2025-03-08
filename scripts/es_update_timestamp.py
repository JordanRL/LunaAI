#!/usr/bin/env python
"""
Command-line utility for updating the timestamp and last_accessed fields of memories in Luna's
Elasticsearch memory index.
"""

import argparse
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from adapters.elasticsearch_adapter import ElasticsearchAdapter


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Update timestamps of memories in Luna's Elasticsearch index."
    )

    # Required arguments - either ID or query must be provided
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--id", help="ID of the memory to update")
    group.add_argument("--query", help="Search query to find memories to update")

    # New timestamp values - timestamp is required, last_accessed is optional
    parser.add_argument(
        "--timestamp",
        required=True,
        help="New timestamp value (ISO format: YYYY-MM-DDThh:mm:ss.sssZ)",
    )
    parser.add_argument(
        "--last-accessed", help="New last_accessed value (ISO format: YYYY-MM-DDThh:mm:ss.sssZ)"
    )

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
        "--memory-type",
        choices=["episodic", "emotional", "semantic", "relationship"],
        help="Filter by memory type (when using --query)",
    )
    parser.add_argument("--user-id", help="Filter by user ID (when using --query)")
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum number of memories to update (default: 100, when using --query)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be updated without making changes"
    )
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--verbose", action="store_true", help="Show detailed information")

    return parser.parse_args()


def validate_timestamp(timestamp_str):
    """Validate that the timestamp is in correct ISO format."""
    try:
        datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def format_datetime(dt_str):
    """Format datetime string for display."""
    if not dt_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return dt_str


def get_memories_by_query(es_adapter, args):
    """Get memories matching the provided query arguments."""
    # Build the query
    query = {"query": {"match_all": {}}}

    # Add filters to a bool query
    must_clauses = []
    filter_clauses = []

    # Filter by memory type
    if args.memory_type:
        filter_clauses.append({"term": {"memory_type": args.memory_type}})

    # Filter by user ID
    if args.user_id:
        filter_clauses.append({"term": {"user_id": args.user_id}})

    # Search content
    if args.query:
        must_clauses.append(
            {
                "multi_match": {
                    "query": args.query,
                    "fields": ["content", "keywords^2", "context", "participants"],
                }
            }
        )

    # Apply filters if any
    if must_clauses or filter_clauses:
        bool_query = {}
        if must_clauses:
            bool_query["must"] = must_clauses
        if filter_clauses:
            bool_query["filter"] = filter_clauses
        query = {"query": {"bool": bool_query}}

    # Add sort order and size
    query["sort"] = [{"timestamp": {"order": "desc"}}, {"importance": {"order": "desc"}}]
    query["size"] = args.limit

    if args.verbose:
        print(f"Search query: {json.dumps(query, indent=2)}")

    # Execute the search query
    response = es_adapter.search(query=query, index_name=es_adapter.memory_index_name)
    hits = response.get("hits", {}).get("hits", [])

    memories = []
    for hit in hits:
        memories.append({"id": hit["_id"], "source": hit["_source"]})

    return memories


def update_memory_timestamp(
    es_adapter, memory_id, new_timestamp, new_last_accessed=None, dry_run=False, verbose=False
):
    """Update the timestamp and optionally last_accessed for a specific memory."""
    try:
        # If dry run, just print what would happen
        if dry_run:
            return True

        # Prepare updates
        updates = {"timestamp": new_timestamp}
        if new_last_accessed:
            updates["last_accessed"] = new_last_accessed

        # Perform the actual update
        result = es_adapter.update_memory(memory_id, updates)

        if verbose:
            print(f"Update result for memory {memory_id}: {result}")

        return result

    except Exception as e:
        print(f"Error updating memory {memory_id}: {str(e)}")
        return False


def main():
    """Main entry point."""
    args = parse_arguments()

    # Validate timestamp formats
    if not validate_timestamp(args.timestamp):
        print(f"Error: Invalid timestamp format: {args.timestamp}")
        print("Please use ISO format: YYYY-MM-DDThh:mm:ss.sssZ")
        return 1

    if args.last_accessed and not validate_timestamp(args.last_accessed):
        print(f"Error: Invalid last_accessed format: {args.last_accessed}")
        print("Please use ISO format: YYYY-MM-DDThh:mm:ss.sssZ")
        return 1

    try:
        # Create the Elasticsearch adapter
        es_adapter = ElasticsearchAdapter(
            host=args.host,
            memory_index_name=args.index or ElasticsearchAdapter.DEFAULT_MEMORY_INDEX,
        )

        # Get memories to update
        memories_to_update = []

        if args.id:
            # Single memory mode
            memory = es_adapter.get_memory(args.id)
            if not memory:
                print(f"Error: Memory {args.id} not found.")
                return 1

            memories_to_update.append({"id": args.id, "source": memory.get("_source", {})})
        else:
            # Query mode
            memories_to_update = get_memories_by_query(es_adapter, args)

        # Show preview
        if not memories_to_update:
            print("No memories found matching the criteria.")
            return 0

        print(f"Found {len(memories_to_update)} memories to update:")
        for i, memory in enumerate(memories_to_update[:10], 1):
            mem_id = memory.get("id")
            content = memory.get("source", {}).get("content", "")
            content_preview = content[:60] + ("..." if len(content) > 60 else "")
            memory_type = memory.get("source", {}).get("memory_type", "")
            current_timestamp = memory.get("source", {}).get("timestamp", "")
            formatted_current = format_datetime(current_timestamp)
            current_last_accessed = memory.get("source", {}).get("last_accessed", "")
            formatted_last_accessed = format_datetime(current_last_accessed)

            print(f"{i}. ID: {mem_id}")
            print(f"   Type: {memory_type}")
            print(f"   Content: {content_preview}")
            print(f"   Current timestamp: {formatted_current}")
            print(f"   New timestamp: {args.timestamp} ({format_datetime(args.timestamp)})")

            if args.last_accessed:
                print(f"   Current last_accessed: {formatted_last_accessed}")
                print(
                    f"   New last_accessed: {args.last_accessed} ({format_datetime(args.last_accessed)})"
                )
            print()

        if len(memories_to_update) > 10:
            print(f"... and {len(memories_to_update) - 10} more")

        # Confirm action unless forced
        if not args.force and not args.dry_run:
            fields_to_update = "timestamp"
            if args.last_accessed:
                fields_to_update += " and last_accessed"

            confirmation = input(
                f"Update {fields_to_update} for {len(memories_to_update)} memories? (y/N): "
            )
            if confirmation.lower() != "y":
                print("Operation cancelled.")
                return 0

        # Perform updates
        success_count = 0
        for memory in memories_to_update:
            memory_id = memory.get("id")
            if args.dry_run:
                update_msg = f"Would update memory {memory_id} timestamp to {args.timestamp}"
                if args.last_accessed:
                    update_msg += f" and last_accessed to {args.last_accessed}"
                print(update_msg)
                success_count += 1
            else:
                result = update_memory_timestamp(
                    es_adapter,
                    memory_id,
                    args.timestamp,
                    args.last_accessed,
                    args.dry_run,
                    args.verbose,
                )
                if result:
                    success_count += 1

        # Show summary
        action = "Would update" if args.dry_run else "Updated"
        print(f"{action} {success_count}/{len(memories_to_update)} memories.")

        return 0

    except Exception as e:
        print(f"ERROR: {str(e)}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
