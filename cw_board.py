"""
Crystal Wizards - Game Board Implementation
REFACTORED VERSION with New Clean Board Layout

MAJOR CHANGES MADE:
1. **New Board Structure**:
   - Center circle (healing springs) - unchanged functionality
   - 4 rectangles at cardinal directions: North=Green, South=Yellow, East=Red, West=Blue
   - 12 outer hexagons (was 10 pentagons) - better spacing and visual appeal
   - 4 mines at cardinal directions: North=Yellow mine, South=Green mine, West=Red mine, East=Blue mine

2. **Clean Connection System**:
   - Replaced messy criss-crossed connections with logical shortest-path connections
   - Center connects only to 4 rectangles (cardinal directions)
   - Each rectangle connects to center + 3 spatially adjacent hexagons
   - Hexagons form a clean ring - each connects to immediate neighbors
   - Mines connect to specific hexagons at cardinal positions

3. **Color Scheme Update**:
   - Mine colors now match opposite rectangles for strategic balance
   - Yellow mine (North) teleports to Yellow rectangle (South)
   - Green mine (South) teleports to Green rectangle (North)
   - Red mine (West) teleports to Red rectangle (East)
   - Blue mine (East) teleports to Blue rectangle (West)

4. **Improved Code Structure**:
   - Uses NewBoardLayout class for clean separation of concerns
   - Maintains backward compatibility with existing game logic
   - All connections are now logically calculated rather than hardcoded
"""

import math
from cw_entities import Die, HealingHotSpringsDie
from new_board_layout import NewBoardLayout, convert_old_to_new_position, convert_new_to_old_position
import pygame
from pygame.locals import QUIT, MOUSEBUTTONDOWN, KEYDOWN, K_ESCAPE

