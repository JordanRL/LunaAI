"""XML template-based prompt management system for LunaAI.

This module provides classes for loading, parsing and manipulating XML-based system prompts
using the standard library's xml.etree.ElementTree module.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from xml.etree import ElementTree as ET


class PromptTemplate:
    """A class for managing XML-based system prompts.

    This class allows loading XML templates, traversing the XML tree,
    and provides helper methods for updating text or adding nodes.
    """

    def __init__(self, template_path: str):
        """Initialize the PromptTemplate with an XML template file.

        Args:
            template_path: Path to the XML template file
        """
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template file not found: {template_path}")

        self.template_path = template_path
        self.tree = ET.parse(template_path)
        self.root = self.tree.getroot()

    def get_node(self, path: str) -> Optional[ET.Element]:
        """Find a node in the XML tree using an XPath-like string.

        Args:
            path: Path to the node, using '/' as separator (e.g., 'YourIdentity/YourContext')

        Returns:
            The Element if found, None otherwise
        """
        if not path:
            return self.root

        current = self.root
        parts = path.split("/")

        for part in parts:
            found = False
            for child in current:
                if child.tag == part:
                    current = child
                    found = True
                    break

            if not found:
                return None

        return current

    def update_text(self, path: str, text: str) -> bool:
        """Update the text content of a node.

        Args:
            path: Path to the node
            text: New text content

        Returns:
            True if successful, False if node not found
        """
        node = self.get_node(path)
        if node is None:
            return False

        node.text = text
        return True

    def add_node(
        self,
        parent_path: str,
        tag: str,
        text: Optional[str] = None,
        attributes: Optional[Dict[str, str]] = None,
    ) -> Optional[ET.Element]:
        """Add a new node to the XML tree.

        Args:
            parent_path: Path to the parent node
            tag: Tag name for the new node
            text: Optional text content for the new node
            attributes: Optional dictionary of attributes for the new node

        Returns:
            The newly created Element if successful, None otherwise
        """
        parent = self.get_node(parent_path)
        if parent is None:
            return None

        new_node = ET.SubElement(parent, tag, attrib=attributes or {})
        if text:
            new_node.text = text

        return new_node

    def replace_placeholders(self, replacements: Dict[str, str]) -> None:
        """Replace placeholders in the XML template with actual values.

        Args:
            replacements: Dictionary mapping placeholder names to replacement values
        """
        xml_str = ET.tostring(self.root, encoding="unicode")

        for placeholder, value in replacements.items():
            xml_str = xml_str.replace(f"{{{placeholder}}}", value)

        # Parse the modified XML string back into the tree
        new_root = ET.fromstring(xml_str)
        # Recreate the tree with the new root
        self.tree = ET.ElementTree(new_root)
        self.root = new_root

    def get_all_placeholders(self) -> List[str]:
        """Find all placeholders in the XML template.

        Returns:
            List of placeholder names (without curly braces)
        """
        xml_str = ET.tostring(self.root, encoding="unicode")
        placeholders = []

        # Simple parsing to find all {PLACEHOLDER} patterns
        start_idx = 0
        while True:
            start_idx = xml_str.find("{", start_idx)
            if start_idx == -1:
                break

            end_idx = xml_str.find("}", start_idx)
            if end_idx == -1:
                break

            placeholder = xml_str[start_idx + 1 : end_idx]
            if placeholder not in placeholders:
                placeholders.append(placeholder)

            start_idx = end_idx + 1

        return placeholders

    def to_string(self) -> str:
        """Convert the XML tree to a string.

        Returns:
            String representation of the XML
        """
        return ET.tostring(self.root, encoding="unicode")

    def to_file(self, file_path: str) -> None:
        """Write the XML tree to a file.

        Args:
            file_path: Path to the output file
        """
        self.tree.write(file_path, encoding="utf-8", xml_declaration=True)

    def find_elements_by_text(self, search_text: str) -> List[ET.Element]:
        """Find all elements containing the specified text.

        Args:
            search_text: Text to search for

        Returns:
            List of elements containing the search text
        """
        results = []

        def _search_recursive(element: ET.Element) -> None:
            if element.text and search_text in element.text:
                results.append(element)

            for child in element:
                _search_recursive(child)

        _search_recursive(self.root)
        return results

    @classmethod
    def from_config(cls, config_path: str) -> "PromptTemplate":
        """Create a PromptTemplate from a JSON configuration file.

        The JSON config should contain:
        - template_path: Path to the XML template file
        - nodes: Nested object structure mirroring the XML hierarchy with node content
        - placeholders: Dictionary of placeholder values to substitute

        Args:
            config_path: Path to the JSON config file

        Returns:
            A configured PromptTemplate instance
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")

        # Load the JSON config
        with open(config_path, "r") as f:
            config = json.load(f)

        # Resolve template path (relative to config file location)
        config_dir = os.path.dirname(os.path.abspath(config_path))
        template_path = os.path.normpath(os.path.join(config_dir, config["template_path"]))

        # Create the template
        template = cls(template_path)

        # Apply node updates from the config
        if "nodes" in config:
            node_config = config["nodes"]
            cls._apply_node_config(template, "", node_config)

        return template

    @staticmethod
    def _apply_node_config(
        template: "PromptTemplate", path: str, node_config: Dict[str, Any]
    ) -> None:
        """Recursively apply node configuration to the template.

        Args:
            template: The PromptTemplate to modify
            path: Current path in the XML tree
            node_config: Node configuration dictionary
        """

        def _convert_to_title_case(tag: str) -> str:
            """Convert snake_case or kebab-case to TitleCase."""
            # Handle kebab-case
            if "-" in tag:
                parts = tag.split("-")
            # Handle snake_case
            elif "_" in tag:
                parts = tag.split("_")
            else:
                # Already camelCase or TitleCase - convert to parts for consistency
                import re

                parts = re.findall(r"[A-Z](?:[a-z]+)|[a-z]+", tag)

            # Title case each part and join
            return "".join(part.title() for part in parts)

        for key, value in node_config.items():
            # Convert key to title case for XML path
            title_case_key = _convert_to_title_case(key)

            current_path = f"{path}/{title_case_key}" if path else title_case_key

            if key == "_text" and isinstance(value, str):
                # Special key for node text
                template.update_text(path, value)
            elif isinstance(value, dict):
                # Nested structure - recursively process
                PromptTemplate._apply_node_config(template, current_path, value)
            elif isinstance(value, (list, tuple)):
                # Handle lists/arrays
                node = template.get_node(current_path)
                if node is None:
                    # Create the node if it doesn't exist
                    node = template.add_node(path, title_case_key)
                else:
                    # Clear existing children
                    for child in list(node):
                        node.remove(child)

                # Add a child node for each list item
                for i, item in enumerate(value):
                    item_tag = f"Item{i+1}"
                    if isinstance(item, dict):
                        item_node = template.add_node(current_path, item_tag)
                        item_path = f"{current_path}/{item_tag}"
                        PromptTemplate._apply_node_config(template, item_path, item)
                    else:
                        template.add_node(current_path, item_tag, text=str(item))
            elif isinstance(value, str):
                # Text content for the node
                if not template.update_text(current_path, value):
                    # Create the node if it doesn't exist
                    template.add_node(path, title_case_key, text=value)
            elif value is not None:
                # Handle other types (numbers, booleans, etc.)
                if not template.update_text(current_path, str(value)):
                    # Create the node if it doesn't exist
                    template.add_node(path, title_case_key, text=str(value))

    def load_placeholder_file(self, placeholder_name: str, file_path: str) -> None:
        """Load a placeholder value from a file.

        Args:
            placeholder_name: Name of the placeholder (without curly braces)
            file_path: Path to the file containing the placeholder value
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Placeholder file not found: {file_path}")

        with open(file_path, "r") as f:
            content = f.read()

        replacements = {placeholder_name: content}
        self.replace_placeholders(replacements)

    def remove_node(self, path: str) -> bool:
        """Remove a node and all its children from the XML tree.

        Args:
            path: Path to the node to remove

        Returns:
            True if successful, False if node not found or is the root node
        """
        if not path:
            return False  # Cannot remove the root node

        # Find the parent node and the node to remove
        parent_path, _, node_tag = path.rpartition("/")
        parent = self.get_node(parent_path)

        if parent is None:
            return False

        # Find the child node to remove
        for child in list(parent):  # Create a copy of the list to avoid modification issues
            if child.tag == node_tag:
                parent.remove(child)
                return True

        return False

    def apply_dict(self, data: Dict[str, Any], parent_path: str = "") -> None:
        """Apply a dictionary to the template as modifications.

        This method takes a dictionary and applies it to the template, adding nodes
        and text as necessary. It uses the dict keys as tag names, converting them
        from snake_case or kebab-case to TitleCase.

        Args:
            data: Dictionary of modifications to apply
            parent_path: Optional path to the parent node where modifications start.
                         If not provided, starts from the root node.
        """

        def _convert_to_title_case(tag: str) -> str:
            """Convert snake_case or kebab-case to TitleCase."""
            # Handle kebab-case
            if "-" in tag:
                parts = tag.split("-")
            # Handle snake_case
            else:
                parts = tag.split("_")

            # Title case each part and join
            return "".join(part.title() for part in parts)

        # Feature flag paths that should not be recreated if they were removed
        feature_disabled_paths = [
            "YourIdentity/YourPersonaIdentity",
            "YourIdentity/YourPersonality",
            "YourIdentity/YourBackstoryAndPersonalHistory",
            "YourIdentity/YourValues",
            "YourIdentity/YourBeliefs",
            "YourIdentity/YourRelationships",
            "YourKnowledge/EmotionalState",
            "YourKnowledge/Intuition",
            "YourKnowledge/WorkingMemory",
            "YourKnowledge/RecentMemory",
            "YourKnowledge/UserProfile",
            "YourKnowledge/UserRelationship",
            "YourCognitiveStructure",
            "YourCognitiveStructure/Capabilities",
            "YourCognitiveStructure/Agents",
            "YourCognitiveStructure/InteractionTypes",
        ]

        def _apply_recursive(current_data: Dict[str, Any], current_path: str) -> None:
            """Recursively apply dict data to the template."""
            parent_node = self.get_node(current_path)

            if parent_node is None:
                return

            for key, value in current_data.items():
                # Convert tag name to TitleCase
                title_case_tag = _convert_to_title_case(key)

                # Create path for this node
                node_path = f"{current_path}/{title_case_tag}" if current_path else title_case_tag

                # Skip this node if it was intentionally removed due to feature flags
                if node_path in feature_disabled_paths and self.get_node(node_path) is None:
                    continue

                # Check if node exists
                node = self.get_node(node_path)

                if isinstance(value, dict):
                    # If node doesn't exist, create it (unless it was intentionally removed)
                    if node is None and node_path not in feature_disabled_paths:
                        self.add_node(current_path, title_case_tag)

                    # Recursively process the nested dict
                    _apply_recursive(value, node_path)
                elif isinstance(value, (list, tuple)):
                    # If the value is a list, create child nodes for each item
                    if node is None:
                        if node_path not in feature_disabled_paths:
                            node = self.add_node(current_path, title_case_tag)
                        else:
                            continue  # Skip this node and its children
                    else:
                        # Clear existing children
                        for child in list(node):
                            node.remove(child)

                    # Add a child node for each list item
                    for i, item in enumerate(value):
                        item_tag = f"Item{i+1}"
                        if isinstance(item, dict):
                            item_node = self.add_node(node_path, item_tag)
                            item_path = f"{node_path}/{item_tag}"
                            _apply_recursive(item, item_path)
                        else:
                            self.add_node(node_path, item_tag, text=str(item))
                else:
                    # For leaf nodes with simple values
                    if node is None:
                        if node_path not in feature_disabled_paths:
                            self.add_node(current_path, title_case_tag, text=str(value))
                    else:
                        self.update_text(node_path, str(value))

        # Start the recursive application
        _apply_recursive(data, parent_path)
