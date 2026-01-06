# PydanticAI Refactoring Plan

This document outlines the step-by-step plan for refactoring the Luna system to leverage PydanticAI while maintaining backward compatibility during the transition.

## Phase 1: Core Infrastructure

### 1.1 Create Basic Adapters
- ✅ Create adapter module for converting between domain models and PydanticAI models
- ✅ Create example PydanticAI implementation for reference

### 1.2 Restructure Configuration
- Create PydanticAI-compatible model configuration
- Add provider-agnostic model settings
- Implement environment configuration for multiple providers

### 1.3 Tool Registration System
- Convert tool registration to use PydanticAI's function tool pattern
- Create tool registry that works with both legacy and PydanticAI tools
- Enable tools to be registered with multiple agent types

## Phase 2: Agent Refactoring

### 2.1 Agent Implementation
- Create PydanticAI agent factory
- Implement agent configuration loading for PydanticAI agents
- Enable system prompt compilation for PydanticAI agents

### 2.2 Conversation History
- Modify conversation service to work with PydanticAI message history
- Create adapter functions for message history conversion
- Implement context tracking for multi-agent conversations

### 2.3 Agent Testing
- Create test suite for PydanticAI agent integration
- Test cross-compatibility between legacy and PydanticAI systems
- Create utilities for agent debugging and monitoring

## Phase 3: Hub Architecture

### 3.1 Multi-Agent Orchestration
- Implement hub architecture using PydanticAI's multi-agent capabilities
- Create routing mechanism for agent-to-agent communication
- Enable structured data exchange between agents

### 3.2 Metrics and Monitoring
- Capture metrics from PydanticAI agent executions
- Track token usage and API limits
- Implement usage reporting and analytics

### 3.3 Integration Testing
- End-to-end tests for the complete multi-agent system
- Performance comparison between legacy and PydanticAI implementations
- Evaluate API compatibility across multiple providers

## Phase 4: Feature Enhancements

### 4.1 Provider-Specific Features
- Enable model-specific optimizations when available
- Implement streaming responses
- Support for thinking mode agents

### 4.2 Structured Data
- Convert response handling to use structured outputs
- Create domain-specific validation for agent responses
- Enable automatic result validation

### 4.3 Advanced Tools
- Support for tool parameters with complex types
- Implement tool result validation
- Create retry mechanisms for tool failures

## Migration Transition Strategy

### Approach 1: Shadow Implementation
- Create PydanticAI implementations alongside legacy code
- Test both implementations in parallel
- Switch components gradually as they are validated

### Approach 2: Domain Boundary Migration
- Convert outer layers first (adapters, tools)
- Gradually migrate inward to core components
- Maintain compatibility layers between old and new systems

### Approach 3: Agent-by-Agent Migration
- Convert one agent type completely and test
- Move to the next agent after validating
- Ensure cross-compatibility during migration

## Technical Challenges

### Challenge 1: System Prompt Management
- PydanticAI uses a different system prompt mechanism
- Need to convert our XML-based prompts to PydanticAI format
- Maintain token replacement capabilities

### Challenge 2: Tool Registration
- Our tools use JSON schema directly
- PydanticAI generates schemas from Python types
- Need to ensure consistent tool definitions

### Challenge 3: Message Formats
- Different internal representation of messages
- Need to handle vendor-specific content formats
- Maintain compatibility with existing services

## Next Steps

1. Begin with basic adapter implementation
2. Create PydanticAI agent factory
3. Convert one agent type completely as proof of concept
4. Develop testing strategy for both systems
5. Gradually expand to more agent types
