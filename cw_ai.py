
"""
Crystal Wizards - Strategic AI System
Complete AI overhaul with three difficulty levels: Easy, Medium, Hard
"""

import random
from collections import defaultdict

class BaseAI:
    """Base class for all AI difficulty levels"""
    
    def __init__(self, wizard, difficulty='easy'):
        self.wizard = wizard
        self.difficulty = difficulty
        self.turn_plan = []  # Multi-action turn planning
        
    def execute_turn(self, game):
        """Execute a complete turn for the AI"""
        self.turn_plan = self.plan_turn(game)
        
        for action in self.turn_plan:
            if game.current_actions >= game.max_actions_per_turn:
                break
                
            success = self.execute_action(action, game)
            if not success:
                # If planned action fails, try a backup action
                backup = self.get_backup_action(game)
                if backup:
                    self.execute_action(backup, game)
    
    def plan_turn(self, game):
        """Override in subclasses - plan the entire turn"""
        return []
    
    def execute_action(self, action, game):
        """Execute a single action"""
        action_type = action['type']
        
        if action_type == 'move':
            return game.move_player(self.wizard, action['target'])
        elif action_type == 'mine':
            if 'roll_result' in action:
                return game.resolve_mine_with_roll(self.wizard, self.wizard.location, action['roll_result'])
            else:
                return game.mine_white_crystal(self.wizard, action['position'])
        elif action_type == 'lay_card':
            return self.wizard.lay_down_spell_card(action['card_index'])
        elif action_type == 'charge_card':
            card = action['card']
            return card.add_crystals(action['crystal_color'], action['amount'], self.wizard)
        elif action_type == 'cast_spell':
            return game.cast_spell(self.wizard, action['spell_card'], action.get('gui'))
        
        return False
    
    def get_backup_action(self, game):
        """Get a simple backup action if planned action fails"""
        if game.can_move(self.wizard):
            # Try to move to any adjacent position with crystals
            adjacent = game.board.get_adjacent_positions(self.wizard.location)
            for pos in adjacent:
                if game.board.has_crystals_at_position(pos):
                    return {'type': 'move', 'target': pos}
        return None

class EasyAI(BaseAI):
    """Easy difficulty - improved basic AI with slight strategic elements"""
    
    def plan_turn(self, game):
        actions = []
        
        # Simple priority: Cast spells > Mine > Lay cards > Move
        
        # 1. Try to cast spells if we have them and enemies nearby
        if game.can_cast_spell(self.wizard):
            spell_action = self.try_cast_spell(game)
            if spell_action:
                actions.append(spell_action)
        
        # 2. Lay down a card if we have none laid down and have crystals
        if len(self.wizard.cards_laid_down) == 0 and self.wizard.get_total_crystals() >= 2:
            lay_action = self.try_lay_card(game)
            if lay_action:
                actions.append(lay_action)
        
        # 3. Charge a card if we have one laid down
        charge_action = self.try_charge_card(game)
        if charge_action:
            actions.append(charge_action)
        
        # 4. Mine crystals if we're on a crystal tile
        if game.can_mine(self.wizard):
            mine_action = self.try_mine(game)
            if mine_action:
                actions.append(mine_action)
        
        # 5. Move towards crystals or healing
        remaining_moves = min(3 - len([a for a in actions if a['type'] == 'move']), 
                             game.max_actions_per_turn - len(actions))
        for _ in range(remaining_moves):
            if game.can_move(self.wizard):
                move_action = self.try_move(game)
                if move_action:
                    actions.append(move_action)
        
        return actions[:game.max_actions_per_turn - game.current_actions]
    
    def try_cast_spell(self, game):
        """Try to cast a spell if enemies are adjacent"""
        for spell_card in self.wizard.cards_laid_down:
            if spell_card.is_fully_charged():
                enemies = game.get_adjacent_enemies(self.wizard)
                if enemies:
                    return {'type': 'cast_spell', 'spell_card': spell_card}
        return None
    
    def try_lay_card(self, game):
        """Try to lay down a spell card"""
        if self.wizard.hand:
            # Pick the first affordable card, or just the first card
            for i, card in enumerate(self.wizard.hand):
                if self.can_eventually_afford(card):
                    return {'type': 'lay_card', 'card_index': i}
            return {'type': 'lay_card', 'card_index': 0}
        return None
    
    def try_charge_card(self, game):
        """Try to charge a laid down card"""
        for card in self.wizard.cards_laid_down:
            if not card.is_fully_charged():
                # Try to charge with any crystal we have
                for color in ['red', 'blue', 'green', 'yellow', 'white']:
                    if self.wizard.crystals[color] > 0:
                        return {'type': 'charge_card', 'card': card, 
                               'crystal_color': color, 'amount': 1}
        return None
    
    def try_mine(self, game):
        """Try to mine at current location"""
        pos = self.wizard.location
        
        # Heal if low health and at healing springs
        if game.board.is_healing_springs(pos) and self.wizard.health < 4:
            roll = random.randint(1, 3)  # Healing springs die
            return {'type': 'mine', 'roll_result': roll}
        
        # Mine white crystals if available
        if game.board.has_crystals_at_position(pos) and not game.board.is_mine(pos):
            return {'type': 'mine', 'position': pos}
        
        # Mine colored crystals if at a mine
        if game.board.is_mine(pos) and self.wizard.get_total_crystals() < 5:
            roll = random.randint(1, 6)
            return {'type': 'mine', 'roll_result': roll}
        
        return None
    
    def try_move(self, game):
        """Try to move to a beneficial position"""
        current_pos = self.wizard.location
        adjacent = game.board.get_adjacent_positions(current_pos)
        
        best_pos = None
        best_score = -1
        
        for pos in adjacent:
            score = self.evaluate_position(pos, game)
            if score > best_score:
                best_score = score
                best_pos = pos
        
        if best_pos:
            return {'type': 'move', 'target': best_pos}
        return None
    
    def evaluate_position(self, pos, game):
        """Simple position evaluation"""
        score = 0
        
        # Prefer positions with crystals
        if game.board.has_crystals_at_position(pos):
            score += 10
        
        # Prefer healing springs if low health
        if self.wizard.health <= 3 and game.board.is_healing_springs(pos):
            score += 15
        
        # Prefer being near enemies if we have charged spells
        enemies_nearby = len(game.get_adjacent_enemies_at_position(pos, self.wizard))
        if enemies_nearby > 0 and self.wizard.has_charged_spells():
            score += 8 * enemies_nearby
        
        return score
    
    def can_eventually_afford(self, card):
        """Check if we can eventually afford this card"""
        total_cost = card.get_total_cost()
        total_crystals = self.wizard.get_total_crystals()
        return total_crystals >= total_cost * 0.3  # Very lenient

