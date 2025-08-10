"""
Crystal Wizards - UI Helper Module
Contains button classes and highlighting functionality for improved UX
"""

import pygame
import math

class Button:
    """Simple button class with hover and click states"""
    
    def __init__(self, x, y, width, height, text, font, 
                 normal_color=(200, 200, 200), hover_color=(220, 220, 220), 
                 text_color=(0, 0, 0), border_color=(0, 0, 0)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.border_color = border_color
        self.is_hovered = False
        self.is_pressed = False
        self.enabled = True
        
    def handle_event(self, event, sound_manager=None):
        """Handle mouse events and return True if button was clicked"""
        if not self.enabled:
            return False
            
        mouse_pos = pygame.mouse.get_pos()
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:  # Left click
                self.is_pressed = True
                return False
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.is_pressed and self.is_hovered:
                self.is_pressed = False
                if sound_manager:
                    sound_manager.play_sound("click")
                return True  # Button was clicked
            self.is_pressed = False
            
        return False
    
    def draw(self, screen):
        """Draw the button on the screen"""
        if not self.enabled:
            color = (150, 150, 150)  # Disabled color
        elif self.is_pressed:
            color = (180, 180, 180)  # Pressed color
        elif self.is_hovered:
            color = self.hover_color
        else:
            color = self.normal_color
            
        # Draw button background
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, self.border_color, self.rect, 2)
        
        # Draw text
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

class HighlightManager:
    """Manages highlighting of board positions"""
    
    def __init__(self):
        self.highlighted_positions = set()
        self.highlight_color = (255, 255, 0, 128)  # Yellow with transparency
        self.highlight_type = None  # 'move', 'mine', or None
        
    def clear_highlights(self):
        """Clear all highlighted positions"""
        self.highlighted_positions.clear()
        self.highlight_type = None
        
    def set_move_highlights(self, positions):
        """Set positions to highlight for movement"""
        self.highlighted_positions = set(positions)
        self.highlight_type = 'move'
        
    def set_mine_highlights(self, positions):
        """Set positions to highlight for mining"""
        self.highlighted_positions = set(positions)
        self.highlight_type = 'mine'

    def set_cast_highlights(self, positions):
        """Set positions to highlight for casting spells"""
        self.highlighted_positions = set(positions)
        self.highlight_type = 'cast'
        
    def is_highlighted(self, position):
        """Check if a position is highlighted"""
        return position in self.highlighted_positions
        
    def draw_highlight(self, screen, position, coords, radius=40):
        """Draw highlight effect at given coordinates"""
        if position in self.highlighted_positions:
            x, y = coords
            
            # Create a surface with per-pixel alpha for transparency
            highlight_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            
            if self.highlight_type == 'move':
                # Green highlight for movement
                pygame.draw.circle(highlight_surface, (0, 255, 0, 100), (radius, radius), radius)
            elif self.highlight_type == 'mine':
                # Blue highlight for mining
                pygame.draw.circle(highlight_surface, (0, 100, 255, 100), (radius, radius), radius)

            elif self.highlight_type == 'cast':
                # Red highlight for casting spells
                pygame.draw.circle(highlight_surface, (255, 0, 0, 100), (radius, radius), radius)
            else:
                # Default yellow highlight
                pygame.draw.circle(highlight_surface, (255, 255, 0, 100), (radius, radius), radius)
                
            # Blit the highlight surface to the screen
            screen.blit(highlight_surface, (x - radius, y - radius))

        

class SoundManager:
    """Simple sound manager for game audio feedback"""
    
    def __init__(self):
        self.sounds = {}
        self.enabled = True
        
        # Initialize pygame mixer if not already done
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except pygame.error:
            print("Warning: Could not initialize audio system. Sound disabled.")
            self.enabled = False
            
    def load_sound(self, name, filepath):
        """Load a sound file"""
        try:
            self.sounds[name] = pygame.mixer.Sound(filepath)
        except pygame.error:
            print(f"Warning: Could not load sound {filepath}")
            self.sounds[name] = None
            
    def play_sound(self, name):
        """Play a loaded sound"""
        if self.enabled and name in self.sounds and self.sounds[name]:
            self.sounds[name].play()
            
    def set_enabled(self, enabled):
        """Enable or disable sound"""
        self.enabled = enabled

class ActionPanel:
    """Panel containing action buttons for the current player"""
    
    def __init__(self, x, y, font, scale_factor=1.0):
        self.x = x
        self.y = y
        self.font = font
        self.scale_factor = scale_factor
        
        # Scale button dimensions for visibility
        self.button_width = int(120 * scale_factor)
        self.button_height = int(50 * scale_factor) 
        self.button_spacing = int(15 * scale_factor)
        
        # Create action buttons in a 2x2 grid for better space usage
        self.move_button = Button(
            x, y, self.button_width, self.button_height,
            "Move", font, normal_color=(100, 200, 100)
        )
        
        self.mine_button = Button(
            x + self.button_width + self.button_spacing, y,
            self.button_width, self.button_height,
            "Mine", font, normal_color=(100, 100, 200)
        )
        
        # Second row of buttons
        button_row_2_y = y + self.button_height + self.button_spacing
        
        self.cast_button = Button(
            x, button_row_2_y,
            self.button_width, self.button_height,
            "Cast Spell", font, normal_color=(200, 100, 100)
        )
        
        self.end_turn_button = Button(
            x + self.button_width + self.button_spacing, button_row_2_y,
            self.button_width, self.button_height,
            "End Turn", font, normal_color=(200, 200, 100)
        )
        
        self.buttons = [self.move_button, self.mine_button, self.cast_button, self.end_turn_button]
        self.selected_action = None
        
    def handle_event(self, event, game):
        """Handle events for all buttons and return the action taken"""
        current_player = game.get_current_player()
        
        # Update button enabled states
        self.move_button.enabled = game.can_move(current_player)
        self.mine_button.enabled = game.can_mine(current_player)
        self.cast_button.enabled = game.can_cast_spell(current_player)
        self.end_turn_button.enabled = True
        
        # Handle button clicks
        if self.move_button.handle_event(event):
            self.selected_action = 'move' if self.selected_action != 'move' else None
            return 'move_selected'
            
        if self.mine_button.handle_event(event):
            self.selected_action = 'mine' if self.selected_action != 'mine' else None
            return 'mine_selected'
            
        if self.cast_button.handle_event(event):
            self.selected_action = 'cast' if self.selected_action != 'cast' else None
            return 'cast_selected'
            
        if self.end_turn_button.handle_event(event):
            self.selected_action = None
            return 'end_turn'
            
        return None
        
    def draw(self, screen):
        """Draw all buttons"""
        for button in self.buttons:
            button.draw(screen)
            
        # Draw selection indicator
        if self.selected_action == 'move':
            pygame.draw.rect(screen, (0, 255, 0), self.move_button.rect, 3)
        elif self.selected_action == 'mine':
            pygame.draw.rect(screen, (0, 0, 255), self.mine_button.rect, 3)
        elif self.selected_action == 'cast':
            pygame.draw.rect(screen, (255, 0, 0), self.cast_button.rect, 3)
