#!/usr/bin/env python
"""
Command-line utility for listing memories in Luna's Elasticsearch memory index.
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
    parser = argparse.ArgumentParser(description="List memories in Luna's Elasticsearch index.")

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
    parser.add_argument(
        "--limit", type=int, default=100, help="Maximum number of memories to return (default: 100)"
    )
    parser.add_argument("--keywords", nargs="*", help="Filter by keywords")
    parser.add_argument("--content", help="Search for text in memory content")
    parser.add_argument(
        "--importance",
        type=int,
        choices=range(1, 11),
        help="Filter by minimum importance level (1-10)",
    )
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument(
        "--full", action="store_true", help="Show full memory details (default is summary)"
    )

    return parser.parse_args()


def format_datetime(dt_str):
    """Format datetime string for display."""
    if not dt_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return dt_str


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

        # Add filters to a bool query
        must_clauses = []
        filter_clauses = []

        # Filter by memory type
        if args.memory_type:
            filter_clauses.append({"term": {"memory_type": args.memory_type}})

        # Filter by user ID
        if args.user_id:
            filter_clauses.append({"term": {"user_id": args.user_id}})

        # Filter by importance
        if args.importance:
            filter_clauses.append({"range": {"importance": {"gte": args.importance}}})

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
        if args.index == ElasticsearchAdapter.DEFAULT_MEMORY_INDEX:
            query["sort"] = [{"timestamp": {"order": "desc"}}, {"importance": {"order": "desc"}}]
        elif args.index == ElasticsearchAdapter.DEFAULT_USER_PROFILE_INDEX:
            # Nothing for now
            pass
        elif args.index == ElasticsearchAdapter.DEFAULT_USER_RELATIONSHIP_INDEX:
            # Nothing for now
            pass
        query["size"] = args.limit

        # Execute the search query
        response = es_adapter.search(query=query, index_name=es_adapter.memory_index_name)
        hits = response.get("hits", {}).get("hits", [])
        total = response.get("hits", {}).get("total", {})

        if isinstance(total, dict):
            total_count = total.get("value", 0)
        else:
            total_count = total

        # Format and output the results
        if args.json:
            # JSON output format
            if args.full:
                output = {"total": total_count, "memories": [hit["_source"] for hit in hits]}
            else:
                output = {
                    "total": total_count,
                    "memories": [
                        {
                            "id": hit["_id"],
                            "content": (
                                hit["_source"].get("content", "")[:100] + "..."
                                if len(hit["_source"].get("content", "")) > 100
                                else hit["_source"].get("content", "")
                            ),
                            "memory_type": hit["_source"].get("memory_type", ""),
                            "importance": hit["_source"].get("importance", 0),
                            "timestamp": hit["_source"].get("timestamp", ""),
                            "user_id": hit["_source"].get("user_id", ""),
                        }
                        for hit in hits
                    ],
                }
            print(json.dumps(output, indent=2))
        else:
            # Text output format
            print(f"Index: {es_adapter.memory_index_name}")
            print(f"Total memories: {total_count}")
            print(f"Showing: {len(hits)}")
            print("-" * 80)

            for hit in hits:
                source = hit["_source"]
                memory_id = hit["_id"]
                content = source.get("content", "")
                memory_type = source.get("memory_type", "")
                importance = source.get("importance", 0)
                timestamp = format_datetime(source.get("timestamp", ""))
                user_id = source.get("user_id", "N/A")

                print(f"ID: {memory_id}")
                print(f"Type: {memory_type}")
                print(f"Importance: {importance}")
                print(f"Created: {timestamp}")
                print(f"User: {user_id}")

                if args.full:
                    # Show full content and all fields
                    print(f"Content: {content}")

                    # Show type-specific fields
                    if memory_type == "episodic":
                        participants = source.get("participants", [])
                        context = source.get("context", "")
                        print(
                            f"Participants: {', '.join(participants) if participants else 'None'}"
                        )
                        print(f"Context: {context}")

                    elif memory_type == "semantic":
                        certainty = source.get("certainty", 0)
                        domain = source.get("domain", "")
                        source_name = source.get("source", "")
                        print(f"Certainty: {certainty}")
                        print(f"Domain: {domain}")
                        print(f"Source: {source_name}")

                    elif memory_type == "emotional":
                        trigger = source.get("trigger", "")
                        event_pleasure = source.get("event_pleasure", 0)
                        event_arousal = source.get("event_arousal", 0)
                        print(f"Trigger: {trigger}")
                        print(
                            f"Emotion: pleasure={event_pleasure:.2f}, arousal={event_arousal:.2f}"
                        )

                    elif memory_type == "relationship":
                        relationship_type = source.get("relationship_type", "")
                        closeness = source.get("closeness", 0)
                        trust = source.get("trust", 0)
                        print(f"Relationship type: {relationship_type}")
                        print(f"Closeness: {closeness:.2f}")
                        print(f"Trust: {trust:.2f}")

                    # Show common fields
                    keywords = source.get("keywords", [])
                    if keywords:
                        print(f"Keywords: {', '.join(keywords)}")
                else:
                    # Show summary
                    content_preview = content[:100] + "..." if len(content) > 100 else content
                    print(f"Content: {content_preview}")

                print("-" * 80)

        return 0

    except Exception as e:
        print(f"ERROR: {str(e)}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
