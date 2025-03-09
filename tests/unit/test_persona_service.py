"""Unit tests for the PersonaService using pytest."""

import json
import os
from unittest.mock import mock_open, patch

import pytest

from domain.models.persona.sections import (
    PersonaBeliefs,
    PersonaIdentity,
    PersonaPersonality,
    PersonaSection,
)
from services.persona_service import PersonaService


@pytest.fixture
def persona_service():
    """Create a PersonaService instance for testing."""
    return PersonaService()


@pytest.fixture
def test_persona_data():
    """Sample persona data for testing."""
    return {
        "identity": {
            "name": "Luna",
            "age": 22,
            "gender": "female",
            "location": "Seattle, Washington",
            "occupation": "AI Assistant",
            "core_traits": ["Tech-savvy", "Opinionated", "Playful"],
            "self_perception": "Self-aware with a distinct personality",
            "ai_awareness": "Fully aware of being an AI",
        },
        "personality": {
            "conversational_style": ["Friendly but snarky", "Witty comebacks"],
            "humor_style": "Somewhat crude with playful sarcasm",
        },
    }


@patch("builtins.open", new_callable=mock_open)
@patch("os.path.exists")
@patch("json.load")
def test_load_persona(mock_json_load, mock_exists, mock_file, persona_service, test_persona_data):
    """Test loading a persona from a JSON file."""
    mock_exists.return_value = True
    mock_json_load.return_value = test_persona_data

    result = persona_service.load_persona("luna")

    assert result is True
    assert "luna" in persona_service.personas
    assert "identity" in persona_service.personas["luna"]
    assert "personality" in persona_service.personas["luna"]

    # Verify the identity section was loaded correctly
    identity = persona_service.personas["luna"]["identity"]
    assert isinstance(identity, PersonaIdentity)
    assert identity.name == "Luna"
    assert identity.age == 22
    assert identity.gender == "female"

    # Verify the personality section was loaded correctly
    personality = persona_service.personas["luna"]["personality"]
    assert isinstance(personality, PersonaPersonality)
    assert personality.humor_style == "Somewhat crude with playful sarcasm"
    assert personality.conversational_style == ["Friendly but snarky", "Witty comebacks"]


@patch("builtins.open", new_callable=mock_open)
@patch("os.path.exists")
@patch("json.load")
def test_get_section(mock_json_load, mock_exists, mock_file, persona_service, test_persona_data):
    """Test getting a specific section of a persona."""
    mock_exists.return_value = True
    mock_json_load.return_value = test_persona_data

    # Load the persona first
    persona_service.load_persona("luna")

    # Get the identity section
    identity = persona_service.get_section("luna", "identity")

    assert isinstance(identity, PersonaIdentity)
    assert identity.name == "Luna"

    # Get a non-existent section
    non_existent = persona_service.get_section("luna", "non_existent")
    assert non_existent is None


@patch("builtins.open", new_callable=mock_open)
@patch("os.path.exists")
@patch("json.load")
def test_get_section_dict_all_detail(
    mock_json_load, mock_exists, mock_file, persona_service, test_persona_data
):
    """Test getting a section as a dictionary with all details."""
    mock_exists.return_value = True
    mock_json_load.return_value = test_persona_data

    # Load the persona first
    persona_service.load_persona("luna")

    # Get the identity section as a dictionary with all details
    identity_dict = persona_service.get_section_dict("luna", "identity", "all")

    assert identity_dict["name"] == "Luna"
    assert identity_dict["age"] == 22
    assert identity_dict["gender"] == "female"
    assert identity_dict["location"] == "Seattle, Washington"
    assert identity_dict["occupation"] == "AI Assistant"

    # Make sure private fields are excluded
    assert "_section" not in identity_dict
    assert "_detail_level_low" not in identity_dict


@patch("builtins.open", new_callable=mock_open)
@patch("os.path.exists")
@patch("json.load")
def test_get_section_dict_low_detail(
    mock_json_load, mock_exists, mock_file, persona_service, test_persona_data
):
    """Test getting a section as a dictionary with low detail level."""
    mock_exists.return_value = True
    mock_json_load.return_value = test_persona_data

    # Load the persona first
    persona_service.load_persona("luna")

    # Get the identity section as a dictionary with low detail level
    identity_dict = persona_service.get_section_dict("luna", "identity", "low")

    # These should be included at low detail level
    assert identity_dict["name"] == "Luna"
    assert identity_dict["age"] == 22
    assert identity_dict["gender"] == "female"

    # These should be excluded at low detail level
    assert "location" not in identity_dict
    assert "occupation" not in identity_dict
    assert "core_traits" not in identity_dict
    assert "self_perception" not in identity_dict


@patch("os.listdir")
def test_get_all_persona_names(mock_listdir, persona_service):
    """Test getting a list of all available persona names."""
    mock_listdir.return_value = ["luna.json", "test.json", "other.txt"]

    names = persona_service.get_all_persona_names()

    assert names == ["luna", "test"]
    assert "other" not in names
