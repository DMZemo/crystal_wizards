"""
Crystal Wizards - New Clean Board Layout System (FIXED VERSION)
Implements the new board design with clean shortest-path connections
All crossing connections between rectangles and hexagons have been eliminated.
"""

import math

class NewBoardLayout:
    """New board layout with clean connections and logical positioning"""
    
    def __init__(self):
        # New board structure:
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
        
        # 4 rectangles at cardinal directions connected to center
        # Color scheme: North=Green, South=Yellow, East=Red, West=Blue
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
        
        # 12 outer hexagons in a ring (grey with white crystals)
        for i in range(12):
            hex_id = f'hex_{i}'
            self.positions[hex_id] = {
                'type': 'outer_hexagon',
                'color': 'grey',
                'shape': 'hexagon',
                'crystals': 1,  # Start with 1 white crystal each
                'ring_position': i
            }
        
        # 4 mines outside the ring at cardinal directions
        # Color scheme: North=Yellow mine, South=Green mine, West=Red mine, East=Blue mine
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
                'crystals': 9,
                'direction': config['direction']
            }
    
    def create_clean_connections(self):
        """Create clean, logical connections based on spatial adjacency"""
        # Center connects to all 4 rectangles (cardinal directions only)
        self.connections['center'] = ['rect_north', 'rect_south', 'rect_east', 'rect_west']
        
        # Each rectangle connects to center and 3 spatially adjacent hexagons
        # Fixed mapping to eliminate crossings - each rectangle connects to hexagons in its own quadrant
        # Based on 12 hexagons in 30-degree increments: hex_0=East(0°), hex_3=South(90°), hex_6=West(180°), hex_9=North(270°)
        rect_to_hex_mapping = {
            'rect_north': [8, 9, 10],   # Northwest, North, Northeast hexagons
            'rect_east': [11, 0, 1],      # Northeast, East, Southeast hexagons  
            'rect_south': [2, 3, 4],     # Southeast, South, Southwest hexagons 
            'rect_west': [5, 6, 7]       # Southwest, West, Northwest hexagons
        }
        
        for rect_id, hex_indices in rect_to_hex_mapping.items():
            hex_connections = [f'hex_{i}' for i in hex_indices]
            self.connections[rect_id] = ['center'] + hex_connections
        
        # Outer hexagons form a clean ring - each connects to immediate neighbors and its adjacent rectangle
        for i in range(12):
            hex_id = f'hex_{i}'
            connections = []
            
            # Connect to adjacent hexagons in the ring
            prev_hex = f'hex_{(i-1) % 12}'
            next_hex = f'hex_{(i+1) % 12}'
            connections.extend([prev_hex, next_hex])
            
            # Connect to appropriate rectangle based on spatial position
            for rect_id, hex_indices in rect_to_hex_mapping.items():
                if i in hex_indices:
                    connections.append(rect_id)
                    break
            
            self.connections[hex_id] = connections
        
        # Mines connect to cardinal hexagons (spatially adjacent)
        mine_to_hex_mapping = {
            'mine_north': [9],    # North mine connects to hex_0 (North position)
            'mine_east': [0],     # East mine connects to hex_3 (East position)
            'mine_south': [3],    # South mine connects to hex_6 (South position)  
            'mine_west': [6]      # West mine connects to hex_9 (West position)
        }
        
        # Set up bidirectional connections between mines and hexagons
        for mine_id, hex_indices in mine_to_hex_mapping.items():
            hex_connections = [f'hex_{i}' for i in hex_indices]
            self.connections[mine_id] = hex_connections
            
            # Add mine connections to the hexagons
            for hex_idx in hex_indices:
                hex_id = f'hex_{hex_idx}'
                if mine_id not in self.connections[hex_id]:
                    self.connections[hex_id].append(mine_id)
    
    def calculate_screen_coordinates(self, center_x=400, center_y=400):
        """Calculate screen coordinates for all positions"""
        # Center circle
        self.position_coordinates['center'] = (center_x, center_y)
        
        # Rectangles at cardinal directions
        rect_distance = 80
        rect_positions = {
            'rect_north': (center_x, center_y - rect_distance),
            'rect_south': (center_x, center_y + rect_distance),
            'rect_east': (center_x + rect_distance, center_y),
            'rect_west': (center_x - rect_distance, center_y)
        }
        self.position_coordinates.update(rect_positions)
        
        # 12 outer hexagons in a ring
        hex_distance = 150
        for i in range(12):
            angle_rad = math.radians(i * 30)  # 360/12 = 30 degrees apart
            x = center_x + hex_distance * math.cos(angle_rad)
            y = center_y + hex_distance * math.sin(angle_rad)
            self.position_coordinates[f'hex_{i}'] = (int(x), int(y))
        
        # Mines outside the ring at cardinal directions
        mine_distance = 220
        mine_positions = {
            'mine_north': (center_x, center_y - mine_distance),
            'mine_south': (center_x, center_y + mine_distance),
            'mine_east': (center_x + mine_distance, center_y),
            'mine_west': (center_x - mine_distance, center_y)
        }
        self.position_coordinates.update(mine_positions)
    
    def get_position_info(self, position_id):
        """Get information about a specific position"""
        return self.positions.get(position_id, {})
    
    def get_connections(self, position_id):
        """Get all positions connected to the given position"""
        return self.connections.get(position_id, [])
    
    def is_adjacent(self, pos1, pos2):
        """Check if two positions are adjacent"""
        return pos2 in self.connections.get(pos1, [])
    
    def get_all_positions(self):
        """Get all position IDs"""
        return list(self.positions.keys())
    
    def get_outer_ring_positions(self):
        """Get all outer hexagon positions for wizard placement"""
        return [f'hex_{i}' for i in range(12)]
    
    def get_mine_positions(self):
        """Get all mine position IDs"""
        return ['mine_north', 'mine_south', 'mine_east', 'mine_west']
    
    def validate_connectivity(self):
        """Validate that the board is fully connected"""
        if not self.positions:
            return False
        
        # BFS to check connectivity
        start_pos = list(self.positions.keys())[0]
        visited = set()
        queue = [start_pos]
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            for adjacent in self.get_connections(current):
                if adjacent not in visited:
                    queue.append(adjacent)
        
        return len(visited) == len(self.positions)

