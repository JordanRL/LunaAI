"""
Unit tests for the PromptService.

This module contains tests for the PromptService class which manages
system prompt loading, preprocessing, and compilation using the PromptTemplate.
"""

import json
import os
import tempfile
from typing import Dict, Generator
from unittest.mock import MagicMock, patch

import pytest

from core.prompt import PromptTemplate
from domain.models.agent import AgentConfig
from domain.models.enums import AgentType
from services.prompt_service import PromptService


@pytest.fixture
def mock_agent_config() -> AgentConfig:
    """Fixture to create a mock agent configuration."""
    mock_config = AgentConfig(
        name=AgentType.DISPATCHER,
        description="Test agent",
        model="test-model",
        max_tokens=1000,
        temperature=0.7,
        features={
            "persona_config": {"identity": True, "personality": True, "backstory": False},
            "cognitive": True,
            "cognitive_structure": {
                "capabilities": True,
                "agents": True,
                "interaction_types": True,
            },
            "emotion_block": True,
            "working_memory": True,
            "recent_memory": True,
            "user_profile": True,
            "user_relationship": True,
            "intuition": True,
        },
    )
    return mock_config


@pytest.fixture
def template_xml() -> str:
    """Fixture to provide a sample XML template."""
    return """<SystemPrompt>
        <YourIdentity>
            <YourContext>This is the context</YourContext>
            <YourRoleAndPurpose>
                <YourAgentType>test_agent</YourAgentType>
                <YourPrimaryObjective>Test objective</YourPrimaryObjective>
            </YourRoleAndPurpose>
            <YourPersonaIdentity></YourPersonaIdentity>
            <YourPersonality></YourPersonality>
            <YourBackstoryAndPersonalHistory></YourBackstoryAndPersonalHistory>
        </YourIdentity>
        <YourKnowledge>
            <EmotionalState></EmotionalState>
            <WorkingMemory></WorkingMemory>
        </YourKnowledge>
    </SystemPrompt>"""


@pytest.fixture
def mock_persona_service() -> MagicMock:
    """Fixture to create a mock PersonaService."""
    mock_service = MagicMock()

    # Setup get_section method
    def mock_get_section(persona_name, section_name):
        if persona_name == "luna" and section_name in ["identity", "personality"]:
            return MagicMock()
        return None

    # Setup get_section_dict method
    def mock_get_section_dict(persona_name, section_name, detail_level):
        if persona_name == "luna":
            if section_name == "identity":
                return {"name": "Luna", "age": 25, "occupation": "AI Assistant"}
            elif section_name == "personality":
                return {"traits": ["curious", "empathetic", "honest"]}
        return {}

    mock_service.get_section.side_effect = mock_get_section
    mock_service.get_section_dict.side_effect = mock_get_section_dict

    return mock_service


@pytest.fixture
def setup_service(
    template_xml: str, mock_persona_service: MagicMock
) -> Generator[Dict[str, any], None, None]:
    """Fixture to set up the PromptService with mock files and PersonaService."""
    # Create temporary directories and files
    temp_dir = tempfile.mkdtemp()
    system_prompts_dir = os.path.join(temp_dir, "system_prompts", "dispatcher")

    # Create directories
    os.makedirs(system_prompts_dir, exist_ok=True)

    # Write XML template in the Template.xml location (parent directory)
    template_dir = os.path.join(temp_dir, "system_prompts")
    template_path = os.path.join(template_dir, "Template.xml")
    with open(template_path, "w") as f:
        f.write(template_xml)

    # Create system.json that points to the template
    json_content = {
        "template_path": "../Template.xml",
        "nodes": {
            "YourIdentity": {
                "YourRoleAndPurpose": {
                    "YourAgentType": "dispatcher",
                    "YourPrimaryObjective": "Test agent objective",
                }
            }
        },
    }

    json_path = os.path.join(system_prompts_dir, "system.json")
    with open(json_path, "w") as f:
        json.dump(json_content, f)

    # Create and configure service with injected persona service
    service = PromptService(persona_service=mock_persona_service)

    # Patch paths
    service.project_root = temp_dir

    yield {
        "service": service,
        "temp_dir": temp_dir,
        "json_path": json_path,
        "template_path": template_path,
        "mock_persona_service": mock_persona_service,
    }

    # Cleanup
    # (Let the system handle temp directory cleanup)


