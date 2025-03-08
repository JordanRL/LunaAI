#!/usr/bin/env python
"""
Command-line utility for counting memories in Luna's Elasticsearch memory index.
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
    parser = argparse.ArgumentParser(description="Count memories in Luna's Elasticsearch index.")

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
        help="Filter by memory type",
    )
    parser.add_argument("--user-id", help="Filter by user ID")

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()

    try:
        # Create the Elasticsearch adapter
        es_adapter = ElasticsearchAdapter(
            host=args.host,
            memory_index_name=args.index or ElasticsearchAdapter.DEFAULT_MEMORY_INDEX,
        )

        # Build the query
        query = {"query": {"match_all": {}}}

        # Add filters
        filters = []
        if args.memory_type:
            filters.append({"term": {"memory_type": args.memory_type}})
        if args.user_id:
            filters.append({"term": {"user_id": args.user_id}})

        # Apply filters if any
        if filters:
            query = {"query": {"bool": {"filter": filters}}}

        # Execute the count query
        response = es_adapter.es.count(index=es_adapter.memory_index_name, body=query)
        count = response.get("count", 0)

        # Print results
        print(f"Index: {es_adapter.memory_index_name}")
        if args.memory_type:
            print(f"Memory type: {args.memory_type}")
        if args.user_id:
            print(f"User ID: {args.user_id}")
        print(f"Total memories: {count}")

        return 0

    except Exception as e:
        print(f"ERROR: {str(e)}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
