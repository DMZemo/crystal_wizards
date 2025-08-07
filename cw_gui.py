"""
Crystal Wizards - Pygame GUI Implementation
REFACTORED VERSION with New Clean Board Layout

MAJOR VISUAL CHANGES MADE:
1. **New Shape System**:
   - Center: Circle (was pentagon) - cleaner, more intuitive
   - Rectangles: Properly colored rectangles at cardinal directions
   - Outer ring: Hexagons (was pentagons) - 12 positions instead of 10
   - Mines: Large colored circles with clear labels

2. **Clean Connection Drawing**:
   - Connections now draw as clean straight lines
   - No more criss-crossed messy connections
   - Lines connect logically between adjacent positions only

3. **Updated Color Scheme**:
   - Rectangles: North=Green, South=Yellow, East=Red, West=Blue
   - Mines: North=Yellow, South=Green, West=Red, East=Blue
   - All colors now follow logical cardinal direction mapping

4. **Improved Visual Clarity**:
   - Better spacing between elements
   - Clearer shape differentiation (circle, rectangle, hexagon)
   - Enhanced mine visibility with crystal counts
   - Proper highlighting system for player actions
"""

import pygame
import math
import sys
from cw_entities import AIWizard
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
        self.game = game
        self.screen_width = 1200
        self.screen_height = 800
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Crystal Wizards")
        
        # Fonts
        pygame.font.init()
        self.font_small = pygame.font.Font(None, 20)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_large = pygame.font.Font(None, 32)
        
        # Board layout parameters
        self.board_center_x = 400
        self.board_center_y = 400
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
        self.action_panel = ActionPanel(850, 280, self.font_medium)
        
        self.dice_manager = DiceRollManager(self.screen, self.font_large)
        self.is_dice_rolling = False
        self.pending_action = None
        
        self.sound_manager.load_sounds()
        
        self.current_action_mode = None
        
        self.position_coords = {}
        self.calculate_position_coordinates()
    
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
                adjacent_empty = self.game.board.get_adjacent_empty_positions(current_player.location)
                self.highlight_manager.set_move_highlights(adjacent_empty)
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
        if self.current_action_mode == 'move':
            if self.highlight_manager.is_highlighted(position):
                if self.game.move_player(current_player, position):
                    self.sound_manager.play_move()
                    self.current_action_mode = None
                    self.highlight_manager.clear_highlights()
                    if self.action_panel.selected_action == 'move':
                        adjacent_empty = self.game.board.get_adjacent_empty_positions(current_player.location)
                        self.highlight_manager.set_move_highlights(adjacent_empty)
        
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
            if self.game.mine_white_crystal(player, position):
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

        if success:
            if player.health > old_health:
                self.sound_manager.play_heal()
            
            if player.location != old_location:
                self.sound_manager.play_teleport()
            elif position != 'center':
                self.sound_manager.play_mine()
        
        self.pending_action = None
        self.current_action_mode = None
        self.highlight_manager.clear_highlights()

    def handle_ui_click(self, pos, current_player):
        """Handle clicks on UI elements"""
        card_y = 600
        for i, card in enumerate(current_player.hand):
            card_x = 850 + i * 110
            if (card_x <= pos[0] <= card_x + 100 and 
                card_y <= pos[1] <= card_y + 140):
                if card not in current_player.cards_laid_down:
                    current_player.lay_down_spell_card(i)
                break
        
        laid_card_y = 450
        for i, card in enumerate(current_player.cards_laid_down):
            card_x = 850 + i * 110
            if (card_x <= pos[0] <= card_x + 100 and 
                laid_card_y <= pos[1] <= laid_card_y + 140):
                self.selected_spell_card = card
                break
        
        if self.selected_spell_card:
            crystal_y = 350
            colors = ['red', 'blue', 'green', 'yellow', 'white']
            for i, color in enumerate(colors):
                crystal_x = 850 + i * 30
                if (crystal_x <= pos[0] <= crystal_x + 25 and 
                    crystal_y <= pos[1] <= crystal_y + 25):

                    if color != 'white' and current_player.crystals[color] > 0:
                        if self.selected_spell_card.add_crystals(color, 1, current_player):
                            self.sound_manager.play_charge()
                            break

                    elif color == 'white' and current_player.crystals['white'] > 0:
                        spell = self.selected_spell_card
                        for target_color in spell.cost:
                            needed = spell.cost[target_color] - spell.crystals_used.get(target_color, 0)
                            if needed > 0:
                                if spell.add_crystals('white', 1, current_player):
                                    self.sound_manager.play_charge()
                                    break
                        break
        
        if 1050 <= pos[0] <= 1150 and 50 <= pos[1] <= 90:
            self.game.end_turn()
            self.sound_manager.play_sound('click', 0.8)
        
        if 1050 <= pos[0] <= 1150 and 100 <= pos[1] <= 140:
            if self.selected_spell_card and self.selected_spell_card.is_fully_charged():
                damage = self.selected_spell_card.get_damage()
                if self.game.cast_spell(current_player, self.selected_spell_card):
                    self.sound_manager.play_spell_cast(damage)
                    self.selected_spell_card = None
    
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
        
        self.draw_board()
        self.draw_ui()
        
        if self.game.game_over:
            self.draw_game_over()
    
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
        self.draw_spell_cards()
        self.draw_action_buttons()
        # FIXED: Draw the new status panel
        self.draw_game_status_panel()
    
    def draw_turn_indicator(self):
        """Draw a clear turn indicator at the top of the screen"""
        current_player = self.game.get_current_player()
        
        pygame.draw.rect(self.screen, COLORS['white'], (10, 10, 780, 50))
        pygame.draw.rect(self.screen, COLORS['black'], (10, 10, 780, 50), 2)
        
        turn_text = f"{current_player.color.title()} Wizard's Turn"
        if isinstance(current_player, AIWizard):
            turn_text += " (AI)"
        
        text_surface = self.font_large.render(turn_text, True, COLORS['black'])
        self.screen.blit(text_surface, (20, 25))
        
        if self.current_action_mode:
            action_text = f"Action: {self.current_action_mode.title()}"
            action_surface = self.font_medium.render(action_text, True, COLORS['blue'])
            self.screen.blit(action_surface, (400, 30))
    
    def draw_player_info(self):
        """Draw current player information"""
        current_player = self.game.get_current_player()
        
        pygame.draw.rect(self.screen, COLORS['white'], (850, 50, 300, 200))
        pygame.draw.rect(self.screen, COLORS['black'], (850, 50, 300, 200), 2)
        
        y_offset = 60
        player_text = f"{current_player.color.title()} Wizard"
        if isinstance(current_player, AIWizard): player_text += " (AI)"
        text = self.font_large.render(player_text, True, COLORS['black'])
        self.screen.blit(text, (860, y_offset))
        y_offset += 35
        
        health_text = f"Health: {current_player.health}/{current_player.max_health}"
        text = self.font_medium.render(health_text, True, COLORS['black'])
        self.screen.blit(text, (860, y_offset))
        y_offset += 25
        
        crystal_text = "Crystals:"
        text = self.font_medium.render(crystal_text, True, COLORS['black'])
        self.screen.blit(text, (860, y_offset))
        y_offset += 25
        
        x_offset = 860
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
        self.screen.blit(text, (860, y_offset))
        
        y_offset += 20
        limits_text = f"Moves: {self.game.moves_used}/3  Mines: {self.game.mines_used}/2  Spells: {self.game.spells_cast}/1"
        text = self.font_small.render(limits_text, True, COLORS['black'])
        self.screen.blit(text, (860, y_offset))
    
    def draw_spell_cards(self):
        """Draw spell cards in hand and laid down"""
        current_player = self.game.get_current_player()
        
        hand_label = self.font_medium.render("Hand:", True, COLORS['black'])
        self.screen.blit(hand_label, (850, 570))
        
        for i, card in enumerate(current_player.hand):
            x = 850 + i * 110
            y = 600
            self.draw_spell_card(card, x, y, in_hand=True)
        
        if current_player.cards_laid_down:
            laid_label = self.font_medium.render("Charging:", True, COLORS['black'])
            self.screen.blit(laid_label, (850, 420))
            
            for i, card in enumerate(current_player.cards_laid_down):
                x = 850 + i * 110
                y = 450
                selected = (card == self.selected_spell_card)
                self.draw_spell_card(card, x, y, in_hand=False, selected=selected)
        
        if self.selected_spell_card:
            crystal_label = self.font_medium.render("Place Crystals:", True, COLORS['black'])
            self.screen.blit(crystal_label, (850, 320))
            
            colors = ['red', 'blue', 'green', 'yellow', 'white']
            for i, color in enumerate(colors):
                x = 850 + i * 30
                y = 350
                pygame.draw.circle(self.screen, COLORS[color], (x + 12, y + 12), 12)
                pygame.draw.circle(self.screen, COLORS['black'], (x + 12, y + 12), 12, 2)
                
                required = self.selected_spell_card.cost.get(color, 0)
                placed = self.selected_spell_card.crystals_used.get(color, 0)
                
                if required > 0:
                    text = self.font_small.render(f"{placed}/{required}", True, COLORS['black'])
                    self.screen.blit(text, (x, y + 30))
    
    def draw_spell_card(self, card, x, y, in_hand=True, selected=False):
        """Draw a single spell card"""
        card_color = COLORS['white'] if not selected else COLORS['light_blue']
        pygame.draw.rect(self.screen, card_color, (x, y, 100, 140))
        border_color = COLORS['gold'] if selected else COLORS['black']
        pygame.draw.rect(self.screen, border_color, (x, y, 100, 140), 2)
        
        damage_text = self.font_large.render(str(card.get_damage()), True, COLORS['black'])
        damage_rect = damage_text.get_rect(center=(x + 50, y + 20))
        self.screen.blit(damage_text, damage_rect)
        
        y_offset = y + 40
        for color, cost in card.cost.items():
            if cost > 0:
                pygame.draw.circle(self.screen, COLORS.get(color, COLORS['wild']), (x + 20, y_offset), 8)
                pygame.draw.circle(self.screen, COLORS['black'], (x + 20, y_offset), 8, 1)
                cost_text = self.font_small.render(str(cost), True, COLORS['black'])
                self.screen.blit(cost_text, (x + 35, y_offset - 8))
                y_offset += 20
        
        if not in_hand:
            progress = card.get_charging_progress()
            progress_text = f"{int(progress * 100)}%"
            text = self.font_small.render(progress_text, True, COLORS['black'])
            self.screen.blit(text, (x + 5, y + 120))
            
            bar_width, bar_height = 90, 8
            pygame.draw.rect(self.screen, COLORS['grey'], (x + 5, y + 105, bar_width, bar_height))
            pygame.draw.rect(self.screen, COLORS['green'], (x + 5, y + 105, int(bar_width * progress), bar_height))
    
    def draw_action_buttons(self):
        """Draw action buttons (Legacy UI elements, kept for compatibility)"""
        pygame.draw.rect(self.screen, COLORS['red'], (1050, 50, 100, 40))
        pygame.draw.rect(self.screen, COLORS['black'], (1050, 50, 100, 40), 2)
        end_turn_text = self.font_medium.render("End Turn", True, COLORS['white'])
        end_turn_rect = end_turn_text.get_rect(center=(1100, 70))
        self.screen.blit(end_turn_text, end_turn_rect)
        
        can_cast = (self.selected_spell_card and self.selected_spell_card.is_fully_charged() and self.game.can_cast_spell(self.game.get_current_player()))
        button_color = COLORS['blue'] if can_cast else COLORS['grey']
        pygame.draw.rect(self.screen, button_color, (1050, 100, 100, 40))
        pygame.draw.rect(self.screen, COLORS['black'], (1050, 100, 100, 40), 2)
        cast_text = self.font_medium.render("Cast Spell", True, COLORS['white'])
        cast_rect = cast_text.get_rect(center=(1100, 120))
        self.screen.blit(cast_text, cast_rect)

    def draw_game_status_panel(self):
        """FIXED: Draw the ticker tape and all player statuses at the bottom."""
        panel_rect = pygame.Rect(10, 650, 820, 140)
        pygame.draw.rect(self.screen, COLORS['white'], panel_rect)
        pygame.draw.rect(self.screen, COLORS['black'], panel_rect, 2)

        # --- Draw Ticker Tape (Left Side) ---
        log_area_rect = pygame.Rect(panel_rect.x + 10, panel_rect.y + 10, 480, 120)
        log_title = self.font_medium.render("Action Log", True, COLORS['black'])
        self.screen.blit(log_title, (log_area_rect.x, log_area_rect.y))
        
        # Display the last 5 log entries
        log_entries = list(self.game.action_log)[-5:]
        y_offset = log_area_rect.bottom - 20
        for entry in reversed(log_entries):
            log_text = self.font_small.render(entry, True, COLORS['dark_grey'])
            self.screen.blit(log_text, (log_area_rect.x + 5, y_offset))
            y_offset -= 18
            if y_offset < log_area_rect.y + 20:
                break

        # --- Draw All Player Status (Right Side) ---
        status_area_rect = pygame.Rect(panel_rect.x + 510, panel_rect.y + 10, 300, 120)
        status_title = self.font_medium.render("All Wizards", True, COLORS['black'])
        self.screen.blit(status_title, (status_area_rect.x, status_area_rect.y))

        y_offset = status_area_rect.y + 30
        for player in self.game.players:
            # Player Name and Health
            player_color = COLORS.get(player.color, COLORS['black'])
            status_text = f"{player.color.title()}: {player.health}/{player.max_health} HP"
            text_surface = self.font_small.render(status_text, True, player_color)
            self.screen.blit(text_surface, (status_area_rect.x, y_offset))
            
            # Crystal Counts
            x_offset = status_area_rect.x + 150
            for crystal_color_str in ['red', 'blue', 'green', 'yellow', 'white']:
                count = player.crystals.get(crystal_color_str, 0)
                if count > 0:
                    crystal_color = COLORS[crystal_color_str]
                    pygame.draw.circle(self.screen, crystal_color, (x_offset, y_offset + 8), 6)
                    pygame.draw.circle(self.screen, COLORS['black'], (x_offset, y_offset + 8), 6, 1)
                    count_surf = self.font_small.render(str(count), True, COLORS['black'])
                    self.screen.blit(count_surf, (x_offset + 8, y_offset))
                    x_offset += 30

            y_offset += 25
            if y_offset > status_area_rect.bottom - 15:
                break

    def draw_game_over(self):
        """Draw game over screen"""
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        game_over_text = self.font_large.render("GAME OVER", True, COLORS['white'])
        game_over_rect = game_over_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 - 50))
        self.screen.blit(game_over_text, game_over_rect)
        
        winner_text = "No Winner!"
        winner_color = COLORS['white']
        if self.game.winner:
            winner_text = f"{self.game.winner.color.title()} Wizard Wins!"
            winner_color = COLORS[self.game.winner.color]
        
        text = self.font_large.render(winner_text, True, winner_color)
        text_rect = text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        self.screen.blit(text, text_rect)
        
        instruction_text = "Press ESC to exit"
        text = self.font_medium.render(instruction_text, True, COLORS['white'])
        text_rect = text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 50))
        self.screen.blit(text, text_rect)