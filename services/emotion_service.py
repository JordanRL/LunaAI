"""
Emotion service interface for Luna.

This module defines the interface for emotion management.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from domain.models.emotion import EmotionalState, EmotionalProfile, EmotionAdjustmentRequest

class EmotionService(ABC):
    """
    Interface for emotion management.
    
    This service manages Luna's emotional state and provides methods
    for adjusting emotions and querying emotional status.
    """
    
    @abstractmethod
    def get_current_state(self) -> EmotionalState:
        """
        Get the current emotional state.
        
        Returns:
            EmotionalState: Current emotional state
        """
        pass
    
    @abstractmethod
    def get_relative_state(self) -> Dict[str, float]:
        """
        Get current emotional state relative to baseline.
        
        Returns:
            Dict[str, float]: State relative to baseline
        """
        pass
    
    @abstractmethod
    def adjust_emotion(self, request: EmotionAdjustmentRequest) -> EmotionalState:
        """
        Adjust the emotional state.
        
        Args:
            request: Details of the emotional adjustment
            
        Returns:
            EmotionalState: New emotional state after adjustment
        """
        pass
    
    @abstractmethod
    def decay(self) -> None:
        """
        Decay emotional state toward baseline.
        """
        pass
    
    @abstractmethod
    def get_emotion_label(self) -> str:
        """
        Get a human-readable label for the current emotional state.
        
        Returns:
            str: Emotion label
        """
        pass
    
    @abstractmethod
    def get_emotional_history(self, limit: int = 10) -> List[EmotionalState]:
        """
        Get the history of emotional states.
        
        Args:
            limit: Maximum number of states to return
            
        Returns:
            List[EmotionalState]: History of emotional states
        """
        pass