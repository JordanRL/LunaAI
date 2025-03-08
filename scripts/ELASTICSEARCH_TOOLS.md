# Elasticsearch Administration Tools

These utilities help you manage Luna's Elasticsearch storage. They provide command-line interfaces for common administrative tasks related to memory management and index information.

## Prerequisites

- Python 3.9+
- Elasticsearch server running (default: http://localhost:9200)
- Project environment set up (dependencies installed)

## Available Tools

### 1. Insert Memory from File (`es_insert_memory.py`)

Inserts a memory from a JSON file into Luna's Elasticsearch index.

```bash
./es_insert_memory.py example_memory.json [options]
```

Options:
- `--host URL` - Elasticsearch host URL (default: http://localhost:9200)
- `--index NAME` - Override the default index name
- `--rebuild` - Rebuild the index before inserting (WARNING: deletes existing memories)

Example JSON file format:
```json
{
  "type": "episodic",
  "content": "User shared that they enjoy hiking in the mountains.",
  "importance": 7,
  "user_id": "user123",
  "keywords": ["hiking", "mountains"],
  "emotion": {
    "pleasure": 0.8,
    "arousal": 0.6,
    "dominance": 0.5
  },
  "participants": ["user123", "Luna"],
  "context": "Casual conversation about hobbies"
}
```

### 2. Count Memories (`es_count_memories.py`)

Counts the memories in an Elasticsearch index, optionally filtered by type or user.

```bash
./es_count_memories.py [options]
```

Options:
- `--host URL` - Elasticsearch host URL
- `--index NAME` - Override the default index name
- `--memory-type TYPE` - Filter by memory type (episodic, emotional, semantic, relationship)
- `--user-id ID` - Filter by user ID

### 3. List Memories (`es_list_memories.py`)

Lists memories from an Elasticsearch index with various filtering options.

```bash
./es_list_memories.py [options]
```

Options:
- `--host URL` - Elasticsearch host URL
- `--index NAME` - Override the default index name
- `--memory-type TYPE` - Filter by memory type
- `--user-id ID` - Filter by user ID
- `--limit N` - Maximum number of memories to return (default: 100)
- `--keywords LIST` - Filter by keywords (space-separated)
- `--content TEXT` - Search for text in memory content
- `--importance N` - Filter by minimum importance level (1-10)
- `--json` - Output in JSON format
- `--full` - Show full memory details (default is summary)

### 4. Delete Memory (`es_delete_memory.py`)

Deletes memories from an Elasticsearch index, either by ID or by query.

```bash
# Delete by ID
./es_delete_memory.py --id MEMORY_ID [options]

# Delete by query
./es_delete_memory.py --query [query options]
```

Options:
- `--host URL` - Elasticsearch host URL
- `--index NAME` - Override the default index name
- `--memory-type TYPE` - Filter by memory type (with --query)
- `--user-id ID` - Filter by user ID (with --query)
- `--keywords LIST` - Filter by keywords (with --query)
- `--content TEXT` - Search for text in memory content (with --query)
- `--importance N` - Filter by maximum importance level (with --query)
- `--limit N` - Maximum number of memories to delete (default: 10)
- `--force` - Skip confirmation prompt when deleting multiple memories

## Examples

### Insert a memory from a file

```bash
./es_insert_memory.py example_memory.json
```

### Count all memories

```bash
./es_count_memories.py
```

### Count all emotional memories for a specific user

```bash
./es_count_memories.py --memory-type emotional --user-id user123
```

### List the 10 most recent episodic memories

```bash
./es_list_memories.py --memory-type episodic --limit 10
```

### List memories containing "hiking" in content

```bash
./es_list_memories.py --content hiking
```

### Delete a specific memory by ID

```bash
./es_delete_memory.py --id 1a2b3c4d5e6f7g8h9i0j
```

### Delete all semantic memories with importance 3 or less

```bash
./es_delete_memory.py --query --memory-type semantic --importance 3
```

### 5. Update Memory Timestamps (`es_update_timestamp.py`)

Updates the timestamp and optionally last_accessed fields for one or more memories in the Elasticsearch index.

```bash
# Update a single memory by ID
./es_update_timestamp.py --id MEMORY_ID --timestamp "2025-03-07T12:00:00.000Z" [options]

# Update timestamp and last_accessed
./es_update_timestamp.py --id MEMORY_ID --timestamp "2025-03-07T12:00:00.000Z" --last-accessed "2025-03-07T15:30:00.000Z" [options]

# Update multiple memories by query
./es_update_timestamp.py --query "search term" --timestamp "2025-03-07T12:00:00.000Z" [options]
```

Options:
- `--timestamp` - New timestamp value (ISO format, required)
- `--last-accessed` - New last_accessed value (ISO format, optional)
- `--host URL` - Elasticsearch host URL (default: http://localhost:9200)
- `--index NAME` - Override the default index name
- `--memory-type TYPE` - Filter by memory type (with --query)
- `--user-id ID` - Filter by user ID (with --query)
- `--limit N` - Maximum number of memories to update (default: 100, with --query)
- `--dry-run` - Show what would be updated without making changes
- `--force` - Skip confirmation prompt
- `--verbose` - Show detailed information

Examples:

```bash
# Update a specific memory's timestamp
./es_update_timestamp.py --id 1a2b3c4d5e6f7g8h9i0j --timestamp "2025-03-07T12:00:00.000Z"

# Update all memories containing "hiking" to have yesterday's date
./es_update_timestamp.py --query "hiking" --timestamp "2025-03-06T00:00:00.000Z"

# Update all episodic memories for a user (dry run first)
./es_update_timestamp.py --query "" --memory-type episodic --user-id user123 --timestamp "2025-01-01T00:00:00.000Z" --dry-run

# Update both timestamp and last_accessed
./es_update_timestamp.py --id 1a2b3c4d5e6f7g8h9i0j --timestamp "2025-03-01T00:00:00.000Z" --last-accessed "2025-03-07T15:30:00.000Z"
```

### 6. List Elasticsearch Indices (`es_list_indices.py`)

Lists all Elasticsearch indices with optional detailed information.

```bash
./es_list_indices.py [options]
```

Options:
- `--host URL` - Elasticsearch host URL (default: http://localhost:9200)
- `--detailed` - Display detailed information about each index
- `--pattern PATTERN` - Index name pattern to filter by (default: "*")
- `--json` - Output in JSON format

## Examples for Index Management

### List all indices

```bash
./es_list_indices.py
```

### List all luna-related indices with detailed information

```bash
./es_list_indices.py --pattern "luna-*" --detailed
```

### Get detailed JSON output for a specific index

```bash
./es_list_indices.py --pattern "luna-memories" --detailed --json
```

### 6. Delete Elasticsearch Indices (`es_delete_index.py`)

Permanently delete one or more Elasticsearch indices.

```bash
# Delete a specific index
./es_delete_index.py --index INDEX_NAME [options]

# Delete multiple indices matching a pattern
./es_delete_index.py --pattern "PATTERN*" [options]
```

Options:
- `--host URL` - Elasticsearch host URL (default: http://localhost:9200)
- `--force` - Skip confirmation prompt (WARNING: immediate deletion)

### Delete a specific index

```bash
./es_delete_index.py --index luna-test-memories
```

### Delete all test indices

```bash
./es_delete_index.py --pattern "test-*"
```

### Force delete without confirmation (for scripts)

```bash
./es_delete_index.py --index luna-old-index --force
```

### 7. Rebuild Elasticsearch Indices (`es_rebuild_indices.py`)

Rebuild Luna's Elasticsearch indices with proper mappings and settings using the adapter.

```bash
./es_rebuild_indices.py [options]
```

Options:
- `--host URL` - Elasticsearch host URL (default: http://localhost:9200)
- `--index-type TYPE` - Type of index to rebuild (choices: all, memories, profiles, relationships, default: all)
- `--memory-index NAME` - Override the default memory index name
- `--profile-index NAME` - Override the default user profile index name
- `--relationship-index NAME` - Override the default user relationship index name
- `--force` - Skip confirmation prompt

### Rebuild all indices

```bash
./es_rebuild_indices.py
```

### Rebuild only the memory index

```bash
./es_rebuild_indices.py --index-type memories
```

### Rebuild with custom index names

```bash
./es_rebuild_indices.py --memory-index custom-memories --profile-index custom-profiles
```

### Force rebuild for scripting

```bash
./es_rebuild_indices.py --force
```

### 8. Interactive Memory Creator (`es_interactive_memory.py`)

Interactive tool to create memory JSON files for Luna through a guided process.

```bash
./es_interactive_memory.py [options]
```

Options:
- `--output PATH` - Output file path (default: memory_TIMESTAMP.json)
- `--insert` - Insert the created memory into Elasticsearch after creation
- `--host URL` - Elasticsearch host URL (when using --insert)
- `--index NAME` - Override the default index name (when using --insert)

This interactive tool will guide you through the process of creating:
- Episodic memories (events, conversations)
- Semantic memories (facts, knowledge)
- Emotional memories (feelings, responses)
- Relationship memories (connection patterns)

The tool validates your input to ensure it meets the requirements for Luna's memory system.

### Create a memory and save to a JSON file

```bash
./es_interactive_memory.py
```

### Create a memory and directly insert it into Elasticsearch

```bash
./es_interactive_memory.py --insert
```

### Create a memory with a specific output file name

```bash
./es_interactive_memory.py --output my_memory.json
```

### 9. Interactive User Profile Creator (`es_interactive_profile.py`)

Interactive tool to create user profiles for Luna through a guided process.

```bash
./es_interactive_profile.py [options]
```

Options:
- `--output PATH` - Output file path (default: user_profile_USERID_TIMESTAMP.json)
- `--insert` - Insert the created profile into Elasticsearch after creation
- `--host URL` - Elasticsearch host URL (when using --insert)
- `--index NAME` - Override the default user profile index name (when using --insert)

This interactive tool will guide you through the process of creating a comprehensive user profile including:
- Biographical information (name, age, location, etc.)
- Personal context (family, pets, living situation, life events)
- Preferences (topics, media, food, activities)
- Behavioral patterns (communication style, learning preferences)
- Values and beliefs (core values, worldview, ethics)

### Create a user profile and save to a JSON file

```bash
./es_interactive_profile.py
```

### Create a user profile and directly insert it into Elasticsearch

```bash
./es_interactive_profile.py --insert
```

### 10. Interactive User Relationship Creator (`es_interactive_relationship.py`)

Interactive tool to create user relationships for Luna through a guided process.

```bash
./es_interactive_relationship.py [options]
```

Options:
- `--output PATH` - Output file path (default: user_relationship_USERID_TIMESTAMP.json)
- `--insert` - Insert the created relationship into Elasticsearch after creation
- `--host URL` - Elasticsearch host URL (when using --insert)
- `--index NAME` - Override the default user relationship index name (when using --insert)

This interactive tool will guide you through the process of creating a detailed user relationship including:
- Relationship stage information
- Emotional dynamics (comfort level, trust, sensitive topics)
- Relationship history (key moments, inside references)
- Conversation patterns (successful approaches, communication adjustments)
- Luna's subjective experience (connection quality, growth, authenticity)
- Intervention strategies (anxiety response, motivation support, conflict resolution)

### Create a user relationship and save to a JSON file

```bash
./es_interactive_relationship.py
```

### Create a user relationship and directly insert it into Elasticsearch

```bash
./es_interactive_relationship.py --insert
```
