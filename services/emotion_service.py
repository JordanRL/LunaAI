"""
Emotion service interface for Luna.

This module defines the interface for emotion management.
"""

import math
from datetime import datetime
from typing import Any, Dict, List, Optional

from domain.models.emotion import (
    EmotionAdjustment,
    EmotionAdjustmentRequest,
    EmotionalProfile,
    EmotionalState,
)


class EmotionService:
    """
    Interface for emotion management.

    This service manages Luna's emotional state and provides methods
    for adjusting emotions and querying emotional status.
    """

    def __init__(self):
        """Initialize the emotion service with a default emotional profile."""
        self.profile = EmotionalProfile()

        # Initialize with default emotional state
        self.profile.current_state = EmotionalState(
            pleasure=self.profile.baseline_pleasure,
            arousal=self.profile.baseline_arousal,
            dominance=self.profile.baseline_dominance,
            reason="Initial state",
        )

        # Add initial state to history
        self.profile.history.append(self.profile.current_state)

    def get_current_state(self) -> EmotionalState:
        """
        Get the current emotional state.

        Returns:
            EmotionalState: Current emotional state
        """
        return self.profile.current_state

    def get_relative_state(self) -> Dict[str, float]:
        """
        Get current emotional state relative to baseline.

        Returns:
            Dict[str, float]: State relative to baseline
        """
        return self.profile.get_relative_state()

    def adjust_emotion(self, request: EmotionAdjustmentRequest) -> EmotionalState:
        """
        Adjust the emotional state.

        Args:
            request: Details of the emotional adjustment

        Returns:
            EmotionalState: New emotional state after adjustment
        """
        # Get current values
        current_pleasure = self.profile.current_state.pleasure
        current_arousal = self.profile.current_state.arousal
        current_dominance = self.profile.current_state.dominance

        # Calculate new values based on adjustments
        new_pleasure = self._clamp_value(
            current_pleasure + EmotionAdjustment.to_value(request.pleasure_adjustment)
        )
        new_arousal = self._clamp_value(
            current_arousal + EmotionAdjustment.to_value(request.arousal_adjustment)
        )
        new_dominance = self._clamp_value(
            current_dominance + EmotionAdjustment.to_value(request.dominance_adjustment)
        )

        # Create new emotional state
        new_state = EmotionalState(
            pleasure=new_pleasure,
            arousal=new_arousal,
            dominance=new_dominance,
            timestamp=datetime.now(),
            reason=request.reason,
        )

        # Update current state
        self.profile.current_state = new_state

        # Add to history
        self.profile.history.append(new_state)

        # Limit history size
        if len(self.profile.history) > 100:
            self.profile.history = self.profile.history[-100:]

        return new_state

    def decay(self) -> None:
        """
        Decay emotional state toward baseline.
        """
        # Get current values
        current_pleasure = self.profile.current_state.pleasure
        current_arousal = self.profile.current_state.arousal
        current_dominance = self.profile.current_state.dominance

        # Get baseline values
        baseline_pleasure = self.profile.baseline_pleasure
        baseline_arousal = self.profile.baseline_arousal
        baseline_dominance = self.profile.baseline_dominance

        # Calculate decay amount based on decay rate
        decay_amount = self.profile.decay_rate

        # Apply decay toward baseline
        new_pleasure = self._decay_toward_baseline(
            current_pleasure, baseline_pleasure, decay_amount
        )
        new_arousal = self._decay_toward_baseline(current_arousal, baseline_arousal, decay_amount)
        new_dominance = self._decay_toward_baseline(
            current_dominance, baseline_dominance, decay_amount
        )

        # Only create a new state if there's a significant change
        if (
            abs(new_pleasure - current_pleasure) > 0.01
            or abs(new_arousal - current_arousal) > 0.01
            or abs(new_dominance - current_dominance) > 0.01
        ):
            new_state = EmotionalState(
                pleasure=new_pleasure,
                arousal=new_arousal,
                dominance=new_dominance,
                timestamp=datetime.now(),
                reason="Natural decay",
            )

            # Update current state
            self.profile.current_state = new_state

            # Add to history
            self.profile.history.append(new_state)

            # Limit history size
            if len(self.profile.history) > 100:
                self.profile.history = self.profile.history[-100:]

    def get_emotion_label(self) -> str:
        """
        Get a human-readable label for the current emotional state.

        Returns:
            str: Emotion label
        """
        pleasure = self.profile.current_state.pleasure
        arousal = self.profile.current_state.arousal
        dominance = self.profile.current_state.dominance

        # Determine emotion label based on PAD values
        if pleasure > 0.7:
            if arousal > 0.7:
                if dominance > 0.7:
                    return "Joyful"
                elif dominance < 0.3:
                    return "Excited"
                else:
                    return "Happy"
            elif arousal < 0.3:
                if dominance > 0.7:
                    return "Content"
                elif dominance < 0.3:
                    return "Relaxed"
                else:
                    return "Calm"
            else:
                if dominance > 0.7:
                    return "Satisfied"
                elif dominance < 0.3:
                    return "Pleasant"
                else:
                    return "Positive"
        elif pleasure < 0.3:
            if arousal > 0.7:
                if dominance > 0.7:
                    return "Angry"
                elif dominance < 0.3:
                    return "Anxious"
                else:
                    return "Frustrated"
            elif arousal < 0.3:
                if dominance > 0.7:
                    return "Disappointed"
                elif dominance < 0.3:
                    return "Sad"
                else:
                    return "Melancholy"
            else:
                if dominance > 0.7:
                    return "Dissatisfied"
                elif dominance < 0.3:
                    return "Unhappy"
                else:
                    return "Negative"
        else:
            if arousal > 0.7:
                if dominance > 0.7:
                    return "Engaged"
                elif dominance < 0.3:
                    return "Surprised"
                else:
                    return "Alert"
            elif arousal < 0.3:
                if dominance > 0.7:
                    return "Thoughtful"
                elif dominance < 0.3:
                    return "Reflective"
                else:
                    return "Calm"
            else:
                if dominance > 0.7:
                    return "Confident"
                elif dominance < 0.3:
                    return "Reserved"
                else:
                    return "Neutral"

    def get_emotional_history(self, limit: int = 10) -> List[EmotionalState]:
        """
        Get the history of emotional states.

        Args:
            limit: Maximum number of states to return

        Returns:
            List[EmotionalState]: History of emotional states
        """
        return self.profile.history[-limit:] if self.profile.history else []

    def _clamp_value(self, value: float) -> float:
        """
        Clamp a value between 0.0 and 1.0.

        Args:
            value: Value to clamp

        Returns:
            float: Clamped value
        """
        return max(0.0, min(1.0, value))

    def _decay_toward_baseline(self, current: float, baseline: float, decay_amount: float) -> float:
        """
        Decay a value toward baseline.

        Args:
            current: Current value
            baseline: Baseline value
            decay_amount: Amount to decay

        Returns:
            float: New value
        """
        if abs(current - baseline) < decay_amount:
            return baseline

        if current > baseline:
            return current - decay_amount
        else:
            return current + decay_amount
