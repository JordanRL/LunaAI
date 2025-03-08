#!/usr/bin/env python
"""
Command-line utility for deleting memories from Luna's Elasticsearch memory index.
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
    parser = argparse.ArgumentParser(description="Delete memories from Luna's Elasticsearch index.")

    # Operation mode group
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--id", help="ID of the memory to delete")
    group.add_argument(
        "--query",
        action="store_true",
        help="Delete memories matching the provided query parameters",
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
        help="Filter by memory type (only with --query)",
    )
    parser.add_argument("--user-id", help="Filter by user ID (only with --query)")
    parser.add_argument("--keywords", nargs="*", help="Filter by keywords (only with --query)")
    parser.add_argument("--content", help="Search for text in memory content (only with --query)")
    parser.add_argument(
        "--importance",
        type=int,
        choices=range(1, 11),
        help="Filter by maximum importance level (1-10) (only with --query)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of memories to delete when using --query (default: 10)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt when deleting multiple memories",
    )

    return parser.parse_args()


def delete_by_id(es_adapter, memory_id):
    """Delete a single memory by ID."""
    try:
        # First, retrieve the memory to confirm it exists
        response = es_adapter.get_memory(memory_id)

        if not response.get("found", False):
            print(f"ERROR: Memory with ID {memory_id} not found.")
            return False

        # Print memory details for confirmation
        source = response.get("_source", {})
        content = source.get("content", "")
        memory_type = source.get("memory_type", "unknown")

        print("Deleting memory:")
        print(f"ID: {memory_id}")
        print(f"Type: {memory_type}")
        print(f"Content: {content[:100]}{'...' if len(content) > 100 else ''}")

        # Delete the memory
        result = es_adapter.delete_memory(memory_id)

        if result:
            print(f"SUCCESS: Memory {memory_id} deleted.")
            return True
        else:
            print(f"ERROR: Failed to delete memory {memory_id}.")
            return False

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False


def delete_by_query(es_adapter, args):
    """Delete memories matching a query."""
    try:
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

        # Filter by importance (lower priority)
        if args.importance:
            filter_clauses.append({"range": {"importance": {"lte": args.importance}}})

        # Search content
        if args.content:
            must_clauses.append({"match": {"content": args.content}})

        # Filter by keywords
        if args.keywords:
            for keyword in args.keywords:
                must_clauses.append({"match": {"keywords": keyword}})

        # Apply filters if any
        if must_clauses or filter_clauses:
            bool_query = {}
            if must_clauses:
                bool_query["must"] = must_clauses
            if filter_clauses:
                bool_query["filter"] = filter_clauses
            query = {"query": {"bool": bool_query}}

        # Add sort order and size
        query["sort"] = [
            {"importance": {"order": "asc"}},  # Delete least important first
            {"timestamp": {"order": "asc"}},  # Delete oldest first
        ]
        query["size"] = args.limit

        # Execute the search query to find memories to delete
        response = es_adapter.search(query=query, index_name=es_adapter.memory_index_name)
        hits = response.get("hits", {}).get("hits", [])
        total_matches = response.get("hits", {}).get("total", {})

        if isinstance(total_matches, dict):
            total_count = total_matches.get("value", 0)
        else:
            total_count = total_matches

        if not hits:
            print("No memories found matching the query criteria.")
            return False

        # Print memories to be deleted
        print(f"Found {total_count} memories matching criteria. Will delete up to {args.limit}:")
        print("-" * 80)

        for i, hit in enumerate(hits, 1):
            source = hit.get("_source", {})
            memory_id = hit.get("_id", "unknown")
            content = source.get("content", "")
            memory_type = source.get("memory_type", "unknown")
            importance = source.get("importance", 0)

            print(f"{i}. ID: {memory_id}")
            print(f"   Type: {memory_type}")
            print(f"   Importance: {importance}")
            print(f"   Content: {content[:100]}{'...' if len(content) > 100 else ''}")

        print("-" * 80)

        # Ask for confirmation unless --force is specified
        if not args.force:
            confirm = input(f"Delete these {len(hits)} memories? (y/N): ")
            if confirm.lower() not in ["y", "yes"]:
                print("Operation cancelled.")
                return False

        # Delete each memory
        success_count = 0

        for hit in hits:
            memory_id = hit.get("_id", "unknown")
            result = es_adapter.delete_memory(memory_id)
            if result:
                success_count += 1

        print(f"SUCCESS: Deleted {success_count} out of {len(hits)} memories.")
        return success_count > 0

    except Exception as e:
        print(f"ERROR: {str(e)}")
        traceback.print_exc()
        return False


def main():
    """Main entry point."""
    args = parse_arguments()

    try:
        # Create the Elasticsearch adapter
        es_adapter = ElasticsearchAdapter(
            host=args.host,
            memory_index_name=args.index or ElasticsearchAdapter.DEFAULT_MEMORY_INDEX,
        )

        # Execute the appropriate delete operation
        if args.id:
            # Delete by specific ID
            success = delete_by_id(es_adapter, args.id)
        else:
            # Delete by query parameters
            success = delete_by_query(es_adapter, args)

        return 0 if success else 1

    except Exception as e:
        print(f"ERROR: {str(e)}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
