"""
Crystal Wizards - Game Board Implementation
Refactored to use positions[<pos>]['crystals'] as single source of truth
for white crystals (hex tiles), removing duplicate white_crystals usage.
"""

import math
import random
import pygame
from pygame.locals import QUIT, MOUSEBUTTONDOWN, KEYDOWN, K_ESCAPE

class NewBoardLayout:
    """New board layout with clean connections and logical positioning"""

    def __init__(self):
        # Board structure:
        # - Center circle (healing springs)
        # - 4 rectangles at cardinal directions connected to center
        # - 12 outer hexagons in a ring
        # - 4 mines outside the ring at cardinal directions
        self.positions = {}
        self.connections = {}
        self.position_coordinates = {}

    def initialize_layout(self):
        """Initialize the new board layout"""
        self.create_positions()
        self.create_clean_connections()
        self.calculate_screen_coordinates()

    def create_positions(self):
        """Create all board positions with new structure"""
        # Center circle (healing springs)
        self.positions['center'] = {
            'type': 'healing_springs',
            'color': 'white',
            'shape': 'circle',
            'crystals': 0
        }

        # 4 rectangles (North=Green, South=Yellow, East=Red, West=Blue)
        rect_config = {
            'rect_north': {'color': 'green', 'direction': 'north'},
            'rect_south': {'color': 'yellow', 'direction': 'south'},
            'rect_east': {'color': 'red', 'direction': 'east'},
            'rect_west': {'color': 'blue', 'direction': 'west'}
        }
        for rect_id, config in rect_config.items():
            self.positions[rect_id] = {
                'type': 'rectangle',
                'color': config['color'],
                'shape': 'rectangle',
                'crystals': 0,
                'direction': config['direction']
            }

        # 12 outer hexagons
        for i in range(12):
            self.positions[f'hex_{i}'] = {
                'type': 'outer_hexagon',
                'color': 'grey',
                'shape': 'hexagon',
                # hex tiles start with 1 white crystal
                'crystals': 1,
                'ring_position': i
            }

        # 4 mines (North=Yellow, South=Green, West=Red, East=Blue)
        mine_config = {
            'mine_north': {'color': 'yellow', 'direction': 'north'},
            'mine_south': {'color': 'green', 'direction': 'south'},
            'mine_west': {'color': 'red', 'direction': 'west'},
            'mine_east': {'color': 'blue', 'direction': 'east'}
        }
        for mine_id, config in mine_config.items():
            self.positions[mine_id] = {
                'type': 'mine',
                'color': config['color'],
                'shape': 'circle',
                # mines are separately counted (board.mines) but keep field here for completeness
                'crystals': 0,
                'direction': config['direction']
            }

    def create_clean_connections(self):
        """Create clean, logical connections"""
        self.connections['center'] = ['rect_north', 'rect_south', 'rect_east', 'rect_west']

        rect_to_hex = {
            'rect_north': [8, 9, 10],
            'rect_east': [11, 0, 1],
            'rect_south': [2, 3, 4],
            'rect_west': [5, 6, 7]
        }

        for rect_id, hex_indices in rect_to_hex.items():
            self.connections[rect_id] = ['center'] + [f'hex_{i}' for i in hex_indices]

        for i in range(12):
            hex_id = f'hex_{i}'
            prev_hex = f'hex_{(i - 1) % 12}'
            next_hex = f'hex_{(i + 1) % 12}'
            self.connections[hex_id] = [prev_hex, next_hex]
            for rect_id, hex_indices in rect_to_hex.items():
                if i in hex_indices:
                    self.connections[hex_id].append(rect_id)

        mine_to_hex = {
            'mine_north': [9],
            'mine_east': [0],
            'mine_south': [3],
            'mine_west': [6]
        }
        for mine_id, hex_indices in mine_to_hex.items():
            self.connections[mine_id] = [f'hex_{i}' for i in hex_indices]
            for hex_idx in hex_indices:
                self.connections[f'hex_{hex_idx}'].append(mine_id)

    def calculate_screen_coordinates(self, center_x=400, center_y=400):
        self.position_coordinates['center'] = (center_x, center_y)

        rect_distance = 80
        self.position_coordinates.update({
            'rect_north': (center_x, center_y - rect_distance),
            'rect_south': (center_x, center_y + rect_distance),
            'rect_east': (center_x + rect_distance, center_y),
            'rect_west': (center_x - rect_distance, center_y)
        })

        hex_distance = 150
        for i in range(12):
            angle_rad = math.radians(i * 30)
            x = center_x + hex_distance * math.cos(angle_rad)
            y = center_y + hex_distance * math.sin(angle_rad)
            self.position_coordinates[f'hex_{i}'] = (int(x), int(y))

        mine_distance = 220
        self.position_coordinates.update({
            'mine_north': (center_x, center_y - mine_distance),
            'mine_south': (center_x, center_y + mine_distance),
            'mine_east': (center_x + mine_distance, center_y),
            'mine_west': (center_x - mine_distance, center_y)
        })

    def get_outer_ring_positions(self):
        return [f'hex_{i}' for i in range(12)]

    def get_connections(self, position):
        return self.connections.get(position, [])
    
    def is_adjacent(self, pos1, pos2):
        """Check if two positions are adjacent"""
        return pos2 in self.connections.get(pos1, [])

