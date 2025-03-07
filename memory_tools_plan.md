# LunaAI Memory System Tools Implementation Plan

## Overview
We'll implement a comprehensive set of memory tools to interact with the LunaAI memory system, using a hybrid approach that offers both general and specialized tools.

## Tool Structure

### 1. General Memory Read Tool
**MemoryReadTool**
- Purpose: Search across all memory types
- Parameters:
  - `query`: Text search
  - `importance_threshold`: Minimum importance level
  - `limit`: Number of results (default 5)
  - `emotional_state`: Optional emotional context
  - `keywords`: List of keywords to search for
  - `user_id`: Optional filter by user
  - `memory_type`: Optional filter by type

### 2. Specialized Memory Write Tools (Create & Update)
Each tool will use a JSON Schema with `oneOf` to handle both creation and update:

**EpisodicMemoryWriteTool**
- Create parameters (required: content, participants, context):
  - `content`: Memory content text
  - `participants`: List of people involved
  - `context`: Situation context
  - `importance`: Importance rating (1-10)
  - `keywords`: List of keywords
  - `emotional_state`: Optional emotional context
  - `user_id`: Optional user association
- Update parameters (required: memory_id):
  - `memory_id`: ID of memory to update
  - Any fields from above that need updating

**SemanticMemoryWriteTool**
- Create parameters (required: content, domain, certainty):
  - `content`: Memory content text
  - `domain`: Knowledge domain
  - `certainty`: Confidence level
  - `verifiability`: Verifiability rating
  - `source`: Information source
  - `source_reliability`: Source reliability rating
  - `importance`: Importance rating
  - `keywords`: List of keywords
  - `emotional_state`: Optional emotional context
  - `user_id`: Optional user association
- Update parameters (required: memory_id):
  - `memory_id`: ID of memory to update
  - Any fields from above that need updating

**EmotionalMemoryWriteTool**
- Create parameters (required: content, trigger, emotional_state):
  - `content`: Memory content text
  - `trigger`: What triggered the emotion
  - `event_pleasure`: Pleasure rating
  - `event_arousal`: Arousal rating
  - `event_dominance`: Dominance rating
  - `emotional_state`: Emotional context
  - `importance`: Importance rating
  - `keywords`: List of keywords
  - `user_id`: Optional user association
- Update parameters (required: memory_id):
  - `memory_id`: ID of memory to update
  - Any fields from above that need updating

**RelationshipMemoryWriteTool**
- Create parameters (required: content, relationship_type):
  - `content`: Memory content text
  - `relationship_type`: Type of relationship
  - `closeness`: Closeness rating
  - `trust`: Trust rating
  - `apprehension`: Apprehension rating
  - `shared_experiences`: List of shared experiences
  - `connection_points`: List of connection points
  - `inside_references`: List of inside references
  - `importance`: Importance rating
  - `keywords`: List of keywords
  - `emotional_state`: Optional emotional context
  - `user_id`: Optional user association
- Update parameters (required: memory_id):
  - `memory_id`: ID of memory to update
  - Any fields from above that need updating

### 3. Specialized Memory Read Tools

**EpisodicMemoryReadTool**
- All common fields from MemoryReadTool
- Plus episodic-specific:
  - `participants`: List of people to match
  - `context`: Situation context to match

**SemanticMemoryReadTool**
- All common fields from MemoryReadTool
- Plus semantic-specific:
  - `domain`: Knowledge domain
  - `certainty_threshold`: Minimum confidence level
  - `verifiability_threshold`: Minimum verifiability
  - `source`: Filter by information source
  - `source_reliability_threshold`: Minimum source reliability

**EmotionalMemoryReadTool**
- All common fields from MemoryReadTool
- Plus emotional-specific:
  - `trigger`: What triggered the emotion
  - `event_pleasure_threshold`: Minimum pleasure rating
  - `event_arousal_threshold`: Minimum arousal rating
  - `event_dominance_threshold`: Minimum dominance rating

**RelationshipMemoryReadTool**
- All common fields from MemoryReadTool
- Plus relationship-specific:
  - `relationship_type`: Type of relationship
  - `closeness_threshold`: Minimum closeness
  - `trust_threshold`: Minimum trust
  - `apprehension_threshold`: Minimum apprehension
  - `shared_experiences`: Filter by shared experiences
  - `connection_points`: Filter by connection points
  - `inside_references`: Filter by inside references

## Implementation Steps

1. **Create Tool Schema Definitions**
   - Define JSON Schema for each tool
   - Ensure proper validation of required fields
   - Document usage examples

2. **Implement Tool Handlers**
   - Create handlers for each tool
   - Map tool parameters to appropriate memory/query objects
   - Connect to MemoryService for storage/retrieval

3. **Tool Registration**
   - Register tools with LunaAI's tool registry
   - Ensure proper discovery by agents

4. **Testing**
   - Create unit tests for each tool
   - Create integration tests between tools and memory service
   - Verify all operations (create, update, read) work as expected

5. **Documentation**
   - Document each tool's usage for agents
   - Provide examples of common operations

This plan provides a clear path to implementing a comprehensive set of memory tools that will make it easy for agents to interact with the LunaAI memory system, while maintaining proper separation of concerns and clear interfaces.