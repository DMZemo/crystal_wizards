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
from ui import Button, HighlightManager, SoundManager, ActionPanel

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
        self.sound_manager = SoundManager()
        self.action_panel = ActionPanel(850, 280, self.font_medium)
        
        # Load sounds (optional - will fail gracefully if files don't exist)
        try:
            self.sound_manager.load_sound('click', 'assets/click.wav')
        except:
            pass  # Sound files are optional
        
        # Current action state
        self.current_action_mode = None  # 'move', 'mine', 'cast', or None
        
        # Position coordinates cache
        self.position_coords = {}
        self.calculate_position_coordinates()
    
    def calculate_position_coordinates(self):
        """Pre-calculate screen coordinates for all board positions using new layout"""
        # Center circle
        self.position_coords['center'] = (self.board_center_x, self.board_center_y)
        
        # 4 rectangles at cardinal directions (North=Green, South=Yellow, East=Red, West=Blue)
        self.position_coords.update({
            'rect_north': (self.board_center_x, self.board_center_y - self.rect_distance),
            'rect_south': (self.board_center_x, self.board_center_y + self.rect_distance),
            'rect_east': (self.board_center_x + self.rect_distance, self.board_center_y),
            'rect_west': (self.board_center_x - self.rect_distance, self.board_center_y)
        })
        
        # 12 outer hexagons in a ring
        for i in range(12):
            angle_rad = math.radians(i * 30)  # 360/12 = 30 degrees apart
            x = self.board_center_x + self.outer_distance * math.cos(angle_rad)
            y = self.board_center_y + self.outer_distance * math.sin(angle_rad)
            self.position_coords[f'hex_{i}'] = (int(x), int(y))
        
        # 4 mines at cardinal directions (North=Yellow, South=Green, West=Red, East=Blue)
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
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_mouse_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    self.handle_key_press(event.key)
                
                # Handle action panel events
                self.handle_action_panel_event(event)
            
            # Handle AI turns
            current_player = self.game.get_current_player()
            if isinstance(current_player, AIWizard) and not self.game.game_over:
                pygame.time.wait(1000)  # Brief pause to show AI thinking
                self.game.execute_ai_turn(current_player)
                if self.game.current_actions >= self.game.max_actions_per_turn:
                    self.game.end_turn()
            
            self.draw()
            pygame.display.flip()
            clock.tick(60)
        
        pygame.quit()
        sys.exit()
    
    def handle_mouse_click(self, pos):
        """Handle mouse clicks on the game board and UI"""
        if self.game.game_over:
            return
        
        current_player = self.game.get_current_player()
        if isinstance(current_player, AIWizard):
            return  # Don't handle clicks during AI turn
        
        # Check if clicking on a board position
        clicked_position = self.get_position_at_coordinates(pos)
        if clicked_position:
            self.handle_board_click(clicked_position, current_player)
        
        # Check if clicking on UI elements
        self.handle_ui_click(pos, current_player)
    
    def handle_action_panel_event(self, event):
        """Handle action panel events"""
        action = self.action_panel.handle_event(event, self.game)
        current_player = self.game.get_current_player()
        
        if action == 'move_selected':
            if self.current_action_mode == 'move':
                self.current_action_mode = None
                self.highlight_manager.clear_highlights()
            else:
                self.current_action_mode = 'move'
                # Highlight adjacent empty positions
                adjacent_empty = self.game.board.get_adjacent_empty_positions(current_player.location)
                self.highlight_manager.set_move_highlights(adjacent_empty)
        
        elif action == 'mine_selected':
            if self.current_action_mode == 'mine':
                self.current_action_mode = None
                self.highlight_manager.clear_highlights()
            else:
                self.current_action_mode = 'mine'
                # Highlight mineable positions
                mineable = self.game.board.get_mineable_positions(current_player.location)
                self.highlight_manager.set_mine_highlights(mineable)
        
        elif action == 'cast_selected':
            if self.current_action_mode == 'cast':
                self.current_action_mode = None
                self.highlight_manager.clear_highlights()
            else:
                self.current_action_mode = 'cast'
                # Keep existing spell card system
        
        elif action == 'end_turn':
            self.game.end_turn()
            self.current_action_mode = None
            self.highlight_manager.clear_highlights()
            self.sound_manager.play_sound('click')
    
    def get_position_at_coordinates(self, screen_pos):
        """Find which board position was clicked"""
        click_x, click_y = screen_pos
        
        for position, (pos_x, pos_y) in self.position_coords.items():
            distance = math.sqrt((click_x - pos_x)**2 + (click_y - pos_y)**2)
            if distance <= 25:  # Click tolerance
                return position
        
        return None
    
    def handle_board_click(self, position, current_player):
        """Handle clicks on board positions"""
        if self.current_action_mode == 'move':
            # Try to move to clicked position
            if self.highlight_manager.is_highlighted(position):
                if self.game.move_player(current_player, position):
                    self.sound_manager.play_sound('click')
                    self.current_action_mode = None
                    self.highlight_manager.clear_highlights()
                    # Update highlights for new position if move button still selected
                    if self.action_panel.selected_action == 'move':
                        adjacent_empty = self.game.board.get_adjacent_empty_positions(current_player.location)
                        self.highlight_manager.set_move_highlights(adjacent_empty)
        
        elif self.current_action_mode == 'mine':
            # Try to mine at clicked position
            if self.highlight_manager.is_highlighted(position):
                if position == current_player.location:
                    # Mine current position
                    if self.game.can_mine(current_player):
                        self.game.mine_action(current_player)
                        self.sound_manager.play_sound('click')
                        self.current_action_mode = None
                        self.highlight_manager.clear_highlights()
                else:
                    # Mine adjacent position (if game supports it)
                    # For now, just clear highlights
                    self.current_action_mode = None
                    self.highlight_manager.clear_highlights()
        else:
            # Default behavior - select wizard or try basic actions
            if position == current_player.location:
                # Clicked on own wizard - could show info or do nothing
                pass
            else:
                # Try to move to clicked position (old behavior)
                if self.game.can_move(current_player):
                    if self.game.move_player(current_player, position):
                        self.sound_manager.play_sound('click')
    
    def handle_ui_click(self, pos, current_player):
        """Handle clicks on UI elements"""
        # Check spell card clicks
        card_y = 600
        for i, card in enumerate(current_player.hand):
            card_x = 850 + i * 110
            if (card_x <= pos[0] <= card_x + 100 and 
                card_y <= pos[1] <= card_y + 140):
                if card not in current_player.cards_laid_down:
                    current_player.lay_down_spell_card(i)
                break
        
        # Check laid down spell cards for crystal placement
        laid_card_y = 450
        for i, card in enumerate(current_player.cards_laid_down):
            card_x = 850 + i * 110
            if (card_x <= pos[0] <= card_x + 100 and 
                laid_card_y <= pos[1] <= laid_card_y + 140):
                self.selected_spell_card = card
                break
        
        # Check crystal placement on selected spell card
        if self.selected_spell_card:
            crystal_y = 350
            colors = ['red', 'blue', 'green', 'yellow', 'white']
            for i, color in enumerate(colors):
                crystal_x = 850 + i * 30
                if (crystal_x <= pos[0] <= crystal_x + 25 and 
                    crystal_y <= pos[1] <= crystal_y + 25):

                    # Case 1: normal color crystal clicked
                    if color != 'white' and current_player.crystals[color] > 0:
                        if self.selected_spell_card.add_crystals(color, 1, current_player):
                            break  # success

                    # Case 2: white crystal clicked - try to fulfill any unmet color or wild cost
                    elif color == 'white' and current_player.crystals['white'] > 0:
                        spell = self.selected_spell_card
                        # Try match specific unmet colors first
                        for target_color in spell.cost:
                            needed = spell.cost[target_color] - spell.crystals_used.get(target_color, 0)
                            if needed > 0:
                                # Try using white as substitute
                                if spell.add_crystals('white', 1, current_player):
                                    break  # success
                        break
                    
            # Exit loop after handling crystal placement           
        
        # Check end turn button
        if 1050 <= pos[0] <= 1150 and 50 <= pos[1] <= 90:
            self.game.end_turn()
        
        # Check cast spell button
        if 1050 <= pos[0] <= 1150 and 100 <= pos[1] <= 140:
            if self.selected_spell_card and self.selected_spell_card.is_fully_charged():
                self.game.cast_spell(current_player, self.selected_spell_card)
                self.selected_spell_card = None
    
    def handle_key_press(self, key):
        """Handle keyboard input"""
        if key == pygame.K_SPACE:
            self.game.end_turn()
        elif key == pygame.K_ESCAPE:
            self.selected_spell_card = None
    
    def draw(self):
        """Draw the entire game state"""
        self.screen.fill(COLORS['light_grey'])
        
        # Draw board
        self.draw_board()
        
        # Draw UI
        self.draw_ui()
        
        # Draw game over screen if applicable
        if self.game.game_over:
            self.draw_game_over()
    
    def draw_board(self):
        """Draw the game board with new clean layout"""
        # Draw connections first (clean lines between positions)
        self.draw_connections()
        
        # Draw highlights behind positions
        for position, coords in self.position_coords.items():
            self.highlight_manager.draw_highlight(self.screen, position, coords)
        
        # Draw positions
        for position, coords in self.position_coords.items():
            self.draw_position(position, coords)
        
        # Draw wizards
        self.draw_wizards()
    
    def draw_connections(self):
        """Draw clean lines connecting adjacent board positions"""
        drawn_connections = set()  # Avoid drawing the same line twice
        
        # Get connections from the board
        connections = getattr(self.game.board, 'connections', {})
        if hasattr(self.game.board, 'layout'):
            connections = self.game.board.layout.connections
        
        for position, adjacent_list in connections.items():
            if position in self.position_coords:
                start_pos = self.position_coords[position]
                for adjacent in adjacent_list:
                    if adjacent in self.position_coords:
                        # Create a unique identifier for this connection
                        connection_id = tuple(sorted([position, adjacent]))
                        if connection_id not in drawn_connections:
                            drawn_connections.add(connection_id)
                            end_pos = self.position_coords[adjacent]
                            pygame.draw.line(self.screen, COLORS['white'], 
                                           start_pos, end_pos, 2)
    
    def draw_position(self, position, coords):
        """Draw a single board position with correct shape and color"""
        x, y = coords
        
        # Determine position type and draw accordingly
        if position == 'center':
            # Center circle (healing springs) - white circle
            pygame.draw.circle(self.screen, COLORS['white'], (x, y), 25)
            pygame.draw.circle(self.screen, COLORS['black'], (x, y), 25, 2)
            # Add healing symbol
            pygame.draw.circle(self.screen, COLORS['light_blue'], (x, y), 15)
            text = self.font_small.render("H", True, COLORS['blue'])
            text_rect = text.get_rect(center=(x, y))
            self.screen.blit(text, text_rect)
        
        elif position.startswith('rect_'):
            # Rectangular tiles with correct colors
            color_map = {
                'rect_north': COLORS['green'],
                'rect_south': COLORS['yellow'],
                'rect_east': COLORS['red'],
                'rect_west': COLORS['blue']
            }
            color = color_map.get(position, COLORS['grey'])
            pygame.draw.rect(self.screen, color, (x-20, y-15, 40, 30))
            pygame.draw.rect(self.screen, COLORS['black'], (x-20, y-15, 40, 30), 2)
        
        elif position.startswith('hex_'):
            # Outer hexagon tiles (grey with white crystals)
            self.draw_hexagon(x, y, 20, COLORS['grey'], COLORS['black'])
            
            # Draw white crystals if present
            crystal_count = self.game.board.white_crystals.get(position, 0)
            if crystal_count > 0:
                pygame.draw.circle(self.screen, COLORS['white'], (x, y), 8)
                pygame.draw.circle(self.screen, COLORS['black'], (x, y), 8, 1)
        
        elif position.startswith('mine_'):
            # Colored mines with correct color scheme
            color_map = {
                'mine_north': COLORS['yellow'],  # North = Yellow mine
                'mine_south': COLORS['green'],   # South = Green mine
                'mine_west': COLORS['red'],      # West = Red mine
                'mine_east': COLORS['blue']      # East = Blue mine
            }
            color = color_map.get(position, COLORS['grey'])
            
            # Draw mine as large colored circle
            pygame.draw.circle(self.screen, color, (x, y), 30)
            pygame.draw.circle(self.screen, COLORS['black'], (x, y), 30, 4)
            
            # Show crystal count in center
            mine_color = self.game.board.get_mine_color_from_position(position)
            if mine_color:
                crystal_count = self.game.board.mines[mine_color]['crystals']
                text = self.font_large.render(str(crystal_count), True, COLORS['white'])
                text_rect = text.get_rect(center=(x, y))
                self.screen.blit(text, text_rect)
            
            # Add mine label above
            direction = position.split('_')[1].title()
            mine_label = f"{direction} Mine"
            label_text = self.font_small.render(mine_label, True, COLORS['black'])
            label_rect = label_text.get_rect(center=(x, y - 45))
            self.screen.blit(label_text, label_rect)
    
    def draw_hexagon(self, x, y, radius, fill_color, border_color):
        """Draw a hexagon shape"""
        points = []
        for i in range(6):
            angle = math.radians(i * 60)  # 60 degrees apart
            px = x + radius * math.cos(angle)
            py = y + radius * math.sin(angle)
            points.append((px, py))
        
        pygame.draw.polygon(self.screen, fill_color, points)
        pygame.draw.polygon(self.screen, border_color, points, 2)
    
    def draw_wizards(self):
        """Draw wizard pieces on the board; if multiple wizards occupy the same tile, display them without overlap"""
        position_wizards = {}

        # Normalize all wizard data into lists for consistent rendering
        for position, data in self.game.board.wizards_on_board.items():
            if isinstance(data, list):
                position_wizards[position] = data
            else:
                position_wizards[position] = [data]

        for position, wizards in position_wizards.items():
            if position in self.position_coords:
                x, y = self.position_coords[position]
                count = len(wizards)

                if count == 1:
                    wx, wy = x, y - 5
                    wizard = wizards[0]
                    wizard_color = getattr(wizard, 'color', 'black')
                    color = COLORS.get(wizard_color, COLORS['black'])
                    pygame.draw.circle(self.screen, color, (wx, wy), 12)
                    pygame.draw.circle(self.screen, COLORS['black'], (wx, wy), 12, 2)
                    text = self.font_small.render("W", True, COLORS['white'])
                    text_rect = text.get_rect(center=(wx, wy))
                    self.screen.blit(text, text_rect)

                elif count == 2:
                    offset = 16
                    for i, wizard in enumerate(wizards):
                        wx = x + (-offset if i == 0 else offset)
                        wy = y - 5
                        wizard_color = getattr(wizard, 'color', 'black')
                        color = COLORS.get(wizard_color, COLORS['black'])
                        pygame.draw.circle(self.screen, color, (wx, wy), 12)
                        pygame.draw.circle(self.screen, COLORS['black'], (wx, wy), 12, 2)
                        text = self.font_small.render("W", True, COLORS['white'])
                        text_rect = text.get_rect(center=(wx, wy))
                        self.screen.blit(text, text_rect)

                else:
                    # Arrange 3+ wizards in a circle around the center of the tile
                    radius = 20
                    angle_step = 360 / count
                    for i, wizard in enumerate(wizards):
                        angle_deg = i * angle_step
                        angle_rad = math.radians(angle_deg)
                        wx = x + int(radius * math.cos(angle_rad))
                        wy = y + int(radius * math.sin(angle_rad)) - 5
                        wizard_color = getattr(wizard, 'color', 'black')
                        color = COLORS.get(wizard_color, COLORS['black'])
                        pygame.draw.circle(self.screen, color, (wx, wy), 12)
                        pygame.draw.circle(self.screen, COLORS['black'], (wx, wy), 12, 2)
                        text = self.font_small.render("W", True, COLORS['white'])
                        text_rect = text.get_rect(center=(wx, wy))
                        self.screen.blit(text, text_rect)


    
    def draw_ui(self):
        """Draw the user interface"""
        # Draw turn indicator at the top
        self.draw_turn_indicator()
        
        # Draw player info panel
        self.draw_player_info()
        
        # Draw new action panel
        self.action_panel.draw(self.screen)
        
        # Draw spell cards
        self.draw_spell_cards()
        
        # Draw action buttons (old system - keep for spell casting)
        self.draw_action_buttons()
        
        # Draw turn info
        self.draw_turn_info()
    
    def draw_turn_indicator(self):
        """Draw a clear turn indicator at the top of the screen"""
        current_player = self.game.get_current_player()
        
        # Background for turn indicator
        pygame.draw.rect(self.screen, COLORS['white'], (10, 10, 780, 50))
        pygame.draw.rect(self.screen, COLORS['black'], (10, 10, 780, 50), 2)
        
        # Turn text
        turn_text = f"{current_player.color.title()} Wizard's Turn"
        if isinstance(current_player, AIWizard):
            turn_text += " (AI)"
        
        text_surface = self.font_large.render(turn_text, True, COLORS['black'])
        self.screen.blit(text_surface, (20, 25))
        
        # Action indicator
        if self.current_action_mode:
            action_text = f"Action: {self.current_action_mode.title()}"
            action_surface = self.font_medium.render(action_text, True, COLORS['blue'])
            self.screen.blit(action_surface, (400, 30))
    
    def draw_player_info(self):
        """Draw current player information"""
        current_player = self.game.get_current_player()
        
        # Player info background
        pygame.draw.rect(self.screen, COLORS['white'], (850, 50, 300, 200))
        pygame.draw.rect(self.screen, COLORS['black'], (850, 50, 300, 200), 2)
        
        y_offset = 70
        
        # Player name and color
        player_text = f"{current_player.color.title()} Wizard"
        if isinstance(current_player, AIWizard):
            player_text += " (AI)"
        text = self.font_large.render(player_text, True, COLORS['black'])
        self.screen.blit(text, (860, y_offset))
        y_offset += 30
        
        # Health
        health_text = f"Health: {current_player.health}/{current_player.max_health}"
        text = self.font_medium.render(health_text, True, COLORS['black'])
        self.screen.blit(text, (860, y_offset))
        y_offset += 25
        
        # Crystals
        crystal_text = "Crystals:"
        text = self.font_medium.render(crystal_text, True, COLORS['black'])
        self.screen.blit(text, (860, y_offset))
        y_offset += 20
        
        # Draw crystal counts with colored circles
        x_offset = 860
        for color in ['red', 'blue', 'green', 'yellow', 'white']:
            count = current_player.crystals[color]
            if count > 0:
                pygame.draw.circle(self.screen, COLORS[color], (x_offset + 10, y_offset + 10), 8)
                pygame.draw.circle(self.screen, COLORS['black'], (x_offset + 10, y_offset + 10), 8, 1)
                
                count_text = self.font_small.render(str(count), True, COLORS['black'])
                self.screen.blit(count_text, (x_offset + 25, y_offset + 5))
                x_offset += 50
        
        # Actions remaining
        y_offset += 40
        actions_text = f"Actions: {self.game.current_actions}/{self.game.max_actions_per_turn}"
        text = self.font_medium.render(actions_text, True, COLORS['black'])
        self.screen.blit(text, (860, y_offset))
        
        # Action limits
        y_offset += 20
        limits_text = f"Moves: {self.game.moves_used}/3  Mines: {self.game.mines_used}/2  Spells: {self.game.spells_cast}/1"
        text = self.font_small.render(limits_text, True, COLORS['black'])
        self.screen.blit(text, (860, y_offset))
    
    def draw_spell_cards(self):
        """Draw spell cards in hand and laid down"""
        current_player = self.game.get_current_player()
        
        # Cards in hand
        hand_label = self.font_medium.render("Hand:", True, COLORS['black'])
        self.screen.blit(hand_label, (850, 570))
        
        for i, card in enumerate(current_player.hand):
            x = 850 + i * 110
            y = 600
            self.draw_spell_card(card, x, y, in_hand=True)
        
        # Laid down cards (being charged)
        if current_player.cards_laid_down:
            laid_label = self.font_medium.render("Charging:", True, COLORS['black'])
            self.screen.blit(laid_label, (850, 420))
            
            for i, card in enumerate(current_player.cards_laid_down):
                x = 850 + i * 110
                y = 450
                selected = (card == self.selected_spell_card)
                self.draw_spell_card(card, x, y, in_hand=False, selected=selected)
        
        # Crystal placement area
        if self.selected_spell_card:
            crystal_label = self.font_medium.render("Place Crystals:", True, COLORS['black'])
            self.screen.blit(crystal_label, (850, 320))
            
            colors = ['red', 'blue', 'green', 'yellow', 'white']
            for i, color in enumerate(colors):
                x = 850 + i * 30
                y = 350
                
                # Draw crystal slot
                pygame.draw.circle(self.screen, COLORS[color], (x + 12, y + 12), 12)
                pygame.draw.circle(self.screen, COLORS['black'], (x + 12, y + 12), 12, 2)
                
                # Show required vs placed
                required = self.selected_spell_card.cost.get(color, 0)
                placed = self.selected_spell_card.crystals_used.get(color, 0)
                
                if required > 0:
                    text = self.font_small.render(f"{placed}/{required}", True, COLORS['black'])
                    self.screen.blit(text, (x, y + 30))
    
    def draw_spell_card(self, card, x, y, in_hand=True, selected=False):
        """Draw a single spell card"""
        # Card background
        card_color = COLORS['white'] if not selected else COLORS['light_blue']
        pygame.draw.rect(self.screen, card_color, (x, y, 100, 140))
        border_color = COLORS['gold'] if selected else COLORS['black']
        pygame.draw.rect(self.screen, border_color, (x, y, 100, 140), 2)
        
        # Damage value
        damage_text = self.font_large.render(str(card.get_damage()), True, COLORS['black'])
        damage_rect = damage_text.get_rect(center=(x + 50, y + 20))
        self.screen.blit(damage_text, damage_rect)
        
        # Crystal costs
        y_offset = y + 40
        for color, cost in card.cost.items():
            if cost > 0:
                # Draw crystal
                pygame.draw.circle(self.screen, COLORS[color], (x + 20, y_offset), 8)
                pygame.draw.circle(self.screen, COLORS['black'], (x + 20, y_offset), 8, 1)
                
                # Draw cost number
                cost_text = self.font_small.render(str(cost), True, COLORS['black'])
                self.screen.blit(cost_text, (x + 35, y_offset - 8))
                
                y_offset += 20
        
        # Show charging progress if laid down
        if not in_hand:
            progress = card.get_charging_progress()
            progress_text = f"{int(progress * 100)}%"
            text = self.font_small.render(progress_text, True, COLORS['black'])
            self.screen.blit(text, (x + 5, y + 120))
            
            # Progress bar
            bar_width = 90
            bar_height = 8
            pygame.draw.rect(self.screen, COLORS['grey'], (x + 5, y + 105, bar_width, bar_height))
            pygame.draw.rect(self.screen, COLORS['green'], (x + 5, y + 105, int(bar_width * progress), bar_height))
    
    def draw_action_buttons(self):
        """Draw action buttons"""
        # End Turn button
        pygame.draw.rect(self.screen, COLORS['red'], (1050, 50, 100, 40))
        pygame.draw.rect(self.screen, COLORS['black'], (1050, 50, 100, 40), 2)
        end_turn_text = self.font_medium.render("End Turn", True, COLORS['white'])
        end_turn_rect = end_turn_text.get_rect(center=(1100, 70))
        self.screen.blit(end_turn_text, end_turn_rect)
        
        # Cast Spell button (only if spell is selected and charged)
        if (self.selected_spell_card and self.selected_spell_card.is_fully_charged() 
            and self.game.can_cast_spell(self.game.get_current_player())):
            pygame.draw.rect(self.screen, COLORS['blue'], (1050, 100, 100, 40))
            pygame.draw.rect(self.screen, COLORS['black'], (1050, 100, 100, 40), 2)
            cast_text = self.font_medium.render("Cast Spell", True, COLORS['white'])
            cast_rect = cast_text.get_rect(center=(1100, 120))
            self.screen.blit(cast_text, cast_rect)
    
    def draw_turn_info(self):
        """Draw turn and game status information"""
        # Current turn info
        current_player = self.game.get_current_player()
        turn_text = f"Current Turn: {current_player.color.title()}"
        if isinstance(current_player, AIWizard):
            turn_text += " (AI thinking...)"
        
        text = self.font_large.render(turn_text, True, COLORS['black'])
        self.screen.blit(text, (50, 50))
        
        # Player status summary
        y_offset = 100
        for player in self.game.players:
            if player.health > 0:
                status_text = f"{player.color.title()}: {player.health} HP, {player.get_total_crystals()} crystals"
                color = COLORS[player.color]
                text = self.font_medium.render(status_text, True, color)
                self.screen.blit(text, (50, y_offset))
                y_offset += 25
    
    def draw_game_over(self):
        """Draw game over screen"""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(128)
        overlay.fill(COLORS['black'])
        self.screen.blit(overlay, (0, 0))
        
        # Game over text
        game_over_text = self.font_large.render("GAME OVER", True, COLORS['white'])
        game_over_rect = game_over_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 - 50))
        self.screen.blit(game_over_text, game_over_rect)
        
        # Winner text
        if self.game.winner:
            winner_text = f"{self.game.winner.color.title()} Wizard Wins!"
            winner_color = COLORS[self.game.winner.color]
        else:
            winner_text = "No Winner!"
            winner_color = COLORS['white']
        
        text = self.font_large.render(winner_text, True, winner_color)
        text_rect = text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        self.screen.blit(text, text_rect)
        
        # Instructions
        instruction_text = "Press ESC to exit"
        text = self.font_medium.render(instruction_text, True, COLORS['white'])
        text_rect = text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 50))
        self.screen.blit(text, text_rect)
