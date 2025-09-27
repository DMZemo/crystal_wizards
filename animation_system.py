
"""
Crystal Wizards - Animation System
Handles smooth animations for wizard movement and other game elements
"""

import pygame
import math
from typing import Dict, Tuple, Optional, Callable

class Animation:
    """Base animation class"""
    
    def __init__(self, duration: float, easing_func: Optional[Callable] = None):
        self.duration = duration
        self.elapsed = 0.0
        self.completed = False
        self.easing_func = easing_func or self.linear_ease
        
    def update(self, dt: float) -> float:
        """Update animation and return progress (0.0 to 1.0)"""
        if self.completed:
            return 1.0
            
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.elapsed = self.duration
            self.completed = True
            
        progress = self.elapsed / self.duration
        return self.easing_func(progress)
        
    def is_completed(self) -> bool:
        """Check if animation is completed"""
        return self.completed
        
    @staticmethod
    def linear_ease(t: float) -> float:
        """Linear easing function"""
        return t
        
    @staticmethod
    def ease_out_cubic(t: float) -> float:
        """Cubic ease-out function"""
        return 1 - pow(1 - t, 3)
        
    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        """Cubic ease-in-out function"""
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2

class MovementAnimation(Animation):
    """Animation for wizard movement"""
    
    def __init__(self, start_pos: Tuple[float, float], end_pos: Tuple[float, float], 
                 duration: float = 0.5):
        super().__init__(duration, self.ease_out_cubic)
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.current_pos = start_pos
        
    def update(self, dt: float) -> Tuple[float, float]:
        """Update animation and return current position"""
        progress = super().update(dt)
        
        # Interpolate position
        x = self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * progress
        y = self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * progress
        
        # Add slight arc to movement for more natural feel
        arc_height = 20
        arc_progress = math.sin(progress * math.pi)
        y -= arc_height * arc_progress
        
        self.current_pos = (x, y)
        return self.current_pos

class PulseAnimation(Animation):
    """Pulsing animation for highlights and effects"""
    
    def __init__(self, min_scale: float = 0.8, max_scale: float = 1.2, duration: float = 1.0):
        super().__init__(duration)
        self.min_scale = min_scale
        self.max_scale = max_scale
        self.loop = True
        
    def update(self, dt: float) -> float:
        """Update animation and return current scale"""
        progress = super().update(dt)
        
        # Create pulsing effect using sine wave
        pulse = math.sin(progress * 2 * math.pi)
        scale = self.min_scale + (self.max_scale - self.min_scale) * (pulse + 1) / 2
        
        # Reset for looping
        if self.completed and self.loop:
            self.elapsed = 0.0
            self.completed = False
            
        return scale

class FadeAnimation(Animation):
    """Fade in/out animation"""
    
    def __init__(self, start_alpha: float, end_alpha: float, duration: float = 0.5):
        super().__init__(duration, self.ease_in_out_cubic)
        self.start_alpha = start_alpha
        self.end_alpha = end_alpha
        
    def update(self, dt: float) -> float:
        """Update animation and return current alpha"""
        progress = super().update(dt)
        alpha = self.start_alpha + (self.end_alpha - self.start_alpha) * progress
        return max(0, min(255, alpha))

class AnimationManager:
    """Manages all active animations"""
    
    def __init__(self):
        self.wizard_animations: Dict[str, MovementAnimation] = {}
        self.pulse_animations: Dict[str, PulseAnimation] = {}
        self.fade_animations: Dict[str, FadeAnimation] = {}
        self.wizard_positions: Dict[str, Tuple[float, float]] = {}
        
    def start_wizard_movement(self, wizard_id: str, start_pos: Tuple[float, float], 
                            end_pos: Tuple[float, float], duration: float = 0.5):
        """Start a movement animation for a wizard"""
        self.wizard_animations[wizard_id] = MovementAnimation(start_pos, end_pos, duration)
        
    def start_pulse_animation(self, element_id: str, min_scale: float = 0.8, 
                            max_scale: float = 1.2, duration: float = 1.0):
        """Start a pulse animation for an element"""
        self.pulse_animations[element_id] = PulseAnimation(min_scale, max_scale, duration)
        
    def start_fade_animation(self, element_id: str, start_alpha: float, 
                           end_alpha: float, duration: float = 0.5):
        """Start a fade animation for an element"""
        self.fade_animations[element_id] = FadeAnimation(start_alpha, end_alpha, duration)
        
    def update(self, dt: float):
        """Update all animations"""
        # Update wizard movement animations
        completed_movements = []
        for wizard_id, animation in self.wizard_animations.items():
            pos = animation.update(dt)
            self.wizard_positions[wizard_id] = pos
            if animation.is_completed():
                completed_movements.append(wizard_id)
                
        # Remove completed movement animations
        for wizard_id in completed_movements:
            del self.wizard_animations[wizard_id]
            
        # Update pulse animations
        for element_id, animation in self.pulse_animations.items():
            animation.update(dt)
            
        # Update fade animations
        completed_fades = []
        for element_id, animation in self.fade_animations.items():
            animation.update(dt)
            if animation.is_completed():
                completed_fades.append(element_id)
                
        # Remove completed fade animations
        for element_id in completed_fades:
            del self.fade_animations[element_id]
            
    def get_wizard_position(self, wizard_id: str, default_pos: Tuple[float, float]) -> Tuple[float, float]:
        """Get current animated position for a wizard"""
        return self.wizard_positions.get(wizard_id, default_pos)
        
    def get_pulse_scale(self, element_id: str) -> float:
        """Get current pulse scale for an element"""
        animation = self.pulse_animations.get(element_id)
        if animation:
            return animation.update(0)  # Get current value without advancing time
        return 1.0
        
    def get_fade_alpha(self, element_id: str) -> float:
        """Get current fade alpha for an element"""
        animation = self.fade_animations.get(element_id)
        if animation:
            return animation.update(0)  # Get current value without advancing time
        return 255.0
        
    def is_wizard_moving(self, wizard_id: str) -> bool:
        """Check if a wizard is currently moving"""
        return wizard_id in self.wizard_animations
        
    def stop_wizard_movement(self, wizard_id: str):
        """Stop movement animation for a wizard"""
        if wizard_id in self.wizard_animations:
            del self.wizard_animations[wizard_id]
        if wizard_id in self.wizard_positions:
            del self.wizard_positions[wizard_id]
            
    def stop_pulse_animation(self, element_id: str):
        """Stop pulse animation for an element"""
        if element_id in self.pulse_animations:
            del self.pulse_animations[element_id]
            
    def clear_all(self):
        """Clear all animations"""
        self.wizard_animations.clear()
        self.pulse_animations.clear()
        self.fade_animations.clear()
        self.wizard_positions.clear()

# Global animation manager instance
animation_manager = AnimationManager()
