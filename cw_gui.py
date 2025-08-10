"""
Crystal Wizards - Pygame GUI Implementation

"""

import pygame
import math
import sys
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
    'wild': (230, 50, 230)  # Purple
}

class GameGUI:
    def __init__(self, game):
        """Initialize the game GUI to fill the entire screen in a closable window."""
        self.game = game

        # Initialize pygame display if not already done
        if not pygame.get_init():
            pygame.init()

        # Get the current display resolution
        info = pygame.display.Info()
        self.screen_width = info.current_w
        self.screen_height = info.current_h

        # Create a regular window sized to the full screen (closable)
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Crystal Wizards")

        # Fonts
        pygame.font.init()
        self.font_small = pygame.font.Font(None, 20)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_large = pygame.font.Font(None, 32)

        # Board layout parameters (you may later adapt these to screen size if desired)
        self.board_center_x = self.screen_width // 2 - 200  # was 400; keep relative if needed
        self.board_center_y = self.screen_height // 2       # was 400
        self.center_radius = 30
        self.rect_distance = 80
        self.outer_distance = 150
        self.mine_distance = 220

        # UI state
        self.selected_wizard = None
        self.selected_spell_card = None
        self.show_spell_details = False

        # New UI components
        self.highlight_manager = HighlightManager()
        self.sound_manager = sound_manager
        # If ActionPanel expects fixed coords, you can still place it relative to width/height
        self.action_panel = ActionPanel(self.screen_width - 350, 280, self.font_medium)

        self.dice_manager = DiceRollManager(self.screen, self.font_large)
        self.is_dice_rolling = False
        self.pending_action = None

        self.sound_manager.load_sounds()

        self.current_action_mode = None

        self.position_coords = {}
        self.calculate_position_coordinates()
        
        # Initialize spell card fan layout variables
        self.spell_card_rects = []  # Will store actual rects for click detection
        self.visible_hand = []  # Cards to display in fan

    
    def show_blocking_dialog(self, wizard, damage, caster):
        """Show a dialog for blocking a spell"""
        # This method can be implemented to show a dialog box
        # For now, we will just print the message
        print(f"{caster.color.title()} Wizard is casting a spell with {damage} damage on {wizard.color.title()} Wizard. Block it?")
        # In a real GUI, you would show a dialog here and return True/False based on user input
        # For now, just return 0 (no blocking) to avoid interrupting gameplay
        return 0
    
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
    
    def run(self):
        """Main game loop"""
        clock = pygame.time.Clock()
        running = True
        
        self.game.initialize_game()
        
        while running:
            if not self.is_dice_rolling:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        self.handle_mouse_click(event.pos)
                    elif event.type == pygame.KEYDOWN:
                        self.handle_key_press(event.key)
                    elif event.type == pygame.VIDEORESIZE:
                        self.handle_resize(event)
                    
                    self.handle_action_panel_event(event)
            
            current_player = self.game.get_current_player()
            if isinstance(current_player, AIWizard) and not self.game.game_over and not self.is_dice_rolling:
                pygame.time.wait(1000)
                self.game.execute_ai_turn(current_player)
                if self.game.current_actions >= self.game.max_actions_per_turn:
                    self.game.end_turn()
            
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
        # Recalculate board center and other proportional elements
        self.board_center_x = self.screen_width // 2 - 200
        self.board_center_y = self.screen_height // 2
        self.calculate_position_coordinates()
        
        # Update action panel position
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
                # FIXED: Allow wizards to move to any adjacent position, not just empty ones
                # This restores the original multi-wizard positioning functionality
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
            self.current_action_mode = None
            self.highlight_manager.clear_highlights()
            self.sound_manager.play_sound('click', 0.8)
    
    def get_position_at_coordinates(self, screen_pos):
        """Find which board position was clicked"""
        click_x, click_y = screen_pos
        
        for position, (pos_x, pos_y) in self.position_coords.items():
            distance = math.sqrt((click_x - pos_x)**2 + (click_y - pos_y)**2)
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
                        # Show error message if casting failed
                        print("Failed to cast spell.")
            return

        if self.current_action_mode == 'move':
            if self.highlight_manager.is_highlighted(position):
                if self.game.move_player(current_player, position):
                    self.sound_manager.play_move()
                    self.current_action_mode = None
                    self.highlight_manager.clear_highlights()
                    if self.action_panel.selected_action == 'move':
                        # FIXED: Consistent with above fix - allow movement to occupied positions
                        adjacent_positions = self.game.board.get_adjacent_positions(current_player.location)
                        self.highlight_manager.set_move_highlights(adjacent_positions)
        
        elif self.current_action_mode == 'mine':
            if self.highlight_manager.is_highlighted(position):
                self.initiate_mine_sequence(current_player, position)

        else:
            if self.game.can_move(current_player):
                if self.game.move_player(current_player, position):
                    self.sound_manager.play_move()
    
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
        """Callback function executed after dice animation finishes."""
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
        """Show visual feedback for reserve full"""
        # Simple implementation - could be enhanced with a popup
        pass

    def handle_ui_click(self, pos, current_player):
        """Handle clicks on UI elements"""
        # Check for spell card fan clicks first (new system)
        clicked_card_index = self.get_spell_card_fan_click(pos, current_player)
        if clicked_card_index is not None:
            return
        
        # Check crystal placement clicks
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
                        # Lay down the card for charging
                        current_player.lay_down_spell_card(i)
                        self.sound_manager.play_sound('click', 0.8)
                elif i - len(current_player.hand) < len(current_player.cards_laid_down):
                    # Click on a laid down card - select it
                    card_index = i - len(current_player.hand)
                    self.selected_spell_card = current_player.cards_laid_down[card_index]
                    self.sound_manager.play_sound('click', 0.8)
                return i
        return None
    
    def get_crystal_placement_click(self, pos, current_player):
        """Check if click was on crystal placement UI"""
        # Crystal placement area - positioned relative to screen size
        crystal_area_x = int(self.screen_width * 0.75)  # 75% of screen width
        crystal_area_y = int(self.screen_height * 0.45)  # 45% of screen height
        
        colors = ['red', 'blue', 'green', 'yellow', 'white']
        for i, color in enumerate(colors):
            crystal_x = crystal_area_x + i * 35
            crystal_y = crystal_area_y
            if (crystal_x <= pos[0] <= crystal_x + 30 and 
                crystal_y <= pos[1] <= crystal_y + 30):

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
        if self.is_dice_rolling: return
        if key == pygame.K_SPACE:
            self.game.end_turn()
        elif key == pygame.K_ESCAPE:
            self.selected_spell_card = None
    
    def draw(self):
        """Draw the entire game state"""
        self.screen.fill(COLORS['light_grey'])
        
        # Update blocking highlight animations
        self.update_blocking_highlights()
        
        self.draw_board()
        self.draw_ui()
        
        if self.game.game_over:
            self.draw_game_over()
    
    def update_blocking_highlights(self):
        """Update any animated highlights"""
        # This method can be implemented if blocking highlights are needed
        pass
    
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
            color_map = {'rect_north': COLORS['green'], 'rect_south': COLORS['yellow'], 'rect_east': COLORS['red'], 'rect_west': COLORS['blue']}
            color = color_map.get(position, COLORS['grey'])
            pygame.draw.rect(self.screen, color, (x-20, y-15, 40, 30))
            pygame.draw.rect(self.screen, COLORS['black'], (x-20, y-15, 40, 30), 2)
        
        elif position.startswith('hex_'):
            self.draw_hexagon(x, y, 20, COLORS['grey'], COLORS['black'])
            crystal_count = self.game.board.white_crystals.get(position, 0)
            if crystal_count > 0:
                pygame.draw.circle(self.screen, COLORS['white'], (x, y), 8)
                pygame.draw.circle(self.screen, COLORS['black'], (x, y), 8, 1)
        
        elif position.startswith('mine_'):
            color_map = {'mine_north': COLORS['yellow'], 'mine_south': COLORS['green'], 'mine_west': COLORS['red'], 'mine_east': COLORS['blue']}
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
                    
                    # Draw blocking highlight effect if wizard is blocking
                    if hasattr(wizard, 'is_blocking_highlighted') and wizard.is_blocking_highlighted:
                        # Draw pulsing golden highlight around wizard
                        current_time = pygame.time.get_ticks()
                        pulse_alpha = int(100 + 100 * abs(math.sin(current_time * 0.01)))  # Pulsing effect
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
        self.draw_spell_cards_fan()  # New fan layout
        self.draw_game_status_panel()
    
    def draw_turn_indicator(self):
        """Draw a clear turn indicator at the top of the screen"""
        current_player = self.game.get_current_player()
        
        indicator_width = int(self.screen_width * 0.6)  # 60% of screen width
        pygame.draw.rect(self.screen, COLORS['white'], (10, 10, indicator_width, 50))
        pygame.draw.rect(self.screen, COLORS['black'], (10, 10, indicator_width, 50), 2)
        
        turn_text = f"{current_player.color.title()} Wizard's Turn"
        if isinstance(current_player, AIWizard):
            turn_text += " (AI)"
        
        text_surface = self.font_large.render(turn_text, True, COLORS['black'])
        self.screen.blit(text_surface, (20, 25))
        
        if self.current_action_mode:
            action_text = f"Action: {self.current_action_mode.title()}"
            action_surface = self.font_medium.render(action_text, True, COLORS['blue'])
            self.screen.blit(action_surface, (int(self.screen_width * 0.3), 30))
    
    def draw_player_info(self):
        """Draw current player information"""
        current_player = self.game.get_current_player()
        
        # Position player info box proportionally
        info_x = int(self.screen_width * 0.68)  # 68% from left
        info_width = int(self.screen_width * 0.3)  # 30% of screen width
        
        pygame.draw.rect(self.screen, COLORS['white'], (info_x, 50, info_width, 200))
        pygame.draw.rect(self.screen, COLORS['black'], (info_x, 50, info_width, 200), 2)
        
        y_offset = 60
        player_text = f"{current_player.color.title()} Wizard"
        if isinstance(current_player, AIWizard): player_text += " (AI)"
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
        """Draw spell cards in an elegant fan layout in bottom-right corner for hand and a seprate area for laid down cards"""
        current_player = self.game.get_current_player()
        
        # Clear previous card rects
        self.spell_card_rects = []
        
        # show cards in hand
        for i, card in enumerate(current_player.hand):
            if i >= 3:
                break

        # show cards laid down
        for i, card in enumerate(current_player.cards_laid_down):
            if i >= 3:
                break

        all_cards = current_player.hand + current_player.cards_laid_down
        if not all_cards:
            return
        
        # Fan layout parameters - all proportional to screen size
        fan_center_x = int(self.screen_width * 0.85)  # 85% from left
        fan_center_y = int(self.screen_height * 0.95)  # 85% from top
        fan_radius = int(self.screen_height * 0.30)  # 30% of screen height
        
        # Card dimensions scaled to screen
        card_width = int(self.screen_width * 0.12)  # 16% of screen width
        card_height = int(self.screen_height * 0.30)  # 30% of screen height
        
        # Calculate positions for up to 3 cards in fan
        visible_cards = all_cards[:3]  # Show maximum 3 cards
        angle_spread = 23  # degrees between cards
        
        for i, card in enumerate(visible_cards):
            # Calculate rotation angle for fan effect
            if len(visible_cards) == 1:
                angle = 0
            else:
                angle = -angle_spread + (i * (2 * angle_spread) / (len(visible_cards) - 1))
            
            # Calculate card position on the fan arc
            angle_rad = math.radians(angle - 90)  # -90 to point upward
            card_x = fan_center_x + int(fan_radius * math.cos(angle_rad))
            card_y = fan_center_y + int(fan_radius * math.sin(angle_rad))
            
            # Determine if this card is in hand or laid down
            is_in_hand = i < len(current_player.hand)
            is_selected = (not is_in_hand and card == self.selected_spell_card)

            # toggle between hand and laid down cards
            if is_in_hand:
                # If card is in hand, it should not be selected
                is_selected = False
            else:
                # If card is laid down, it can be selected
                is_selected = (card == self.selected_spell_card)
            
            # Draw the card
            self.draw_spell_card_in_fan(card, card_x, card_y, card_width, card_height, 
                                      angle, is_in_hand, is_selected, current_player)
    
    def draw_spell_card_in_fan(self, card, x, y, width, height, rotation_angle, 
                              is_in_hand, is_selected, current_player):
        """Draw a single spell card in the fan layout with rotation"""
        # Create card surface
        card_surface = pygame.Surface((width, height))
        
        # Card background color
        if is_selected:
            card_color = COLORS['gold']
        elif is_in_hand:
            card_color = COLORS['white']
        else:
            card_color = COLORS['light_blue']
        
        card_surface.fill(card_color)
        
        # Draw border
        border_color = COLORS['black']
        if is_selected:
            border_color = COLORS['gold']
        pygame.draw.rect(card_surface, border_color, (0, 0, width, height), 3)
        
        # Draw damage number at top
        damage_text = pygame.font.Font(None, int(height * 0.2)).render(
            str(card.get_damage()), True, COLORS['black'])
        damage_rect = damage_text.get_rect(center=(width // 2, height // 6))
        card_surface.blit(damage_text, damage_rect)
        
        # Draw crystal requirements with color coding
        y_offset = height // 3
        crystal_size = max(8, int(width * 0.15))
        font_size = max(12, int(width * 0.2))
        cost_font = pygame.font.Font(None, font_size)
        
        for color, cost in card.cost.items():
            if cost > 0:
                # Draw crystal circle
                crystal_x = width // 4
                pygame.draw.circle(card_surface, COLORS.get(color, COLORS['wild']), 
                                 (crystal_x, y_offset), crystal_size)
                pygame.draw.circle(card_surface, COLORS['black'], 
                                 (crystal_x, y_offset), crystal_size, 2)
                
                # Show cost with color coding for met/unmet requirements
                if not is_in_hand:  # Only show progress for laid down cards
                    placed = card.crystals_used.get(color, 0)
                    progress_text = f"{placed}/{cost}"
                    # Color code: green if met, red if unmet
                    text_color = COLORS['green'] if placed >= cost else COLORS['red']
                else:
                    progress_text = str(cost)
                    text_color = COLORS['black']
                
                cost_text = cost_font.render(progress_text, True, text_color)
                card_surface.blit(cost_text, (crystal_x + crystal_size + 5, y_offset - font_size // 2))
                y_offset += crystal_size * 2 + 5
        
        # Add charging progress bar for laid down cards
        if not is_in_hand:
            progress = card.get_charging_progress()
            bar_y = height - 20
            bar_width = width - 10
            bar_height = 6
            
            # Background bar
            pygame.draw.rect(card_surface, COLORS['grey'], (5, bar_y, bar_width, bar_height))
            # Progress bar
            progress_width = int(bar_width * progress)
            bar_color = COLORS['green'] if progress >= 1.0 else COLORS['yellow']
            pygame.draw.rect(card_surface, bar_color, (5, bar_y, progress_width, bar_height))
            
            # Progress percentage
            progress_text = f"{int(progress * 100)}%"
            progress_surface = self.font_small.render(progress_text, True, COLORS['black'])
            card_surface.blit(progress_surface, (5, bar_y - 15))
        
        # Rotate the card surface if needed
        if rotation_angle != 0:
            card_surface = pygame.transform.rotate(card_surface, rotation_angle)
        
        # Calculate final position (center the rotated surface)
        final_rect = card_surface.get_rect(center=(x, y))
        
        # Store rect for click detection (use original unrotated dimensions for simplicity)
        click_rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
        self.spell_card_rects.append(click_rect)
        
        # Draw the card
        self.screen.blit(card_surface, final_rect)
        
        # Draw crystal placement UI if spell card is selected
        if self.selected_spell_card:
            self.draw_crystal_placement_ui(current_player)
    
    def draw_crystal_placement_ui(self, current_player):
        """Draw the crystal placement interface"""
        crystal_area_x = int(self.screen_width * 0.75)  # 75% from left
        crystal_area_y = int(self.screen_height * 0.45)  # 45% from top
        
        # Label
        label_font = pygame.font.Font(None, 20)
        crystal_label = label_font.render("Place Crystals:", True, COLORS['black'])
        self.screen.blit(crystal_label, (crystal_area_x, crystal_area_y - 25))
        
        # Crystal circles for placement
        colors = ['red', 'blue', 'green', 'yellow', 'white']
        for i, color in enumerate(colors):
            x = crystal_area_x + i * 35
            y = crystal_area_y
            
            # Draw crystal circle
            pygame.draw.circle(self.screen, COLORS[color], (x + 15, y + 15), 15)
            pygame.draw.circle(self.screen, COLORS['black'], (x + 15, y + 15), 15, 2)
            
            # Show requirement and current count
            required = self.selected_spell_card.cost.get(color, 0)
            placed = self.selected_spell_card.crystals_used.get(color, 0)
            
            if required > 0:
                progress_text = f"{placed}/{required}"
                text_color = COLORS['green'] if placed >= required else COLORS['black']
                progress_surface = self.font_small.render(progress_text, True, text_color)
                self.screen.blit(progress_surface, (x, y + 35))
    
    def draw_game_status_panel(self):
        """Draw the ticker tape and all player statuses at the bottom."""
        panel_height = int(self.screen_height * 0.18)  # 18% of screen height
        panel_y = self.screen_height - panel_height - 10
        panel_width = int(self.screen_width * 0.65)  # 65% of screen width
        
        panel_rect = pygame.Rect(10, panel_y, panel_width, panel_height)
        pygame.draw.rect(self.screen, COLORS['white'], panel_rect)
        pygame.draw.rect(self.screen, COLORS['black'], panel_rect, 2)

        # --- Draw Ticker Tape (Left Side) ---
        log_width = int(panel_width * 0.6)  # 60% of panel width
        log_area_rect = pygame.Rect(panel_rect.x + 10, panel_rect.y + 10, 
                                   log_width, panel_height - 20)
        
        log_title = self.font_medium.render("Action Log", True, COLORS['black'])
        self.screen.blit(log_title, (log_area_rect.x, log_area_rect.y))
        
        # Display the last 5 log entries
        if hasattr(self.game, 'action_log'):
            log_entries = list(self.game.action_log)[-5:]
            y_offset = log_area_rect.bottom - 20
            for entry in reversed(log_entries):
                log_text = self.font_small.render(entry, True, COLORS['dark_grey'])
                self.screen.blit(log_text, (log_area_rect.x + 5, y_offset))
                y_offset -= 18
                if y_offset < log_area_rect.y + 20:
                    break

        # --- Draw All Player Status (Right Side) ---
        status_width = int(panel_width * 0.35)  # 35% of panel width
        status_area_rect = pygame.Rect(panel_rect.x + log_width + 20, panel_rect.y + 10, 
                                      status_width, panel_height - 20)
        
        status_title = self.font_medium.render("All Wizards", True, COLORS['black'])
        self.screen.blit(status_title, (status_area_rect.x, status_area_rect.y))

        y_offset = status_area_rect.y + 25
        for player in self.game.players:
            # Player Name and Health
            player_color = COLORS.get(player.color, COLORS['black'])
            status_text = f"{player.color.title()}: {player.health}/{player.max_health} HP"
            text_surface = self.font_small.render(status_text, True, player_color)
            self.screen.blit(text_surface, (status_area_rect.x, y_offset))
            
            # Crystal Counts
            x_offset = status_area_rect.x + 120
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
        # Create semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.fill(COLORS['black'])
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0, 0))
        
        # Game over text
        game_over_font = pygame.font.Font(None, int(self.screen_height * 0.08))
        game_over_text = game_over_font.render("GAME OVER", True, COLORS['white'])
        game_over_rect = game_over_text.get_rect(center=(self.screen_width // 2, 
                                                        self.screen_height // 2 - 100))
        self.screen.blit(game_over_text, game_over_rect)
        
        # Winner text
        winner_font = pygame.font.Font(None, int(self.screen_height * 0.05))
        winner = self.game.get_winner()
        if winner:
            winner_text = winner_font.render(f"{winner.color.title()} Wizard Wins!", 
                                           True, COLORS['gold'])
            winner_rect = winner_text.get_rect(center=(self.screen_width // 2, 
                                                      self.screen_height // 2))
            self.screen.blit(winner_text, winner_rect)


def main():    # Simple test to run the GUI with a sample game
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
