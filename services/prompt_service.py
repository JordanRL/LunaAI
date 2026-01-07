"""
Prompt service for handling system prompt token replacement.

This service manages the three-stage prompt processing system:
1. Raw: The file as it is read from the file system with no tokens replaced
2. Pre-processed: The file with relatively stable tokens replaced
3. Compiled: The file as it is sent to the agent with all tokens replaced

This service uses the PromptTemplate class from core/prompt.py for XML template handling
and PersonaService for persona information.
"""

import json
import os
from copy import deepcopy
from typing import Any, Dict, Optional

from core.prompt import PromptTemplate
from domain.models.agent import AgentConfig
from services.persona_service import PersonaService


class PromptService:
    """
    Service for managing system prompt token replacement.

    This service handles the loading, caching, and token replacement for system prompts
    using the PromptTemplate class for XML manipulation and PersonaService for persona data.
    """

    def __init__(self, persona_service: Optional[PersonaService] = None):
        """
        Initialize the prompt service.

        Args:
            persona_service: Optional PersonaService instance for persona data
        """
        self.prompt_templates: Dict[str, PromptTemplate] = {}
        self.preprocessed_templates: Dict[str, PromptTemplate] = {}
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Inject or create persona service
        self.persona_service = persona_service or PersonaService()

    def load_prompt_template(self, agent_name: str) -> PromptTemplate:
        """
        Load the system prompt template for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            PromptTemplate instance for the agent
        """
        # Check if we already have this template cached
        if agent_name in self.prompt_templates:
            return self.prompt_templates[agent_name]

        # Determine file path
        system_prompts_dir = os.path.join(self.project_root, "system_prompts", agent_name)
        json_path = os.path.join(system_prompts_dir, "system.json")

        if not os.path.exists(json_path):
            raise FileNotFoundError(f"No system prompt found for agent {agent_name}")

        # Create and cache the template
        template = PromptTemplate.from_config(json_path)
        self.prompt_templates[agent_name] = template
        return template

    def preprocess_prompt(self, agent_config: AgentConfig, replacements: Dict[str, Any]) -> str:
        """
        Preprocess a system prompt by replacing relatively stable content.

        This method uses a dictionary-based approach for applying replacements to the template,
        organizing the data to match the XML structure.

        Args:
            agent_config: Agent configuration
            replacements: Dictionary of replacements (can be path-based or direct structure)

        Returns:
            Preprocessed system prompt as string
        """
        agent_name = agent_config.name.value

        # Load the template if not already cached
        if agent_name not in self.prompt_templates:
            self.load_prompt_template(agent_name)

        # Create a copy of the template for preprocessing
        template = self.prompt_templates[agent_name]
        preprocessed_template = deepcopy(template)

        # Initialize empty structured replacements dict
        structured_replacements = {}

        # Add persona information based on agent_config settings
        persona_name = replacements.get("PERSONA_NAME", "luna")
        features = agent_config.features
        if "persona_config" in features:
            persona_config = features["persona_config"]
            for persona_section, include in persona_config.items():
                if include:
                    if isinstance(include, str) and include == "none":
                        continue
                    elif isinstance(include, str):
                        detail = include.lower()
                    else:
                        detail = "all"
                    # Convert section name to expected format (identity -> identity)
                    section_name = persona_section.lower()

                    # Map section name to appropriate XML path
                    xml_section_map = {
                        "identity": "your_persona_identity",
                        "personality": "your_personality",
                        "backstory": "your_backstory_and_personal_history",
                        "values": "your_values",
                        "beliefs": "your_beliefs",
                        "relationships": "your_relationships",
                    }

                    xml_key = xml_section_map.get(section_name)
                    if xml_key:
                        # Get content from PersonaService
                        section_dict = self.persona_service.get_section_dict(
                            persona_name, section_name, detail
                        )
                        if section_dict:
                            # Make sure your_identity exists in structured_replacements
                            if "your_identity" not in structured_replacements:
                                structured_replacements["your_identity"] = {}
                            # Add to structured replacements
                            structured_replacements["your_identity"][xml_key] = section_dict

        # Process content from original replacements - first handle any that might be structured
        replacements_copy = dict(replacements)

        # Process structured dicts that might be in the replacements
        for key, value in replacements.items():
            if isinstance(value, dict) and key != "PERSONA_NAME":
                # This is a structured dictionary - add it to structured_replacements
                snake_key = key.lower().replace("-", "_")
                structured_replacements[snake_key] = value
                # Remove from the replacements_copy to avoid duplicate processing
                del replacements_copy[key]

        # Add other content sections based on features
        knowledge_map = {
            "emotion_block": "emotional_state",
            "intuition": "intuition",
            "working_memory": "working_memory",
            "recent_memory": "recent_memory",
            "user_profile": "user_profile",
            "user_relationship": "user_relationship",
        }

        # Process feature-based content
        for feature, enabled in features.items():
            if feature in knowledge_map and enabled:
                # Get the corresponding XML section name
                section_name = knowledge_map[feature]

                # Check if we have content for this section in replacements
                if section_name.upper() in replacements_copy:
                    # Make sure your_knowledge exists in structured_replacements
                    if "your_knowledge" not in structured_replacements:
                        structured_replacements["your_knowledge"] = {}
                    structured_replacements["your_knowledge"][section_name] = replacements_copy[
                        section_name.upper()
                    ]
                    # Remove from the replacements_copy to avoid duplicate processing
                    del replacements_copy[section_name.upper()]

        # Process custom path-style replacements provided in the input
        for key, value in list(replacements_copy.items()):
            # Skip special keys
            if key == "PERSONA_NAME":
                del replacements_copy[key]
                continue

            # Handle path-style keys (containing slashes)
            if "/" in key:
                parts = key.lower().split("/")
                # Convert parts to snake_case for apply_dict
                parts = [part.replace("-", "_") for part in parts]

                # Build nested structure
                current = structured_replacements
                for i, part in enumerate(parts):
                    if i == len(parts) - 1:
                        # Final part - set the value
                        current[part] = value
                    else:
                        # Intermediate part - create dict if needed
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                # Remove from the replacements_copy to avoid duplicate processing
                del replacements_copy[key]

        # Always apply structured replacements if we have any
        if structured_replacements:
            preprocessed_template.apply_dict(structured_replacements)

        # For backwards compatibility, also apply any non-special keys from original replacements
        # that weren't already handled through structured replacements
        if replacements_copy:
            preprocessed_template.apply_dict(replacements_copy)

        # Process feature flags to remove nodes
        self._process_feature_flags(preprocessed_template, agent_config.features)

        # Cache the preprocessed template
        self.preprocessed_templates[agent_name] = preprocessed_template

        return preprocessed_template.to_string()

    def compile_prompt(
        self,
        agent_name: str,
        replacements: Optional[Dict[str, Any]] = None,
        token_replacements: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Compile a system prompt by replacing all dynamic content.

        This method uses a dictionary-based approach for applying replacements to the template,
        organizing the data to match the XML structure.

        Args:
            agent_name: Name of the agent
            replacements: Optional dictionary of replacements (can use structure-based keys)
            token_replacements: Optional dictionary of replacements that are string replaced in the compiled prompt

        Returns:
            Fully compiled system prompt
        """
        # Get the preprocessed template
        if agent_name not in self.preprocessed_templates:
            raise ValueError(f"Agent {agent_name} hasn't been preprocessed yet")

        # Create a copy of the preprocessed template for final compilation
        preprocessed_template = self.preprocessed_templates[agent_name]
        compiled_template = deepcopy(preprocessed_template)
        # Copy XML content from preprocessed template to compiled template
        compiled_template.root = preprocessed_template.root

        # Apply dynamic replacements
        if replacements:
            # Initialize empty structured replacements dict
            structured_replacements = {}

            # Map common token names to proper XML paths
            token_map = {
                "WORKING_MEMORY": "your_knowledge/working_memory",
                "RECENT_MEMORY": "your_knowledge/recent_memory",
                "INTUITION": "your_knowledge/intuition",
                "USER_PROFILE": "your_knowledge/user_profile",
                "USER_RELATIONSHIP": "your_knowledge/user_relationship",
                "PAD_PLEASURE": "your_knowledge/emotional_state/pleasure",
                "PAD_AROUSAL": "your_knowledge/emotional_state/arousal",
                "PAD_DOMINANCE": "your_knowledge/emotional_state/dominance",
                "PAD_DESCRIPTOR": "your_knowledge/emotional_state/descriptor",
            }

            # Process token mappings to structured paths
            for token, path in token_map.items():
                if token in replacements:
                    parts = path.lower().split("/")

                    # Build nested structure
                    current = structured_replacements
                    for i, part in enumerate(parts):
                        if i == len(parts) - 1:
                            # Final part - set the value
                            current[part] = replacements[token]
                        else:
                            # Intermediate part - create dict if needed
                            if part not in current:
                                current[part] = {}
                            current = current[part]

            # Process other replacements
            for key, value in replacements.items():
                # Skip tokens we've already processed
                if key in token_map:
                    continue

                # Handle path-style keys (containing slashes)
                if "/" in key:
                    parts = key.lower().split("/")
                    # Convert parts to snake_case for apply_dict
                    parts = [part.replace("-", "_") for part in parts]

                    # Build nested structure
                    current = structured_replacements
                    for i, part in enumerate(parts):
                        if i == len(parts) - 1:
                            # Final part - set the value
                            current[part] = value
                        else:
                            # Intermediate part - create dict if needed
                            if part not in current:
                                current[part] = {}
                            current = current[part]

            # If no path-style replacements were used, use the original replacements dict
            # (excluding tokens we've already processed)
            if not any("/" in key for key in replacements.keys() if key not in token_map):
                filtered_replacements = {
                    k: v for k, v in replacements.items() if k not in token_map
                }
                # Only use direct replacements if we haven't built any structured_replacements
                if not structured_replacements and filtered_replacements:
                    compiled_template.apply_dict(filtered_replacements)
                else:
                    compiled_template.apply_dict(structured_replacements)
            else:
                # Apply structured replacements using apply_dict
                compiled_template.apply_dict(structured_replacements)

        prompt_string = compiled_template.to_string()

        if token_replacements:
            for key, value in token_replacements.items():
                prompt_string = prompt_string.replace(key, value)

        return prompt_string

    def _process_feature_flags(self, template: PromptTemplate, features: Dict[str, Any]) -> None:
        """
        Process feature flags and remove nodes based on disabled features.

        Args:
            template: The PromptTemplate to process
            features: Dictionary of feature flags from agent config
        """
        # Map of feature flags to corresponding XML nodes
        feature_node_map = {
            # Persona config sections
            "persona_config.identity": "YourIdentity/YourPersonaIdentity",
            "persona_config.personality": "YourIdentity/YourPersonality",
            "persona_config.backstory": "YourIdentity/YourBackstoryAndPersonalHistory",
            "persona_config.values": "YourIdentity/YourValues",
            "persona_config.beliefs": "YourIdentity/YourBeliefs",
            "persona_config.relationships": "YourIdentity/YourRelationships",
            # Other content sections
            "emotion_block": "YourKnowledge/EmotionalState",
            "intuition": "YourKnowledge/Intuition",
            "recent_memory": "YourKnowledge/RecentMemory",
            "working_memory": "YourKnowledge/WorkingMemory",
            "user_relationship": "YourKnowledge/UserRelationship",
            "user_profile": "YourKnowledge/UserProfile",
        }

        # Process persona_config features
        if "persona_config" in features and isinstance(features["persona_config"], dict):
            for section, enabled in features["persona_config"].items():
                feature_key = f"persona_config.{section}"
                if feature_key in feature_node_map and not enabled:
                    template.remove_node(feature_node_map[feature_key])

        # Process other features
        for feature, enabled in features.items():
            if feature == "persona_config":
                continue  # Already handled separately

            if feature in feature_node_map and not enabled:
                template.remove_node(feature_node_map[feature])

        # Handle cognitive structure features
        if "cognitive" in features and not features["cognitive"]:
            # Remove entire cognitive structure if cognitive flag is false
            template.remove_node("YourCognitiveStructure")
        elif "cognitive_structure" in features and isinstance(
            features["cognitive_structure"], dict
        ):
            # Handle individual cognitive structure sections
            cognitive_sections = {
                "capabilities": "YourCognitiveStructure/Capabilities",
                "agents": "YourCognitiveStructure/Agents",
                "interaction_types": "YourCognitiveStructure/InteractionTypes",
            }

            for section, path in cognitive_sections.items():
                if (
                    section in features["cognitive_structure"]
                    and not features["cognitive_structure"][section]
                ):
                    template.remove_node(path)

    def invalidate_preprocessed(self, agent_name: Optional[str] = None) -> None:
        """
        Invalidate the preprocessed cache for an agent or all agents.

        Args:
            agent_name: Name of the agent to invalidate, or None for all agents
        """
        if agent_name:
            if agent_name in self.preprocessed_templates:
                del self.preprocessed_templates[agent_name]
        else:
            self.preprocessed_templates.clear()

    def load_raw_prompt(self, agent_name: str) -> str:
        """
        Legacy method to maintain backward compatibility.

        Args:
            agent_name: Name of the agent

        Returns:
            Raw system prompt text
        """
        template = self.load_prompt_template(agent_name)
        return template.to_string()
