"""
Unit tests for the EmotionService.
"""

import unittest
from datetime import datetime
from unittest.mock import patch

from domain.models.emotion import (
    EmotionAdjustment,
    EmotionAdjustmentRequest,
    EmotionalProfile,
    EmotionalState,
)
from services.emotion_service import EmotionService


class TestEmotionService(unittest.TestCase):
    """Tests for the EmotionService class."""

    def setUp(self):
        """Set up test fixtures."""
        self.emotion_service = EmotionService()

    def test_initialization(self):
        """Test that the service initializes with proper default values."""
        # Check that profile is initialized
        self.assertIsInstance(self.emotion_service.profile, EmotionalProfile)

        # Check that current state is initialized to baseline values
        current_state = self.emotion_service.profile.current_state
        self.assertAlmostEqual(
            current_state.pleasure, self.emotion_service.profile.baseline_pleasure
        )
        self.assertAlmostEqual(current_state.arousal, self.emotion_service.profile.baseline_arousal)
        self.assertAlmostEqual(
            current_state.dominance, self.emotion_service.profile.baseline_dominance
        )

        # Check that history contains the initial state
        self.assertEqual(len(self.emotion_service.profile.history), 1)
        self.assertEqual(self.emotion_service.profile.history[0], current_state)

    def test_get_current_state(self):
        """Test getting the current emotional state."""
        state = self.emotion_service.get_current_state()

        # Verify it returns the current state from the profile
        self.assertEqual(state, self.emotion_service.profile.current_state)

        # Modify the state and check the method returns the updated state
        new_state = EmotionalState(pleasure=0.8, arousal=0.7, dominance=0.6, reason="Test state")
        self.emotion_service.profile.current_state = new_state

        updated_state = self.emotion_service.get_current_state()
        self.assertEqual(updated_state, new_state)

    def test_get_relative_state(self):
        """Test getting the emotional state relative to baseline."""
        # Set up a known state difference from baseline
        self.emotion_service.profile.baseline_pleasure = 0.6
        self.emotion_service.profile.baseline_arousal = 0.5
        self.emotion_service.profile.baseline_dominance = 0.7

        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.7, arousal=0.4, dominance=0.5, reason="Test relative state"
        )

        relative = self.emotion_service.get_relative_state()

        # Verify calculations
        self.assertAlmostEqual(relative["pleasure"], 0.1)  # 0.7 - 0.6
        self.assertAlmostEqual(relative["arousal"], -0.1)  # 0.4 - 0.5
        self.assertAlmostEqual(relative["dominance"], -0.2)  # 0.5 - 0.7

    def test_adjust_emotion(self):
        """Test adjusting emotions with various adjustment levels."""
        # Start with known values
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.5, arousal=0.5, dominance=0.5, reason="Initial test state"
        )

        # Reset history for this test
        self.emotion_service.profile.history = [self.emotion_service.profile.current_state]

        # Test significant increase
        request = EmotionAdjustmentRequest(
            pleasure_adjustment=EmotionAdjustment.SIGNIFICANT_INCREASE,
            arousal_adjustment=EmotionAdjustment.MODERATE_INCREASE,
            dominance_adjustment=EmotionAdjustment.SLIGHT_INCREASE,
            reason="Test adjustment",
        )

        new_state = self.emotion_service.adjust_emotion(request)

        # Verify values are adjusted correctly
        self.assertAlmostEqual(new_state.pleasure, 0.8)  # 0.5 + 0.3
        self.assertAlmostEqual(new_state.arousal, 0.65)  # 0.5 + 0.15
        self.assertAlmostEqual(new_state.dominance, 0.55)  # 0.5 + 0.05
        self.assertEqual(new_state.reason, "Test adjustment")

        # Verify history is updated
        self.assertEqual(len(self.emotion_service.profile.history), 2)
        self.assertEqual(self.emotion_service.profile.history[-1], new_state)

        # Test clamping at upper bound
        request = EmotionAdjustmentRequest(
            pleasure_adjustment=EmotionAdjustment.SIGNIFICANT_INCREASE, reason="Test upper bound"
        )

        upper_state = self.emotion_service.adjust_emotion(request)
        self.assertAlmostEqual(upper_state.pleasure, 1.0)  # Clamped to 1.0 (0.8 + 0.3 = 1.1)

        # Test clamping at lower bound
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.1, arousal=0.1, dominance=0.1, reason="Low state"
        )

        request = EmotionAdjustmentRequest(
            pleasure_adjustment=EmotionAdjustment.SIGNIFICANT_DECREASE, reason="Test lower bound"
        )

        lower_state = self.emotion_service.adjust_emotion(request)
        self.assertAlmostEqual(lower_state.pleasure, 0.0)  # Clamped to 0.0 (0.1 - 0.3 = -0.2)

        # Verify history limit is enforced
        # Fill the history with many states
        for i in range(100):
            self.emotion_service.adjust_emotion(EmotionAdjustmentRequest(reason=f"State {i}"))

        # History should be capped at 100 items
        self.assertEqual(len(self.emotion_service.profile.history), 100)

        # Verify the most recent states are kept (the oldest ones are discarded)
        self.assertTrue(
            any(state.reason == "State 99" for state in self.emotion_service.profile.history)
        )
        self.assertTrue(
            any(state.reason == "State 98" for state in self.emotion_service.profile.history)
        )
        self.assertFalse(
            any(state.reason == "Test adjustment" for state in self.emotion_service.profile.history)
        )

    def test_decay(self):
        """Test the natural decay of emotions toward baseline."""
        # Set up baseline and current state with difference
        self.emotion_service.profile.baseline_pleasure = 0.5
        self.emotion_service.profile.baseline_arousal = 0.5
        self.emotion_service.profile.baseline_dominance = 0.5
        self.emotion_service.profile.decay_rate = 0.1

        # Reset history for this test and add many states to test history limiting
        self.emotion_service.profile.history = []

        # Add 101 initial states to the history to test history limiting in decay
        for i in range(101):
            self.emotion_service.profile.history.append(
                EmotionalState(
                    pleasure=0.5 + (i * 0.01),
                    arousal=0.5,
                    dominance=0.5,
                    reason=f"Initial state {i}",
                )
            )

        # Verify history size before decay
        self.assertEqual(len(self.emotion_service.profile.history), 101)

        # Set current state significantly above baseline
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.8, arousal=0.8, dominance=0.8, reason="High emotional state"
        )

        # Apply decay
        self.emotion_service.decay()

        # Check values have decayed toward baseline
        current = self.emotion_service.profile.current_state
        self.assertAlmostEqual(current.pleasure, 0.7)  # 0.8 - 0.1 decay
        self.assertAlmostEqual(current.arousal, 0.7)
        self.assertAlmostEqual(current.dominance, 0.7)
        self.assertEqual(current.reason, "Natural decay")

        # Verify history is limited to 100 items
        self.assertEqual(len(self.emotion_service.profile.history), 100)

        # Test decay when already at baseline
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.5, arousal=0.5, dominance=0.5, reason="At baseline"
        )

        # Reset history for clean test
        self.emotion_service.profile.history = [self.emotion_service.profile.current_state]
        initial_history_len = len(self.emotion_service.profile.history)
        self.emotion_service.decay()

        # Should not create a new state when at baseline (no change)
        self.assertEqual(len(self.emotion_service.profile.history), initial_history_len)

        # Test decay below baseline
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.3, arousal=0.3, dominance=0.3, reason="Below baseline"
        )

        self.emotion_service.decay()

        # Values should move toward baseline (increase)
        current = self.emotion_service.profile.current_state
        self.assertAlmostEqual(current.pleasure, 0.4)  # 0.3 + 0.1 decay toward baseline
        self.assertAlmostEqual(current.arousal, 0.4)
        self.assertAlmostEqual(current.dominance, 0.4)

    def test_decay_minimal_change(self):
        """Test that decay only creates a new state for significant changes."""
        # Looking at the implementation, the change needs to be >0.01 to create
        # a new state, but for a small change, _decay_toward_baseline will return
        # the baseline directly (not a small increment), which actually does cause
        # a change >0.01.

        # For this test, we'll create a scenario where the decay_toward_baseline
        # function returns a very small change

        # Set up the baseline and current state with a minimal difference
        # that's larger than decay_amount but still very small
        self.emotion_service.profile.baseline_pleasure = 0.5
        self.emotion_service.profile.baseline_arousal = 0.5
        self.emotion_service.profile.baseline_dominance = 0.5

        # Set a very small decay rate (smaller than the difference from baseline)
        self.emotion_service.profile.decay_rate = 0.001

        # Reset history for this test
        self.emotion_service.profile.history = []

        # Current state with a difference smaller than the 0.01 threshold for recording
        # but larger than the decay_amount
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.505,  # 0.005 difference, which is > decay_amount but < 0.01
            arousal=0.5,
            dominance=0.5,
            reason="Minimal difference",
        )

        # Add current state to history
        self.emotion_service.profile.history.append(self.emotion_service.profile.current_state)
        history_len_before = len(self.emotion_service.profile.history)

        # Apply decay - should result in pleasure = 0.504 (a 0.001 change)
        self.emotion_service.decay()

        # Verify the change was too small to record a new state
        self.assertEqual(len(self.emotion_service.profile.history), history_len_before)

    def test_get_emotion_label(self):
        """Test getting human-readable emotion labels based on PAD values."""
        # Test all PAD value combinations to ensure complete coverage of the emotion label mapping

        # === High Pleasure Group (> 0.7) ===

        # High pleasure, high arousal, high dominance
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.8, arousal=0.8, dominance=0.8
        )
        self.assertEqual(self.emotion_service.get_emotion_label(), "Joyful")

        # High pleasure, high arousal, low dominance
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.8, arousal=0.8, dominance=0.2
        )
        self.assertEqual(self.emotion_service.get_emotion_label(), "Excited")

        # High pleasure, high arousal, medium dominance
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.8, arousal=0.8, dominance=0.5
        )
        self.assertEqual(self.emotion_service.get_emotion_label(), "Happy")

        # High pleasure, low arousal, high dominance
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.8, arousal=0.2, dominance=0.8
        )
        self.assertEqual(self.emotion_service.get_emotion_label(), "Content")

        # High pleasure, low arousal, low dominance
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.8, arousal=0.2, dominance=0.2
        )
        self.assertEqual(self.emotion_service.get_emotion_label(), "Relaxed")

        # High pleasure, low arousal, medium dominance
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.8, arousal=0.2, dominance=0.5
        )
        self.assertEqual(self.emotion_service.get_emotion_label(), "Calm")

        # High pleasure, medium arousal, high dominance
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.8, arousal=0.5, dominance=0.8
        )
        self.assertEqual(self.emotion_service.get_emotion_label(), "Satisfied")

        # High pleasure, medium arousal, low dominance
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.8, arousal=0.5, dominance=0.2
        )
        self.assertEqual(self.emotion_service.get_emotion_label(), "Pleasant")

        # High pleasure, medium arousal, medium dominance
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.8, arousal=0.5, dominance=0.5
        )
        self.assertEqual(self.emotion_service.get_emotion_label(), "Positive")

        # === Low Pleasure Group (< 0.3) ===

        # Low pleasure, high arousal, high dominance
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.2, arousal=0.8, dominance=0.8
        )
        self.assertEqual(self.emotion_service.get_emotion_label(), "Angry")

        # Low pleasure, high arousal, low dominance
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.2, arousal=0.8, dominance=0.2
        )
        self.assertEqual(self.emotion_service.get_emotion_label(), "Anxious")

        # Low pleasure, high arousal, medium dominance
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.2, arousal=0.8, dominance=0.5
        )
        self.assertEqual(self.emotion_service.get_emotion_label(), "Frustrated")

        # Low pleasure, low arousal, high dominance
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.2, arousal=0.2, dominance=0.8
        )
        self.assertEqual(self.emotion_service.get_emotion_label(), "Disappointed")

        # Low pleasure, low arousal, low dominance
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.2, arousal=0.2, dominance=0.2
        )
        self.assertEqual(self.emotion_service.get_emotion_label(), "Sad")

        # Low pleasure, low arousal, medium dominance
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.2, arousal=0.2, dominance=0.5
        )
        self.assertEqual(self.emotion_service.get_emotion_label(), "Melancholy")

        # Low pleasure, medium arousal, high dominance
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.2, arousal=0.5, dominance=0.8
        )
        self.assertEqual(self.emotion_service.get_emotion_label(), "Dissatisfied")

        # Low pleasure, medium arousal, low dominance
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.2, arousal=0.5, dominance=0.2
        )
        self.assertEqual(self.emotion_service.get_emotion_label(), "Unhappy")

        # Low pleasure, medium arousal, medium dominance
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.2, arousal=0.5, dominance=0.5
        )
        self.assertEqual(self.emotion_service.get_emotion_label(), "Negative")

        # === Medium Pleasure Group (0.3-0.7) ===

        # Medium pleasure, high arousal, high dominance
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.5, arousal=0.8, dominance=0.8
        )
        self.assertEqual(self.emotion_service.get_emotion_label(), "Engaged")

        # Medium pleasure, high arousal, low dominance
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.5, arousal=0.8, dominance=0.2
        )
        self.assertEqual(self.emotion_service.get_emotion_label(), "Surprised")

        # Medium pleasure, high arousal, medium dominance
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.5, arousal=0.8, dominance=0.5
        )
        self.assertEqual(self.emotion_service.get_emotion_label(), "Alert")

        # Medium pleasure, low arousal, high dominance
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.5, arousal=0.2, dominance=0.8
        )
        self.assertEqual(self.emotion_service.get_emotion_label(), "Thoughtful")

        # Medium pleasure, low arousal, low dominance
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.5, arousal=0.2, dominance=0.2
        )
        self.assertEqual(self.emotion_service.get_emotion_label(), "Reflective")

        # Medium pleasure, low arousal, medium dominance
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.5, arousal=0.2, dominance=0.5
        )
        self.assertEqual(self.emotion_service.get_emotion_label(), "Calm")

        # Medium pleasure, medium arousal, high dominance
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.5, arousal=0.5, dominance=0.8
        )
        self.assertEqual(self.emotion_service.get_emotion_label(), "Confident")

        # Medium pleasure, medium arousal, low dominance
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.5, arousal=0.5, dominance=0.2
        )
        self.assertEqual(self.emotion_service.get_emotion_label(), "Reserved")

        # Medium values - neutral zone
        self.emotion_service.profile.current_state = EmotionalState(
            pleasure=0.5, arousal=0.5, dominance=0.5
        )
        self.assertEqual(self.emotion_service.get_emotion_label(), "Neutral")

    def test_get_emotional_history(self):
        """Test retrieving the emotional state history."""
        # Reset history for this test
        self.emotion_service.profile.history = []

        # Create a series of states
        for i in range(5):
            self.emotion_service.profile.history.append(
                EmotionalState(
                    pleasure=0.5 + (i * 0.1), arousal=0.5, dominance=0.5, reason=f"Test state {i}"
                )
            )

        # Get all history
        history = self.emotion_service.get_emotional_history(limit=10)
        self.assertEqual(len(history), 5)  # 5 test states

        # Get limited history
        limited_history = self.emotion_service.get_emotional_history(limit=3)
        self.assertEqual(len(limited_history), 3)

        # Verify most recent states are returned (the last 3 states)
        self.assertEqual(limited_history[0].pleasure, 0.7)  # 0.5 + (2 * 0.1)
        self.assertEqual(limited_history[1].pleasure, 0.8)  # 0.5 + (3 * 0.1)
        self.assertEqual(limited_history[2].pleasure, 0.9)  # 0.5 + (4 * 0.1)
        self.assertEqual(limited_history[2].reason, "Test state 4")

        # Test with empty history
        self.emotion_service.profile.history = []
        empty_history = self.emotion_service.get_emotional_history()
        self.assertEqual(len(empty_history), 0)

    def test_clamp_value(self):
        """Test the _clamp_value helper method."""
        # Test values within bounds
        self.assertAlmostEqual(self.emotion_service._clamp_value(0.5), 0.5)

        # Test values above upper bound
        self.assertAlmostEqual(self.emotion_service._clamp_value(1.5), 1.0)

        # Test values below lower bound
        self.assertAlmostEqual(self.emotion_service._clamp_value(-0.5), 0.0)

        # Test boundary values
        self.assertAlmostEqual(self.emotion_service._clamp_value(0.0), 0.0)
        self.assertAlmostEqual(self.emotion_service._clamp_value(1.0), 1.0)

    def test_decay_toward_baseline(self):
        """Test the _decay_toward_baseline helper method."""
        # Test decay when current > baseline
        decayed = self.emotion_service._decay_toward_baseline(0.8, 0.5, 0.1)
        self.assertAlmostEqual(decayed, 0.7)  # 0.8 - 0.1

        # Test decay when current < baseline
        decayed = self.emotion_service._decay_toward_baseline(0.3, 0.5, 0.1)
        self.assertAlmostEqual(decayed, 0.4)  # 0.3 + 0.1

        # Test when difference < decay amount (should snap to baseline)
        decayed = self.emotion_service._decay_toward_baseline(0.52, 0.5, 0.1)
        self.assertAlmostEqual(decayed, 0.5)  # Snap to baseline

        # Test when already at baseline
        decayed = self.emotion_service._decay_toward_baseline(0.5, 0.5, 0.1)
        self.assertAlmostEqual(decayed, 0.5)  # No change


if __name__ == "__main__":
    unittest.main()