def test_load_prompt_template(setup_service: Dict[str, any]) -> None:
    """Test loading a prompt template."""
    service = setup_service["service"]

    # Test loading a template
    template = service.load_prompt_template("dispatcher")

    # Verify it's a PromptTemplate instance
    assert isinstance(template, PromptTemplate)
    assert template.root.tag == "SystemPrompt"

    # Check that it's cached
    assert "dispatcher" in service.prompt_templates


def test_preprocess_prompt(setup_service: Dict[str, any], mock_agent_config: AgentConfig) -> None:
    """Test preprocessing a prompt with token replacements."""
    service = setup_service["service"]

    # Preprocess the prompt
    result = service.preprocess_prompt(mock_agent_config, {"WORKING_MEMORY": "Test memory"})

    # Check that the result is a string
    assert isinstance(result, str)

    # Check that additional tokens were replaced (working_memory provided in the template)
    assert "Test memory" in result

    # Check that the preprocessed template was cached
    assert mock_agent_config.name.value in service.preprocessed_templates

    # Verify the persona service was called with the right methods
    mock_persona_service = setup_service["mock_persona_service"]
    mock_persona_service.get_section_dict.assert_any_call("luna", "identity", "all")
    mock_persona_service.get_section_dict.assert_any_call("luna", "personality", "all")


def test_preprocess_prompt_with_persona_integration(
    setup_service: Dict[str, any], mock_agent_config: AgentConfig
) -> None:
    """Test preprocessing a prompt with PersonaService integration."""
    service = setup_service["service"]
    mock_persona_service = setup_service["mock_persona_service"]

    # Preprocess the prompt with persona name specified
    result = service.preprocess_prompt(
        mock_agent_config, {"PERSONA_NAME": "luna", "WORKING_MEMORY": "Test memory"}
    )

    # Check that the result is a string
    assert isinstance(result, str)

    # Check for JSON data from persona service
    assert "Luna" in result  # From identity mock data
    assert "curious" in result  # From personality mock data

    # Verify the persona service was called with correct parameters
    mock_persona_service.get_section_dict.assert_any_call("luna", "identity", "all")
    mock_persona_service.get_section_dict.assert_any_call("luna", "personality", "all")


def test_compile_prompt(setup_service: Dict[str, any], mock_agent_config: AgentConfig) -> None:
    """Test compiling a preprocessed prompt."""
    service = setup_service["service"]

    # Preprocess the prompt first
    service.preprocess_prompt(mock_agent_config, {"USER_NAME": "Test User"})

    # Compile the prompt with additional dynamic tokens
    result = service.compile_prompt(
        mock_agent_config.name.value, {"WORKING_MEMORY": "Test working memory"}
    )

    # Check that compilation worked
    assert isinstance(result, str)
    assert "Test working memory" in result

    # Try compiling an unprocessed prompt
    with pytest.raises(ValueError):
        service.compile_prompt("non_existent_agent")