# Helper functions for converting between old and new position IDs
def convert_old_to_new_position(old_position):
    """Convert old position IDs to new position IDs"""
    conversion_map = {
        'center': 'center',
        'rect_red': 'rect_east',
        'rect_blue': 'rect_west', 
        'rect_green': 'rect_north',
        'rect_yellow': 'rect_south',
        'mine_red': 'mine_west',
        'mine_blue': 'mine_east',
        'mine_green': 'mine_south', 
        'mine_yellow': 'mine_north'
    }
    
    # Convert outer positions
    if old_position.startswith('outer_'):
        old_num = int(old_position.split('_')[1])
        # Map old 10-position ring to new 12-position ring
        new_num = (old_num * 12) // 10
        return f'hex_{new_num}'
    
    return conversion_map.get(old_position, old_position)

def convert_new_to_old_position(new_position):
    """Convert new position IDs back to old position IDs (for compatibility)"""
    reverse_map = {
        'center': 'center',
        'rect_east': 'rect_red',
        'rect_west': 'rect_blue',
        'rect_north': 'rect_green', 
        'rect_south': 'rect_yellow',
        'mine_west': 'mine_red',
        'mine_east': 'mine_blue',
        'mine_south': 'mine_green',
        'mine_north': 'mine_yellow'
    }
    
    # Convert hex positions
    if new_position.startswith('hex_'):
        new_num = int(new_position.split('_')[1])
        # Map new 12-position ring to old 10-position ring
        old_num = (new_num * 10) // 12
        return f'outer_{old_num}'
    
    return reverse_map.get(new_position, new_position)
