"""
Prompt service for handling system prompt token replacement.

This service manages the three-stage prompt processing system:
1. Raw: The file as it is read from the file system with no tokens replaced
2. Pre-processed: The file with relatively stable tokens replaced
3. Compiled: The file as it is sent to the agent with all tokens replaced
"""
import os
import re
from typing import Dict, Any, Optional

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
        
        # Load persona files
        self._load_persona_files()
    
    def _load_persona_files(self) -> None:
        """Load all persona config files from the persona_configs directory."""
        persona_dir = os.path.join(self.project_root, "persona_configs")
        
        for filename in os.listdir(persona_dir):
            if filename.endswith(".md"):
                file_path = os.path.join(persona_dir, filename)
                name = os.path.splitext(filename)[0].upper()
                
                with open(file_path, 'r') as file:
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
        md_path = os.path.join(system_prompts_dir, "system.md")
        
        if os.path.exists(xml_path):
            with open(xml_path, 'r') as file:
                prompt = file.read()
        elif os.path.exists(md_path):
            with open(md_path, 'r') as file:
                prompt = file.read()
        else:
            raise FileNotFoundError(f"No system prompt found for agent {agent_name}")
        
        # Cache the raw prompt
        self.raw_prompts[agent_name] = prompt
        return prompt
    
    def preprocess_prompt(self, agent_name: str, agent_config: Dict[str, Any]) -> str:
        """
        Preprocess a system prompt by replacing relatively stable tokens.
        
        Args:
            agent_name: Name of the agent
            agent_config: Agent configuration data from agent.json
            
        Returns:
            Preprocessed system prompt
        """
        # Load the raw prompt if not already cached
        if agent_name not in self.raw_prompts:
            self.load_raw_prompt(agent_name)
        
        raw_prompt = self.raw_prompts[agent_name]
        preprocessed = raw_prompt
        
        # Replace persona information based on agent_config settings
        persona_config = agent_config.get("persona_config", {})
        
        # For each persona file, check if it should be included for this agent
        for token_name, content in self.persona_files.items():
            config_key = token_name.lower()
            if persona_config.get(config_key, False):
                preprocessed = self._replace_token(preprocessed, token_name, content)
            else:
                # If not included, replace with empty string
                preprocessed = self._replace_token(preprocessed, token_name, "")
        
        # Replace user profile information if available
        # This could be expanded based on the TODO_FEATURES.md specifications
        
        # Cache the preprocessed prompt
        self.preprocessed_prompts[agent_name] = preprocessed
        return preprocessed
    
    def compile_prompt(
        self, 
        agent_name: str, 
        working_memory: Optional[str] = None,
        user_profile: Optional[str] = None,
        emotional_state: Optional[Dict[str, Any]] = None,
        intuition: Optional[str] = None
    ) -> str:
        """
        Compile a system prompt by replacing all dynamic tokens.
        
        Args:
            agent_name: Name of the agent
            working_memory: Current working memory content
            user_profile: Current user profile information
            emotional_state: Current emotional state data
            intuition: Current intuition content
            
        Returns:
            Fully compiled system prompt
        """
        # Get the preprocessed prompt
        if agent_name not in self.preprocessed_prompts:
            raise ValueError(f"Agent {agent_name} hasn't been preprocessed yet")
        
        preprocessed = self.preprocessed_prompts[agent_name]
        compiled = preprocessed
        
        # Replace working memory
        if working_memory is not None:
            compiled = self._replace_token(compiled, "WORKING_MEMORY", working_memory)
        else:
            compiled = self._replace_token(compiled, "WORKING_MEMORY", "No relevant memories at this time.")
        
        # Replace user profile
        if user_profile is not None:
            compiled = self._replace_token(compiled, "USER_PROFILE", user_profile)
        else:
            compiled = self._replace_token(compiled, "USER_PROFILE", "No user profile information available.")
        
        # Replace emotional state values
        if emotional_state is not None:
            compiled = self._replace_token(compiled, "PAD_PLEASURE", str(emotional_state.get("pleasure", 0.5)))
            compiled = self._replace_token(compiled, "PAD_AROUSAL", str(emotional_state.get("arousal", 0.5)))
            compiled = self._replace_token(compiled, "PAD_DOMINANCE", str(emotional_state.get("dominance", 0.5)))
            compiled = self._replace_token(compiled, "PAD_DESCRIPTOR", emotional_state.get("descriptor", "neutral"))
        else:
            compiled = self._replace_token(compiled, "PAD_PLEASURE", "0.5")
            compiled = self._replace_token(compiled, "PAD_AROUSAL", "0.5")
            compiled = self._replace_token(compiled, "PAD_DOMINANCE", "0.5")
            compiled = self._replace_token(compiled, "PAD_DESCRIPTOR", "neutral")
        
        # Replace intuition
        if intuition is not None:
            compiled = self._replace_token(compiled, "INTUITION", intuition)
        else:
            compiled = self._replace_token(compiled, "INTUITION", "No intuitive insights at this time.")
        
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