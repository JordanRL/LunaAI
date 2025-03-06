# Features

## System Prompt Replacement Tokens

Several planned features require a generalized and clean way to dynamically replace tokens such as {TOKEN} within an agent's system prompt. For some features it would be most convenient to do this replacement when the API request is made, and for others it would be most convenient to do at application start.

The system prompts for each agent would have three stages:

- Raw file: The file as it is read from the file system, with no tokens replaced.
- Pre-Processed: The file has had relatively stable tokens replaced, with highly dynamic tokens still unreplaced.
- Compiled: The file as it is sent to the agent, with all tokens replaced.

Both the raw file and the pre-processed files would need to be stored in a variable in memory. The raw files would be pre-processed once during startup, and then processed again from the raw file at any point that the information injected during the pre-processing stage changes.

### Short Term Memory

To avoid having Luna re-request some of the same memory information with every conversation turn, there should be a space in the dispatcher prompt that is dedicated to "short term memory" or "working memory" where the memories that are most recently relevant that Luna has actually retrieved are stored and then injected into the prompt for future conversation turns.

The size of this could be configurable, adjustable, and dynamic. It would be best to do this replacement just before the API call to allow the most up-to-date recall information to be used, at the compilation stage.

### User Profile

This should be something that is available in the system prompt so that Luna doesn't need to make as many requests asking for contextual information about who she is talking to. This could be done at the pre-processor stage.

### User Relationship Information

This is something that should be injected into the relationship_manager prompt so that it doesn't need a tool request to grab it. This can be done at the pre-processor stage.

### Current Emotional State

The emotional state information which is tracked in the application for Luna. This will be injected into the emotion_processor prompt at the compilation stage.

## Subconsciousness Agent

Developing an agent that is outside of the normal agent pipeline and response structure could be interesting. Such an agent would get a copy of the conversation turn, and then get the chance to insert things into the system prompt, or modify things in the system prompt without the knowledge of the normal dispatcher-agent-outputter workflow. This could result in something like intuition emerging.

## Heartbeat

Create an out-of-band heartbeat prompt. The idea behind this is to give Luna occasional or scheduled "heartbeat" events where instead of responding to a user message, she is given a message such as "[HEARTBEAT] Timestamp: 2025-03-05 22:15:12" and allowed to use token generation for her own purposes, thinking, and so on, instead of producing output for a chat.

The potential for this to produce emergent behavior is enticing and fascinating.