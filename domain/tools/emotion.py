"""
Emotion tools for managing Luna's emotional state.
"""

from copy import deepcopy
from typing import Any, Dict, List, Optional

from domain.models.emotion import (
    EmotionAdjustment,
    EmotionAdjustmentRequest,
    EmotionalProfile,
    EmotionalState,
)
from domain.models.tool import Tool, ToolCategory
from services.emotion_service import EmotionService


class EmotionAdjustmentTool(Tool):
    """Tool for adjusting Luna's emotional state."""

    def __init__(self, emotion_service: EmotionService):
        """Initialize the emotion adjustment tool."""
        super().__init__(
            name="adjust_emotion",
            description="""Adjust Luna's current emotional state based on events and interactions.

This tool allows you to shift Luna's emotional state along three dimensions:
- Pleasure: How positive/negative Luna feels (0.0 = very negative, 1.0 = very positive)
- Arousal: How energetic/calm Luna feels (0.0 = very calm, 1.0 = very excited)
- Dominance: How dominant/submissive (high or low agency) Luna feels (0.0 = very submissive/passive, 1.0 = very dominant/willful)

Luna's emotional state will naturally decay toward her baseline over time.
Use this tool to make meaningful adjustments when events warrant an emotional reaction.""",
            input_schema={
                "type": "object",
                "properties": {
                    "pleasure_adjustment": {
                        "type": "string",
                        "description": "How to adjust Luna's pleasure/valence",
                        "enum": [adj.value for adj in EmotionAdjustment],
                        "default": "no_change",
                    },
                    "arousal_adjustment": {
                        "type": "string",
                        "description": "How to adjust Luna's arousal/activation",
                        "enum": [adj.value for adj in EmotionAdjustment],
                        "default": "no_change",
                    },
                    "dominance_adjustment": {
                        "type": "string",
                        "description": "How to adjust Luna's dominance/agency",
                        "enum": [adj.value for adj in EmotionAdjustment],
                        "default": "no_change",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for this emotional adjustment",
                    },
                },
                "required": ["reason"],
            },
            handler=self.handle,
            category=ToolCategory.EMOTION,
        )
        self.emotion_service = emotion_service

    def handle(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Handle emotional adjustment requests."""
        # Get adjustments with defaults
        pleasure_adj_str = tool_input.get("pleasure_adjustment", "no_change")
        arousal_adj_str = tool_input.get("arousal_adjustment", "no_change")
        dominance_adj_str = tool_input.get("dominance_adjustment", "no_change")
        reason = tool_input.get("reason", "No reason provided")

        # Convert string values to enum
        pleasure_adj = EmotionAdjustment(pleasure_adj_str)
        arousal_adj = EmotionAdjustment(arousal_adj_str)
        dominance_adj = EmotionAdjustment(dominance_adj_str)

        # Create emotion adjustment request
        emotion_adjustment_request = EmotionAdjustmentRequest(
            pleasure_adjustment=pleasure_adj,
            arousal_adjustment=arousal_adj,
            dominance_adjustment=dominance_adj,
            reason=reason,
        )

        self.emotion_service.adjust_emotion(emotion_adjustment_request)

        # Return current emotional state and interpretation
        return {
            "current_emotional_state": self.emotion_service.get_current_state().to_dict(),
            "relative_to_baseline": self.emotion_service.get_relative_state(),
            "emotion_label": self.emotion_service.get_emotion_label(),
            "changes": {
                "pleasure": EmotionAdjustment.to_value(pleasure_adj),
                "arousal": EmotionAdjustment.to_value(arousal_adj),
                "dominance": EmotionAdjustment.to_value(dominance_adj),
            },
        }