def test_feature_flag_removes_placeholder_nodes(
    setup_service: Dict[str, any], mock_agent_config: AgentConfig
) -> None:
    """Test that feature flags properly remove nodes that would contain placeholders."""
    service = setup_service["service"]

    # Create a template with nodes to be controlled by feature flags
    template_xml = """<SystemPrompt>
        <YourIdentity>
            <YourPersonaIdentity></YourPersonaIdentity>
        </YourIdentity>
        <YourKnowledge>
            <EmotionalState></EmotionalState>
            <WorkingMemory></WorkingMemory>
        </YourKnowledge>
    </SystemPrompt>"""

    # Update Template.xml
    with open(setup_service["template_path"], "w") as f:
        f.write(template_xml)

    # Update the system.json to use the updated template
    json_content = {
        "template_path": "../Template.xml",
        "nodes": {"YourIdentity": {"YourRoleAndPurpose": {"YourAgentType": "dispatcher"}}},
    }

    with open(setup_service["json_path"], "w") as f:
        json.dump(json_content, f)

    # Clear the template cache
    service.prompt_templates.clear()

    # Create agent config with disabled features
    agent_config = AgentConfig(
        name=AgentType.DISPATCHER,
        description="Test agent",
        model="test-model",
        max_tokens=1000,
        temperature=0.7,
        features={
            "persona_config": {"identity": False},
            "emotion_block": False,
            "working_memory": False,
            "cognitive": True,
            "cognitive_structure": {
                "capabilities": True,
                "agents": True,
                "interaction_types": True,
            },
            "recent_memory": True,
            "user_profile": True,
            "user_relationship": True,
            "intuition": True,
        },
    )

    # Preprocess with the agent config that has disabled features
    result = service.preprocess_prompt(agent_config, {})

    # Check that feature-disabled nodes were removed
    assert "<YourPersonaIdentity>" not in result
    assert "<EmotionalState>" not in result
    assert "<WorkingMemory>" not in result


def test_invalidate_preprocessed(
    setup_service: Dict[str, any], mock_agent_config: AgentConfig
) -> None:
    """Test invalidating preprocessed templates."""
    service = setup_service["service"]

    # Preprocess a prompt
    service.preprocess_prompt(mock_agent_config, {})
    assert mock_agent_config.name.value in service.preprocessed_templates

    # Invalidate specific agent
    service.invalidate_preprocessed(mock_agent_config.name.value)
    assert mock_agent_config.name.value not in service.preprocessed_templates

    # Preprocess again
    service.preprocess_prompt(mock_agent_config, {})
    assert mock_agent_config.name.value in service.preprocessed_templates

    # Invalidate all
    service.invalidate_preprocessed()
    assert len(service.preprocessed_templates) == 0


def test_load_raw_prompt(setup_service: Dict[str, any]) -> None:
    """Test the legacy load_raw_prompt method."""
    service = setup_service["service"]

    # Load raw prompt
    raw_prompt = service.load_raw_prompt("dispatcher")

    # Check it returns a string
    assert isinstance(raw_prompt, str)
    assert "<SystemPrompt>" in raw_prompt


def test_file_not_found_handling(setup_service: Dict[str, any]) -> None:
    """Test handling of non-existent files."""
    service = setup_service["service"]

    # Test with a non-existent agent
    with pytest.raises(FileNotFoundError):
        service.load_prompt_template("non_existent_agent")


def test_template_caching(setup_service: Dict[str, any]) -> None:
    """Test that templates are properly cached."""
    service = setup_service["service"]

    # First load the template - should hit the filesystem
    template1 = service.load_prompt_template("dispatcher")
    assert isinstance(template1, PromptTemplate)

    # Load it again - should use the cached version
    template2 = service.load_prompt_template("dispatcher")
    assert template1 is template2  # Should be the same object instance


