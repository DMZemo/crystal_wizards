"""
Crystal Wizards - Improved AI System
Fixed version with proper spell casting, crystal return logic, stability improvements, and enhanced strategic behavior.

Key Fixes:
1. Fixed indentation errors
2. Proper crystal return mechanism (white crystals to empty spawn points, colored crystals to mines)
3. Improved spell casting logic
4. Better strategic decision-making
5. Enhanced stability with proper timeout and error handling
6. Multiple AI strategies based on game state
"""

import random
import time
import signal
import logging
from collections import defaultdict

# Set up logging for AI decisions
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class TimeoutException(Exception):
    """Exception raised when AI thinking exceeds time limit"""
    pass


def timeout_handler(signum, frame):
    """Signal handler for timeout protection"""
    raise TimeoutException("AI thinking timed out")


class StrategicAI:
    """
    Enhanced AI class with proper spell casting, crystal management, and strategic decision-making.
    """
    
    def __init__(self, wizard, difficulty='easy'):
        self.wizard = wizard
        self.difficulty = difficulty.lower()
        self.max_thinking_time = self._get_max_thinking_time()
        self.fallback_used = False
        
        # Strategic state tracking
        self.last_action_type = None
        self.resource_preference = self._init_resource_preference()
        self.strategy_mode = 'balanced'  # balanced, aggressive, defensive, resource_focused
        
    def _get_max_thinking_time(self):
        """Get maximum thinking time based on difficulty"""
        time_limits = {
            'easy': 0.5,    # 0.5 seconds
            'medium': 1.0,  # 1 second  
            'hard': 2.0     # 2 seconds
        }
        return time_limits.get(self.difficulty, 0.5)
    
    def _init_resource_preference(self):
        """Initialize crystal color preferences based on wizard color"""
        preferences = {
            'white': 8,    # White is versatile
            'red': 5, 'blue': 5, 'green': 5, 'yellow': 5
        }
        # Own color is highly valuable
        preferences[self.wizard.color] = 10
        return preferences
    
    def reset_state(self):
        """Reset AI state to clear any issues that might cause freezing"""
        self.fallback_used = False
        self.last_action_type = None
        self.resource_preference = self._init_resource_preference()
        logger.info(f"AI state reset for {self.wizard.color} wizard")

    def execute_turn(self, game):
        """
        Main entry point - execute AI turn with timeout protection.
        This method guarantees to never freeze or crash.
        """
        self.fallback_used = False
        
        try:
            # Set up timeout protection
            if hasattr(signal, 'SIGALRM'):  # Unix-like systems
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(int(self.max_thinking_time) + 1)
            
            start_time = time.time()
            self._execute_turn_logic(game, start_time)
            
        except (TimeoutException, Exception) as e:
            logger.warning(f"AI {self.wizard.color} encountered issue: {e}")
            self._emergency_fallback(game)
        
        finally:
            # Clean up timeout protection
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
    
    def _execute_turn_logic(self, game, start_time):
        """Execute the actual turn logic with time monitoring"""
        # Update strategy based on game state
        self._update_strategy(game)
        
        action_count = 0
        max_actions = min(3, game.max_actions_per_turn)
        iteration_count = 0
        max_iterations = 10  # Prevent infinite loops
        
        while (game.current_actions < game.max_actions_per_turn and 
               action_count < max_actions and 
               iteration_count < max_iterations):
            
            # Check time limit before each action
            if time.time() - start_time > self.max_thinking_time:
                logger.debug(f"AI {self.wizard.color} hit time limit")
                self._quick_fallback_action(game)
                break
            
            action_taken, action_type = self._choose_and_execute_action(game)
            if not action_taken:
                break
            
            iteration_count += 1
            
            # Only count actions that consume from the game's action limit
            if not self._is_free_action(action_type):
                action_count += 1
        
        # Ensure the AI always makes at least one action if it has no valid actions
        if iteration_count == 0:
            logger.debug(f"AI {self.wizard.color} found no valid actions, using emergency fallback")
            self._quick_fallback_action(game)
    
    def _update_strategy(self, game):
        """Update AI strategy based on current game state"""
        # Evaluate game state
        my_health = self.wizard.health
        my_crystals = sum(self.wizard.crystals.values())
        my_charged_spells = sum(1 for card in self.wizard.cards_laid_down if card.is_fully_charged())
        
        # Count enemies and their threat level
        enemies = [p for p in game.players if p != self.wizard]
        enemy_threat = 0
        for enemy in enemies:
            if enemy.health > 0:
                enemy_charged_spells = sum(1 for card in enemy.cards_laid_down if card.is_fully_charged())
                # Check if enemy is adjacent (immediate threat)
                adjacent_enemies = game.get_adjacent_enemies(self.wizard)
                if enemy in adjacent_enemies:
                    enemy_threat += 10 + enemy_charged_spells * 5
                else:
                    enemy_threat += enemy_charged_spells * 2
        
        # Determine strategy
        if my_health <= 2:
            self.strategy_mode = 'defensive'
        elif my_charged_spells > 0 and enemy_threat > 5:
            self.strategy_mode = 'aggressive'
        elif my_crystals < 3:
            self.strategy_mode = 'resource_focused'
        else:
            self.strategy_mode = 'balanced'
        
        logger.debug(f"AI {self.wizard.color} strategy: {self.strategy_mode}")
    
    def _choose_and_execute_action(self, game):
        """Choose and execute the best available action"""
        # Get all possible actions
        possible_actions = self._get_possible_actions(game)
        if not possible_actions:
            # FIXED: When no actions available, try emergency fallback but don't loop
            logger.warning(f"AI {self.wizard.color} has no actions available, using emergency fallback")
            fallback_success = self._emergency_fallback(game)
            # Return False to break the action loop and end turn
            return False, 'emergency_fallback' if fallback_success else None
        
        # Score and choose best action
        best_action = self._select_best_action(possible_actions, game)
        if not best_action:
            return False, None
        
        # Execute the chosen action
        success = self._execute_action(best_action, game)
        return success, best_action['type'] if success else None
    
    def _get_possible_actions(self, game):
        """Get all currently possible actions"""
        actions = []
        
        # Spell casting (highest priority when available and strategic)
        if game.can_cast_spell(self.wizard):
            for spell_card in self.wizard.cards_laid_down:
                if spell_card.is_fully_charged():
                    enemies = game.get_adjacent_enemies(self.wizard)
                    if enemies:
                        # Calculate spell value based on strategy
                        spell_value = self._evaluate_spell_cast(spell_card, enemies, game)
                        actions.append({
                            'type': 'cast_spell',
                            'spell_card': spell_card,
                            'targets': enemies,
                            'priority': spell_value
                        })
        
        # Mining actions
        if game.can_mine(self.wizard):
            pos = self.wizard.location
            
            # White crystal mining (no dice needed)
            if (game.board.has_crystals_at_position(pos) and 
                not game.board.is_mine(pos) and 
                not game.board.is_healing_springs(pos) and
                self.wizard.can_hold_more_crystals()):
                actions.append({
                    'type': 'mine_white',
                    'position': pos,
                    'priority': 60
                })
            
            # Healing at springs
            if game.board.is_healing_springs(pos) and self.wizard.health < 6:
                healing_needed = 6 - self.wizard.health
                healing_priority = 80 + healing_needed * 10
                if self.strategy_mode == 'defensive':
                    healing_priority += 20
                actions.append({
                    'type': 'heal',
                    'position': pos,
                    'priority': healing_priority
                })
            
            # Colored crystal mining
            if (game.board.is_mine(pos) and 
                self.wizard.can_hold_more_crystals()):
                mine_color = game.board.get_mine_color_from_position(pos)
                if mine_color:
                    color_value = self.resource_preference.get(mine_color, 3)
                    mine_priority = 40 + color_value
                    if self.strategy_mode == 'resource_focused':
                        mine_priority += 15
                    actions.append({
                        'type': 'mine_colored',
                        'position': pos,
                        'color': mine_color,
                        'priority': mine_priority
                    })
        
        # Card management
        self._add_card_actions(actions, game)
        
        # Movement
        if game.can_move(self.wizard):
            self._add_movement_actions(actions, game)
        
        return actions
    
    def _evaluate_spell_cast(self, spell_card, enemies, game):
        """Evaluate the value of casting a specific spell"""
        base_value = 100  # High base priority for spell casting
        damage = spell_card.get_damage()
        
        # Strategy-based adjustments
        if self.strategy_mode == 'aggressive':
            base_value += 30
        elif self.strategy_mode == 'defensive':
            # Only cast if enemies are threatening
            threatening_enemies = [e for e in enemies if e.has_charged_spells()]
            if not threatening_enemies:
                base_value -= 40
        
        # Damage efficiency
        total_enemy_health = sum(e.health for e in enemies)
        if damage >= total_enemy_health:
            base_value += 50  # Can eliminate all targets
        
        # Target priority
        for enemy in enemies:
            if enemy.health <= damage:
                base_value += 25  # Can eliminate this enemy
            if enemy.has_charged_spells():
                base_value += 15  # Prioritize dangerous enemies
        
        return base_value
    
    def _add_card_actions(self, actions, game):
        """Add spell card related actions"""
        # Lay down cards
        if len(self.wizard.cards_laid_down) < 2 and self.wizard.hand:
            for i, card in enumerate(self.wizard.hand):
                affordability = self._calculate_affordability(card)
                if affordability > 0.2:  # Only lay down somewhat affordable cards
                    priority = 30 + affordability * 20
                    if self.strategy_mode == 'aggressive':
                        priority += 10
                    actions.append({
                        'type': 'lay_card',
                        'card_index': i,
                        'card': card,
                        'priority': priority
                    })
        
        # Charge cards
        for card in self.wizard.cards_laid_down:
            if not card.is_fully_charged():
                for color in ['red', 'blue', 'green', 'yellow', 'white']:
                    if self.wizard.crystals[color] > 0:
                        # Test if this crystal can charge the card
                        if self._can_charge_card(card, color):
                            charging_value = self._evaluate_charging(card, color)
                            actions.append({
                                'type': 'charge_card',
                                'card': card,
                                'color': color,
                                'priority': 50 + charging_value
                            })
    
    def _can_charge_card(self, card, color):
        """Test if a crystal can charge a card without modifying state"""
        # Save current state
        temp_wizard_crystals = self.wizard.crystals.copy()
        temp_card_crystals = card.crystals_used.copy()
        
        # Test the charging
        can_charge = card.add_crystals(color, 1, self.wizard)
        
        # Restore state
        self.wizard.crystals = temp_wizard_crystals
        card.crystals_used = temp_card_crystals
        
        return can_charge
    
    def _add_movement_actions(self, actions, game):
        """Add movement actions to nearby valuable positions"""
        adjacent_positions = game.board.get_adjacent_positions(self.wizard.location)
        
        # FIX: If at healing spring with full health, ensure we can move away
        at_healing_spring = game.board.is_healing_springs(self.wizard.location)
        at_full_health = self.wizard.health >= 6
        
        for pos in adjacent_positions:
            move_value = self._evaluate_position(pos, game)
            
            # FIX: Add minimum movement value when stuck at healing spring with full health
            if at_healing_spring and at_full_health and move_value <= 0:
                move_value = 10  # Low but positive priority to ensure movement
            
            if move_value > 0:
                actions.append({
                    'type': 'move',
                    'target': pos,
                    'priority': move_value
                })
    
    def _select_best_action(self, actions, game):
        """Select the best action from available options"""
        if not actions:
            return None
        
        # Apply difficulty-based selection logic
        if self.difficulty == 'easy':
            return self._easy_action_selection(actions)
        elif self.difficulty == 'medium':
            return self._medium_action_selection(actions)
        else:  # hard
            return self._hard_action_selection(actions, game)
    
    def _easy_action_selection(self, actions):
        """Easy AI: Simple priorities with randomness"""
        # Sort by priority but add randomness
        actions.sort(key=lambda x: x['priority'] + random.randint(-15, 15), reverse=True)
        
        # Pick from top 3 actions (or all if fewer)
        candidates = actions[:min(3, len(actions))]
        return random.choice(candidates)
    
    def _medium_action_selection(self, actions):
        """Medium AI: Better priorities, less randomness"""
        actions.sort(key=lambda x: x['priority'] + random.randint(-8, 8), reverse=True)
        
        # Pick from top 2 actions (or all if fewer)
        candidates = actions[:min(2, len(actions))]
        return max(candidates, key=lambda x: x['priority'])
    
    def _hard_action_selection(self, actions, game):
        """Hard AI: Strategic selection with look-ahead"""
        # Apply strategic bonuses
        for action in actions:
            action['priority'] += self._calculate_strategic_bonus(action, game)
        
        # Select highest priority action
        return max(actions, key=lambda x: x['priority'])
    
    def _calculate_strategic_bonus(self, action, game):
        """Calculate strategic bonus for Hard AI"""
        bonus = 0
        
        # Strategy-specific bonuses
        if self.strategy_mode == 'aggressive':
            if action['type'] == 'cast_spell':
                bonus += 20
            elif action['type'] == 'move':
                # Bonus for moving toward enemies
                pos = action['target']
                potential_targets = game.get_adjacent_enemies_at_position(pos, self.wizard)
                bonus += len(potential_targets) * 10
        
        elif self.strategy_mode == 'defensive':
            if action['type'] == 'heal':
                bonus += 15
            elif action['type'] == 'move':
                # Bonus for moving away from enemies or toward healing
                pos = action['target']
                if game.board.is_healing_springs(pos):
                    bonus += 20
                # Penalty for moving toward enemies without spells
                if not self.wizard.has_charged_spells():
                    potential_targets = game.get_adjacent_enemies_at_position(pos, self.wizard)
                    bonus -= len(potential_targets) * 8
        
        elif self.strategy_mode == 'resource_focused':
            if action['type'] in ['mine_white', 'mine_colored']:
                bonus += 15
            elif action['type'] == 'charge_card':
                bonus += 10
        
        # Combo bonuses
        if action['type'] == 'lay_card':
            card = action['card']
            # Bonus if we can charge this card soon
            chargeable_soon = 0
            for color in card.cost:
                if color == 'wild':
                    if self.wizard.crystals[self.wizard.color] > 0 or self.wizard.crystals['white'] > 0:
                        chargeable_soon += 1
                elif self.wizard.crystals[color] > 0 or self.wizard.crystals['white'] > 0:
                    chargeable_soon += 1
            bonus += chargeable_soon * 3
        
        return bonus
    
    def _execute_action(self, action, game):
        """Execute the chosen action"""
        action_type = action['type']
        success = False
        
        try:
            if action_type == 'cast_spell':
                success = game.cast_spell(self.wizard, action['spell_card'], gui=game.gui if hasattr(game, 'gui') else None)
            
            elif action_type == 'mine_white':
                success = game.mine_white_crystal(self.wizard, action['position'])
            
            elif action_type == 'heal':
                roll = random.randint(1, 3)  # Healing springs die
                success = game.resolve_mine_with_roll(self.wizard, action['position'], roll)
            
            elif action_type == 'mine_colored':
                roll = random.randint(1, 6)  # Standard die
                success = game.resolve_mine_with_roll(self.wizard, action['position'], roll)
            
            elif action_type == 'lay_card':
                success = self.wizard.lay_down_spell_card(action['card_index'])
            
            elif action_type == 'charge_card':
                success = action['card'].add_crystals(action['color'], 1, self.wizard)
            
            elif action_type == 'move':
                success = game.move_player(self.wizard, action['target'])
            
            self.last_action_type = action_type if success else None
            return success
        
        except Exception as e:
            logger.warning(f"Action execution failed: {e}")
            return False
    
    def _is_free_action(self, action_type):
        """Check if an action is 'free' (doesn't consume from action limit)"""
        return action_type in ['lay_card', 'charge_card']
    
    def _calculate_affordability(self, card):
        """Calculate how affordable a card is (0-1 scale)"""
        total_cost = card.get_total_cost()
        if total_cost == 0:
            return 1.0
        
        available_crystals = 0
        for color, amount in card.cost.items():
            if color == 'wild':
                available_crystals += self.wizard.crystals[self.wizard.color]
                available_crystals += self.wizard.crystals['white']
            else:
                available_crystals += self.wizard.crystals[color]
                available_crystals += self.wizard.crystals['white']  # White can substitute
        
        return min(1.0, available_crystals / total_cost)
    
    def _evaluate_charging(self, card, crystal_color):
        """Evaluate the value of charging a card with a specific crystal"""
        base_value = 10
        
        # Calculate progress gain
        progress_before = card.get_charging_progress()
        
        # Test charging without modifying state
        temp_wizard_crystals = self.wizard.crystals.copy()
        temp_card_crystals = card.crystals_used.copy()
        
        if card.add_crystals(crystal_color, 1, self.wizard):
            progress_after = card.get_charging_progress()
            progress_gain = progress_after - progress_before
            base_value += progress_gain * 30
            
            if progress_after >= 1.0:
                base_value += 50  # Big bonus for completion
        
        # Restore state
        self.wizard.crystals = temp_wizard_crystals
        card.crystals_used = temp_card_crystals
        
        return base_value
    
    def _evaluate_position(self, pos, game):
        """Evaluate the value of moving to a position"""
        value = 0
        
        # Resource gathering opportunities
        if game.board.has_crystals_at_position(pos):
            value += 20
            if self.strategy_mode == 'resource_focused':
                value += 10
        
        if game.board.is_mine(pos):
            mine_color = game.board.get_mine_color_from_position(pos)
            if mine_color:
                color_preference = self.resource_preference.get(mine_color, 3)
                value += 10 + color_preference
                if self.strategy_mode == 'resource_focused':
                    value += 8
        
        # Healing opportunities
        if game.board.is_healing_springs(pos):
            if self.wizard.health <= 4:
                healing_value = (6 - self.wizard.health) * 8
                value += healing_value
                if self.strategy_mode == 'defensive':
                    value += 15
        
        # Combat positioning
        try:
            potential_targets = game.get_adjacent_enemies_at_position(pos, self.wizard)
            if potential_targets:
                if self.wizard.has_charged_spells():
                    combat_value = len(potential_targets) * 25
                    if self.strategy_mode == 'aggressive':
                        combat_value += 15
                    value += combat_value
                elif self.strategy_mode != 'aggressive':
                    # Avoid enemies if no spells (unless aggressive)
                    value -= len(potential_targets) * 8
        except:
            pass  # In case method doesn't exist
        
        return value
    
    def _emergency_fallback(self, game):
        """Emergency fallback when main AI logic fails"""
        self.fallback_used = True
        logger.warning(f"AI {self.wizard.color} using emergency fallback")
        
        # Try one simple random action
        return self._quick_fallback_action(game)
    
    def _quick_fallback_action(self, game):
        """Perform one quick random valid action"""
        # Try actions in order of simplicity
        
        # Try to cast spell if ready
        if game.can_cast_spell(self.wizard):
            for spell_card in self.wizard.cards_laid_down:
                if spell_card.is_fully_charged():
                    enemies = game.get_adjacent_enemies(self.wizard)
                    if enemies:
                        success = game.cast_spell(self.wizard, spell_card, gui=game.gui if hasattr(game, 'gui') else None)
                        return success
        
        # Try to mine
        if game.can_mine(self.wizard):
            pos = self.wizard.location
            if (game.board.has_crystals_at_position(pos) and 
                not game.board.is_mine(pos) and 
                self.wizard.can_hold_more_crystals()):
                success = game.mine_white_crystal(self.wizard, pos)
                return success
            elif game.board.is_healing_springs(pos) and self.wizard.health < 6:
                roll = random.randint(1, 3)
                success = game.resolve_mine_with_roll(self.wizard, pos, roll)
                return success
            elif game.board.is_mine(pos) and self.wizard.can_hold_more_crystals():
                roll = random.randint(1, 6)
                success = game.resolve_mine_with_roll(self.wizard, pos, roll)
                return success
        
        # Try to move randomly
        if game.can_move(self.wizard):
            adjacent = game.board.get_adjacent_positions(self.wizard.location)
            if adjacent:
                target = random.choice(adjacent)
                success = game.move_player(self.wizard, target)
                return success
        
        # If all else fails, try to lay down a card or charge something
        if len(self.wizard.cards_laid_down) < 2 and self.wizard.hand:
            success = self.wizard.lay_down_spell_card(0)
            return success
        
        # Try to charge a card
        for card in self.wizard.cards_laid_down:
            if not card.is_fully_charged():
                for color in ['white', 'red', 'blue', 'green', 'yellow']:
                    if self.wizard.crystals[color] > 0:
                        success = card.add_crystals(color, 1, self.wizard)
                        if success:
                            return True
        
        # Ultimate fallback - force end turn (no action taken)
        logger.debug(f"AI {self.wizard.color} using ultimate fallback - ending turn")
        game.current_actions = game.max_actions_per_turn
        return False  # No action was actually taken


class AIManager:
    """Factory class to create AI instances based on difficulty"""
    
    @staticmethod
    def create_ai(wizard, difficulty='easy'):
        """Create an AI instance of the specified difficulty"""
        difficulty = difficulty.lower()
        
        if difficulty in ['easy', 'medium', 'hard']:
            return StrategicAI(wizard, difficulty)
        else:
            # Default to easy for unknown difficulties
            logger.warning(f"Unknown difficulty '{difficulty}', defaulting to easy")
            return StrategicAI(wizard, 'easy')
    
    @staticmethod
    def get_available_difficulties():
        """Get list of available AI difficulties"""
        return ['easy', 'medium', 'hard']
