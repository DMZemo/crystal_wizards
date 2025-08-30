
"""
Crystal Wizards - Blood Magic Dialog
Handles the Blood Magic mechanic UI where players choose dice assignments
"""

import pygame
from ui import Button

class BloodMagicDialog:
    """Dialog for Blood Magic dice assignment"""
    
    def __init__(self, screen, font_medium, font_large):
        self.screen = screen
        self.font_medium = font_medium
        self.font_large = font_large
        self.is_active = False
        self.dice_results = [0, 0]  # Two dice results
        self.callback = None
        self.wizard_color = None
        
        # Dialog dimensions
        self.dialog_width = 500
        self.dialog_height = 350
        self.dialog_x = (screen.get_width() - self.dialog_width) // 2
        self.dialog_y = (screen.get_height() - self.dialog_height) // 2
        
        # Colors
        self.colors = {
            'dialog_bg': (240, 240, 240),
            'border': (0, 0, 0),
            'text': (0, 0, 0),
            'dice_bg': (255, 255, 255),
            'dice_border': (0, 0, 0),
            'button_normal': (200, 200, 200),
            'button_hover': (220, 220, 220),
            'red': (220, 50, 50),
            'blue': (50, 50, 220),
            'green': (50, 220, 50),
            'yellow': (255, 215, 0),
            'blood_magic': (150, 0, 0)
        }
        
        # Create buttons - positioned dynamically in show()
        self.buttons = []
        
    def show(self, dice1, dice2, wizard_color, callback):
        """Show the Blood Magic dialog with two dice results"""
        self.is_active = True
        self.dice_results = [dice1, dice2]
        self.callback = callback
        self.wizard_color = wizard_color
        
        # Create buttons dynamically
        self.buttons = []
        button_width = 120
        button_height = 35
        
        # Buttons for Die 1
        die1_x = self.dialog_x + 80
        button_y = self.dialog_y + 220
        
        self.buttons.append(Button(
            die1_x - button_width//2, button_y, button_width, button_height,
            f"Mining ({dice1})", self.font_medium,
            normal_color=(100, 150, 200), hover_color=(120, 170, 220)
        ))
        
        self.buttons.append(Button(
            die1_x - button_width//2, button_y + 45, button_width, button_height,
            f"Health ({dice1})", self.font_medium,
            normal_color=(200, 100, 100), hover_color=(220, 120, 120)
        ))
        
        # Buttons for Die 2
        die2_x = self.dialog_x + 320
        
        self.buttons.append(Button(
            die2_x - button_width//2, button_y, button_width, button_height,
            f"Mining ({dice2})", self.font_medium,
            normal_color=(100, 150, 200), hover_color=(120, 170, 220)
        ))
        
        self.buttons.append(Button(
            die2_x - button_width//2, button_y + 45, button_width, button_height,
            f"Health ({dice2})", self.font_medium,
            normal_color=(200, 100, 100), hover_color=(220, 120, 120)
        ))
        
    def handle_event(self, event):
        """Handle dialog events"""
        if not self.is_active:
            return False
        
        # Handle button clicks
        for i, button in enumerate(self.buttons):
            if button.handle_event(event):
                if i == 0:  # Die 1 -> Mining
                    self._assign_dice(0, 'mining')
                elif i == 1:  # Die 1 -> Health
                    self._assign_dice(0, 'health')
                elif i == 2:  # Die 2 -> Mining
                    self._assign_dice(1, 'mining')
                elif i == 3:  # Die 2 -> Health
                    self._assign_dice(1, 'health')
                return True
        
        return False
    
    def _assign_dice(self, dice_index, assignment):
        """Assign a die to mining or health"""
        mining_die = self.dice_results[dice_index]
        health_die = self.dice_results[1 - dice_index]
        
        if assignment == 'health':
            mining_die, health_die = health_die, mining_die
        
        self.is_active = False
        if self.callback:
            self.callback(mining_die, health_die)
    
    def draw(self):
        """Draw the Blood Magic dialog"""
        if not self.is_active:
            return
        
        # Draw semi-transparent overlay
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))
        
        # Draw dialog background
        dialog_rect = pygame.Rect(self.dialog_x, self.dialog_y, self.dialog_width, self.dialog_height)
        pygame.draw.rect(self.screen, self.colors['dialog_bg'], dialog_rect, border_radius=10)
        pygame.draw.rect(self.screen, self.colors['border'], dialog_rect, 3, border_radius=10)
        
        # Draw title with blood magic theme
        title_text = "🩸 BLOOD MAGIC 🩸"
        title_surface = self.font_large.render(title_text, True, self.colors['blood_magic'])
        title_rect = title_surface.get_rect(centerx=self.dialog_x + self.dialog_width // 2, y=self.dialog_y + 20)
        self.screen.blit(title_surface, title_rect)
        
        # Draw explanation
        explanation1 = "You rolled TWO dice! Choose which die result"
        explanation2 = "goes to mining and which goes to health:"
        
        exp1_surface = self.font_medium.render(explanation1, True, self.colors['text'])
        exp1_rect = exp1_surface.get_rect(centerx=self.dialog_x + self.dialog_width // 2, y=self.dialog_y + 60)
        self.screen.blit(exp1_surface, exp1_rect)
        
        exp2_surface = self.font_medium.render(explanation2, True, self.colors['text'])
        exp2_rect = exp2_surface.get_rect(centerx=self.dialog_x + self.dialog_width // 2, y=self.dialog_y + 85)
        self.screen.blit(exp2_surface, exp2_rect)
        
        # Draw dice
        dice_size = 70
        dice1_x = self.dialog_x + 80
        dice2_x = self.dialog_x + 320
        dice_y = self.dialog_y + 130
        
        # Die 1
        dice1_rect = pygame.Rect(dice1_x - dice_size//2, dice_y, dice_size, dice_size)
        pygame.draw.rect(self.screen, self.colors['dice_bg'], dice1_rect, border_radius=8)
        pygame.draw.rect(self.screen, self.colors['dice_border'], dice1_rect, 3, border_radius=8)
        
        dice1_text = self.font_large.render(str(self.dice_results[0]), True, self.colors['text'])
        dice1_text_rect = dice1_text.get_rect(center=dice1_rect.center)
        self.screen.blit(dice1_text, dice1_text_rect)
        
        # Die 2
        dice2_rect = pygame.Rect(dice2_x - dice_size//2, dice_y, dice_size, dice_size)
        pygame.draw.rect(self.screen, self.colors['dice_bg'], dice2_rect, border_radius=8)
        pygame.draw.rect(self.screen, self.colors['dice_border'], dice2_rect, 3, border_radius=8)
        
        dice2_text = self.font_large.render(str(self.dice_results[1]), True, self.colors['text'])
        dice2_text_rect = dice2_text.get_rect(center=dice2_rect.center)
        self.screen.blit(dice2_text, dice2_text_rect)
        
        # Draw "VS" between dice
        vs_text = self.font_large.render("VS", True, self.colors['blood_magic'])
        vs_rect = vs_text.get_rect(centerx=self.dialog_x + self.dialog_width // 2, centery=dice_y + dice_size//2)
        self.screen.blit(vs_text, vs_rect)
        
        # Draw buttons
        for button in self.buttons:
            button.draw(self.screen)