def test_cognitive_structure_feature_flags(setup_service: Dict[str, any]) -> None:
    """Test handling of cognitive structure feature flags."""
    service = setup_service["service"]

    # Create a test template with cognitive structure sections
    template_xml = """<SystemPrompt>
        <YourIdentity>
            <YourRoleAndPurpose>
                <YourAgentType>test_agent</YourAgentType>
            </YourRoleAndPurpose>
        </YourIdentity>
        <YourCognitiveStructure>
            <Capabilities></Capabilities>
            <Agents></Agents>
            <InteractionTypes></InteractionTypes>
        </YourCognitiveStructure>
    </SystemPrompt>"""

    # Update Template.xml
    with open(setup_service["template_path"], "w") as f:
        f.write(template_xml)

    # Update the system.json to use the updated template
    json_content = {"template_path": "../Template.xml", "nodes": {}}

    with open(setup_service["json_path"], "w") as f:
        json.dump(json_content, f)

    # Clear the template cache
    service.prompt_templates.clear()

    # Test with cognitive structure disabled
    agent_config_no_cognitive = AgentConfig(
        name=AgentType.DISPATCHER,
        description="Test agent",
        model="test-model",
        max_tokens=1000,
        temperature=0.7,
        features={
            "cognitive": False,  # Disable entire cognitive structure
            "persona_config": {},  # Required by AgentConfig validation
            "cognitive_structure": {},  # Not actually used when cognitive is False
        },
    )

    result = service.preprocess_prompt(agent_config_no_cognitive, {})
    assert "<YourCognitiveStructure>" not in result

    # Test with specific cognitive structure sections disabled
    agent_config_partial_cognitive = AgentConfig(
        name=AgentType.DISPATCHER,
        description="Test agent",
        model="test-model",
        max_tokens=1000,
        temperature=0.7,
        features={
            "cognitive": True,
            "persona_config": {},  # Required by AgentConfig validation
            "cognitive_structure": {
                "capabilities": False,  # Disable just capabilities
                "agents": True,
                "interaction_types": True,
            },
        },
    )

    result = service.preprocess_prompt(agent_config_partial_cognitive, {})
    assert "<YourCognitiveStructure>" in result  # Structure should exist
    assert "<Capabilities>" not in result  # Capabilities should be removed
    # The XML serialization might use self-closing tags
    assert any(tag in result for tag in ["<Agents>", "<Agents />"])  # Agents should remain
    assert any(
        tag in result for tag in ["<InteractionTypes>", "<InteractionTypes />"]
    )  # InteractionTypes should remain


def test_persona_detail_levels(setup_service: Dict[str, any]) -> None:
    """Test handling of persona detail levels."""
    service = setup_service["service"]
    mock_persona_service = setup_service["mock_persona_service"]

    # Reset mock to track new calls
    mock_persona_service.get_section_dict.reset_mock()

    # Test with string-based detail levels
    agent_config = AgentConfig(
        name=AgentType.DISPATCHER,
        description="Test agent",
        model="test-model",
        max_tokens=1000,
        temperature=0.7,
        features={
            "cognitive": True,
            "cognitive_structure": {
                "capabilities": True,
                "agents": True,
                "interaction_types": True,
            },
            "persona_config": {
                "identity": "low",  # String detail level
                "personality": "high",  # String detail level
                "backstory": "none",  # None detail level
            },
        },
    )

    service.preprocess_prompt(agent_config, {"PERSONA_NAME": "luna"})

    # Verify persona service was called with correct detail levels
    mock_persona_service.get_section_dict.assert_any_call("luna", "identity", "low")
    mock_persona_service.get_section_dict.assert_any_call("luna", "personality", "high")

    # Verify backstory was not requested (should be skipped)
    for call in mock_persona_service.get_section_dict.call_args_list:
        args, _ = call
        if args[1] == "backstory":
            assert False, "Backstory should not be requested when detail is 'none'"


# Note: The following tests have been removed as they tested functionality
# that has been replaced with a different implementation approach.
# They were testing direct token replacement, while the system now uses
# structured dictionary-based replacements with XML node paths.
#
# - test_preprocess_with_complex_replacements
# - test_preprocess_with_path_replacements
# - test_compile_with_path_replacements