class GameBoard:
    def __init__(self):
        # NEW: Use the clean board layout system
        self.layout = NewBoardLayout()
        self.wizards_on_board = {}
        
        # Mine data - updated for new color scheme
        # North=Yellow mine, South=Green mine, West=Red mine, East=Blue mine
        self.mines = {
            'yellow': {'crystals': 9, 'position': 'mine_north'},
            'green': {'crystals': 9, 'position': 'mine_south'},
            'red': {'crystals': 9, 'position': 'mine_west'},
            'blue': {'crystals': 9, 'position': 'mine_east'}
        }
        
        # Special positions - updated for new layout
        self.healing_springs_position = 'center'
        self.colored_rectangles = {
            'red': 'rect_east',
            'blue': 'rect_west', 
            'green': 'rect_north',
            'yellow': 'rect_south',
        }
        
        # White crystals on grey hexagon tiles
        self.white_crystals = {}
        
        # Legacy compatibility - expose layout data through old interface
        self.positions = {}
        self.connections = {}
        
    def initialize_board(self):
        """Set up the board layout and connections using new clean system"""
        # Initialize the new layout system
        self.layout.initialize_layout()
        
        # Expose layout data through legacy interface for compatibility
        self.positions = self.layout.positions.copy()
        self.connections = self.layout.connections.copy()
        
        # Initialize white crystals on outer hexagons
        self.place_initial_crystals()
        
    def place_initial_crystals(self):
        """Place initial white crystals on outer hexagon tiles"""
        for i in range(12):
            hex_id = f'hex_{i}'
            self.white_crystals[hex_id] = 1
    
    def get_outer_ring_positions(self):
        """Get all outer ring positions for wizard placement"""
        return self.layout.get_outer_ring_positions()
    
    def is_adjacent(self, pos1, pos2):
        """Check if two positions are adjacent using new clean connections"""
        return self.layout.is_adjacent(pos1, pos2)
    
    def get_adjacent_positions(self, position):
        """Get all positions adjacent to the given position"""
        return self.layout.get_connections(position)
    
    def get_adjacent_empty_positions(self, position):
        """Get adjacent positions that are not occupied by wizards"""
        adjacent_positions = self.get_adjacent_positions(position)
        return [pos for pos in adjacent_positions]
    
    def get_mineable_positions(self, position):
        """Get positions that have crystals available for mining"""
        # Include current position if it has crystals
        mineable = []
        if self.has_crystals_at_position(position):
            mineable.append(position)
        
        # Include adjacent positions with crystals
        adjacent_positions = self.get_adjacent_positions(position)
        for pos in adjacent_positions:
            if self.has_crystals_at_position(pos):
                mineable.append(pos)
        
        return mineable
    
 
    def is_position_occupied(self, position):
        """Check if a position is occupied by a wizard"""
        return position in self.wizards_on_board
    
    def get_wizard_at_position(self, position):
        """Get the list of wizards at a specific position"""
        return self.wizards_on_board.get(position)
    
    def add_wizard_to_position(self, position, wizard):
        """
        Add a wizard to a position. Ensures wizards are stored in a list
        and prevents the same wizard from being added twice.
        """
        if position not in self.wizards_on_board:
            self.wizards_on_board[position] = []
        
        if wizard not in self.wizards_on_board[position]:
            self.wizards_on_board[position].append(wizard)

    def set_wizard_at_position(self, position, wizard):
        """
        Corrected: Places a wizard at a given position. If other wizards are
        present, this wizard is added to the list for that tile. This ensures
        multiple wizards can occupy the same space without overwriting each other.
        """
        # This method was the cause of the bug. It now correctly calls
        # add_wizard_to_position to append to the list instead of overwriting it.
        self.add_wizard_to_position(position, wizard)
    
    def remove_wizard_from_position(self, position, wizard):
        """
        Corrected: Remove a specific wizard from a position.
        The original implementation deleted all wizards at the location.
        NOTE: The calling code (in your game logic) must be updated to pass the wizard object,
        e.g., self.board.remove_wizard_from_position(old_position, player)
        """
        # Check if the position exists and the wizard is actually there
        if position in self.wizards_on_board and wizard in self.wizards_on_board[position]:
            # Remove the specific wizard from the list
            self.wizards_on_board[position].remove(wizard)
            
            # If the list at the position becomes empty, remove the key to keep the dictionary clean.
            if not self.wizards_on_board[position]:
                del self.wizards_on_board[position]

    def is_healing_springs(self, position):
        """Check if position is the healing springs"""
        return position == 'center'
    
    def is_mine(self, position):
        """Check if position is a crystal mine"""
        return position.startswith('mine_')
    
    def has_crystals_at_position(self, position):
        """Check if position has crystals available for mining"""
        if position in self.white_crystals and self.white_crystals[position] > 0:
            return True
        if position.startswith('mine_'):
            mine_color = self._get_mine_color_from_position(position)
            return self.mines[mine_color]['crystals'] > 0
        return position == 'center'  # Healing springs always available
    
    def get_mine_color_from_position(self, mine_position):
        """Get the color of crystals at a mine position"""
        if not isinstance(mine_position, str):
            return None
        
        mine_color_map = {
            'mine_north': 'yellow',
            'mine_south': 'green', 
            'mine_west': 'red',
            'mine_east': 'blue'
        }
        return mine_color_map.get(mine_position)
    
    def use_blood_magic_prompt(self, wizard, mine_color):
        """
        Prompt the wizard to use blood magic for mining.
        Integrated with Pygame GUI: shows a clickable dialog box.
        """

        screen = pygame.display.get_surface()
        font = pygame.font.Font(None, 36)

        dialog_width, dialog_height = 400, 160
        screen_rect = screen.get_rect()
        dialog_rect = pygame.Rect(
            (screen_rect.centerx - dialog_width // 2, screen_rect.centery - dialog_height // 2),
            (dialog_width, dialog_height)
        )

        yes_button = pygame.Rect(dialog_rect.x + 50, dialog_rect.bottom - 60, 100, 40)
        no_button = pygame.Rect(dialog_rect.right - 150, dialog_rect.bottom - 60, 100, 40)

        while True:
            pygame.draw.rect(screen, (240, 240, 240), dialog_rect)
            pygame.draw.rect(screen, (0, 0, 0), dialog_rect, 2)

            title = font.render(f"{wizard.name}, use Blood Magic?", True, (0, 0, 0))
            screen.blit(title, (dialog_rect.x + 20, dialog_rect.y + 20))

            pygame.draw.rect(screen, (0, 200, 0), yes_button)
            pygame.draw.rect(screen, (0, 0, 0), yes_button, 2)
            yes_text = font.render("Yes", True, (255, 255, 255))
            screen.blit(yes_text, yes_text.get_rect(center=yes_button.center))

            pygame.draw.rect(screen, (200, 0, 0), no_button)
            pygame.draw.rect(screen, (0, 0, 0), no_button, 2)
            no_text = font.render("No", True, (255, 255, 255))
            screen.blit(no_text, no_text.get_rect(center=no_button.center))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    exit()
                elif event.type == MOUSEBUTTONDOWN:
                    if yes_button.collidepoint(event.pos):
                        return True
                    elif no_button.collidepoint(event.pos):
                        return False
                elif event.type == KEYDOWN and event.key == K_ESCAPE:
                    return False
        

    def mine_at_position(self, position, wizard):
        """Perform mining action at a position"""
        if position == 'center':
            healing_roll = HealingHotSpringsDie.roll()
            wizard.heal(healing_roll)

            outer_positions = [pos for pos in self.get_outer_ring_positions()]
            if outer_positions:
                import random
                teleport_pos = random.choice(outer_positions)
                return ({}, teleport_pos)
            return ({}, None)

        elif position.startswith('mine_'):
            mine_color = self._get_mine_color_from_position(position)
            mine_crystals = self.mines[mine_color]['crystals']

            if mine_crystals <= 0:
                return None

            use_blood_magic = False
            if wizard.color == mine_color:
                if hasattr(wizard, 'use_blood_magic_prompt'):
                    use_blood_magic = wizard.use_blood_magic_prompt(mine_color)
                else:
                    use_blood_magic = True  # default AI logic

            if use_blood_magic:
                die1 = Die.roll()
                die2 = Die.roll()

                if hasattr(wizard, 'choose_blood_magic_dice'):
                    health_die, mine_die = wizard.choose_blood_magic_dice(die1, die2)
                else:
                    if die1 <= mine_crystals and die2 <= mine_crystals:
                        mine_die = max(die1, die2)
                        health_die = min(die1, die2)
                    elif die1 <= mine_crystals:
                        mine_die = die1
                        health_die = die2
                    elif die2 <= mine_crystals:
                        mine_die = die2
                        health_die = die1
                    else:
                        mine_die = max(die1, die2)
                        health_die = min(die1, die2)

                wizard.heal(health_die)
            else:
                mine_die = Die.roll()

            mine_roll = mine_die

            if mine_roll <= mine_crystals:
                crystals_gained = {mine_color: mine_roll}
                self.mines[mine_color]['crystals'] -= mine_roll
                teleport_pos = self.colored_rectangles[mine_color]
                return (crystals_gained, teleport_pos)

            return None

        elif position in self.white_crystals and self.white_crystals[position] > 0:
            self.white_crystals[position] -= 1
            return ({'white': 1}, None)

        return None

    
    def add_white_crystals_to_empty_tiles(self, amount):
        """Add white crystals back to empty grey hexagon tiles"""
        empty_tiles = [pos for pos in self.white_crystals.keys() 
                      if self.white_crystals[pos] == 0]
        
        import random
        for _ in range(amount):
            if empty_tiles:
                tile = random.choice(empty_tiles)
                self.white_crystals[tile] = 1
                empty_tiles.remove(tile)
    
    def distance_to_healing_springs(self, position):
        """Calculate distance to healing springs using BFS on clean connections"""
        if position == 'center':
            return 0
        
        visited = set()
        queue = [(position, 0)]
        
        while queue:
            current_pos, distance = queue.pop(0)
            if current_pos in visited:
                continue
            visited.add(current_pos)
            
            if current_pos == 'center':
                return distance
            
            for adjacent in self.get_adjacent_positions(current_pos):
                if adjacent not in visited:
                    queue.append((adjacent, distance + 1))
        
        return float('inf')  # Should never happen in connected graph
    
    def get_position_info(self, position):
        """Get detailed information about a position"""
        info = self.layout.get_position_info(position).copy()
        
        if position in self.white_crystals:
            info['white_crystals'] = self.white_crystals[position]
        
        if position in self.wizards_on_board:
            info['wizard'] = self.wizards_on_board[position]
        
        return info
    
    def is_fully_connected(self):
        """Test if the board graph is fully connected using new layout system"""
        return self.layout.validate_connectivity()
    
    @property 
    def mine_spaces(self):
        """Get all mine position IDs"""
        return self.layout.get_mine_positions()
    
    def _get_mine_color_from_position(self, mine_position):
        """Internal helper to get mine color from position"""
        return self.get_mine_color_from_position(mine_position)
    
    def get_colored_rectangle_position(self, color):
        """Get the position of the colored rectangle for a given color"""
        return self.colored_rectangles.get(color)
