"""
Unit tests for the PromptTemplate class.

This module contains tests for all the functionality of the PromptTemplate class,
which handles loading, parsing, and manipulating XML-based system prompts.
"""

import os
import tempfile
from typing import Dict, Generator
from unittest.mock import mock_open, patch

import pytest

from core.prompt import PromptTemplate


@pytest.fixture
def template_files() -> Generator[Dict[str, str], None, None]:
    """Fixture to create temporary template and config files."""
    template_xml = """<SystemPrompt>
        <YourIdentity>
            <YourContext>This is the context</YourContext>
            <YourRoleAndPurpose>
                <YourAgentType>test_agent</YourAgentType>
                <YourPrimaryObjective>Test objective</YourPrimaryObjective>
            </YourRoleAndPurpose>
            <YourPersonaIdentity>{PERSONA_IDENTITY}</YourPersonaIdentity>
        </YourIdentity>
    </SystemPrompt>"""

    config_json = """{
        "template_path": "../template.xml",
        "nodes": {
            "YourIdentity": {
                "YourRoleAndPurpose": {
                    "YourAgentType": "configured_agent",
                    "YourPrimaryObjective": "Configured objective"
                }
            }
        },
        "placeholders": {
            "PERSONA_IDENTITY": "Sample identity"
        }
    }"""

    # Create temporary files
    with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
        f.write(template_xml)
        template_path = f.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(config_json)
        config_path = f.name

    # Return file paths to the test
    yield {"template_path": template_path, "config_path": config_path}

    # Cleanup after test is done
    if os.path.exists(template_path):
        os.unlink(template_path)
    if os.path.exists(config_path):
        os.unlink(config_path)


def test_init(template_files: Dict[str, str]) -> None:
    """Test initializing the PromptTemplate."""
    template = PromptTemplate(template_files["template_path"])
    assert template.root.tag == "SystemPrompt"


def test_get_node(template_files: Dict[str, str]) -> None:
    """Test retrieving nodes from the XML tree."""
    template = PromptTemplate(template_files["template_path"])

    # Test existing node
    node = template.get_node("YourIdentity/YourRoleAndPurpose/YourAgentType")
    assert node is not None
    assert node.text.strip() == "test_agent"

    # Test nonexistent path
    node = template.get_node("NonexistentPath")
    assert node is None


def test_update_text(template_files: Dict[str, str]) -> None:
    """Test updating text content of a node."""
    template = PromptTemplate(template_files["template_path"])

    # Update node text
    result = template.update_text("YourIdentity/YourRoleAndPurpose/YourAgentType", "new_agent")
    assert result is True

    # Check that the update took effect
    node = template.get_node("YourIdentity/YourRoleAndPurpose/YourAgentType")
    assert node.text == "new_agent"


def test_add_node(template_files: Dict[str, str]) -> None:
    """Test adding a new node to the tree."""
    template = PromptTemplate(template_files["template_path"])

    # Add a new section
    new_node = template.add_node("YourIdentity", "NewSection", "New section content")
    assert new_node is not None

    # Check that the node was added
    node = template.get_node("YourIdentity/NewSection")
    assert node is not None
    assert node.text == "New section content"


def test_remove_node(template_files: Dict[str, str]) -> None:
    """Test removing a node from the tree."""
    template = PromptTemplate(template_files["template_path"])

    # Check node exists before removal
    node = template.get_node("YourIdentity/YourRoleAndPurpose")
    assert node is not None

    # Remove the node
    result = template.remove_node("YourIdentity/YourRoleAndPurpose")
    assert result is True

    # Check that the node was removed
    node = template.get_node("YourIdentity/YourRoleAndPurpose")
    assert node is None

    # Try to remove a non-existent node
    result = template.remove_node("NonexistentPath")
    assert result is False

    # Try to remove root node
    result = template.remove_node("")
    assert result is False


def test_replace_placeholders(template_files: Dict[str, str]) -> None:
    """Test replacing placeholders in the template."""
    template = PromptTemplate(template_files["template_path"])

    # Replace placeholder
    template.replace_placeholders({"PERSONA_IDENTITY": "Test identity"})

    # Check that the placeholder was replaced
    node = template.get_node("YourIdentity/YourPersonaIdentity")
    assert node.text == "Test identity"


def test_get_all_placeholders(template_files: Dict[str, str]) -> None:
    """Test extracting placeholders from the template."""
    template = PromptTemplate(template_files["template_path"])

    # Check that placeholders are detected
    placeholders = template.get_all_placeholders()
    assert "PERSONA_IDENTITY" in placeholders


@patch("os.path.exists")
@patch("builtins.open", new_callable=mock_open)
@patch("core.prompt.ET")
@patch("core.prompt.json.load")
def test_from_config(
    mock_json_load: pytest.MonkeyPatch,
    mock_et: pytest.MonkeyPatch,
    mock_file: pytest.MonkeyPatch,
    mock_exists: pytest.MonkeyPatch,
) -> None:
    """Test loading a template from a JSON configuration."""
    # Configure mocks
    mock_exists.return_value = True
    mock_template = mock_et.parse.return_value
    mock_template.getroot.return_value = mock_et.Element("SystemPrompt")

    # Setup json config return value
    mock_json_load.return_value = {
        "template_path": "../template.xml",
        "nodes": {"YourIdentity": {"YourRoleAndPurpose": {"YourAgentType": "configured_agent"}}},
        "placeholders": {"PERSONA_IDENTITY": "identity.md"},
    }

    # Test the from_config method
    PromptTemplate.from_config("/path/to/config.json")

    # Verify method calls
    mock_et.parse.assert_called_once()
    assert mock_template.getroot.called
