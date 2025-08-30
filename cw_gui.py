"""
Crystal Wizards - Pygame GUI Implementation (Fixed Indentation + Player Names)

This version fixes indentation and updates UI labels to show player-provided
usernames from the start screen when available, falling back to color-based
names otherwise. It also adds a quit confirmation dialog on Esc or window close.
"""

import math
import sys
import pygame
from cw_entities import AIWizard
from cw_game import CrystalWizardsGame
from ui import Button, HighlightManager, ActionPanel
from sound_manager import sound_manager
from dice_animation import DiceRollManager

# Colors
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
    'transparent': (0, 0, 0, 0)  # For transparent surfaces
}


class QuitConfirmDialog:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.visible = False
        self.result = None  # True for Yes, False for No

    def show(self):
        self.visible = True
        self.result = None

    def hide(self):
        self.visible = False

    def run_modal(self):
        """Run a simple modal loop until user selects Yes/No or cancels."""
        self.show()
        clock = pygame.time.Clock()
        while self.visible and self.result is None:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # Treat window close inside dialog as a cancel
                    self.result = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_n):
                        self.result = False
                    elif event.key in (pygame.K_RETURN, pygame.K_y):
                        self.result = True
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    if self._btn_yes.collidepoint((mx, my)):
                        self.result = True
                    elif self._btn_no.collidepoint((mx, my)):
                        self.result = False

            self.draw()
            pygame.display.flip()
            clock.tick(60)

        self.hide()
        return bool(self.result)

    def draw(self):
        sw, sh = self.screen.get_size()
        # Dim background
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        # Dialog
        w, h = int(sw * 0.45), int(sh * 0.25)
        x, y = (sw - w) // 2, (sh - h) // 2
        dialog_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, COLORS['white'], dialog_rect, border_radius=10)
        pygame.draw.rect(self.screen, COLORS['black'], dialog_rect, 2, border_radius=10)

        # Text
        title = self.font.render("Quit Crystal Wizards?", True, COLORS['black'])
        subtitle = pygame.font.Font(None, int(h * 0.36)).render(
            "Are you sure you want to quit?", True, COLORS['dark_grey']
        )
        self.screen.blit(title, title.get_rect(center=(x + w // 2, y + int(h * 0.3))))
        self.screen.blit(subtitle, subtitle.get_rect(center=(x + w // 2, y + int(h * 0.52))))

        # Buttons
        btn_w, btn_h = int(w * 0.28), int(h * 0.26)
        gap = int(w * 0.08)
        bx1 = x + w // 2 - btn_w - gap // 2
        bx2 = x + w // 2 + gap // 2
        by = y + int(h * 0.65)
        self._btn_yes = pygame.Rect(bx1, by, btn_w, btn_h)
        self._btn_no = pygame.Rect(bx2, by, btn_w, btn_h)

        pygame.draw.rect(self.screen, COLORS['green'], self._btn_yes, border_radius=8)
        pygame.draw.rect(self.screen, COLORS['black'], self._btn_yes, 2, border_radius=8)
        pygame.draw.rect(self.screen, COLORS['red'], self._btn_no, border_radius=8)
        pygame.draw.rect(self.screen, COLORS['black'], self._btn_no, 2, border_radius=8)

        yes_text = pygame.font.Font(None, int(btn_h * 1.0)).render("Yes", True, COLORS['white'])
        no_text = pygame.font.Font(None, int(btn_h * 1.0)).render("No", True, COLORS['white'])
        self.screen.blit(yes_text, yes_text.get_rect(center=self._btn_yes.center))
        self.screen.blit(no_text, no_text.get_rect(center=self._btn_no.center))

class BlockingDialog:
    def __init__(self, screen, font, wizard, damage, caster, game=None):
        self.screen = screen
        self.font = font
        self.wizard = wizard
        self.damage = damage
        self.caster = caster
        self.game = game
        self.visible = False
        self.result = None  # Amount of damage blocked (None means still deciding)
        
        # UI state
        self.crystals_to_spend = {'red': 0, 'blue': 0, 'green': 0, 'yellow': 0, 'white': 0}
        self.max_crystals = min(damage, wizard.get_total_crystals_for_blocking())
        self.total_selected = 0
        
        # Calculate dialog dimensions
        sw, sh = self.screen.get_size()
        self.dialog_w = int(sw * 0.7)
        self.dialog_h = int(sh * 0.6)
        self.dialog_x = (sw - self.dialog_w) // 2
        self.dialog_y = (sh - self.dialog_h) // 2
        
    def show(self):
        self.visible = True
        self.result = None
        
    def run_modal(self):
        """Run modal dialog until user confirms blocking choice"""
        self.show()
        clock = pygame.time.Clock()
        
        while self.visible and self.result is None:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.result = 0  # No blocking on quit
                    self.visible = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.result = 0  # No blocking on escape
                        self.visible = False
                    elif event.key == pygame.K_RETURN:
                        self._confirm_blocking()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    self._handle_mouse_click(mx, my)
                        
            # Render the dialog
            self.render()
            pygame.display.flip()
            clock.tick(60)
            
        return self.result if self.result is not None else 0
    
    def _confirm_blocking(self):
        """Confirm the current blocking selection and spend crystals"""
        if self.total_selected > 0:
            # Spend the selected crystals using the new blocking logic
            crystals_spent = {}
            total_blocked = 0
            for color, amount in self.crystals_to_spend.items():
                if amount > 0:
                    available = self.wizard.crystals.get(color, 0)
                    actual_spent = min(amount, available)
                    if actual_spent > 0:
                        self.wizard.crystals[color] -= actual_spent
                        crystals_spent[color] = actual_spent
                        total_blocked += actual_spent
            
            # Handle crystal distribution using new blocking rules
            if self.game and crystals_spent and self.caster:
                attacker_color = getattr(self.caster, 'color', None)
                crystals_to_attacker = {}
                crystals_to_board = {}
                
                for color, amount in crystals_spent.items():
                    if amount > 0:
                        # If blocking crystals match attacker's color, try to give them to attacker
                        if color == attacker_color:
                            # Calculate how many crystals can fit in attacker's reserve (max 6 total)
                            attacker_total = sum(self.caster.crystals.values())
                            space_available = max(0, 6 - attacker_total)
                            crystals_to_give = min(amount, space_available)
                            
                            if crystals_to_give > 0:
                                crystals_to_attacker[color] = crystals_to_give
                                # Add crystals to attacker's reserve
                                self.caster.crystals[color] = self.caster.crystals.get(color, 0) + crystals_to_give
                            
                            # Any excess goes to board
                            excess = amount - crystals_to_give
                            if excess > 0:
                                crystals_to_board[color] = excess
                        else:
                            # Non-matching crystals go to board normally
                            crystals_to_board[color] = amount
                
                # Return non-matching crystals to board
                if crystals_to_board:
                    self.game.return_crystals_to_board(crystals_to_board, self.wizard.location)
                    
                # Log crystal transfers to attacker
                if crystals_to_attacker:
                    total_transferred = sum(crystals_to_attacker.values())
                    self.game.action_log.append(f"{total_transferred} {attacker_color} crystal(s) transferred to {self.caster.color.title()} Wizard's reserve!")
            
            elif self.game and crystals_spent:
                # Fallback to old behavior if no caster specified
                crystals_to_return = {color: amount for color, amount in crystals_spent.items() if amount > 0}
                if crystals_to_return:
                    self.game.return_crystals_to_board(crystals_to_return, self.wizard.location)
            
            self.result = total_blocked
        else:
            self.result = 0
        self.visible = False

    def _handle_mouse_click(self, mx, my):
        """Handle mouse clicks in the blocking dialog"""
        # Crystal selection buttons (+ and - for each color)
        colors = ['red', 'blue', 'green', 'yellow', 'white']
        crystal_section_y = self.dialog_y + 180
        
        for i, color in enumerate(colors):
            if self.wizard.crystals.get(color, 0) == 0:
                continue  # Skip colors the wizard doesn't have
                
            # Calculate button positions for this color
            crystal_x = self.dialog_x + 60 + i * 110
            plus_rect = pygame.Rect(crystal_x + 70, crystal_section_y + 30, 30, 25)
            minus_rect = pygame.Rect(crystal_x + 10, crystal_section_y + 30, 30, 25)
            
            if plus_rect.collidepoint(mx, my):
                # Increase this color if possible
                available = self.wizard.crystals.get(color, 0)
                current = self.crystals_to_spend[color]
                if current < available and self.total_selected < self.max_crystals:
                    self.crystals_to_spend[color] += 1
                    self.total_selected += 1
            elif minus_rect.collidepoint(mx, my):
                # Decrease this color
                if self.crystals_to_spend[color] > 0:
                    self.crystals_to_spend[color] -= 1
                    self.total_selected -= 1
        
        # Action buttons
        button_y = self.dialog_y + self.dialog_h - 60
        
        # Block button
        block_x = self.dialog_x + self.dialog_w // 2 - 120
        block_rect = pygame.Rect(block_x, button_y, 100, 40)
        
        # Skip button  
        skip_x = self.dialog_x + self.dialog_w // 2 + 20
        skip_rect = pygame.Rect(skip_x, button_y, 100, 40)
        
        if block_rect.collidepoint(mx, my):
            self._confirm_blocking()
        elif skip_rect.collidepoint(mx, my):
            # Skip blocking
            self.result = 0
            self.visible = False
        
    def render(self):
        """Render the improved blocking dialog with clear crystal selection"""
        sw, sh = self.screen.get_size()
        
        # Semi-transparent overlay
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Dialog background with rounded corners
        dialog_rect = pygame.Rect(self.dialog_x, self.dialog_y, self.dialog_w, self.dialog_h)
        pygame.draw.rect(self.screen, (45, 45, 65), dialog_rect, border_radius=15)
        pygame.draw.rect(self.screen, (255, 255, 255), dialog_rect, 3, border_radius=15)
        
        # Title section
        title_text = "⚔️ INCOMING ATTACK! ⚔️"
        title_surface = pygame.font.Font(None, 72).render(title_text, True, (255, 100, 100))
        title_x = self.dialog_x + (self.dialog_w - title_surface.get_width()) // 2
        self.screen.blit(title_surface, (title_x, self.dialog_y + 20))
        
        # Attack info section
        attacker_name = getattr(self.caster, 'name', f"{self.caster.color.title()} Wizard")
        defender_name = getattr(self.wizard, 'name', f"{self.wizard.color.title()} Wizard")
        
        attack_info = f"{attacker_name} attacks {defender_name} for {self.damage} damage!"
        attack_surface = self.font.render(attack_info, True, (255, 200, 200))
        attack_x = self.dialog_x + (self.dialog_w - attack_surface.get_width()) // 2
        self.screen.blit(attack_surface, (attack_x, self.dialog_y + 70))
        
        # Defender's crystal reserves section
        reserves_title = f"{defender_name}'s Crystal Reserves:"
        reserves_surface = pygame.font.Font(None, 56).render(reserves_title, True, (200, 255, 200))
        reserves_x = self.dialog_x + (self.dialog_w - reserves_surface.get_width()) // 2
        self.screen.blit(reserves_surface, (reserves_x, self.dialog_y + 110))
        
        # Crystal selection area
        colors = ['red', 'blue', 'green', 'yellow', 'white']
        color_map = {
            'red': (255, 100, 100),
            'blue': (100, 150, 255),
            'green': (100, 255, 100),
            'yellow': (255, 255, 100),
            'white': (255, 255, 255)
        }
        
        crystal_section_y = self.dialog_y + 150
        
        for i, color in enumerate(colors):
            available = self.wizard.crystals.get(color, 0)
            if available == 0:
                continue  # Skip colors the wizard doesn't have
                
            # Calculate positions for this crystal type
            crystal_x = self.dialog_x + 60 + i * 110
            
            # Crystal color indicator
            crystal_color = color_map[color]
            pygame.draw.circle(self.screen, crystal_color, (crystal_x + 50, crystal_section_y + 15), 15)
            pygame.draw.circle(self.screen, (255, 255, 255), (crystal_x + 50, crystal_section_y + 15), 15, 2)
            
            # Color label
            color_label = color.title()
            label_surface = pygame.font.Font(None, 40).render(color_label, True, (255, 255, 255))
            label_x = crystal_x + 50 - label_surface.get_width() // 2
            self.screen.blit(label_surface, (label_x, crystal_section_y + 35))
            
            # Available count
            available_text = f"Have: {available}"
            available_surface = pygame.font.Font(None, 36).render(available_text, True, (200, 200, 200))
            available_x = crystal_x + 50 - available_surface.get_width() // 2
            self.screen.blit(available_surface, (available_x, crystal_section_y + 55))
            
            # Selected count
            selected = self.crystals_to_spend[color]
            selected_text = f"Use: {selected}"
            selected_color = (255, 255, 100) if selected > 0 else (150, 150, 150)
            selected_surface = pygame.font.Font(None, 36).render(selected_text, True, selected_color)
            selected_x = crystal_x + 50 - selected_surface.get_width() // 2
            self.screen.blit(selected_surface, (selected_x, crystal_section_y + 75))
            
            # Plus button
            plus_rect = pygame.Rect(crystal_x + 70, crystal_section_y + 30, 30, 25)
            can_add = selected < available and self.total_selected < self.max_crystals
            plus_color = (0, 150, 0) if can_add else (80, 80, 80)
            pygame.draw.rect(self.screen, plus_color, plus_rect, border_radius=5)
            pygame.draw.rect(self.screen, (255, 255, 255), plus_rect, 2, border_radius=5)
            plus_text = pygame.font.Font(None, 48).render("+", True, (255, 255, 255))
            plus_text_rect = plus_text.get_rect(center=plus_rect.center)
            self.screen.blit(plus_text, plus_text_rect)
            
            # Minus button
            minus_rect = pygame.Rect(crystal_x + 10, crystal_section_y + 30, 30, 25)
            can_remove = selected > 0
            minus_color = (150, 0, 0) if can_remove else (80, 80, 80)
            pygame.draw.rect(self.screen, minus_color, minus_rect, border_radius=5)
            pygame.draw.rect(self.screen, (255, 255, 255), minus_rect, 2, border_radius=5)
            minus_text = pygame.font.Font(None, 48).render("-", True, (255, 255, 255))
            minus_text_rect = minus_text.get_rect(center=minus_rect.center)
            self.screen.blit(minus_text, minus_text_rect)
        
        # Summary section
        summary_y = self.dialog_y + 280
        
        # Blocking summary
        final_damage = max(0, self.damage - self.total_selected)
        summary_text = f"Crystals to spend: {self.total_selected} / {self.max_crystals}"
        summary_surface = pygame.font.Font(None, 52).render(summary_text, True, (255, 255, 100))
        summary_x = self.dialog_x + (self.dialog_w - summary_surface.get_width()) // 2
        self.screen.blit(summary_surface, (summary_x, summary_y))
        
        # Damage preview
        damage_preview = f"Final damage: {final_damage} (blocked: {self.total_selected})"
        preview_color = (100, 255, 100) if self.total_selected > 0 else (255, 200, 200)
        preview_surface = pygame.font.Font(None, 48).render(damage_preview, True, preview_color)
        preview_x = self.dialog_x + (self.dialog_w - preview_surface.get_width()) // 2
        self.screen.blit(preview_surface, (preview_x, summary_y + 30))
        
        # Action buttons
        button_y = self.dialog_y + self.dialog_h - 60
        
        # Block button
        block_x = self.dialog_x + self.dialog_w // 2 - 120
        block_rect = pygame.Rect(block_x, button_y, 100, 40)
        block_enabled = True  # Always allow blocking (even 0 crystals)
        block_color = (0, 120, 200) if block_enabled else (80, 80, 80)
        pygame.draw.rect(self.screen, block_color, block_rect, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), block_rect, 2, border_radius=8)
        
        block_text = "Confirm" if self.total_selected > 0 else "Block None"
        block_surface = pygame.font.Font(None, 44).render(block_text, True, (255, 255, 255))
        block_text_rect = block_surface.get_rect(center=block_rect.center)
        self.screen.blit(block_surface, block_text_rect)
        
        # Skip button (same as Block None, but more explicit)
        skip_x = self.dialog_x + self.dialog_w // 2 + 20
        skip_rect = pygame.Rect(skip_x, button_y, 100, 40)
        pygame.draw.rect(self.screen, (150, 50, 50), skip_rect, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), skip_rect, 2, border_radius=8)
        
        skip_surface = pygame.font.Font(None, 44).render("Skip", True, (255, 255, 255))
        skip_text_rect = skip_surface.get_rect(center=skip_rect.center)
        self.screen.blit(skip_surface, skip_text_rect)
        
        # Instructions
        instruction_text = "Click +/- to select crystals, then Confirm or Skip. Press Enter to confirm."
        instruction_surface = pygame.font.Font(None, 36).render(instruction_text, True, (180, 180, 180))
        instruction_x = self.dialog_x + (self.dialog_w - instruction_surface.get_width()) // 2
        self.screen.blit(instruction_surface, (instruction_x, self.dialog_y + self.dialog_h - 20))

class GameGUI:
    def __init__(self, game):
        """Initialize the game GUI to fill the entire screen in a closable window."""
        self.game = game
        # Set GUI reference in game for blocking dialogs
        game.gui = self

        if not pygame.get_init():
            pygame.init()

        info = pygame.display.Info()
        self.screen_width = info.current_w
        self.screen_height = info.current_h

        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        pygame.display.set_caption("Crystal Wizards")

        pygame.font.init()
        self.font_small = pygame.font.Font(None, 25)
        self.font_medium = pygame.font.Font(None, 30)
        self.font_large = pygame.font.Font(None, 50)

        # Board layout
        self.board_center_x = self.screen_width // 2 - 200
        self.board_center_y = self.screen_height // 2
        self.center_radius = 30
        self.rect_distance = 80
        self.outer_distance = 150
        self.mine_distance = 220

        # UI state
        self.selected_wizard = None
        self.selected_spell_card = None
        self.show_spell_details = False

        self.highlight_manager = HighlightManager()
        self.sound_manager = sound_manager
        self.action_panel = ActionPanel(self.screen_width - 350, 280, self.font_medium)

        self.dice_manager = DiceRollManager(self.screen, self.font_large)
        self.is_dice_rolling = False
        self.pending_action = None

        self.sound_manager.load_sounds()

        self.current_action_mode = None
        
        # AI turn timing variables for non-blocking behavior
        self.ai_turn_start_time = 0
        self.ai_thinking_delay = 1000  # 1000ms delay before AI acts
        self.ai_turn_executed = False

        self.position_coords = {}
        self.calculate_position_coordinates()

        # Spell card horizontal row layout state
        self.spell_card_rects = []
        self.visible_hand = []
        
        # Attack animation system
        self.attack_animations = []
        
        # Crystal return animation system
        self.crystal_return_animations = []
        self.hovered_card_index = None
        self.selected_card_index = None
        self.mouse_pos = (0, 0)

        # Quit dialog
        self.quit_dialog = QuitConfirmDialog(self.screen, self.font_large)

    # ---- Utility for name display ----
    def display_name(self, player):
        name = getattr(player, 'name', None)
        if name:
            return name
        # Fallback to color-based label
        base = f"{player.color.title()} Wizard"
        if isinstance(player, AIWizard):
            base += " (AI)"
        return base

    # ---- Basic helpers ----
    def show_blocking_dialog(self, wizard, damage, caster, game=None):
        """Show the dialog for blocking damage with crystals."""
        # Add attack animation before showing blocking dialog
        if wizard.location in self.position_coords:
            self.add_attack_animation(wizard.location)
        
        dialog = BlockingDialog(self.screen, self.font_medium, wizard, damage, caster, game)
        return dialog.run_modal()
    
    def add_attack_animation(self, position):
        """Add a sparkle attack animation at the given position"""
        if position in self.position_coords:
            x, y = self.position_coords[position]
            animation = {
                'x': x,
                'y': y,
                'start_time': pygame.time.get_ticks(),
                'duration': 1000,  # 1 second
                'particles': []
            }
            
            # Create sparkle particles
            import random
            for _ in range(15):
                particle = {
                    'x': x + random.randint(-30, 30),
                    'y': y + random.randint(-30, 30),
                    'vx': random.uniform(-2, 2),
                    'vy': random.uniform(-2, 2),
                    'life': 1.0,
                    'size': random.randint(2, 6),
                    'color': random.choice([(255, 255, 0), (255, 200, 0), (255, 255, 255), (255, 100, 100)])
                }
                animation['particles'].append(particle)
            
            self.attack_animations.append(animation)
    
    def update_attack_animations(self):
        """Update and remove expired attack animations"""
        current_time = pygame.time.get_ticks()
        
        for animation in self.attack_animations[:]:
            elapsed = current_time - animation['start_time']
            if elapsed >= animation['duration']:
                self.attack_animations.remove(animation)
                continue
            
            # Update particles
            progress = elapsed / animation['duration']
            for particle in animation['particles']:
                particle['x'] += particle['vx']
                particle['y'] += particle['vy']
                particle['life'] = 1.0 - progress
                particle['vy'] += 0.1  # Gravity effect
    
    def draw_attack_animations(self):
        """Draw all active attack animations"""
        for animation in self.attack_animations:
            for particle in animation['particles']:
                if particle['life'] > 0:
                    alpha = int(255 * particle['life'])
                    size = int(particle['size'] * particle['life'])
                    if size > 0:
                        # Create a surface with per-pixel alpha
                        particle_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                        color_with_alpha = (*particle['color'][:3], alpha)
                        pygame.draw.circle(particle_surface, color_with_alpha, (size, size), size)
                        self.screen.blit(particle_surface, (int(particle['x'] - size), int(particle['y'] - size)))
    
    def add_crystal_return_animation(self, from_pos, to_pos, color, count=1):
        """Add animation for crystals returning to the board"""
        if from_pos in self.position_coords and to_pos in self.position_coords:
            start_x, start_y = self.position_coords[from_pos]
            end_x, end_y = self.position_coords[to_pos]
            
            for i in range(count):
                animation = {
                    'start_x': start_x,
                    'start_y': start_y,
                    'end_x': end_x,
                    'end_y': end_y,
                    'current_x': start_x,
                    'current_y': start_y,
                    'color': color,
                    'start_time': pygame.time.get_ticks() + (i * 100),  # Stagger animations
                    'duration': 1500,  # 1.5 seconds
                    'started': False
                }
                self.crystal_return_animations.append(animation)
    
    def update_crystal_return_animations(self):
        """Update crystal return animations"""
        current_time = pygame.time.get_ticks()
        
        for animation in self.crystal_return_animations[:]:
            if not animation['started'] and current_time >= animation['start_time']:
                animation['started'] = True
            
            if not animation['started']:
                continue
                
            elapsed = current_time - animation['start_time']
            if elapsed >= animation['duration']:
                self.crystal_return_animations.remove(animation)
                continue
            
            # Smooth easing animation
            progress = elapsed / animation['duration']
            # Use easeInOutQuad for smooth motion
            if progress < 0.5:
                progress = 2 * progress * progress
            else:
                progress = 1 - 2 * (1 - progress) * (1 - progress)
            
            animation['current_x'] = animation['start_x'] + (animation['end_x'] - animation['start_x']) * progress
            animation['current_y'] = animation['start_y'] + (animation['end_y'] - animation['start_y']) * progress
    
    def draw_crystal_return_animations(self):
        """Draw crystal return animations"""
        for animation in self.crystal_return_animations:
            if animation['started']:
                # Draw crystal as a small colored circle
                color_map = {
                    'red': (255, 100, 100),
                    'blue': (100, 100, 255),
                    'green': (100, 255, 100),
                    'yellow': (255, 255, 100),
                    'white': (255, 255, 255)
                }
                color = color_map.get(animation['color'], (200, 200, 200))
                
                # Draw with a slight glow effect
                pygame.draw.circle(self.screen, color, 
                                 (int(animation['current_x']), int(animation['current_y'])), 8)
                pygame.draw.circle(self.screen, (255, 255, 255), 
                                 (int(animation['current_x']), int(animation['current_y'])), 8, 2)

    def calculate_position_coordinates(self):
        """Pre-calculate screen coordinates for all board positions using new layout"""
        self.position_coords['center'] = (self.board_center_x, self.board_center_y)

        self.position_coords.update({
            'rect_north': (self.board_center_x, self.board_center_y - self.rect_distance),
            'rect_south': (self.board_center_x, self.board_center_y + self.rect_distance),
            'rect_east': (self.board_center_x + self.rect_distance, self.board_center_y),
            'rect_west': (self.board_center_x - self.rect_distance, self.board_center_y)
        })

        for i in range(12):
            angle_rad = math.radians(i * 30)
            x = self.board_center_x + self.outer_distance * math.cos(angle_rad)
            y = self.board_center_y + self.outer_distance * math.sin(angle_rad)
            self.position_coords[f'hex_{i}'] = (int(x), int(y))

        self.position_coords.update({
            'mine_north': (self.board_center_x, self.board_center_y - self.mine_distance),
            'mine_south': (self.board_center_x, self.board_center_y + self.mine_distance),
            'mine_east': (self.board_center_x + self.mine_distance, self.board_center_y),
            'mine_west': (self.board_center_x - self.mine_distance, self.board_center_y)
        })

    # ---- Main loop and events ----
    def run(self):
        """Main game loop"""
        clock = pygame.time.Clock()
        running = True

        self.game.initialize_game()

        while running:
            if not self.is_dice_rolling:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        if self.quit_dialog.run_modal():
                            running = False
                            break
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        self.handle_mouse_click(event.pos)
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            if self.quit_dialog.run_modal():
                                running = False
                                break
                        else:
                            self.handle_key_press(event.key)
                    elif event.type == pygame.VIDEORESIZE:
                        self.handle_resize(event)

                    # Pass all events to action panel
                    self.handle_action_panel_event(event)
                
                # Handle AI failsafe events during AI turns
                current_player = self.game.get_current_player()
                if isinstance(current_player, AIWizard):
                    ai_action = self.action_panel.handle_ai_event(event)
                    if ai_action == 'ai_failsafe':
                        # Reset AI state to clear any frozen/stuck conditions
                        if hasattr(current_player, 'ai_controller') and current_player.ai_controller:
                            current_player.ai_controller.reset_state()
                        # Force end the AI turn
                        self.game.end_turn()
                        # Update button visibility for the new current player
                        new_current_player = self.game.get_current_player()
                        self.action_panel.set_ai_turn_state(isinstance(new_current_player, AIWizard))
                        self.sound_manager.play_sound('click', 0.8)

            current_player = self.game.get_current_player()
            if isinstance(current_player, AIWizard) and not self.game.game_over and not self.is_dice_rolling:
                current_time = pygame.time.get_ticks()
                
                # Check if this is a new AI turn
                if self.ai_turn_start_time == 0:
                    self.ai_turn_start_time = current_time
                    self.ai_turn_executed = False
                
                # Check if enough time has passed and we haven't executed yet
 
                if not self.ai_turn_executed and (current_time - self.ai_turn_start_time) >= self.ai_thinking_delay:
                    self.game.execute_ai_turn(current_player)
                    self.ai_turn_executed = True
                    
                    if self.game.current_actions >= self.game.max_actions_per_turn:
                        self.game.end_turn()
                        # Update button visibility for the new current player
                        new_current_player = self.game.get_current_player()
                        self.action_panel.set_ai_turn_state(isinstance(new_current_player, AIWizard))
                        # Reset for next turn
                        self.ai_turn_start_time = 0
                        self.ai_turn_executed = False
            else:
                # Reset AI turn timer if not an AI turn
                self.ai_turn_start_time = 0
                self.ai_turn_executed = False

            self.draw()

            if self.is_dice_rolling:
                self.is_dice_rolling = self.dice_manager.update_and_draw(self.screen_width // 2, self.screen_height // 2)

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
        sys.exit()

    def handle_resize(self, event):
        """Handle window resize events for dynamic scaling"""
        self.screen_width, self.screen_height = event.w, event.h
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        self.board_center_x = self.screen_width // 2 - 200
        self.board_center_y = self.screen_height // 2
        self.calculate_position_coordinates()
        self.action_panel = ActionPanel(self.screen_width - 350, 280, self.font_medium)

    def handle_mouse_click(self, pos):
        """Handle mouse clicks on the game board and UI"""
        if self.game.game_over or self.is_dice_rolling:
            return

        current_player = self.game.get_current_player()
        if isinstance(current_player, AIWizard):
            return

        clicked_position = self.get_position_at_coordinates(pos)
        if clicked_position:
            self.handle_board_click(clicked_position, current_player)

        self.handle_ui_click(pos, current_player)

    def handle_action_panel_event(self, event):
        """Handle action panel events"""
        action = self.action_panel.handle_event(event, self.game)
        current_player = self.game.get_current_player()

        if action == 'move_selected':
            self.current_action_mode = 'move' if self.current_action_mode != 'move' else None
            if self.current_action_mode == 'move':
                adjacent_positions = self.game.board.get_adjacent_positions(current_player.location)
                self.highlight_manager.set_move_highlights(adjacent_positions)
            else:
                self.highlight_manager.clear_highlights()

        elif action == 'mine_selected':
            self.current_action_mode = 'mine' if self.current_action_mode != 'mine' else None
            if self.current_action_mode == 'mine':
                mineable = self.game.board.get_mineable_positions(current_player.location)
                self.highlight_manager.set_mine_highlights(mineable)
            else:
                self.highlight_manager.clear_highlights()

        elif action == 'cast_selected':
            self.current_action_mode = 'cast' if self.current_action_mode != 'cast' else None
            if self.current_action_mode == 'cast':
                castable = self.game.board.get_castable_positions(current_player.location)
                self.highlight_manager.set_cast_highlights(castable)
            else:
                self.highlight_manager.clear_highlights()

        elif action == 'end_turn':
            self.game.end_turn()
            # Update button visibility for the new current player
            new_current_player = self.game.get_current_player()
            self.action_panel.set_ai_turn_state(isinstance(new_current_player, AIWizard))
            self.current_action_mode = None
            self.highlight_manager.clear_highlights()
            self.sound_manager.play_sound('click', 0.8)

        elif action == 'ai_failsafe':
            # Force end the AI turn
            self.game.end_turn()
            # Update button visibility for the new current player
            new_current_player = self.game.get_current_player()
            self.action_panel.set_ai_turn_state(isinstance(new_current_player, AIWizard))
            self.sound_manager.play_sound('click', 0.8)
            

    def get_position_at_coordinates(self, screen_pos):
        """Find which board position was clicked"""
        click_x, click_y = screen_pos

        for position, (x, y) in self.position_coords.items():
            distance = math.sqrt((click_x - x) ** 2 + (click_y - y) ** 2)
            if distance <= 25:
                return position

        return None

    def handle_board_click(self, position, current_player):
        """Handle clicks on board positions"""
        if self.current_action_mode == 'cast':
            if self.highlight_manager.is_highlighted(position):
                if self.selected_spell_card:
                    if self.game.cast_spell(current_player, self.selected_spell_card, self):
                        self.sound_manager.play_sound('spell_cast', 0.8)
                        self.current_action_mode = None
                        self.highlight_manager.clear_highlights()
                        self.selected_spell_card = None
                    else:
                        print("Failed to cast spell.")
                return

        if self.current_action_mode == 'move':
            if self.highlight_manager.is_highlighted(position):
                if self.game.move_player(current_player, position):
                    self.sound_manager.play_move()
                    self.current_action_mode = None
                    self.highlight_manager.clear_highlights()
                    if self.action_panel.selected_action == 'move':
                        adjacent_positions = self.game.board.get_adjacent_positions(current_player.location)
                        self.highlight_manager.set_move_highlights(adjacent_positions)
                return

        if self.current_action_mode == 'mine':
            if self.highlight_manager.is_highlighted(position):
                self.initiate_mine_sequence(current_player, position)
                return


    def initiate_mine_sequence(self, player, position):
        """Starts the dice rolling animation for a mining action."""
        if not self.game.can_mine(player):
            return

        if position in self.game.board.white_crystals and self.game.board.white_crystals[position] > 0:
            result = self.game.mine_white_crystal(player, position)
            if result == "reserve_full":
                self.show_reserve_full_warning()
            elif result:
                self.sound_manager.play_mine()
                self.current_action_mode = None
                self.highlight_manager.clear_highlights()
            return

        self.is_dice_rolling = True
        self.pending_action = {'player': player, 'position': position}

        if self.game.board.is_healing_springs(position):
            self.dice_manager.roll_healing_dice(self.resolve_mine_sequence)
        elif self.game.board.is_mine(position):
            self.dice_manager.roll_mine_dice(self.resolve_mine_sequence)
        else:
            self.is_dice_rolling = False
            self.pending_action = None

    def resolve_mine_sequence(self, roll_result):
        """Callback executed after dice animation finishes."""
        self.is_dice_rolling = False
        if not self.pending_action:
            return

        player = self.pending_action['player']
        position = self.pending_action['position']

        old_health = player.health
        old_location = player.location

        success = self.game.resolve_mine_with_roll(player, position, roll_result)

        if success == "reserve_full":
            self.show_reserve_full_warning()
        elif success:
            if player.health > old_health:
                self.sound_manager.play_heal()
            if player.location != old_location:
                self.sound_manager.play_teleport()
            elif position != 'center':
                self.sound_manager.play_mine()

        self.pending_action = None
        self.current_action_mode = None
        self.highlight_manager.clear_highlights()

    def show_reserve_full_warning(self):
        """Show visual feedback for reserve full (placeholder)."""
        pass

    def handle_ui_click(self, pos, current_player):
        """Handle clicks on UI elements"""
        clicked_card_index = self.get_spell_card_fan_click(pos, current_player)
        if clicked_card_index is not None:
            return

        if self.selected_spell_card:
            crystal_clicked = self.get_crystal_placement_click(pos, current_player)
            if crystal_clicked:
                return

    def get_spell_card_fan_click(self, pos, current_player):
        """Check if click was on any spell card in the fan layout"""
        for i, rect in enumerate(self.spell_card_rects):
            if rect and rect.collidepoint(pos):
                if i < len(current_player.hand):
                    card = current_player.hand[i]
                    if card not in current_player.cards_laid_down:
                        current_player.lay_down_spell_card(i)
                        self.sound_manager.play_sound('click', 0.8)
                elif i - len(current_player.hand) < len(current_player.cards_laid_down):
                    card_index = i - len(current_player.hand)
                    self.selected_spell_card = current_player.cards_laid_down[card_index]
                    self.sound_manager.play_sound('click', 0.8)
                return i
        return None

    def get_crystal_placement_click(self, pos, current_player):
        """Check if click was on crystal placement UI"""
        crystal_area_x = int(self.screen_width * 0.75)
        crystal_area_y = int(self.screen_height * 0.45)

        colors = ['red', 'blue', 'green', 'yellow', 'white']
        for i, color in enumerate(colors):
            crystal_x = crystal_area_x + i * 35
            crystal_y = crystal_area_y
            if (crystal_x <= pos[0] <= crystal_x + 30 and crystal_y <= pos[1] <= crystal_y + 30):
                if color != 'white' and current_player.crystals[color] > 0:
                    if self.selected_spell_card.add_crystals(color, 1, current_player):
                        self.sound_manager.play_charge()
                        return True
                elif color == 'white' and current_player.crystals['white'] > 0:
                    spell = self.selected_spell_card
                    for target_color in spell.cost:
                        needed = spell.cost[target_color] - spell.crystals_used.get(target_color, 0)
                        if needed > 0:
                            if spell.add_crystals('white', 1, current_player):
                                self.sound_manager.play_charge()
                                return True
                            break
        return False

    def handle_key_press(self, key):
        """Handle keyboard input"""
        if self.is_dice_rolling:
            return
        if key == pygame.K_SPACE:
            self.game.end_turn()
            # Update button visibility for the new current player
            new_current_player = self.game.get_current_player()
            self.action_panel.set_ai_turn_state(isinstance(new_current_player, AIWizard))
        # Esc is handled by quit dialog in the event loop

    # ---- Drawing ----
    def draw(self):
        """Draw the entire game state"""
        self.screen.fill(COLORS['light_grey'])

        self.update_blocking_highlights()
        self.update_attack_animations()
        self.update_crystal_return_animations()
        self.draw_board()
        self.draw_attack_animations()
        self.draw_crystal_return_animations()
        self.draw_ui()
        
        # Draw AI failsafe button during AI turns
        current_player = self.game.get_current_player()
        if isinstance(current_player, AIWizard) and not self.game.game_over:
            self.action_panel.draw_ai_buttons(self.screen)

        if self.game.game_over:
            self.draw_game_over()

    def update_blocking_highlights(self):
        """Update blocking highlights and remove expired ones."""
        current_time = pygame.time.get_ticks()
        
        # Check all wizards for expired blocking highlights
        for wizard in self.game.players:
            if getattr(wizard, 'is_blocking_highlighted', False):
                highlight_start = getattr(wizard, 'blocking_highlight_timer', 0)
                if current_time - highlight_start > 1000:  # 1 second
                    wizard.is_blocking_highlighted = False
                    wizard.blocking_highlight_timer = 0

    def draw_board(self):
        """Draw the game board with new clean layout"""
        self.draw_connections()

        for position, coords in self.position_coords.items():
            self.highlight_manager.draw_highlight(self.screen, position, coords)

        for position, coords in self.position_coords.items():
            self.draw_position(position, coords)

        self.draw_wizards()

    def draw_connections(self):
        """Draw clean lines connecting adjacent board positions"""
        drawn_connections = set()
        connections = self.game.board.layout.connections

        for position, adjacent_list in connections.items():
            if position in self.position_coords:
                start_pos = self.position_coords[position]
                for adjacent in adjacent_list:
                    if adjacent in self.position_coords:
                        connection_id = tuple(sorted([position, adjacent]))
                        if connection_id not in drawn_connections:
                            drawn_connections.add(connection_id)
                            end_pos = self.position_coords[adjacent]
                            pygame.draw.line(self.screen, COLORS['white'], start_pos, end_pos, 2)

    def draw_position(self, position, coords):
        """Draw a single board position with correct shape and color"""
        x, y = coords

        if position == 'center':
            pygame.draw.circle(self.screen, COLORS['white'], (x, y), 25)
            pygame.draw.circle(self.screen, COLORS['black'], (x, y), 25, 2)
            pygame.draw.circle(self.screen, COLORS['light_blue'], (x, y), 15)
            text = self.font_small.render("H", True, COLORS['blue'])
            text_rect = text.get_rect(center=(x, y))
            self.screen.blit(text, text_rect)

        elif position.startswith('rect_'):
            color_map = {
                'rect_north': COLORS['green'],
                'rect_south': COLORS['yellow'],
                'rect_east': COLORS['red'],
                'rect_west': COLORS['blue']
            }
            color = color_map.get(position, COLORS['grey'])
            pygame.draw.rect(self.screen, color, (x - 20, y - 15, 40, 30))
            pygame.draw.rect(self.screen, COLORS['black'], (x - 20, y - 15, 40, 30), 2)

        elif position.startswith('hex_'):
            self.draw_hexagon(x, y, 20, COLORS['grey'], COLORS['black'])
            # Determine crystal count from canonical storage
            crystal_count = 0
            pos_data = self.game.board.positions.get(position)
            if pos_data:
                # for mines, show count from board.mines; for hexes/center use positions[...] crystals
                if pos_data.get('type') == 'mine':
                    mine_color = self.game.board.get_mine_color_from_position(position)
                    if mine_color:
                        crystal_count = self.game.board.mines.get(mine_color, {}).get('crystals', 0)
                else:
                    crystal_count = pos_data.get('crystals', 0)

            # Draw crystal indicator if crystals exist
            if crystal_count > 0:
                # Example: draw a small circle or stack to indicate crystals
                pygame.draw.circle(self.screen, (255, 255, 255), coords, 10)  # white crystal indicator
                # optionally draw count text
                if crystal_count > 1:
                    font = self.font_small
                    text = font.render(str(crystal_count), True, (0, 0, 0))
                    text_rect = text.get_rect(center=(coords[0], coords[1]))
                    self.screen.blit(text, text_rect)

        elif position.startswith('mine_'):
            color_map = {
                'mine_north': COLORS['yellow'],
                'mine_south': COLORS['green'],
                'mine_west': COLORS['red'],
                'mine_east': COLORS['blue']
            }
            color = color_map.get(position, COLORS['grey'])
            pygame.draw.circle(self.screen, color, (x, y), 30)
            pygame.draw.circle(self.screen, COLORS['black'], (x, y), 30, 4)

            mine_color = self.game.board.get_mine_color_from_position(position)
            if mine_color:
                crystal_count = self.game.board.mines[mine_color]['crystals']
                text = self.font_large.render(str(crystal_count), True, COLORS['white'])
                text_rect = text.get_rect(center=(x, y))
                self.screen.blit(text, text_rect)

            direction = position.split('_')[1].title()
            mine_label = f"{direction} Mine"
            label_text = self.font_small.render(mine_label, True, COLORS['black'])
            label_rect = label_text.get_rect(center=(x, y - 45))
            self.screen.blit(label_text, label_rect)

    def draw_hexagon(self, x, y, radius, fill_color, border_color):
        """Draw a hexagon shape"""
        points = []
        for i in range(6):
            angle = math.radians(i * 60)
            px = x + radius * math.cos(angle)
            py = y + radius * math.sin(angle)
            points.append((px, py))

        pygame.draw.polygon(self.screen, fill_color, points)
        pygame.draw.polygon(self.screen, border_color, points, 2)

    def draw_wizards(self):
        """Draw wizard pieces on the board"""
        position_wizards = {}
        for position, data in self.game.board.wizards_on_board.items():
            position_wizards[position] = data if isinstance(data, list) else [data]

        for position, wizards in position_wizards.items():
            if position in self.position_coords:
                x, y = self.position_coords[position]
                count = len(wizards)
                offsets = [(0, -5)] if count == 1 else [(-16, -5), (16, -5)] if count == 2 else []
                if count > 2:
                    radius = 20
                    for i in range(count):
                        angle = math.radians(i * (360 / count))
                        offsets.append((int(radius * math.cos(angle)), int(radius * math.sin(angle)) - 5))

                for i, wizard in enumerate(wizards):
                    wx, wy = x + offsets[i][0], y + offsets[i][1]
                    color = COLORS.get(getattr(wizard, 'color', 'black'), COLORS['black'])

                    # Optional pulsing highlight
                    if getattr(wizard, 'is_blocking_highlighted', False):
                        current_time = pygame.time.get_ticks()
                        pulse_alpha = int(100 + 100 * abs(math.sin(current_time * 0.01)))
                        highlight_color = (*COLORS['gold'][:3], pulse_alpha)
                        highlight_surface = pygame.Surface((30, 30), pygame.SRCALPHA)
                        pygame.draw.circle(highlight_surface, highlight_color, (15, 15), 18)
                        self.screen.blit(highlight_surface, (wx - 15, wy - 15))

                    pygame.draw.circle(self.screen, color, (wx, wy), 12)
                    pygame.draw.circle(self.screen, COLORS['black'], (wx, wy), 12, 2)
                    text = self.font_small.render("W", True, COLORS['white'])
                    text_rect = text.get_rect(center=(wx, wy))
                    self.screen.blit(text, text_rect)

    def draw_ui(self):
        """Draw the user interface"""
        self.draw_turn_indicator()
        self.draw_player_info()
        self.action_panel.draw(self.screen)
        self.draw_spell_cards_fan()
        self.draw_opponent_cards_area()
        self.draw_game_status_panel()

    def draw_turn_indicator(self):
        """Draw a clear turn indicator at the top of the screen"""
        current_player = self.game.get_current_player()

        indicator_width = int(self.screen_width * 0.6)
        pygame.draw.rect(self.screen, COLORS['white'], (10, 10, indicator_width, 50))
        pygame.draw.rect(self.screen, COLORS['black'], (10, 10, indicator_width, 50), 2)

        turn_text = f"{self.display_name(current_player)}'s Turn"
        text_surface = self.font_large.render(turn_text, True, COLORS['black'])
        self.screen.blit(text_surface, (20, 25))

        if self.current_action_mode:
            action_text = f"Action: {self.current_action_mode.title()}"
            action_surface = self.font_medium.render(action_text, True, COLORS['blue'])
            self.screen.blit(action_surface, (int(self.screen_width * 0.3), 30))

    def draw_player_info(self):
        """Draw current player information"""
        current_player = self.game.get_current_player()

        info_x = int(self.screen_width * 0.68)
        info_width = int(self.screen_width * 0.3)

        pygame.draw.rect(self.screen, COLORS['white'], (info_x, 50, info_width, 200))
        pygame.draw.rect(self.screen, COLORS['black'], (info_x, 50, info_width, 200), 2)

        y_offset = 60
        player_text = self.display_name(current_player)
        text = self.font_large.render(player_text, True, COLORS['black'])
        self.screen.blit(text, (info_x + 10, y_offset))
        y_offset += 35

        health_text = f"Health: {current_player.health}/{current_player.max_health}"
        text = self.font_medium.render(health_text, True, COLORS['black'])
        self.screen.blit(text, (info_x + 10, y_offset))
        y_offset += 25

        crystal_text = "Crystals:"
        text = self.font_medium.render(crystal_text, True, COLORS['black'])
        self.screen.blit(text, (info_x + 10, y_offset))
        y_offset += 25

        x_offset = info_x + 10
        for color in ['red', 'blue', 'green', 'yellow', 'white']:
            count = current_player.crystals[color]
            if count > 0:
                pygame.draw.circle(self.screen, COLORS[color], (x_offset + 10, y_offset + 10), 8)
                pygame.draw.circle(self.screen, COLORS['black'], (x_offset + 10, y_offset + 10), 8, 1)
                count_text = self.font_small.render(str(count), True, COLORS['black'])
                self.screen.blit(count_text, (x_offset + 25, y_offset + 5))
                x_offset += 50

        y_offset += 35
        actions_text = f"Actions: {self.game.current_actions}/{self.game.max_actions_per_turn}"
        text = self.font_medium.render(actions_text, True, COLORS['black'])
        self.screen.blit(text, (info_x + 10, y_offset))

        y_offset += 20
        limits_text = f"Moves: {self.game.moves_used}/3  Mines: {self.game.mines_used}/2  Spells: {self.game.spells_cast}/1"
        text = self.font_small.render(limits_text, True, COLORS['black'])
        self.screen.blit(text, (info_x + 10, y_offset))

    def draw_spell_cards_fan(self):
        """Draw spell cards in a horizontal row layout with professional styling"""
        current_player = self.game.get_current_player()
        self.spell_card_rects = []

        all_cards = current_player.hand + current_player.cards_laid_down
        if not all_cards:
            return

        # Update mouse position for hover detection
        self.mouse_pos = pygame.mouse.get_pos()

        # Card dimensions and positioning
        base_card_width = int(self.screen_width * 0.10)
        base_card_height = int(self.screen_height * 0.25)
        hover_scale = 1.3
        card_spacing = base_card_width + 15
        
        # Horizontal row positioning
        total_width = len(all_cards) * card_spacing - 15
        start_x = self.screen_width - total_width - 20
        
        # Hand cards in bottom row, laid down cards in upper row
        hand_y = self.screen_height - base_card_height - 10
        board_y = hand_y - int(base_card_height * 0.7)
        
        self.hovered_card_index = None

        # Draw hand cards (bottom row)
        for i, card in enumerate(current_player.hand):
            card_x = start_x + i * card_spacing
            card_y = hand_y
            is_hovered = self._is_card_hovered(card_x, card_y, base_card_width, base_card_height, i)
            
            if is_hovered:
                self.hovered_card_index = i
                
            self.draw_spell_card_horizontal(
                card, card_x, card_y, base_card_width, base_card_height,
                True, False, is_hovered, current_player, i
            )

        # Draw laid down cards (upper row)  
        for i, card in enumerate(current_player.cards_laid_down):
            card_x = start_x + i * card_spacing
            card_y = board_y
            card_index = len(current_player.hand) + i
            is_hovered = self._is_card_hovered(card_x, card_y, base_card_width, base_card_height, card_index)
            is_selected = (card == self.selected_spell_card)
            
            if is_hovered:
                self.hovered_card_index = card_index
                
            self.draw_spell_card_horizontal(
                card, card_x, card_y, base_card_width, base_card_height,
                False, is_selected, is_hovered, current_player, card_index
            )

    def _is_card_hovered(self, card_x, card_y, card_width, card_height, card_index):
        """Check if mouse is hovering over a card"""
        mx, my = self.mouse_pos
        return (card_x <= mx <= card_x + card_width and 
                card_y <= my <= card_y + card_height)

    def draw_spell_card_horizontal(self, card, x, y, base_width, base_height,
                                 is_in_hand, is_selected, is_hovered, current_player, card_index):
        """Draw a single spell card in horizontal layout with professional styling"""
        
        # Apply hover scaling
        if is_hovered:
            width = int(base_width * 1.3)
            height = int(base_height * 1.3)
            # Adjust position to keep card centered when scaled
            adjusted_x = x - (width - base_width) // 2
            adjusted_y = y - (height - base_height) // 2
        else:
            width = base_width
            height = base_height
            adjusted_x = x
            adjusted_y = y

        # Draw shadow first (professional effect)
        shadow_offset = 3
        shadow_surface = pygame.Surface((width + shadow_offset * 2, height + shadow_offset * 2), pygame.SRCALPHA)
        shadow_color = (0, 0, 0, 60)  # Semi-transparent black
        pygame.draw.rect(shadow_surface, shadow_color, 
                        (shadow_offset, shadow_offset, width, height), border_radius=8)
        self.screen.blit(shadow_surface, (adjusted_x - shadow_offset, adjusted_y - shadow_offset))

        # Create card surface
        card_surface = pygame.Surface((width, height), pygame.SRCALPHA)

        # Card background colors
        if is_selected:
            card_color = COLORS['gold']
        elif is_hovered:
            card_color = (255, 255, 240)  # Light cream color for hover
        elif is_in_hand:
            card_color = COLORS['white']
        else:
            card_color = COLORS['light_blue']

        # Draw card background with rounded corners
        pygame.draw.rect(card_surface, card_color, (0, 0, width, height), border_radius=8)

        # Card border
        border_color = COLORS['gold'] if is_selected else COLORS['black']
        border_width = 4 if is_selected else 2
        pygame.draw.rect(card_surface, border_color, (0, 0, width, height), border_width, border_radius=8)

        # Draw damage number at top center
        damage_font_size = int(height * 0.30)
        damage_font = pygame.font.Font(None, damage_font_size)
        damage_text = damage_font.render(str(card.get_damage()), True, COLORS['black'])
        damage_rect = damage_text.get_rect(center=(width // 2, damage_font_size // 2 + 10))
        card_surface.blit(damage_text, damage_rect)

        # Draw crystal costs (always visible, no rotation)
        y_offset = height // 3
        crystal_size = max(6, int(width * 0.08))
        font_size = max(20, int(width * 0.30))
        cost_font = pygame.font.Font(None, font_size)

        for color, cost in card.cost.items():
            if cost > 0:
                crystal_x = width // 4
                
                # Draw crystal circle
                pygame.draw.circle(card_surface, COLORS.get(color, COLORS['wild']), 
                                 (crystal_x, y_offset), crystal_size)
                pygame.draw.circle(card_surface, COLORS['black'], 
                                 (crystal_x, y_offset), crystal_size, 2)

                # Draw crystal cost/progress text
                if not is_in_hand:
                    placed = card.crystals_used.get(color, 0)
                    progress_text = f"{placed}/{cost}"
                    text_color = COLORS['green'] if placed >= cost else COLORS['red']
                else:
                    progress_text = str(cost)
                    text_color = COLORS['black']

                cost_text = cost_font.render(progress_text, True, text_color)
                card_surface.blit(cost_text, (crystal_x + crystal_size + 5, y_offset - font_size // 2))
                y_offset += crystal_size * 2 + 8

        # Draw charging progress bar for laid down cards
        if not is_in_hand:
            progress = card.get_charging_progress()
            bar_y = height - 25
            bar_width = width - 10
            bar_height = 8
            
            # Background bar
            pygame.draw.rect(card_surface, COLORS['grey'], (5, bar_y, bar_width, bar_height), border_radius=4)
            
            # Progress bar
            progress_width = int(bar_width * progress)
            bar_color = COLORS['green'] if progress >= 1.0 else COLORS['yellow']
            if progress_width > 0:
                pygame.draw.rect(card_surface, bar_color, (5, bar_y, progress_width, bar_height), border_radius=4)
            
            # Progress percentage
            progress_text = f"{int(progress * 100)}%"
            progress_surface = self.font_small.render(progress_text, True, COLORS['black'])
            card_surface.blit(progress_surface, (5, bar_y - 18))

        # Store click detection rectangle (use original position for consistent clicking)
        click_rect = pygame.Rect(x, y, base_width, base_height)
        self.spell_card_rects.append(click_rect)

        # Blit the card to screen
        self.screen.blit(card_surface, (adjusted_x, adjusted_y))

        # Draw crystal placement UI if this card is selected
        if self.selected_spell_card and card == self.selected_spell_card:
            self.draw_crystal_placement_ui(current_player)

    def draw_crystal_placement_ui(self, current_player):
        """Draw the crystal placement interface"""
        crystal_area_x = int(self.screen_width * 0.75)
        crystal_area_y = int(self.screen_height * 0.45)

        label_font = pygame.font.Font(None, 40)
        crystal_label = label_font.render("Place Crystals:", True, COLORS['black'])
        self.screen.blit(crystal_label, (crystal_area_x, crystal_area_y - 25))

        colors = ['red', 'blue', 'green', 'yellow', 'white']
        for i, color in enumerate(colors):
            x = crystal_area_x + i * 35
            y = crystal_area_y
            pygame.draw.circle(self.screen, COLORS[color], (x + 15, y + 15), 15)
            pygame.draw.circle(self.screen, COLORS['black'], (x + 15, y + 15), 15, 2)

            required = self.selected_spell_card.cost.get(color, 0)
            placed = self.selected_spell_card.crystals_used.get(color, 0)
            if required > 0:
                progress_text = f"{placed}/{required}"
                text_color = COLORS['green'] if placed >= required else COLORS['black']
                progress_surface = self.font_small.render(progress_text, True, text_color)
                self.screen.blit(progress_surface, (x, y + 35))

    def draw_opponent_cards_area(self):
        """Draw opponent players' laid down cards in a compact format on the left side"""
        current_player = self.game.get_current_player()
        
        # Get all opponents (players other than current player)
        opponents = [player for player in self.game.players if player != current_player]
        
        if not opponents:
            return
            
        # Define the opponent area dimensions
        area_width = int(self.screen_width * 0.25)  # 25% of screen width
        area_x = 10  # Left margin
        area_y = 70   # Start below turn indicator
        max_area_height = int(self.screen_height * 0.7)  # Max 70% of screen height
        
        # Calculate space per opponent
        opponent_height = min(max_area_height // len(opponents), 200)
        
        for i, opponent in enumerate(opponents):
            opponent_y = area_y + i * (opponent_height + 10)
            
            # Draw opponent section background
            section_rect = pygame.Rect(area_x, opponent_y, area_width, opponent_height)
            pygame.draw.rect(self.screen, COLORS['white'], section_rect)
            pygame.draw.rect(self.screen, COLORS['black'], section_rect, 2)
            
            # Draw opponent name/color header
            header_height = 30
            header_rect = pygame.Rect(area_x, opponent_y, area_width, header_height)
            opponent_color = COLORS.get(opponent.color, COLORS['black'])
            pygame.draw.rect(self.screen, opponent_color, header_rect)
            pygame.draw.rect(self.screen, COLORS['black'], header_rect, 2)
            
            # Opponent name text
            opponent_name = self.display_name(opponent)
            name_font = pygame.font.Font(None, 36)
            name_text = name_font.render(opponent_name, True, COLORS['white'])
            name_rect = name_text.get_rect(center=(area_x + area_width // 2, opponent_y + header_height // 2))
            self.screen.blit(name_text, name_rect)
            
            # Draw opponent's laid down cards
            if opponent.cards_laid_down:
                cards_area_y = opponent_y + header_height + 5
                cards_area_height = opponent_height - header_height - 10
                
                self.draw_opponent_cards_compact(opponent, area_x + 5, cards_area_y, 
                                                area_width - 10, cards_area_height)
            else:
                # Show "No cards played" message
                no_cards_text = self.font_small.render("No cards played", True, COLORS['dark_grey'])
                text_rect = no_cards_text.get_rect(center=(area_x + area_width // 2, 
                                                          opponent_y + header_height + 20))
                self.screen.blit(no_cards_text, text_rect)

    def draw_opponent_cards_compact(self, opponent, x, y, width, height):
        """Draw opponent's cards in a compact grid layout"""
        cards = opponent.cards_laid_down
        if not cards:
            return
            
        # Calculate card dimensions (smaller than main player cards)
        cards_per_row = min(3, len(cards))  # Max 3 cards per row
        rows_needed = (len(cards) + cards_per_row - 1) // cards_per_row
        
        card_width = min((width - 10) // cards_per_row - 5, 80)  # Compact size
        card_height = min(height // rows_needed - 5, 120)  # Compact size
        
        for i, card in enumerate(cards):
            row = i // cards_per_row
            col = i % cards_per_row
            
            # Calculate card position
            cards_in_row = min(cards_per_row, len(cards) - row * cards_per_row)
            row_width = cards_in_row * (card_width + 5) - 5
            start_x = x + (width - row_width) // 2  # Center the row
            
            card_x = start_x + col * (card_width + 5)
            card_y = y + row * (card_height + 5)
            
            self.draw_compact_spell_card(card, card_x, card_y, card_width, card_height)

    def draw_compact_spell_card(self, card, x, y, width, height):
        """Draw a single spell card in compact format"""
        # Create card surface
        card_surface = pygame.Surface((width, height))
        
        # Determine card color based on charging status
        progress = card.get_charging_progress()
        if progress >= 1.0:
            card_color = COLORS['light_blue']  # Fully charged
        else:
            card_color = COLORS['white']  # Still charging
            
        card_surface.fill(card_color)
        
        # Draw border
        border_color = COLORS['green'] if progress >= 1.0 else COLORS['black']
        border_width = 2 if progress >= 1.0 else 1
        pygame.draw.rect(card_surface, border_color, (0, 0, width, height), border_width)
        
        # Draw damage value at top
        damage_font = pygame.font.Font(None, max(32, int(height * 0.30)))
        damage_text = damage_font.render(str(card.get_damage()), True, COLORS['black'])
        damage_rect = damage_text.get_rect(center=(width // 2, height // 8))
        card_surface.blit(damage_text, damage_rect)
        
        # Draw crystal costs
        y_offset = height // 4
        crystal_size = max(4, int(width * 0.08))
        cost_font_size = max(20, int(width * 0.30))
        cost_font = pygame.font.Font(None, cost_font_size)
        
        for color, cost in card.cost.items():
            if cost > 0:
                crystal_x = width // 6
                
                # Draw crystal circle
                pygame.draw.circle(card_surface, COLORS.get(color, COLORS['wild']), 
                                 (crystal_x, y_offset), crystal_size)
                pygame.draw.circle(card_surface, COLORS['black'], 
                                 (crystal_x, y_offset), crystal_size, 1)
                
                # Show progress (placed/required)
                placed = card.crystals_used.get(color, 0)
                progress_text = f"{placed}/{cost}"
                text_color = COLORS['green'] if placed >= cost else COLORS['red']
                
                cost_text = cost_font.render(progress_text, True, text_color)
                card_surface.blit(cost_text, (crystal_x + crystal_size + 2, 
                                            y_offset - cost_font_size // 2))
                y_offset += crystal_size * 2 + 2
        
        # Draw charging progress bar at bottom
        bar_height = max(3, int(height * 0.05))
        bar_y = height - bar_height - 2
        bar_width = width - 4
        
        # Background bar
        pygame.draw.rect(card_surface, COLORS['grey'], (2, bar_y, bar_width, bar_height))
        
        # Progress bar
        progress_width = int(bar_width * progress)
        bar_color = COLORS['green'] if progress >= 1.0 else COLORS['yellow']
        pygame.draw.rect(card_surface, bar_color, (2, bar_y, progress_width, bar_height))
        
        # Progress percentage text (very small)
        if height > 60:  # Only show percentage if card is tall enough
            progress_text = f"{int(progress * 100)}%"
            progress_font = pygame.font.Font(None, max(16, int(height * 0.16)))
            progress_surface = progress_font.render(progress_text, True, COLORS['black'])
            card_surface.blit(progress_surface, (2, bar_y - 12))
        
        # Blit the card to screen
        self.screen.blit(card_surface, (x, y))

    def draw_game_status_panel(self):
        """Draw the ticker tape and all player statuses at the bottom."""
        panel_height = int(self.screen_height * 0.18)
        panel_y = self.screen_height - panel_height - 10
        panel_width = int(self.screen_width * 0.65)

        panel_rect = pygame.Rect(10, panel_y, panel_width, panel_height)
        pygame.draw.rect(self.screen, COLORS['white'], panel_rect)
        pygame.draw.rect(self.screen, COLORS['black'], panel_rect, 2)

        # Ticker/log
        log_width = int(panel_width * 0.6)
        log_area_rect = pygame.Rect(panel_rect.x + 10, panel_rect.y + 10, log_width, panel_height - 20)

        log_title = self.font_medium.render("Action Log", True, COLORS['black'])
        self.screen.blit(log_title, (log_area_rect.x, log_area_rect.y))

        if hasattr(self.game, 'action_log'):
            log_entries = list(self.game.action_log)[-5:]
            y_offset = log_area_rect.bottom - 20
            for entry in reversed(log_entries):
                log_text = self.font_small.render(entry, True, COLORS['dark_grey'])
                self.screen.blit(log_text, (log_area_rect.x + 5, y_offset))
                y_offset -= 18
                if y_offset < log_area_rect.y + 20:
                    break

        # All players status
        status_width = int(panel_width * 0.35)
        status_area_rect = pygame.Rect(panel_rect.x + log_width + 20, panel_rect.y + 10, status_width, panel_height - 20)

        status_title = self.font_medium.render("All Wizards", True, COLORS['black'])
        self.screen.blit(status_title, (status_area_rect.x, status_area_rect.y))

        y_offset = status_area_rect.y + 25
        for player in self.game.players:
            player_color_rgb = COLORS.get(player.color, COLORS['black'])
            status_text = f"{self.display_name(player)}: {player.health}/{player.max_health} HP"
            text_surface = self.font_small.render(status_text, True, player_color_rgb)
            self.screen.blit(text_surface, (status_area_rect.x, y_offset))

            x_offset = status_area_rect.x + 220
            for crystal_color_str in ['red', 'blue', 'green', 'yellow', 'white']:
                count = player.crystals.get(crystal_color_str, 0)
                if count > 0:
                    crystal_color = COLORS[crystal_color_str]
                    pygame.draw.circle(self.screen, crystal_color, (x_offset, y_offset + 8), 6)
                    pygame.draw.circle(self.screen, COLORS['black'], (x_offset, y_offset + 8), 6, 1)
                    count_surface = self.font_small.render(str(count), True, COLORS['black'])
                    self.screen.blit(count_surface, (x_offset + 10, y_offset + 3))
                    x_offset += 25

            y_offset += 20

    def draw_game_over(self):
        """Draw game over screen"""
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.fill(COLORS['black'])
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0, 0))

        game_over_font = pygame.font.Font(None, int(self.screen_height * 0.16))
        game_over_text = game_over_font.render("GAME OVER", True, COLORS['white'])
        game_over_rect = game_over_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 - 100))
        self.screen.blit(game_over_text, game_over_rect)

        winner_font = pygame.font.Font(None, int(self.screen_height * 0.10))
        winner = self.game.get_winner()
        if winner:
            label = f"{self.display_name(winner)} Wins!"
            winner_text = winner_font.render(label, True, COLORS['gold'])
            winner_rect = winner_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            self.screen.blit(winner_text, winner_rect)

def main():
    """Simple test to run the GUI with a sample game"""
    pygame.init()
    try:
        game = CrystalWizardsGame(num_players=2, num_ai=1)
        gui = GameGUI(game)
        gui.run()
    except Exception as e:
        print(f"Error running GUI test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pygame.quit()

if __name__ == "__main__":
    main()