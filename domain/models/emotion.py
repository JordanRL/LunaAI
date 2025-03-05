from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

class EmotionAdjustment(Enum):
    """
    Possible emotional state adjustments.
    """
    NO_CHANGE = "no_change"
    SLIGHT_DECREASE = "slight_decrease"
    MODERATE_DECREASE = "moderate_decrease"
    SIGNIFICANT_DECREASE = "significant_decrease"
    SLIGHT_INCREASE = "slight_increase"
    MODERATE_INCREASE = "moderate_increase"
    SIGNIFICANT_INCREASE = "significant_increase"
    
    @staticmethod
    def to_value(adjustment: 'EmotionAdjustment') -> float:
        """Convert adjustment to numeric value"""
        adjustment_map = {
            EmotionAdjustment.NO_CHANGE: 0.0,
            EmotionAdjustment.SLIGHT_DECREASE: -0.05,
            EmotionAdjustment.MODERATE_DECREASE: -0.15,
            EmotionAdjustment.SIGNIFICANT_DECREASE: -0.30,
            EmotionAdjustment.SLIGHT_INCREASE: 0.05,
            EmotionAdjustment.MODERATE_INCREASE: 0.15,
            EmotionAdjustment.SIGNIFICANT_INCREASE: 0.30
        }
        return adjustment_map[adjustment]

@dataclass
class EmotionalState:
    """
    Represents an emotional state at a point in time using the PAD (Pleasure-Arousal-Dominance) model.
    
    Attributes:
        pleasure: How positive/negative (0.0 = very negative, 1.0 = very positive)
        arousal: How energetic/calm (0.0 = very calm, 1.0 = very excited)
        dominance: How dominant/submissive (0.0 = very submissive, 1.0 = very dominant)
        timestamp: When this emotional state was recorded
        reason: Reason for this emotional state
    """
    pleasure: float  # 0.0 to 1.0
    arousal: float   # 0.0 to 1.0
    dominance: float # 0.0 to 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary representation"""
        return {
            "pleasure": self.pleasure,
            "arousal": self.arousal,
            "dominance": self.dominance
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, float], reason: Optional[str] = None) -> 'EmotionalState':
        """Create from dictionary representation"""
        return cls(
            pleasure=data.get("pleasure", 0.5),
            arousal=data.get("arousal", 0.5),
            dominance=data.get("dominance", 0.5),
            reason=reason
        )

@dataclass
class EmotionalProfile:
    """
    Represents Luna's complete emotional profile, including baseline, 
    current state, and history.
    
    Attributes:
        baseline_pleasure: Baseline pleasure level
        baseline_arousal: Baseline arousal level
        baseline_dominance: Baseline dominance level
        decay_rate: Rate at which emotions return to baseline
        current_state: Current emotional state
        history: History of emotional states
    """
    baseline_pleasure: float = 0.60
    baseline_arousal: float = 0.55
    baseline_dominance: float = 0.65
    decay_rate: float = 0.10
    current_state: EmotionalState = field(default_factory=lambda: EmotionalState(0.60, 0.55, 0.65))
    history: List[EmotionalState] = field(default_factory=list)
    
    def get_baseline(self) -> EmotionalState:
        """Get the baseline emotional state"""
        return EmotionalState(
            pleasure=self.baseline_pleasure,
            arousal=self.baseline_arousal,
            dominance=self.baseline_dominance,
            reason="Baseline state"
        )
        
    def get_relative_state(self) -> Dict[str, float]:
        """Get current state relative to baseline"""
        return {
            "pleasure": self.current_state.pleasure - self.baseline_pleasure,
            "arousal": self.current_state.arousal - self.baseline_arousal,
            "dominance": self.current_state.dominance - self.baseline_dominance
        }

@dataclass
class EmotionAdjustmentRequest:
    """
    Request to adjust Luna's emotional state.
    
    Attributes:
        pleasure_adjustment: How to adjust pleasure
        arousal_adjustment: How to adjust arousal
        dominance_adjustment: How to adjust dominance
        reason: Reason for this adjustment
    """
    pleasure_adjustment: EmotionAdjustment = EmotionAdjustment.NO_CHANGE
    arousal_adjustment: EmotionAdjustment = EmotionAdjustment.NO_CHANGE
    dominance_adjustment: EmotionAdjustment = EmotionAdjustment.NO_CHANGE
    reason: str = "No reason provided"