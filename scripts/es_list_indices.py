#!/usr/bin/env python
"""
Command-line utility for listing Elasticsearch indices in Luna's system.
"""

import argparse
import json
import sys
import traceback
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from elasticsearch import Elasticsearch


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="List Elasticsearch indices in Luna's system.")

    # Optional arguments
    parser.add_argument(
        "--host",
        default="http://localhost:9200",
        help="Elasticsearch host URL (default: http://localhost:9200)",
    )
    parser.add_argument(
        "--detailed", action="store_true", help="Display detailed information about each index"
    )
    parser.add_argument(
        "--pattern", default="*", help='Index name pattern to filter by (default: "*")'
    )
    parser.add_argument("--json", action="store_true", help="Output in JSON format")

    return parser.parse_args()


def format_bytes(size_bytes):
    """Format bytes to human-readable form."""
    if size_bytes == 0:
        return "0 B"

    size_names = ("B", "KB", "MB", "GB", "TB")
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024
        i += 1

    return f"{size_bytes:.2f} {size_names[i]}"


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

        # Get indices information
        indices = es.indices.get(index=args.pattern)

        if not indices:
            print(f"No indices found matching pattern: {args.pattern}")
            return 0

        # If detailed information is requested, get stats for each index
        index_stats = {}
        if args.detailed:
            stats_response = es.indices.stats(index=args.pattern)
            index_stats = stats_response.get("indices", {})

        # Structure output based on format
        if args.json:
            # JSON output
            if args.detailed:
                # Include stats in the output
                result = {}
                for index_name, index_info in indices.items():
                    result[index_name] = {
                        "settings": index_info.get("settings", {}),
                        "mappings": index_info.get("mappings", {}),
                        "stats": index_stats.get(index_name, {}),
                    }
                print(json.dumps(result, indent=2))
            else:
                # Just index names and basic info
                print(json.dumps(indices, indent=2))
        else:
            # Text output
            print(f"Elasticsearch host: {args.host}")
            print(f"Found {len(indices)} indices matching pattern: {args.pattern}")
            print("-" * 80)

            for index_name in sorted(indices.keys()):
                index_info = indices[index_name]
                settings = index_info.get("settings", {})

                # Extract basic info
                creation_date = settings.get("index", {}).get("creation_date", "Unknown")
                try:
                    # Convert from epoch millis to readable date
                    from datetime import datetime

                    creation_date = datetime.fromtimestamp(int(creation_date) / 1000).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                except (ValueError, TypeError):
                    pass

                num_shards = settings.get("index", {}).get("number_of_shards", "Unknown")
                num_replicas = settings.get("index", {}).get("number_of_replicas", "Unknown")

                print(f"Index name: {index_name}")
                print(f"  Created: {creation_date}")
                print(f"  Shards: {num_shards}, Replicas: {num_replicas}")

                if args.detailed and index_name in index_stats:
                    stats = index_stats[index_name]
                    primaries = stats.get("primaries", {})

                    # Get document count
                    doc_count = primaries.get("docs", {}).get("count", 0)

                    # Get size
                    store_size = primaries.get("store", {}).get("size_in_bytes", 0)
                    human_size = format_bytes(store_size)

                    print(f"  Documents: {doc_count}")
                    print(f"  Size: {human_size}")

                    # Get health if available
                    health_response = es.cluster.health(index=index_name)
                    health = health_response.get("status", "unknown")
                    print(f"  Health: {health}")

                # Print mapping keys (field names) at top level
                if args.detailed:
                    mappings = index_info.get("mappings", {})
                    properties = mappings.get("properties", {})
                    if properties:
                        field_names = list(properties.keys())
                        if len(field_names) > 10:
                            field_preview = ", ".join(field_names[:10]) + "..."
                        else:
                            field_preview = ", ".join(field_names)
                        print(f"  Fields: {field_preview}")

                print("-" * 80)

        return 0

    except Exception as e:
        print(f"ERROR: {str(e)}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
