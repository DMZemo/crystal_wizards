
import pygame
import sys

class BloodMagicChoiceDialog:
    """Dialog for choosing between Blood Magic and regular mining"""
    
    def __init__(self, screen, font_medium, font_large):
        self.screen = screen
        self.font_medium = font_medium
        self.font_large = font_large
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        
        # Dialog dimensions
        self.dialog_width = 400
        self.dialog_height = 200
        self.dialog_x = (self.screen_width - self.dialog_width) // 2
        self.dialog_y = (self.screen_height - self.dialog_height) // 2
        
        # Button dimensions
        self.button_width = 150
        self.button_height = 50
        self.button_spacing = 20
        
        # Calculate button positions
        total_button_width = (self.button_width * 2) + self.button_spacing
        button_start_x = self.dialog_x + (self.dialog_width - total_button_width) // 2
        button_y = self.dialog_y + self.dialog_height - 80
        
        self.blood_magic_button = pygame.Rect(button_start_x, button_y, self.button_width, self.button_height)
        self.regular_button = pygame.Rect(button_start_x + self.button_width + self.button_spacing, button_y, self.button_width, self.button_height)
        
        # Colors
        self.bg_color = (40, 40, 60)
        self.border_color = (100, 100, 150)
        self.button_color = (60, 60, 80)
        self.button_hover_color = (80, 80, 100)
        self.blood_magic_color = (120, 40, 40)
        self.blood_magic_hover_color = (140, 60, 60)
        self.text_color = (255, 255, 255)
        
        # State
        self.visible = False
        self.result = None
        self.callback = None
        self.hovered_button = None
        
    def show(self, callback):
        """Show the dialog and set callback for result"""
        self.visible = True
        self.result = None
        self.callback = callback
        
    def hide(self):
        """Hide the dialog"""
        self.visible = False
        self.result = None
        self.callback = None
        
    def handle_event(self, event):
        """Handle pygame events. Returns True if event was consumed."""
        if not self.visible:
            return False
            
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            if self.blood_magic_button.collidepoint(mouse_pos):
                self.hovered_button = 'blood_magic'
            elif self.regular_button.collidepoint(mouse_pos):
                self.hovered_button = 'regular'
            else:
                self.hovered_button = None
            return True
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = event.pos
                if self.blood_magic_button.collidepoint(mouse_pos):
                    self.result = 'blood_magic'
                    self.visible = False
                    if self.callback:
                        self.callback('blood_magic')
                    return True
                elif self.regular_button.collidepoint(mouse_pos):
                    self.result = 'regular'
                    self.visible = False
                    if self.callback:
                        self.callback('regular')
                    return True
                    
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # ESC defaults to regular mining
                self.result = 'regular'
                self.visible = False
                if self.callback:
                    self.callback('regular')
                return True
            elif event.key == pygame.K_b:
                # B key for Blood Magic
                self.result = 'blood_magic'
                self.visible = False
                if self.callback:
                    self.callback('blood_magic')
                return True
            elif event.key == pygame.K_r or event.key == pygame.K_RETURN:
                # R key or Enter for regular mining
                self.result = 'regular'
                self.visible = False
                if self.callback:
                    self.callback('regular')
                return True
                
        return True  # Consume all events when visible
        
    def draw(self):
        """Draw the dialog"""
        if not self.visible:
            return
            
        # Draw semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Draw dialog background
        dialog_rect = pygame.Rect(self.dialog_x, self.dialog_y, self.dialog_width, self.dialog_height)
        pygame.draw.rect(self.screen, self.bg_color, dialog_rect)
        pygame.draw.rect(self.screen, self.border_color, dialog_rect, 3)
        
        # Draw title
        title_text = self.font_large.render("Choose Mining Method", True, self.text_color)
        title_rect = title_text.get_rect(center=(self.dialog_x + self.dialog_width // 2, self.dialog_y + 40))
        self.screen.blit(title_text, title_rect)
        
        # Draw description
        desc_text = self.font_medium.render("You can mine from your matching color mine!", True, self.text_color)
        desc_rect = desc_text.get_rect(center=(self.dialog_x + self.dialog_width // 2, self.dialog_y + 80))
        self.screen.blit(desc_text, desc_rect)
        
        # Draw Blood Magic button
        blood_magic_color = self.blood_magic_hover_color if self.hovered_button == 'blood_magic' else self.blood_magic_color
        pygame.draw.rect(self.screen, blood_magic_color, self.blood_magic_button)
        pygame.draw.rect(self.screen, self.border_color, self.blood_magic_button, 2)
        
        blood_magic_text = self.font_medium.render("Blood Magic", True, self.text_color)
        blood_magic_text_rect = blood_magic_text.get_rect(center=self.blood_magic_button.center)
        self.screen.blit(blood_magic_text, blood_magic_text_rect)
        
        # Draw regular mining button
        regular_color = self.button_hover_color if self.hovered_button == 'regular' else self.button_color
        pygame.draw.rect(self.screen, regular_color, self.regular_button)
        pygame.draw.rect(self.screen, self.border_color, self.regular_button, 2)
        
        regular_text = self.font_medium.render("Regular Mining", True, self.text_color)
        regular_text_rect = regular_text.get_rect(center=self.regular_button.center)
        self.screen.blit(regular_text, regular_text_rect)
        
        # Draw keyboard shortcuts
        shortcut_text = self.font_medium.render("Press B for Blood Magic, R for Regular, ESC to cancel", True, (200, 200, 200))
        shortcut_rect = shortcut_text.get_rect(center=(self.dialog_x + self.dialog_width // 2, self.dialog_y + self.dialog_height - 20))
        self.screen.blit(shortcut_text, shortcut_rect)