class MediumAI(BaseAI):
    """Medium difficulty - strategic AI with priority systems and heuristics"""
    
    def plan_turn(self, game):
        actions = []
        
        # Strategic priority system
        self.analyze_game_state(game)
        
        # 1. Emergency actions first (heal, defend)
        emergency_action = self.handle_emergency(game)
        if emergency_action:
            actions.append(emergency_action)
        
        # 2. Offensive actions if we have opportunities
        offensive_action = self.handle_offensive(game)
        if offensive_action:
            actions.append(offensive_action)
        
        # 3. Strategic spell management
        spell_management_actions = self.manage_spells(game)
        actions.extend(spell_management_actions)
        
        # 4. Resource collection with priorities
        resource_actions = self.collect_resources(game)
        actions.extend(resource_actions)
        
        # 5. Positioning for next turn
        positioning_actions = self.improve_position(game)
        actions.extend(positioning_actions)
        
        return actions[:game.max_actions_per_turn - game.current_actions]
    
    def analyze_game_state(self, game):
        """Analyze current game state for strategic decisions"""
        self.threat_level = self.assess_threat_level(game)
        self.resource_priority = self.determine_resource_priority()
        self.spell_priority = self.determine_spell_priority()
    
    def assess_threat_level(self, game):
        """Assess how much danger we're in"""
        threat = 0
        
        # Check adjacent enemies
        adjacent_enemies = game.get_adjacent_enemies(self.wizard)
        for enemy in adjacent_enemies:
            if enemy.has_charged_spells():
                threat += 10
        
        # Check our health
        if self.wizard.health <= 2:
            threat += 15
        elif self.wizard.health <= 4:
            threat += 5
        
        return threat
    
    def determine_resource_priority(self):
        """Determine crystal collection priorities based on spell needs"""
        priorities = {}
        
        # Analyze spell card needs
        needs = defaultdict(int)
        
        # Check cards in hand and laid down
        all_cards = self.wizard.hand + self.wizard.cards_laid_down
        for card in all_cards:
            for color, amount in card.cost.items():
                if color == 'wild':
                    needs[self.wizard.color] += amount
                else:
                    needs[color] += amount
        
        # Set priorities: needed colors > own color > white > others
        for color in ['red', 'blue', 'green', 'yellow', 'white']:
            if needs[color] > 0:
                priorities[color] = 10 + needs[color]
            elif color == self.wizard.color:
                priorities[color] = 8
            elif color == 'white':
                priorities[color] = 6
            else:
                priorities[color] = 3
        
        return priorities
    
    def determine_spell_priority(self):
        """Determine which spells to focus on charging first"""
        if not self.wizard.cards_laid_down:
            return None
        
        # Prefer lower cost spells that we can complete soon
        best_card = None
        best_score = -1
        
        for card in self.wizard.cards_laid_down:
            if card.is_fully_charged():
                continue
                
            # Score based on: damage/cost ratio, how close to completion
            damage = card.get_damage()
            total_cost = card.get_total_cost()
            progress = card.get_charging_progress()
            
            score = (damage / total_cost) * 10 + progress * 20
            
            if score > best_score:
                best_score = score
                best_card = card
        
        return best_card
    
    def handle_emergency(self, game):
        """Handle emergency situations (low health, immediate threats)"""
        # Heal if very low health and at healing springs
        if self.wizard.health <= 2 and game.board.is_healing_springs(self.wizard.location):
            if game.can_mine(self.wizard):
                roll = random.randint(1, 3)
                return {'type': 'mine', 'roll_result': roll}
        
        # Move to healing springs if critically low health
        if self.wizard.health <= 2 and game.can_move(self.wizard):
            healing_pos = self.find_nearest_healing_springs(game)
            if healing_pos:
                return {'type': 'move', 'target': healing_pos}
        
        return None
    
    def handle_offensive(self, game):
        """Handle offensive opportunities"""
        if game.can_cast_spell(self.wizard):
            # Look for best spell to cast
            best_spell = None
            best_damage = 0
            
            for spell_card in self.wizard.cards_laid_down:
                if spell_card.is_fully_charged():
                    enemies = game.get_adjacent_enemies(self.wizard)
                    if enemies:
                        damage = spell_card.get_damage() * len(enemies)
                        if damage > best_damage:
                            best_damage = damage
                            best_spell = spell_card
            
            if best_spell:
                return {'type': 'cast_spell', 'spell_card': best_spell}
        
        return None
    
    def manage_spells(self, game):
        """Strategic spell card management"""
        actions = []
        
        # Lay down a card if we have room and crystals to charge it
        if len(self.wizard.cards_laid_down) < 2 and self.wizard.get_total_crystals() >= 3:
            card_to_lay = self.choose_best_card_to_lay()
            if card_to_lay is not None:
                actions.append({'type': 'lay_card', 'card_index': card_to_lay})
        
        # Charge priority spell
        priority_spell = self.spell_priority
        if priority_spell:
            charge_action = self.charge_spell_strategically(priority_spell)
            if charge_action:
                actions.append(charge_action)
        
        return actions
    
    def choose_best_card_to_lay(self):
        """Choose the best card to lay down based on our resources"""
        if not self.wizard.hand:
            return None
        
        best_index = None
        best_score = -1
        
        for i, card in enumerate(self.wizard.hand):
            score = self.evaluate_card_to_lay(card)
            if score > best_score:
                best_score = score
                best_index = i
        
        return best_index
    
    def evaluate_card_to_lay(self, card):
        """Evaluate how good a card is to lay down"""
        score = 0
        
        # Prefer cards we can afford
        affordability = self.calculate_affordability(card)
        score += affordability * 20
        
        # Prefer higher damage for cost ratio
        damage_per_cost = card.get_damage() / max(card.get_total_cost(), 1)
        score += damage_per_cost * 10
        
        # Prefer cards that match our resource priorities
        for color, amount in card.cost.items():
            if color in self.resource_priority:
                score += self.resource_priority[color] * amount
        
        return score
    
    def calculate_affordability(self, card):
        """Calculate how easily we can afford this card (0-1)"""
        total_cost = card.get_total_cost()
        if total_cost == 0:
            return 1.0
        
        # Count crystals we can use for this card
        usable_crystals = 0
        for color, amount in card.cost.items():
            if color == 'wild':
                # Wild can be fulfilled by our color or white
                usable_crystals += self.wizard.crystals[self.wizard.color]
                usable_crystals += self.wizard.crystals['white']
            else:
                # Direct color match or white crystals
                usable_crystals += self.wizard.crystals[color]
                usable_crystals += self.wizard.crystals['white']
        
        return min(1.0, usable_crystals / total_cost)
    
    def charge_spell_strategically(self, card):
        """Charge a spell card using optimal crystal selection"""
        if card.is_fully_charged():
            return None
        
        # Find the best crystal type to use
        best_color = None
        best_efficiency = -1
        
        for color in ['red', 'blue', 'green', 'yellow', 'white']:
            if self.wizard.crystals[color] > 0:
                efficiency = self.calculate_charging_efficiency(card, color)
                if efficiency > best_efficiency:
                    best_efficiency = efficiency
                    best_color = color
        
        if best_color:
            return {'type': 'charge_card', 'card': card, 
                   'crystal_color': best_color, 'amount': 1}
        
        return None
    
    def calculate_charging_efficiency(self, card, crystal_color):
        """Calculate efficiency of using a crystal color for charging"""
        # Check if this crystal can actually charge the card
        temp_crystals = self.wizard.crystals.copy()
        original_progress = card.get_charging_progress()
        
        # Simulate adding the crystal
        if card.add_crystals(crystal_color, 1, self.wizard):
            new_progress = card.get_charging_progress()
            efficiency = new_progress - original_progress
            
            # Restore original state (this is a simulation)
            self.wizard.crystals = temp_crystals
            return efficiency
        
        return 0
    
    def collect_resources(self, game):
        """Collect resources based on priorities"""
        actions = []
        
        if game.can_mine(self.wizard):
            mine_action = self.strategic_mine(game)
            if mine_action:
                actions.append(mine_action)
        
        return actions
    
    def strategic_mine(self, game):
        """Mine resources strategically based on priorities"""
        pos = self.wizard.location
        
        # Heal if moderately low health
        if self.wizard.health <= 4 and game.board.is_healing_springs(pos):
            roll = random.randint(1, 3)
            return {'type': 'mine', 'roll_result': roll}
        
        # Mine white crystals (always good)
        if game.board.has_crystals_at_position(pos) and not game.board.is_mine(pos):
            if self.wizard.can_hold_more_crystals():
                return {'type': 'mine', 'position': pos}
        
        # Mine colored crystals based on priority
        if game.board.is_mine(pos):
            mine_color = game.board.get_mine_color(pos)
            if mine_color in self.resource_priority and self.resource_priority[mine_color] >= 5:
                if self.wizard.can_hold_more_crystals():
                    roll = random.randint(1, 6)
                    return {'type': 'mine', 'roll_result': roll}
        
        return None
    
    def improve_position(self, game):
        """Move to improve positioning for future turns"""
        actions = []
        
        remaining_moves = 3 - len([a for a in self.turn_plan if a.get('type') == 'move'])
        
        for _ in range(min(remaining_moves, 2)):  # Save some actions for other activities
            if game.can_move(self.wizard):
                move_action = self.strategic_move(game)
                if move_action:
                    actions.append(move_action)
        
        return actions
    
    def strategic_move(self, game):
        """Make strategic movement decisions"""
        current_pos = self.wizard.location
        adjacent = game.board.get_adjacent_positions(current_pos)
        
        best_pos = None
        best_score = -1
        
        for pos in adjacent:
            score = self.evaluate_position_strategically(pos, game)
            if score > best_score:
                best_score = score
                best_pos = pos
        
        if best_pos:
            return {'type': 'move', 'target': best_pos}
        return None
    
    def evaluate_position_strategically(self, pos, game):
        """Strategic position evaluation"""
        score = 0
        
        # Resource gathering opportunities
        if game.board.has_crystals_at_position(pos):
            score += 15
        
        if game.board.is_mine(pos):
            mine_color = game.board.get_mine_color(pos)
            if mine_color in self.resource_priority:
                score += self.resource_priority[mine_color]
        
        # Tactical positioning
        enemies_in_range = len(game.get_adjacent_enemies_at_position(pos, self.wizard))
        if enemies_in_range > 0:
            if self.wizard.has_charged_spells():
                score += 20 * enemies_in_range  # Good for offense
            else:
                score -= 10 * enemies_in_range  # Bad for defense
        
        # Healing considerations
        if game.board.is_healing_springs(pos):
            if self.wizard.health <= 4:
                score += (6 - self.wizard.health) * 5
        
        return score
    
    def find_nearest_healing_springs(self, game):
        """Find the nearest healing springs position"""
        current_pos = self.wizard.location
        adjacent = game.board.get_adjacent_positions(current_pos)
        
        for pos in adjacent:
            if game.board.is_healing_springs(pos):
                return pos
        
        return None

