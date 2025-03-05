"""
Emotion tools for managing Luna's emotional state.
"""

from typing import Dict, List, Any, Optional

from domain.models.tool import Tool, ToolCategory
from domain.models.emotion import EmotionAdjustment, EmotionalState, EmotionalProfile, EmotionAdjustmentRequest
from debug import debug_manager, DebugLevel, log, log_error


class EmotionAdjustmentTool(Tool):
    """Tool for adjusting Luna's emotional state."""
    
    def __init__(self):
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
                        "default": "no_change"
                    },
                    "arousal_adjustment": {
                        "type": "string",
                        "description": "How to adjust Luna's arousal/activation",
                        "enum": [adj.value for adj in EmotionAdjustment],
                        "default": "no_change"
                    },
                    "dominance_adjustment": {
                        "type": "string",
                        "description": "How to adjust Luna's dominance/agency",
                        "enum": [adj.value for adj in EmotionAdjustment],
                        "default": "no_change"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for this emotional adjustment"
                    }
                },
                "required": ["reason"]
            },
            handler=self.handle,
            category=ToolCategory.EMOTION
        )
    
    def handle(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Handle emotional adjustment requests."""
        from emotional_state import get_emotional_state
        emotional_state = get_emotional_state()
        
        # Get adjustments with defaults
        pleasure_adj_str = tool_input.get("pleasure_adjustment", "no_change")
        arousal_adj_str = tool_input.get("arousal_adjustment", "no_change")
        dominance_adj_str = tool_input.get("dominance_adjustment", "no_change")
        reason = tool_input.get("reason", "No reason provided")
        
        # Convert string values to enum
        pleasure_adj = EmotionAdjustment(pleasure_adj_str)
        arousal_adj = EmotionAdjustment(arousal_adj_str)
        dominance_adj = EmotionAdjustment(dominance_adj_str)
        
        # Get numeric values
        pleasure_value = EmotionAdjustment.to_value(pleasure_adj)
        arousal_value = EmotionAdjustment.to_value(arousal_adj)
        dominance_value = EmotionAdjustment.to_value(dominance_adj)
        
        # Store pre-adjustment values for logging
        old_state = emotional_state.get_current_state()
        
        # Apply adjustments with bounds (0.0 to 1.0)
        emotional_state.pleasure = max(0.0, min(1.0, emotional_state.pleasure + pleasure_value))
        emotional_state.arousal = max(0.0, min(1.0, emotional_state.arousal + arousal_value))
        emotional_state.dominance = max(0.0, min(1.0, emotional_state.dominance + dominance_value))
        
        # Log the change
        log(f"Emotion adjusted: P:{old_state['pleasure']:.2f}→{emotional_state.pleasure:.2f} "
            f"A:{old_state['arousal']:.2f}→{emotional_state.arousal:.2f} "
            f"D:{old_state['dominance']:.2f}→{emotional_state.dominance:.2f}", 
            DebugLevel.STANDARD, debug_manager.symbols.PROCESSING)
        log(f"Reason: {reason[:100]}", DebugLevel.STANDARD)
        
        # Record in history
        emotional_state.record_state(reason)
        
        # Get human-readable emotion label
        emotion_label = emotional_state.get_emotion_label()
        
        # Return current emotional state and interpretation
        return {
            "current_emotional_state": emotional_state.get_current_state(),
            "relative_to_baseline": emotional_state.get_relative_state(),
            "emotion_label": emotion_label,
            "changes": {
                "pleasure": emotional_state.pleasure - old_state["pleasure"],
                "arousal": emotional_state.arousal - old_state["arousal"],
                "dominance": emotional_state.dominance - old_state["dominance"]
            }
        }