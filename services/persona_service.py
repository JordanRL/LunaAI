"""Persona service for managing and retrieving persona information.

This module provides functionality for loading, storing and accessing
persona data from JSON configuration files into strongly typed dataclasses.
"""

import json
import os
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, cast

from domain.models.persona.sections import (
    PersonaBeliefs,
    PersonaHistory,
    PersonaIdentity,
    PersonaPersonality,
    PersonaRelationships,
    PersonaSection,
    PersonaValues,
)

# Type variable for generic persona section types
T = TypeVar("T", bound=PersonaSection)


class PersonaService:
    """Service for managing persona information.

    This service loads persona configurations from JSON files,
    converts them to typed dataclasses, and provides methods
    to access persona information at different detail levels.
    """

    def __init__(self, config_dir: str = "persona_configs"):
        """Initialize the persona service.

        Args:
            config_dir: Directory containing persona configuration files
        """
        self.config_dir = config_dir
        self.personas: Dict[str, Dict[str, PersonaSection]] = {}
        self._section_class_map = {
            "identity": PersonaIdentity,
            "personality": PersonaPersonality,
            "history": PersonaHistory,
            "values": PersonaValues,
            "beliefs": PersonaBeliefs,
            "relationships": PersonaRelationships,
        }

    def load_persona(self, persona_name: str) -> bool:
        """Load a persona configuration from a JSON file.

        Args:
            persona_name: Name of the persona to load (without .json extension)

        Returns:
            True if loading was successful, False otherwise
        """
        file_path = os.path.join(self.config_dir, f"{persona_name}.json")

        if not os.path.exists(file_path):
            return False

        try:
            with open(file_path, "r") as f:
                persona_data = json.load(f)

            persona_sections: Dict[str, PersonaSection] = {}

            # Convert each section to the appropriate dataclass
            for section_name, section_data in persona_data.items():
                if section_name in self._section_class_map:
                    section_class = self._section_class_map[section_name]
                    section_obj = self._dict_to_dataclass(section_class, section_data)
                    persona_sections[section_name] = section_obj

            self.personas[persona_name] = persona_sections
            return True
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading persona {persona_name}: {e}")
            return False

    def get_section(self, persona_name: str, section_name: str) -> Optional[PersonaSection]:
        """Get a specific section of a persona.

        Args:
            persona_name: Name of the persona
            section_name: Name of the section to retrieve

        Returns:
            The section object if found, None otherwise
        """
        if persona_name not in self.personas:
            if not self.load_persona(persona_name):
                return None

        persona = self.personas.get(persona_name, {})
        return persona.get(section_name)

    def get_section_dict(
        self, persona_name: str, section_name: str, detail_level: str = "all"
    ) -> Dict[str, Any]:
        """Get a section as a dictionary at the specified detail level.

        Args:
            persona_name: Name of the persona
            section_name: Name of the section to retrieve
            detail_level: Detail level (low, medium, high, or all)

        Returns:
            Dictionary representation of the section at the requested detail level
        """
        section = self.get_section(persona_name, section_name)

        if section is None:
            return {}

        if detail_level == "all":
            # Return all fields except _section and _detail_level_* fields
            return self._dataclass_to_dict(section, exclude_private=True)

        # Get the fields to include based on the detail level
        if detail_level == "low":
            fields_to_include = section._detail_level_low
        elif detail_level == "medium":
            fields_to_include = section._detail_level_medium
        elif detail_level == "high":
            fields_to_include = section._detail_level_high
        else:
            # Default to all fields if detail level is not recognized
            return self._dataclass_to_dict(section, exclude_private=True)

        # Filter the dictionary to only include the specified fields
        result = {}
        for field_name in fields_to_include:
            if hasattr(section, field_name):
                value = getattr(section, field_name)
                result[field_name] = value

        return result

    def get_full_persona(self, persona_name: str) -> Dict[str, PersonaSection]:
        """Get all sections for a persona.

        Args:
            persona_name: Name of the persona

        Returns:
            Dictionary of all persona sections
        """
        if persona_name not in self.personas:
            if not self.load_persona(persona_name):
                return {}

        return self.personas.get(persona_name, {})

    def get_all_persona_names(self) -> List[str]:
        """Get a list of all available persona names.

        Returns:
            List of persona names
        """
        json_files = [f for f in os.listdir(self.config_dir) if f.endswith(".json")]
        return [os.path.splitext(f)[0] for f in json_files]

    def _dict_to_dataclass(self, cls: Type[T], data: Dict[str, Any]) -> T:
        """Convert a dictionary to a dataclass instance.

        Args:
            cls: The dataclass type to create
            data: Dictionary containing the data

        Returns:
            Instance of the dataclass with the data
        """
        # Filter out any keys that aren't valid fields in the dataclass
        field_names = [f.name for f in fields(cls)]
        filtered_data = {k: v for k, v in data.items() if k in field_names}

        # Create the dataclass instance
        return cls(**filtered_data)

    def _dataclass_to_dict(self, obj: Any, exclude_private: bool = False) -> Dict[str, Any]:
        """Convert a dataclass instance to a dictionary.

        Args:
            obj: The dataclass instance to convert
            exclude_private: Whether to exclude fields starting with underscore

        Returns:
            Dictionary representation of the dataclass
        """
        if not is_dataclass(obj):
            return {}

        result = {}

        for field in fields(obj):
            # Skip private fields if requested
            if exclude_private and field.name.startswith("_"):
                continue

            value = getattr(obj, field.name)

            # Convert nested dataclasses
            if is_dataclass(value):
                result[field.name] = self._dataclass_to_dict(value, exclude_private)
            # Convert lists of dataclasses
            elif isinstance(value, list):
                if value and is_dataclass(value[0]):
                    result[field.name] = [
                        self._dataclass_to_dict(item, exclude_private) for item in value
                    ]
                else:
                    result[field.name] = value
            # Handle dictionaries with dataclass values
            elif isinstance(value, dict) and value and any(is_dataclass(v) for v in value.values()):
                result[field.name] = {
                    k: self._dataclass_to_dict(v, exclude_private) if is_dataclass(v) else v
                    for k, v in value.items()
                }
            else:
                result[field.name] = value

        return result
