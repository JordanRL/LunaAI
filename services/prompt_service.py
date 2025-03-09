"""
Prompt service for handling system prompt token replacement.

This service manages the three-stage prompt processing system:
1. Raw: The file as it is read from the file system with no tokens replaced
2. Pre-processed: The file with relatively stable tokens replaced
3. Compiled: The file as it is sent to the agent with all tokens replaced
"""

import json
import os
import re
from typing import Any, Dict, Optional

from domain.models.agent import AgentConfig


class PromptService:
    """
    Service for managing system prompt token replacement.

    This service handles the loading, caching, and token replacement for system prompts
    in the three-stage process described in TODO_FEATURES.md.
    """

    def __init__(self):
        """Initialize the prompt service."""
        self.raw_prompts: Dict[str, str] = {}
        self.preprocessed_prompts: Dict[str, str] = {}
        self.persona_files: Dict[str, str] = {}
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.prompt_generator = None  # Lazy-loaded to avoid circular imports

        # Load persona files
        self._load_persona_files()

    def _load_persona_files(self) -> None:
        """Load all persona config files from the persona_configs directory."""
        persona_dir = os.path.join(self.project_root, "persona_configs")

        for filename in os.listdir(persona_dir):
            if filename.endswith(".md"):
                file_path = os.path.join(persona_dir, filename)
                name = os.path.splitext(filename)[0].upper()

                with open(file_path, "r") as file:
                    self.persona_files[f"PERSONA_{name}"] = file.read()

    def load_raw_prompt(self, agent_name: str) -> str:
        """
        Load the raw system prompt for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Raw system prompt text
        """
        # Check if we already have this prompt cached
        if agent_name in self.raw_prompts:
            return self.raw_prompts[agent_name]

        # Determine file path - first try XML, then fall back to MD
        system_prompts_dir = os.path.join(self.project_root, "system_prompts", agent_name)
        xml_path = os.path.join(system_prompts_dir, "system.xml")

        if os.path.exists(xml_path):
            with open(xml_path, "r") as file:
                prompt = file.read()
        else:
            raise FileNotFoundError(f"No system prompt found for agent {agent_name}")

        # Cache the raw prompt
        self.raw_prompts[agent_name] = prompt
        return prompt

    def preprocess_prompt(
        self, agent_config: AgentConfig, token_replacements: Dict[str, Any]
    ) -> str:
        """
        Preprocess a system prompt by replacing relatively stable tokens.

        Args:
            agent_config: Agent configuration
            token_replacements: Tokens to replace

        Returns:
            Preprocessed system prompt
        """
        # Load the raw prompt if not already cached
        if agent_config.name.value not in self.raw_prompts:
            self.load_raw_prompt(agent_config.name.value)

        raw_prompt = self.raw_prompts[agent_config.name.value]
        preprocessed = raw_prompt

        # Replace persona information based on agent_config settings
        for persona_file, include in agent_config.persona_config.items():
            if include:
                persona_token = f"PERSONA_{persona_file.upper()}"
                preprocessed = self._replace_token(
                    preprocessed, persona_token, self.persona_files[persona_token]
                )

        # Replace user profile information if available
        for token, replacement in token_replacements.items():
            if isinstance(replacement, dict) or isinstance(replacement, list):
                replacement = json.dumps(replacement)
            elif not isinstance(replacement, str):
                replacement = str(replacement)
            preprocessed = self._replace_token(preprocessed, token, replacement)

        # Cache the preprocessed prompt
        self.preprocessed_prompts[agent_config.name.value] = preprocessed
        return preprocessed

    def compile_prompt(
        self,
        agent_name: str,
        token_replacements: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Compile a system prompt by replacing all dynamic tokens.

        Args:
            agent_name: Name of the agent
            token_replacements: Optional dictionary of token replacements to apply to the system prompt before sending it to the model.

        Returns:
            Fully compiled system prompt
        """
        # Get the preprocessed prompt
        if agent_name not in self.preprocessed_prompts:
            raise ValueError(f"Agent {agent_name} hasn't been preprocessed yet")

        preprocessed = self.preprocessed_prompts[agent_name]
        compiled = preprocessed

        # Replace all tokens that were passed in
        for token, replacement in token_replacements.items():
            compiled = self._replace_token(compiled, token, replacement)

        """
        We want to replace all the tokens that are left in the prompt with an empty string, but we
        also want to remove the XML tags that the leftover tokens are enclosed in.
        """
        if compiled.find("{PAD_PLEASURE}") != -1:
            pattern = r"<EmotionalState>[\s\S]*?</EmotionalState>"
            compiled = re.sub(pattern, "", compiled)
        if compiled.find("{INTUITION}") != -1:
            pattern = r"<Intuition>[\s\S]*?</Intuition>"
            compiled = re.sub(pattern, "", compiled)
        if compiled.find("{WORKING_MEMORY}") != -1:
            pattern = r"<WorkingMemory>[\s\S]*?</WorkingMemory>"
            compiled = re.sub(pattern, "", compiled)
        if compiled.find("{PERSONA_IDENTITY}") != -1:
            pattern = r"<YourPersonaIdentity>[\s\S]*?</YourPersonaIdentity>"
            compiled = re.sub(pattern, "", compiled)
        if compiled.find("{PERSONA_PERSONALITY}") != -1:
            pattern = r"<YourPersonality>[\s\S]*?</YourPersonality>"
            compiled = re.sub(pattern, "", compiled)
        if compiled.find("{PERSONA_BACKSTORY}") != -1:
            pattern = r"<YourBackstoryAndPersonalHistory>[\s\S]*?</YourBackstoryAndPersonalHistory>"
            compiled = re.sub(pattern, "", compiled)
        if compiled.find("{RECENT_MEMORY}") != -1:
            pattern = r"<RecentMemory>[\s\S]*?</RecentMemory>"
            compiled = re.sub(pattern, "", compiled)
        if compiled.find("{USER_PROFILE}") != -1:
            pattern = r"<UserProfile>[\s\S]*?</UserProfile>"
            compiled = re.sub(pattern, "", compiled)
        if compiled.find("{USER_RELATIONSHIP}") != -1:
            pattern = r"<UserRelationship>[\s\S]*?</UserRelationship>"
            compiled = re.sub(pattern, "", compiled)

        return compiled

    def _replace_token(self, text: str, token: str, replacement: str) -> str:
        """
        Replace a token in the text with its replacement.

        Args:
            text: Text to process
            token: Token to replace (without braces)
            replacement: Replacement text

        Returns:
            Text with token replaced
        """
        # Match token with surrounding braces
        pattern = r"\{" + token + r"\}"
        return re.sub(pattern, replacement, text)

    def invalidate_preprocessed(self, agent_name: Optional[str] = None) -> None:
        """
        Invalidate the preprocessed cache for an agent or all agents.

        Args:
            agent_name: Name of the agent to invalidate, or None for all agents
        """
        if agent_name:
            if agent_name in self.preprocessed_prompts:
                del self.preprocessed_prompts[agent_name]
        else:
            self.preprocessed_prompts.clear()

    def reload_persona_files(self) -> None:
        """Reload all persona files from disk and invalidate all preprocessed prompts."""
        self.persona_files.clear()
        self._load_persona_files()
        self.invalidate_preprocessed()
