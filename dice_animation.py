
"""
Crystal Wizards - Animated Dice Rolling System
Provides dramatic dice rolling animations with sound effects
"""

import pygame
import random
import math
import time
from sound_manager import sound_manager

class DiceAnimator:
    """Handles animated dice rolling with dramatic reveals"""
    
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.large_font = pygame.font.Font(None, 72)
        self.is_animating = False
        self.animation_start_time = 0
        self.final_result = 0
        self.dice_type = 'normal'  # 'normal' or 'healing'
        
        # Animation parameters
        self.roll_duration = 2.0  # seconds
        self.reveal_duration = 1.0  # seconds
        self.bounce_height = 20
        self.spin_speed = 10
        
        # Colors
        self.colors = {
            'white': (255, 255, 255),
            'black': (0, 0, 0),
            'red': (220, 50, 50),
            'blue': (50, 50, 220),
            'green': (50, 220, 50),
            'gold': (255, 215, 0),
            'shadow': (100, 100, 100)
        }
    
    def start_roll_animation(self, dice_type='normal', callback=None):
        """Start animated dice roll"""
        self.dice_type = dice_type
        self.is_animating = True
        self.animation_start_time = time.time()
        self.callback = callback
        
        # Determine final result
        if dice_type == 'healing':
            self.final_result = random.choice([1, 1, 1, 2, 2, 3])  # Healing springs die
        else:
            self.final_result = random.randint(1, 6)  # Normal d6
        
        # Play rolling sound
        sound_manager.play_dice_roll()
    
    def update_and_draw(self, center_x, center_y):
        """Update and draw the dice animation"""
        if not self.is_animating:
            return False
        
        current_time = time.time()
        elapsed = current_time - self.animation_start_time
        
        if elapsed < self.roll_duration:
            # Rolling phase
            self._draw_rolling_dice(center_x, center_y, elapsed)
        elif elapsed < self.roll_duration + self.reveal_duration:
            # Reveal phase
            self._draw_reveal_dice(center_x, center_y, elapsed - self.roll_duration)
        else:
            # Animation complete
            self.is_animating = False
            if self.callback:
                self.callback(self.final_result)
            return False
        
        return True
    
    def _draw_rolling_dice(self, center_x, center_y, elapsed):
        """Draw the rolling dice animation"""
        # Calculate bounce
        bounce_progress = (elapsed / self.roll_duration) * 4 * math.pi
        bounce_offset = math.sin(bounce_progress) * self.bounce_height * (1 - elapsed / self.roll_duration)
        
        # Calculate spin
        spin_angle = elapsed * self.spin_speed * 360
        
        # Draw multiple dice for effect
        dice_size = 60
        for i in range(3):
            offset_x = (i - 1) * 20
            offset_y = bounce_offset + (i * 5)
            
            dice_x = center_x + offset_x
            dice_y = center_y + offset_y
            
            # Draw dice shadow
            shadow_rect = pygame.Rect(dice_x - dice_size//2 + 3, dice_y - dice_size//2 + 3, dice_size, dice_size)
            pygame.draw.rect(self.screen, self.colors['shadow'], shadow_rect, border_radius=8)
            
            # Draw dice
            dice_rect = pygame.Rect(dice_x - dice_size//2, dice_y - dice_size//2, dice_size, dice_size)
            color = self.colors['gold'] if self.dice_type == 'healing' else self.colors['white']
            pygame.draw.rect(self.screen, color, dice_rect, border_radius=8)
            pygame.draw.rect(self.screen, self.colors['black'], dice_rect, 3, border_radius=8)
            
            # Draw spinning number
            current_number = random.randint(1, 6)
            self._draw_dice_face(dice_x, dice_y, current_number, dice_size)
        
        # Draw "Rolling..." text
        text = self.font.render("Rolling...", True, self.colors['black'])
        text_rect = text.get_rect(center=(center_x, center_y + 80))
        self.screen.blit(text, text_rect)
    
    def _draw_reveal_dice(self, center_x, center_y, reveal_elapsed):
        """Draw the dramatic result reveal"""
        # Scale effect for dramatic reveal
        scale_factor = 1.0 + (reveal_elapsed / self.reveal_duration) * 0.5
        dice_size = int(80 * scale_factor)
        
        # Pulsing glow effect
        glow_alpha = int(128 * (1 - reveal_elapsed / self.reveal_duration))
        
        # Draw glow
        glow_size = dice_size + 20
        glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        glow_color = (*self.colors['gold'][:3], glow_alpha) if self.dice_type == 'healing' else (*self.colors['blue'][:3], glow_alpha)
        pygame.draw.rect(glow_surf, glow_color, (0, 0, glow_size, glow_size), border_radius=12)
        self.screen.blit(glow_surf, (center_x - glow_size//2, center_y - glow_size//2))
        
        # Draw final dice
        dice_rect = pygame.Rect(center_x - dice_size//2, center_y - dice_size//2, dice_size, dice_size)
        color = self.colors['gold'] if self.dice_type == 'healing' else self.colors['white']
        pygame.draw.rect(self.screen, color, dice_rect, border_radius=10)
        pygame.draw.rect(self.screen, self.colors['black'], dice_rect, 4, border_radius=10)
        
        # Draw final result
        self._draw_dice_face(center_x, center_y, self.final_result, dice_size)
        
        # Draw result text
        result_text = f"Result: {self.final_result}"
        if self.dice_type == 'healing':
            result_text += " (Healing)"
        
        text = self.large_font.render(result_text, True, self.colors['black'])
        text_rect = text.get_rect(center=(center_x, center_y + dice_size//2 + 40))
        self.screen.blit(text, text_rect)
    
    def _draw_dice_face(self, center_x, center_y, number, dice_size):
        """Draw the dots on a dice face"""
        dot_radius = max(3, dice_size // 15)
        dot_color = self.colors['black']
        
        # Dot positions relative to center
        positions = {
            1: [(0, 0)],
            2: [(-0.3, -0.3), (0.3, 0.3)],
            3: [(-0.3, -0.3), (0, 0), (0.3, 0.3)],
            4: [(-0.3, -0.3), (0.3, -0.3), (-0.3, 0.3), (0.3, 0.3)],
            5: [(-0.3, -0.3), (0.3, -0.3), (0, 0), (-0.3, 0.3), (0.3, 0.3)],
            6: [(-0.3, -0.3), (0.3, -0.3), (-0.3, 0), (0.3, 0), (-0.3, 0.3), (0.3, 0.3)]
        }
        
        if number in positions:
            for rel_x, rel_y in positions[number]:
                dot_x = center_x + rel_x * dice_size * 0.3
                dot_y = center_y + rel_y * dice_size * 0.3
                pygame.draw.circle(self.screen, dot_color, (int(dot_x), int(dot_y)), dot_radius)

class DiceRollManager:
    """Manages dice rolling for different game situations"""
    
    def __init__(self, screen, font):
        self.animator = DiceAnimator(screen, font)
        self.pending_rolls = []
        self.current_roll = None
    
    def roll_mine_dice(self, callback):
        """Roll dice for mining action"""
        self.animator.start_roll_animation('normal', callback)
    
    def roll_healing_dice(self, callback):
        """Roll special healing springs dice"""
        self.animator.start_roll_animation('healing', callback)
    
    def roll_blood_magic_dice(self, callback):
        """Roll two dice for blood magic choice"""
        # For now, just roll one die - could be enhanced for dual dice
        self.animator.start_roll_animation('normal', callback)
    
    def update_and_draw(self, center_x, center_y):
        """Update and draw current dice animation"""
        return self.animator.update_and_draw(center_x, center_y)
    
    def is_rolling(self):
        """Check if dice are currently rolling"""
        return self.animator.is_animating