def test_preprocess_with_dictionary_structure(
    setup_service: Dict[str, any], mock_agent_config: AgentConfig
) -> None:
    """Test preprocessing a prompt with structured dictionary replacements."""
    service = setup_service["service"]
    mock_persona_service = setup_service["mock_persona_service"]

    # Disable the persona service for this test
    mock_persona_service.get_section.return_value = None

    # Create a simplified agent config
    agent_config = AgentConfig(
        name=mock_agent_config.name,
        description="Test agent",
        model="test-model",
        features={
            "persona_config": {},  # Empty persona config
            "cognitive": True,
            "cognitive_structure": {
                "capabilities": True,
                "agents": True,
                "interaction_types": True,
            },
            "working_memory": True,
        },
        max_tokens=1000,
        temperature=0.7,
    )

    # Create a test template
    template_xml = """<SystemPrompt>
        <YourKnowledge>
            <WorkingMemory></WorkingMemory>
        </YourKnowledge>
        <YourIdentity></YourIdentity>
    </SystemPrompt>"""

    # Update Template.xml
    with open(setup_service["template_path"], "w") as f:
        f.write(template_xml)

    # Update the system.json to use the updated template
    json_content = {
        "template_path": "../Template.xml",
        "nodes": {"YourIdentity": {"YourRoleAndPurpose": {"YourAgentType": "dispatcher"}}},
    }

    with open(setup_service["json_path"], "w") as f:
        json.dump(json_content, f)

    # Clear the template cache
    service.prompt_templates.clear()

    # Test with path-style replacement (dictionary keys with slashes)
    result = service.preprocess_prompt(
        agent_config,
        {"YourIdentity/Name": "Luna", "YourKnowledge/WorkingMemory": "Test memory content"},
    )

    # Check that the result is a string
    assert isinstance(result, str)

    # Check that path replacements worked (case insensitive)
    assert "luna" in result.lower()
    assert "test memory content" in result.lower()

    # Check that preprocessing with direct structured dictionaries works
    result2 = service.preprocess_prompt(
        agent_config,
        {
            "your_identity": {"description": "Virtual assistant"},
            "your_knowledge": {"working_memory": "Different memory content"},
        },
    )

    # Check content was properly inserted
    assert "virtual assistant" in result2.lower()
    assert "different memory content" in result2.lower()

    # Test the auto-routing to YourKnowledge functionality for non-your_ prefixed dictionaries
    result3 = service.preprocess_prompt(
        agent_config, {"CustomData": {"item1": "Value1", "item2": "Value2"}}
    )

    # Check that non-your_ dictionary was properly added to your_knowledge
    assert "customdata" in result3.lower()
    assert "value1" in result3.lower()
    assert "value2" in result3.lower()


def test_path_based_replacement_in_compile(
    setup_service: Dict[str, any], mock_agent_config: AgentConfig
) -> None:
    """Test path-based replacements in compile method."""
    service = setup_service["service"]

    # Create a test template
    template_xml = """<SystemPrompt>
        <Conversation>
            <History></History>
            <Context></Context>
        </Conversation>
        <YourKnowledge></YourKnowledge>
    </SystemPrompt>"""

    # Update Template.xml
    with open(setup_service["template_path"], "w") as f:
        f.write(template_xml)

    # Update the system.json to use the updated template
    json_content = {
        "template_path": "../Template.xml",
        "nodes": {"YourIdentity": {"YourRoleAndPurpose": {"YourAgentType": "dispatcher"}}},
    }

    with open(setup_service["json_path"], "w") as f:
        json.dump(json_content, f)

    # Clear the template cache
    service.prompt_templates.clear()

    # Preprocess template first
    service.preprocess_prompt(mock_agent_config, {})

    # Now compile with a path-based replacement
    result = service.compile_prompt(
        mock_agent_config.name.value,
        {
            "Conversation/History": "Previous message history",
            "Conversation/Context": "Current context",
        },
    )

    # Check result
    assert "previous message history" in result.lower()
    assert "current context" in result.lower()

    # Test with dictionary auto-routing
    result2 = service.compile_prompt(
        mock_agent_config.name.value,
        {
            # A dictionary that should be automatically added to your_knowledge
            "CustomItem": {"field1": "Value1", "field2": "Value2"},
            # A dictionary that has the your_ prefix
            "your_behavior": {"trait": "Helpful"},
        },
    )

    # Check that non-your_ dictionary was auto-routed to your_knowledge
    assert "customitem" in result2.lower()
    assert "value1" in result2.lower()
    assert "value2" in result2.lower()

    # Check that your_ prefixed dictionary was placed directly in that section
    assert "helpful" in result2.lower()