class GameBoard:
    def __init__(self):
        self.layout = NewBoardLayout()
        self.wizards_on_board = {}  # position -> list of wizards
        self.mines = {
            'yellow': {'crystals': 9, 'position': 'mine_north'},
            'green': {'crystals': 9, 'position': 'mine_south'},
            'red': {'crystals': 9, 'position': 'mine_west'},
            'blue': {'crystals': 9, 'position': 'mine_east'}
        }
        self.colored_rectangles = {
            'red': 'rect_east',
            'blue': 'rect_west',
            'green': 'rect_north',
            'yellow': 'rect_south'
        }
        self.positions = {}
        self.connections = {}

    @property
    def white_crystals(self):
        """
        Returns a dictionary-like interface for white crystal counts by position.
        White crystals are stored on outer hexagon tiles in self.positions.
        """
        white_crystal_dict = {}
        for position, data in self.positions.items():
            if data.get('type') == 'outer_hexagon':
                white_crystal_dict[position] = data.get('crystals', 0)
        return white_crystal_dict

    def initialize_board(self):
        self.layout.initialize_layout()
        # Copy positions and connections from layout (positions include 'crystals')
        self.positions = {k: v.copy() for k, v in self.layout.positions.items()}
        self.connections = {k: list(v) for k, v in self.layout.connections.items()}
        # ensure mines field crystals are reflected in positions where appropriate
        for color, mine in self.mines.items():
            pos = mine['position']
            if pos in self.positions:
                # store mine crystal count separately; positions[<mine>]['crystals'] can be 0 (we rely on self.mines)
                self.positions[pos]['crystals'] = self.positions[pos].get('crystals', 0)

    def place_initial_crystals(self):
        # outer hexes start with 1 white crystal (already set in layout), ensure it's present
        for i in range(12):
            hex_id = f'hex_{i}'
            if hex_id in self.positions:
                self.positions[hex_id]['crystals'] = 1

    def add_white_crystals_to_empty_tiles(self, amount):
        empty_tiles = [pos for pos, data in self.positions.items()
                       if data.get('type') == 'outer_hexagon' and data.get('crystals', 0) == 0]
        for _ in range(amount):
            if empty_tiles:
                tile = random.choice(empty_tiles)
                self.positions[tile]['crystals'] = 1
                empty_tiles.remove(tile)

    def get_all_positions(self):
        return list(self.positions.keys())

    def get_adjacent_positions(self, position):
        return self.layout.get_connections(position)

    def get_adjacent_empty_positions(self, position):
        return [pos for pos in self.get_adjacent_positions(position)
                if not self.wizards_on_board.get(pos)]

    def get_mineable_positions(self, position):
        mineable = []
        if self.has_crystals_at_position(position):
            mineable.append(position)
        return mineable

    def has_crystals_at_position(self, position):
        # Check outer hex (white crystal)
        if position in self.positions:
            pos_data = self.positions[position]
            if pos_data.get('type') == 'outer_hexagon' and pos_data.get('crystals', 0) > 0:
                return True
            if pos_data.get('type') == 'healing_springs':
                # center is a special case (treat as having heal crystals)
                return True
        # Check mines
        if position.startswith('mine_'):
            mine_color = self.get_mine_color_from_position(position)
            if mine_color and self.mines[mine_color]['crystals'] > 0:
                return True
        return False

    def get_mine_color_from_position(self, mine_position):
        return {
            'mine_north': 'yellow',
            'mine_south': 'green',
            'mine_west': 'red',
            'mine_east': 'blue'
        }.get(mine_position)

    def resolve_mine_with_roll(self, position, wizard, mine_roll):
        # position provided may be 'center', 'mine_x' or hex
        if position == 'center':
            wizard.heal(mine_roll)
            return ({}, random.choice(self.layout.get_outer_ring_positions()))
        elif position.startswith('mine_'):
            mine_color = self.get_mine_color_from_position(position)
            if not mine_color or self.mines[mine_color]['crystals'] <= 0:
                return None
            if mine_roll <= self.mines[mine_color]['crystals']:
                # Calculate how many crystals the wizard can actually hold
                current_total = sum(wizard.crystals.values())
                space_available = wizard.max_crystals - current_total
                crystals_to_give = min(mine_roll, space_available)

                # Only remove the crystals that will actually be given to the player
                self.mines[mine_color]['crystals'] -= crystals_to_give
                return ({mine_color: crystals_to_give},
                        self.colored_rectangles[mine_color] if crystals_to_give > 0 else None)
        elif position in self.positions and self.positions[position].get('type') == 'outer_hexagon' and self.positions[position].get('crystals', 0) > 0:
            # Remove the white crystal from the hex tile and return it
            self.positions[position]['crystals'] = max(0, self.positions[position].get('crystals', 0) - 1)
            return ({'white': 1}, None)
        return None

    def add_wizard_to_position(self, position, wizard):
        if position not in self.wizards_on_board:
            self.wizards_on_board[position] = []
        self.wizards_on_board[position].append(wizard)

    def remove_wizard_from_position(self, position, wizard):
        """Remove a wizard from a position"""
        if position in self.wizards_on_board:
            if isinstance(self.wizards_on_board[position], list):
                if wizard in self.wizards_on_board[position]:
                    self.wizards_on_board[position].remove(wizard)
                if len(self.wizards_on_board[position]) == 0:
                    del self.wizards_on_board[position]

    # helper to get crystal count at any position (white or colored mines)
    def get_crystals_at_position(self, position):
        if position.startswith('mine_'):
            mine_color = self.get_mine_color_from_position(position)
            return self.mines[mine_color]['crystals'] if mine_color else 0
        if position in self.positions:
            return self.positions[position].get('crystals', 0)
        return 0
    
    def is_adjacent(self, pos1, pos2):
        """Check if two positions are adjacent"""
        return self.layout.is_adjacent(pos1, pos2)
    
    def is_healing_springs(self, position):
        """Check if a position is a healing springs (center position)"""
        if position in self.positions:
            return self.positions[position].get('type') == 'healing_springs'
        return False
    
    def is_mine(self, position):
        """Check if a position is a mine"""
        return position.startswith('mine_')
    
    def get_wizard_at_position(self, position):
        """Get list of wizards at a specific position"""
        return self.wizards_on_board.get(position, [])
    
    def get_castable_positions(self, position):
        """Get positions where spells can be cast from the given position"""
        # For now, return adjacent positions - this may need refinement based on spell rules
        return self.get_adjacent_positions(position)