class HardAI(BaseAI):
    """Hard difficulty - advanced strategic AI with full game tree evaluation"""
    
    def __init__(self, wizard, difficulty='hard'):
        super().__init__(wizard, difficulty)
        self.game_memory = {}  # Remember game patterns
        self.opponent_patterns = {}  # Track opponent behavior
    
    def plan_turn(self, game):
        """Advanced turn planning with full strategic evaluation"""
        # Deep strategic analysis
        self.full_game_analysis(game)
        
        # Generate all possible action sequences
        action_sequences = self.generate_action_sequences(game)
        
        # Evaluate each sequence
        best_sequence = self.evaluate_action_sequences(action_sequences, game)
        
        return best_sequence
    
    def full_game_analysis(self, game):
        """Comprehensive game state analysis"""
        self.analyze_board_control(game)
        self.analyze_opponent_threats(game)
        self.analyze_resource_economy(game)
        self.analyze_win_conditions(game)
        self.update_opponent_patterns(game)
    
    def analyze_board_control(self, game):
        """Analyze territorial control and positioning"""
        self.board_control = {}
        
        # Evaluate control of key areas
        key_positions = self.identify_key_positions(game)
        for pos in key_positions:
            control_value = self.evaluate_position_control(pos, game)
            self.board_control[pos] = control_value
    
    def identify_key_positions(self, game):
        """Identify strategically important positions"""
        key_positions = []
        
        # Resource-rich positions
        for pos in game.board.get_all_positions():
            if game.board.has_crystals_at_position(pos) or game.board.is_mine(pos):
                key_positions.append(pos)
        
        # Healing springs
        if hasattr(game.board, 'healing_springs_position'):
            key_positions.append(game.board.healing_springs_position)
        
        # Central positions (good for mobility)
        center_positions = self.find_central_positions(game)
        key_positions.extend(center_positions)
        
        return key_positions
    
    def find_central_positions(self, game):
        """Find positions that offer good mobility"""
        # Simple heuristic: positions with many adjacent positions
        central_positions = []
        for pos in game.board.get_all_positions():
            adjacent_count = len(game.board.get_adjacent_positions(pos))
            if adjacent_count >= 4:  # Adjust based on board layout
                central_positions.append(pos)
        return central_positions
    
    def analyze_opponent_threats(self, game):
        """Analyze threats from each opponent"""
        self.opponent_threats = {}
        
        for player in game.players:
            if player != self.wizard:
                threat_level = self.calculate_opponent_threat(player, game)
                self.opponent_threats[player] = threat_level
    
    def calculate_opponent_threat(self, opponent, game):
        """Calculate comprehensive threat level from an opponent"""
        threat = 0
        
        # Immediate threat (adjacency + charged spells)
        if self.is_adjacent_to_opponent(opponent, game):
            for spell in opponent.cards_laid_down:
                if spell.is_fully_charged():
                    threat += spell.get_damage() * 10
        
        # Potential threat (spell charging progress)
        for spell in opponent.cards_laid_down:
            progress = spell.get_charging_progress()
            potential_damage = spell.get_damage()
            threat += progress * potential_damage * 5
        
        # Resource advantage
        opponent_resources = opponent.get_total_crystals()
        our_resources = self.wizard.get_total_crystals()
        if opponent_resources > our_resources:
            threat += (opponent_resources - our_resources) * 2
        
        return threat
    
    def is_adjacent_to_opponent(self, opponent, game):
        """Check if opponent is adjacent to us"""
        our_adjacent = game.board.get_adjacent_positions(self.wizard.location)
        return opponent.location in our_adjacent
    
    def analyze_resource_economy(self, game):
        """Analyze the resource economy and our position in it"""
        self.resource_analysis = {
            'our_resources': self.wizard.get_total_crystals(),
            'resource_needs': self.calculate_resource_needs(),
            'resource_opportunities': self.find_resource_opportunities(game),
            'resource_efficiency': self.calculate_resource_efficiency(),
        }
    
    def calculate_resource_needs(self):
        """Calculate our specific crystal needs"""
        needs = defaultdict(int)
        
        # Analyze all our spells (hand + laid down)
        all_cards = self.wizard.hand + self.wizard.cards_laid_down
        
        for card in all_cards:
            for color, amount in card.cost.items():
                current_charged = card.crystals_used.get(color, 0)
                still_needed = amount - current_charged
                
                if color == 'wild':
                    needs[self.wizard.color] += still_needed
                else:
                    needs[color] += still_needed
        
        return needs
    
    def find_resource_opportunities(self, game):
        """Find the best resource gathering opportunities"""
        opportunities = []
        
        for pos in game.board.get_all_positions():
            if game.board.has_crystals_at_position(pos) or game.board.is_mine(pos):
                distance = self.calculate_distance(self.wizard.location, pos, game)
                resource_value = self.evaluate_resource_position(pos, game)
                
                opportunities.append({
                    'position': pos,
                    'distance': distance,
                    'value': resource_value,
                    'efficiency': resource_value / (distance + 1)
                })
        
        return sorted(opportunities, key=lambda x: x['efficiency'], reverse=True)
    
    def calculate_distance(self, pos1, pos2, game):
        """Calculate movement distance between positions"""
        # Simple Manhattan distance (could be improved with pathfinding)
        x1, y1 = pos1
        x2, y2 = pos2
        return abs(x2 - x1) + abs(y2 - y1)
    
    def evaluate_resource_position(self, pos, game):
        """Evaluate the value of a resource position"""
        value = 0
        
        if game.board.has_crystals_at_position(pos):
            value += 10  # White crystals are always valuable
        
        if game.board.is_mine(pos):
            mine_color = game.board.get_mine_color(pos)
            # Value based on our needs
            needs = self.calculate_resource_needs()
            if mine_color in needs:
                value += needs[mine_color] * 5
            else:
                value += 3  # Still somewhat valuable
        
        return value
    
    def calculate_resource_efficiency(self):
        """Calculate how efficiently we're using resources"""
        total_crystals = self.wizard.get_total_crystals()
        if total_crystals == 0:
            return 0
        
        # Count crystals effectively used in spell charging
        used_crystals = 0
        for card in self.wizard.cards_laid_down:
            used_crystals += sum(card.crystals_used.values())
        
        return used_crystals / total_crystals
    
    def analyze_win_conditions(self, game):
        """Analyze potential paths to victory"""
        self.win_analysis = {
            'can_eliminate_opponent': self.can_eliminate_any_opponent(game),
            'defensive_position': self.evaluate_defensive_position(game),
            'resource_advantage': self.calculate_resource_advantage(game),
            'turns_to_victory': self.estimate_turns_to_victory(game),
        }
    
    def can_eliminate_any_opponent(self, game):
        """Check if we can eliminate any opponent soon"""
        for player in game.players:
            if player != self.wizard:
                if self.can_eliminate_opponent(player, game):
                    return player
        return None
    
    def can_eliminate_opponent(self, opponent, game):
        """Check if we can eliminate a specific opponent"""
        # Check if opponent is in range and we have enough damage
        if self.is_adjacent_to_opponent(opponent, game):
            total_damage = 0
            for spell in self.wizard.cards_laid_down:
                if spell.is_fully_charged():
                    total_damage += spell.get_damage()
            
            return total_damage >= opponent.health
        
        return False
    
    def evaluate_defensive_position(self, game):
        """Evaluate how well we're positioned defensively"""
        defense_score = 0
        
        # Health factor
        defense_score += self.wizard.health * 10
        
        # Distance from threats
        for opponent in game.players:
            if opponent != self.wizard:
                threat = self.opponent_threats.get(opponent, 0)
                distance = self.calculate_distance(self.wizard.location, opponent.location, game)
                defense_score += min(distance * 5, threat)  # Further is safer
        
        # Access to healing
        if game.board.is_healing_springs(self.wizard.location):
            defense_score += 20
        
        return defense_score
    
    def calculate_resource_advantage(self, game):
        """Calculate our resource advantage over opponents"""
        our_resources = self.wizard.get_total_crystals()
        opponent_average = 0
        
        opponent_count = 0
        for player in game.players:
            if player != self.wizard:
                opponent_average += player.get_total_crystals()
                opponent_count += 1
        
        if opponent_count > 0:
            opponent_average /= opponent_count
            return our_resources - opponent_average
        
        return our_resources
    
    def estimate_turns_to_victory(self, game):
        """Estimate how many turns until we can win"""
        # Simple heuristic based on spell completion and opponent health
        min_opponent_health = min(player.health for player in game.players if player != self.wizard)
        
        # Calculate turns needed to charge enough spells
        damage_needed = min_opponent_health
        current_damage_potential = sum(spell.get_damage() for spell in self.wizard.cards_laid_down if spell.is_fully_charged())
        
        if current_damage_potential >= damage_needed:
            return 1  # Can win this turn if in position
        
        # Estimate based on resource gathering and spell charging rates
        remaining_damage_needed = damage_needed - current_damage_potential
        average_spell_damage = 3  # Rough average
        spells_needed = remaining_damage_needed / average_spell_damage
        
        # Rough estimate: 2-3 turns per spell to charge
        return int(spells_needed * 2.5)
    
    def update_opponent_patterns(self, game):
        """Learn from opponent behavior patterns"""
        for player in game.players:
            if player != self.wizard:
                if player not in self.opponent_patterns:
                    self.opponent_patterns[player] = {
                        'aggression': 0,
                        'resource_focus': 0,
                        'spell_preference': defaultdict(int)
                    }
                
                # Update patterns based on current state
                # (This could be expanded with more sophisticated pattern recognition)
    
    def generate_action_sequences(self, game):
        """Generate all viable action sequences for this turn"""
        sequences = []
        max_actions = min(game.max_actions_per_turn - game.current_actions, 3)
        
        # Generate sequences of different lengths
        for length in range(1, max_actions + 1):
            length_sequences = self.generate_sequences_of_length(length, game)
            sequences.extend(length_sequences)
        
        return sequences
    
    def generate_sequences_of_length(self, length, game):
        """Generate action sequences of specific length"""
        if length == 1:
            return [[action] for action in self.get_all_possible_actions(game)]
        
        sequences = []
        base_actions = self.get_all_possible_actions(game)
        
        for base_action in base_actions:
            # Simulate performing this action
            game_copy = self.simulate_action(base_action, game)
            remaining_sequences = self.generate_sequences_of_length(length - 1, game_copy)
            
            for remaining_seq in remaining_sequences:
                sequences.append([base_action] + remaining_seq)
        
        return sequences[:50]  # Limit to prevent explosion
    
    def get_all_possible_actions(self, game):
        """Get all actions possible in current state"""
        actions = []
        
        # Movement actions
        if game.can_move(self.wizard):
            for pos in game.board.get_adjacent_positions(self.wizard.location):
                actions.append({'type': 'move', 'target': pos})
        
        # Mining actions
        if game.can_mine(self.wizard):
            pos = self.wizard.location
            if game.board.has_crystals_at_position(pos) and not game.board.is_mine(pos):
                actions.append({'type': 'mine', 'position': pos})
            elif game.board.is_mine(pos) or game.board.is_healing_springs(pos):
                for roll in [1, 3, 6]:  # Sample different roll outcomes
                    actions.append({'type': 'mine', 'roll_result': roll})
        
        # Spell actions
        if game.can_cast_spell(self.wizard):
            for spell in self.wizard.cards_laid_down:
                if spell.is_fully_charged():
                    actions.append({'type': 'cast_spell', 'spell_card': spell})
        
        # Card laying actions
        if len(self.wizard.cards_laid_down) < 3:  # Assume max 3 laid down
            for i, card in enumerate(self.wizard.hand):
                actions.append({'type': 'lay_card', 'card_index': i})
        
        # Card charging actions
        for card in self.wizard.cards_laid_down:
            if not card.is_fully_charged():
                for color in ['red', 'blue', 'green', 'yellow', 'white']:
                    if self.wizard.crystals[color] > 0:
                        actions.append({'type': 'charge_card', 'card': card, 
                                      'crystal_color': color, 'amount': 1})
        
        return actions
    
    def simulate_action(self, action, game):
        """Simulate performing an action (returns modified game state)"""
        # This would ideally create a deep copy of the game state
        # For now, we'll use a simplified simulation
        # In a full implementation, you'd want a proper game state copy
        return game  # Placeholder
    
    def evaluate_action_sequences(self, sequences, game):
        """Evaluate all action sequences and return the best one"""
        if not sequences:
            return []
        
        best_sequence = None
        best_score = float('-inf')
        
        for sequence in sequences:
            score = self.evaluate_sequence(sequence, game)
            if score > best_score:
                best_score = score
                best_sequence = sequence
        
        return best_sequence or []
    
    def evaluate_sequence(self, sequence, game):
        """Evaluate the strategic value of an action sequence"""
        score = 0
        
        # Simulate the sequence and evaluate the resulting state
        for action in sequence:
            action_score = self.evaluate_single_action(action, game)
            score += action_score
        
        # Add sequence synergy bonuses
        synergy_score = self.calculate_sequence_synergy(sequence)
        score += synergy_score
        
        return score
    
    def evaluate_single_action(self, action, game):
        """Evaluate the value of a single action"""
        action_type = action['type']
        
        if action_type == 'cast_spell':
            return self.evaluate_spell_cast(action, game)
        elif action_type == 'move':
            return self.evaluate_move(action, game)
        elif action_type == 'mine':
            return self.evaluate_mine(action, game)
        elif action_type == 'lay_card':
            return self.evaluate_lay_card(action, game)
        elif action_type == 'charge_card':
            return self.evaluate_charge_card(action, game)
        
        return 0
    
    def evaluate_spell_cast(self, action, game):
        """Evaluate spell casting action"""
        spell_card = action['spell_card']
        damage = spell_card.get_damage()
        
        # Count targets
        targets = game.get_adjacent_enemies(self.wizard)
        if not targets:
            return -10  # Wasted spell
        
        total_damage = damage * len(targets)
        
        # Bonus for eliminating opponents
        elimination_bonus = 0
        for target in targets:
            if target.health <= damage:
                elimination_bonus += 100  # High value for elimination
        
        return total_damage * 10 + elimination_bonus
    
    def evaluate_move(self, action, game):
        """Evaluate movement action"""
        target_pos = action['target']
        
        # Evaluate the position strategically
        position_value = self.evaluate_position_strategically(target_pos, game)
        
        # Consider distance from threats
        threat_distance_bonus = 0
        for opponent in game.players:
            if opponent != self.wizard:
                threat = self.opponent_threats.get(opponent, 0)
                distance = self.calculate_distance(target_pos, opponent.location, game)
                if threat > 50:  # High threat opponent
                    if distance > 1:
                        threat_distance_bonus += 10  # Bonus for staying away from threats
                    else:
                        threat_distance_bonus -= 20  # Penalty for moving closer to threats
        
        return position_value + threat_distance_bonus
    
    def evaluate_mine(self, action, game):
        """Evaluate mining action"""
        base_value = 15  # Base value for any mining
        
        if action.get('position'):
            # White crystal mining
            return base_value + 5  # White crystals are versatile
        
        if 'roll_result' in action:
            # Colored crystal or healing mining
            roll = action['roll_result']
            
            if game.board.is_healing_springs(self.wizard.location):
                # Healing value based on current health
                healing_value = (6 - self.wizard.health) * 10
                return healing_value + roll * 2
            
            # Colored crystal mining
            resource_needs = self.calculate_resource_needs()
            mine_color = game.board.get_mine_color(self.wizard.location)
            
            if mine_color in resource_needs:
                return base_value + resource_needs[mine_color] * 5 + roll * 3
            else:
                return base_value + roll * 2
        
        return base_value
    
    def evaluate_lay_card(self, action, game):
        """Evaluate laying down a card"""
        card_index = action['card_index']
        card = self.wizard.hand[card_index]
        
        # Value based on affordability and strategic value
        affordability = self.calculate_affordability(card)
        strategic_value = self.evaluate_card_strategic_value(card)
        
        return affordability * 20 + strategic_value * 10
    
    def evaluate_card_strategic_value(self, card):
        """Evaluate the strategic value of a card"""
        damage_per_cost = card.get_damage() / max(card.get_total_cost(), 1)
        return damage_per_cost * 10
    
    def evaluate_charge_card(self, action, game):
        """Evaluate charging a card"""
        card = action['card']
        crystal_color = action['crystal_color']
        
        # Value based on progress toward completion
        current_progress = card.get_charging_progress()
        
        # Simulate the charging
        temp_crystals = self.wizard.crystals.copy()
        if card.add_crystals(crystal_color, 1, self.wizard):
            new_progress = card.get_charging_progress()
            progress_gain = new_progress - current_progress
            
            # Restore state
            self.wizard.crystals = temp_crystals
            
            base_value = progress_gain * 30
            
            # Bonus if this completes the card
            if new_progress >= 1.0:
                base_value += 50
            
            return base_value
        
        return 0  # Invalid charging
    
    def calculate_sequence_synergy(self, sequence):
        """Calculate bonus score for action sequence synergy"""
        synergy = 0
        
        # Bonus for completing a spell then casting it
        laying_actions = [a for a in sequence if a['type'] == 'lay_card']
        charging_actions = [a for a in sequence if a['type'] == 'charge_card']
        casting_actions = [a for a in sequence if a['type'] == 'cast_spell']
        
        if laying_actions and charging_actions:
            synergy += 10  # Good synergy
        
        if charging_actions and casting_actions:
            synergy += 20  # Excellent synergy
        
        # Bonus for efficient resource gathering
        mining_actions = [a for a in sequence if a['type'] == 'mine']
        if len(mining_actions) >= 2:
            synergy += 5  # Resource focus bonus
        
        return synergy


class AIManager:
    """Factory class to create AI instances based on difficulty"""
    
    @staticmethod
    def create_ai(wizard, difficulty='easy'):
        """Create an AI instance of the specified difficulty"""
        difficulty = difficulty.lower()
        
        if difficulty == 'easy':
            return EasyAI(wizard, difficulty)
        elif difficulty == 'medium':
            return MediumAI(wizard, difficulty)
        elif difficulty == 'hard':
            return HardAI(wizard, difficulty)
        else:
            # Default to easy
            return EasyAI(wizard, difficulty)
    
    @staticmethod
    def get_available_difficulties():
        """Get list of available AI difficulties"""
        return ['easy', 'medium', 'hard']

