"""
Crystal Wizards - Help Menu System
Adds a comprehensive help menu accessible from the pause menu (Escape key)
"""

import pygame
import sys

# Colors matching the game's existing color scheme
COLORS = {
    'white': (255, 255, 255),
    'black': (0, 0, 0),
    'red': (220, 50, 50),
    'blue': (50, 50, 220),
    'green': (50, 220, 50),
    'yellow': (220, 220, 50),
    'grey': (128, 128, 128),
    'light_grey': (200, 200, 200),
    'dark_grey': (64, 64, 64),
    'brown': (139, 69, 19),
    'light_blue': (173, 216, 230),
    'gold': (255, 215, 0),
    'wild': (230, 50, 230),
}

class HelpDialog:
    def __init__(self, screen, font_medium, font_large):
        self.screen = screen
        self.font_medium = font_medium
        self.font_large = font_large
        self.font_small = pygame.font.Font(None, 24)
        self.visible = False
        self.result = None

    def show(self):
        self.visible = True
        self.result = None

    def hide(self):
        self.visible = False

    def run_modal(self):
        """Run the help dialog until user closes it"""
        self.show()
        clock = pygame.time.Clock()
        while self.visible and self.result is None:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.result = 'close'
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.result = 'close'
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    if hasattr(self, '_btn_close') and self._btn_close.collidepoint((mx, my)):
                        self.result = 'close'

            self.draw()
            pygame.display.flip()
            clock.tick(60)

        self.hide()
        return self.result

    def draw(self):
        sw, sh = self.screen.get_size()
        
        # Dim background
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Help dialog - larger than quit dialog to fit content
        w, h = int(sw * 0.85), int(sh * 0.85)
        x, y = (sw - w) // 2, (sh - h) // 2
        dialog_rect = pygame.Rect(x, y, w, h)
        
        # Dialog background with rounded corners
        pygame.draw.rect(self.screen, COLORS['white'], dialog_rect, border_radius=15)
        pygame.draw.rect(self.screen, COLORS['black'], dialog_rect, 3, border_radius=15)

        # Title
        title = self.font_large.render("How to Play Crystal Wizards", True, COLORS['black'])
        title_rect = title.get_rect(center=(x + w // 2, y + 40))
        self.screen.blit(title, title_rect)

        # Content area
        content_y = y + 80
        content_x = x + 30
        content_width = w - 60
        line_height = 28
        current_y = content_y

        # Help content sections
        help_sections = [
            ("🎯 OBJECTIVE", [
                "Eliminate all opponent wizards by reducing their health to 0.",
                "Last wizard standing wins the game!"
            ]),
            ("🗺️ BOARD LAYOUT", [
                "• Center Circle (White Mine): Contains 12 white crystals; successful mining teleports you to your choice of outer hex",
                "• 4 Colored Rectangles: Starting positions for wizards (Red, Blue, Green, Yellow)",
                "• 12 Outer Hexagons: Empty spaces for movement and positioning",
                "• 4 Mines: Produce colored crystals matching nearby rectangle colors"
            ]),
            ("⚡ ACTIONS (3 per turn)", [
                "• MOVE: Click the Move button, then click an adjacent connected space",
                "• MINE: Click the Mine button, then click the space you're occupying",
                "  (only works if your space is a mine with crystals available)",
                "• CAST SPELL: Click a spell card from your hand, then click the target"
            ]),
            ("💎 RESOURCES", [
                "• Health: Start with 6, die when reduced to 0",
                "• Crystals: Hold max 6 in reserve, used for blocking damage and spell costs",
                "• Spell Cards: Start with 3, draw more from the deck as the game progresses"
            ]),
            ("⚔️ COMBAT SYSTEM", [
                "• Spells deal damage to target wizards",
                "• Defenders can block damage by spending crystals (1 crystal blocks 1 damage)",
                "• Crystals matching the attacker's color go to the attacker's reserve",
                "• Other crystals return to the board where the defender was standing"
            ]),
            ("🏆 WINNING", [
                "Reduce all opponent wizards' health to 0 to win the game.",
                "Use strategy: collect crystals, position wisely, and time your attacks!"
            ])
        ]

        for section_title, section_content in help_sections:
            # Section title
            if current_y + line_height > y + h - 100:  # Check if we're running out of space
                break
                
            title_surface = self.font_medium.render(section_title, True, COLORS['blue'])
            self.screen.blit(title_surface, (content_x, current_y))
            current_y += line_height + 5

            # Section content
            for line in section_content:
                if current_y + line_height > y + h - 100:  # Check if we're running out of space
                    break
                    
                line_surface = self.font_small.render(line, True, COLORS['black'])
                self.screen.blit(line_surface, (content_x + 20, current_y))
                current_y += line_height - 4

            current_y += 10  # Space between sections

        # Close button
        btn_w, btn_h = 120, 40
        btn_x = x + w // 2 - btn_w // 2
        btn_y = y + h - 60
        self._btn_close = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

        pygame.draw.rect(self.screen, COLORS['blue'], self._btn_close, border_radius=8)
        pygame.draw.rect(self.screen, COLORS['black'], self._btn_close, 2, border_radius=8)

        close_text = self.font_medium.render("Close", True, COLORS['white'])
        close_rect = close_text.get_rect(center=self._btn_close.center)
        self.screen.blit(close_text, close_rect)

        # Instructions
        instruction_text = "Press ESC or click Close to return to the pause menu"
        instruction_surface = self.font_small.render(instruction_text, True, COLORS['grey'])
        instruction_rect = instruction_surface.get_rect(center=(x + w // 2, y + h - 20))
        self.screen.blit(instruction_surface, instruction_rect)


class PauseMenuDialog:
    def __init__(self, screen, font_medium, font_large):
        self.screen = screen
        self.font_medium = font_medium
        self.font_large = font_large
        self.visible = False
        self.result = None
        self.help_dialog = HelpDialog(screen, font_medium, font_large)

    def show(self):
        self.visible = True
        self.result = None

    def hide(self):
        self.visible = False

    def run_modal(self):
        """Run the pause menu until user makes a choice"""
        self.show()
        clock = pygame.time.Clock()
        
        while self.visible and self.result is None:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.result = 'quit'
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.result = 'resume'
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    if hasattr(self, '_btn_resume') and self._btn_resume.collidepoint((mx, my)):
                        self.result = 'resume'
                    elif hasattr(self, '_btn_help') and self._btn_help.collidepoint((mx, my)):
                        # Show help dialog
                        self.help_dialog.run_modal()
                        # Don't close pause menu, let user choose again
                    elif hasattr(self, '_btn_quit') and self._btn_quit.collidepoint((mx, my)):
                        self.result = 'quit'

            self.draw()
            pygame.display.flip()
            clock.tick(60)

        self.hide()
        return self.result

    def draw(self):
        sw, sh = self.screen.get_size()
        
        # Dim background
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        # Dialog
        w, h = int(sw * 0.4), int(sh * 0.35)
        x, y = (sw - w) // 2, (sh - h) // 2
        dialog_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, COLORS['white'], dialog_rect, border_radius=15)
        pygame.draw.rect(self.screen, COLORS['black'], dialog_rect, 3, border_radius=15)

        # Title
        title = self.font_large.render("Game Paused", True, COLORS['black'])
        title_rect = title.get_rect(center=(x + w // 2, y + 50))
        self.screen.blit(title, title_rect)

        # Buttons
        btn_w, btn_h = int(w * 0.6), int(h * 0.15)
        btn_x = x + (w - btn_w) // 2
        gap = 15

        # Resume button
        resume_y = y + 100
        self._btn_resume = pygame.Rect(btn_x, resume_y, btn_w, btn_h)
        pygame.draw.rect(self.screen, COLORS['green'], self._btn_resume, border_radius=8)
        pygame.draw.rect(self.screen, COLORS['black'], self._btn_resume, 2, border_radius=8)
        resume_text = self.font_medium.render("Resume Game", True, COLORS['white'])
        resume_rect = resume_text.get_rect(center=self._btn_resume.center)
        self.screen.blit(resume_text, resume_rect)

        # Help button
        help_y = resume_y + btn_h + gap
        self._btn_help = pygame.Rect(btn_x, help_y, btn_w, btn_h)
        pygame.draw.rect(self.screen, COLORS['blue'], self._btn_help, border_radius=8)
        pygame.draw.rect(self.screen, COLORS['black'], self._btn_help, 2, border_radius=8)
        help_text = self.font_medium.render("Help", True, COLORS['white'])
        help_rect = help_text.get_rect(center=self._btn_help.center)
        self.screen.blit(help_text, help_rect)

        # Quit button
        quit_y = help_y + btn_h + gap
        self._btn_quit = pygame.Rect(btn_x, quit_y, btn_w, btn_h)
        pygame.draw.rect(self.screen, COLORS['red'], self._btn_quit, border_radius=8)
        pygame.draw.rect(self.screen, COLORS['black'], self._btn_quit, 2, border_radius=8)
        quit_text = self.font_medium.render("Quit Game", True, COLORS['white'])
        quit_rect = quit_text.get_rect(center=self._btn_quit.center)
        self.screen.blit(quit_text, quit_rect)

        # Instructions
        instruction_text = "Press ESC to resume • Click Help to learn how to play"
        instruction_surface = pygame.font.Font(None, 24).render(instruction_text, True, COLORS['grey'])
        instruction_rect = instruction_surface.get_rect(center=(x + w // 2, y + h - 20))
        self.screen.blit(instruction_surface, instruction_rect)


# Integration instructions for cw_gui.py:
"""
To integrate this help menu system into your existing cw_gui.py file:

1. Add this import at the top of cw_gui.py:
   from help_menu_system import PauseMenuDialog

2. In the GameGUI.__init__ method, replace the quit_dialog initialization:
   # Replace this line:
   # self.quit_dialog = QuitConfirmDialog(self.screen, self.font_large)
   # With this line:
   self.pause_menu = PauseMenuDialog(self.screen, self.font_medium, self.font_large)

3. In the run() method, replace the quit dialog calls:
   # Replace these lines:
   # if self.quit_dialog.run_modal():
   #     running = False
   #     break
   # With these lines:
   result = self.pause_menu.run_modal()
   if result == 'quit':
       running = False
       break
   elif result == 'resume':
       continue  # Just continue the game loop

4. Do the same replacement for both the pygame.QUIT event and the pygame.K_ESCAPE event.

This will give you a proper pause menu with Resume, Help, and Quit options, where Help opens
a comprehensive guide to playing Crystal Wizards.
"""
