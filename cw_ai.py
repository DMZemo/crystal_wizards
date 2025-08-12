"""
Crystal Wizards - Robust AI System
Redesigned for reliability, appropriate difficulty scaling, and never freezing.

Features:
- Timeout protection with hard time limits
- Failsafe mechanisms that prevent freezes
- Easy/Medium/Hard difficulty scaling
- Simple but effective heuristics
- Robust error handling
"""

import random
import time
import signal
import logging
from collections import defaultdict

# Set up logging for AI decisions (optional debug info)
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class TimeoutException(Exception):
    """Exception raised when AI thinking exceeds time limit"""
    pass


def timeout_handler(signum, frame):
    """Signal handler for timeout protection"""
    raise TimeoutException("AI thinking timed out")


class SafeAI:
    """
    Base AI class with timeout protection and failsafe mechanisms.
    Never allows the AI to freeze or crash the game.
    """
    
    def __init__(self, wizard, difficulty='easy'):
        self.wizard = wizard
        self.difficulty = difficulty.lower()
        self.max_thinking_time = self._get_max_thinking_time()
        self.fallback_used = False
        
        # Simple state tracking for better decisions
        self.last_action_type = None
        self.resource_preference = self._init_resource_preference()
    
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
            self.wizard.color: 10,  # Own color is highly valuable
            'white': 8,             # White is versatile
            'red': 5, 'blue': 5, 'green': 5, 'yellow': 5
        }
        preferences.pop(self.wizard.color, None)  # Remove duplicate
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
        action_count = 0
        max_actions = min(3, game.max_actions_per_turn)
        # BUGFIX: Add iteration counter to prevent infinite loops with free actions
        iteration_count = 0
        max_iterations = 10  # Prevent infinite loops (3 real actions + up to 7 free actions)
        
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
            
            iteration_count += 1  # BUGFIX: Always increment iteration counter
                
            # Only count actions that consume from the game's action limit
            if not self._is_free_action(action_type):
                action_count += 1
                
        # BUGFIX: Log if we hit iteration limit to help debug any remaining issues
        if iteration_count >= max_iterations:
            logger.debug(f"AI {self.wizard.color} hit iteration limit ({max_iterations})")
            
        # BUGFIX: Ensure the AI always makes at least one action if it has no valid actions
        if iteration_count == 0:
            logger.debug(f"AI {self.wizard.color} found no valid actions, using emergency fallback")
            self._quick_fallback_action(game)
    
    def _choose_and_execute_action(self, game):
        """Choose and execute the best available action"""
        # Get all possible actions
        possible_actions = self._get_possible_actions(game)
        if not possible_actions:
            return False, None
        
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
        
        # Spell casting (highest priority when available)
        if game.can_cast_spell(self.wizard):
            for spell_card in self.wizard.cards_laid_down:
                if spell_card.is_fully_charged():
                    enemies = game.get_adjacent_enemies(self.wizard)
                    if enemies:
                        actions.append({
                            'type': 'cast_spell',
                            'spell_card': spell_card,
                            'targets': enemies,
                            'priority': 100
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
                actions.append({
                    'type': 'heal',
                    'position': pos,
                    'priority': 80 + healing_needed * 10
                })
            
            # Colored crystal mining
            if (game.board.is_mine(pos) and 
                self.wizard.can_hold_more_crystals()):
                mine_color = getattr(game.board, 'get_mine_color', lambda x: 'unknown')(pos)
                color_value = self.resource_preference.get(mine_color, 3)
                actions.append({
                    'type': 'mine_colored',
                    'position': pos,
                    'color': mine_color,
                    'priority': 40 + color_value
                })
        
        # Card management
        self._add_card_actions(actions, game)
        
        # Movement
        if game.can_move(self.wizard):
            self._add_movement_actions(actions, game)
        
        return actions
    
    def _add_card_actions(self, actions, game):
        """Add spell card related actions"""
        # Lay down cards
        if len(self.wizard.cards_laid_down) < 2 and self.wizard.hand:
            for i, card in enumerate(self.wizard.hand):
                affordability = self._calculate_affordability(card)
                if affordability > 0.3:  # Only lay down affordable cards
                    actions.append({
                        'type': 'lay_card',
                        'card_index': i,
                        'card': card,
                        'priority': 30 + affordability * 20
                    })
        
        # Charge cards
        for card in self.wizard.cards_laid_down:
            if not card.is_fully_charged():
                for color in ['red', 'blue', 'green', 'yellow', 'white']:
                    if self.wizard.crystals[color] > 0:
                        # Test if this crystal can charge the card without contaminating state
                        temp_crystals = self.wizard.crystals.copy()
                        temp_crystals_used = card.crystals_used.copy()
                        
                        can_charge = card.add_crystals(color, 1, self.wizard)
                        
                        # Restore both wizard crystals AND card crystals_used state
                        self.wizard.crystals = temp_crystals
                        card.crystals_used = temp_crystals_used
                        
                        if can_charge:
                            charging_value = self._evaluate_charging(card, color)
                            actions.append({
                                'type': 'charge_card',
                                'card': card,
                                'color': color,
                                'priority': 50 + charging_value
                            })
    
    def _add_movement_actions(self, actions, game):
        """Add movement actions to nearby valuable positions"""
        adjacent_positions = game.board.get_adjacent_positions(self.wizard.location)
        
        for pos in adjacent_positions:
            move_value = self._evaluate_position(pos, game)
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
        actions.sort(key=lambda x: x['priority'] + random.randint(-10, 10), reverse=True)
        
        # Pick from top 3 actions (or all if fewer)
        candidates = actions[:min(3, len(actions))]
        return random.choice(candidates)
    
    def _medium_action_selection(self, actions):
        """Medium AI: Better priorities, less randomness"""
        actions.sort(key=lambda x: x['priority'] + random.randint(-5, 5), reverse=True)
        
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
        
        # Bonus for actions that set up future combos
        if action['type'] == 'lay_card':
            # Prefer cards we can charge soon
            card = action['card']
            for color in card.cost:
                if color == 'wild':
                    if self.wizard.crystals[self.wizard.color] > 0 or self.wizard.crystals['white'] > 0:
                        bonus += 5
                elif self.wizard.crystals[color] > 0 or self.wizard.crystals['white'] > 0:
                    bonus += 5
        
        if action['type'] == 'move':
            # Prefer positions that set up multiple future opportunities
            pos = action['target']
            future_opportunities = 0
            
            if game.board.has_crystals_at_position(pos):
                future_opportunities += 1
            if game.board.is_mine(pos):
                future_opportunities += 1
            if game.board.is_healing_springs(pos) and self.wizard.health < 6:
                future_opportunities += 1
            
            # Check for potential spell targets
            potential_targets = game.get_adjacent_enemies_at_position(pos, self.wizard)
            if potential_targets and self.wizard.has_charged_spells():
                future_opportunities += 2
            
            bonus += future_opportunities * 3
        
        return bonus
    
    def _execute_action(self, action, game):
        """Execute the chosen action"""
        action_type = action['type']
        success = False
        
        try:
            if action_type == 'cast_spell':
                success = game.cast_spell(self.wizard, action['spell_card'])
            
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
        
        # Bonus if this completes the card
        progress_before = card.get_charging_progress()
        temp_crystals = self.wizard.crystals.copy()
        temp_crystals_used = card.crystals_used.copy()
        
        if card.add_crystals(crystal_color, 1, self.wizard):
            progress_after = card.get_charging_progress()
            # Restore both wizard crystals AND card crystals_used state
            self.wizard.crystals = temp_crystals
            card.crystals_used = temp_crystals_used
            
            progress_gain = progress_after - progress_before
            base_value += progress_gain * 30
            
            if progress_after >= 1.0:
                base_value += 50  # Big bonus for completion
        
        return base_value
    
    def _evaluate_position(self, pos, game):
        """Evaluate the value of moving to a position"""
        value = 0
        
        # Resource gathering opportunities
        if game.board.has_crystals_at_position(pos):
            value += 20
        
        if game.board.is_mine(pos):
            mine_color = getattr(game.board, 'get_mine_color', lambda x: 'unknown')(pos)
            color_preference = self.resource_preference.get(mine_color, 3)
            value += 10 + color_preference
        
        # Healing opportunities
        if game.board.is_healing_springs(pos):
            if self.wizard.health <= 4:
                value += (6 - self.wizard.health) * 8
        
        # Combat positioning
        try:
            potential_targets = game.get_adjacent_enemies_at_position(pos, self.wizard)
            if potential_targets and self.wizard.has_charged_spells():
                value += len(potential_targets) * 25
            elif potential_targets and not self.wizard.has_charged_spells():
                value -= len(potential_targets) * 5  # Avoid enemies if no spells
        except:
            pass  # In case method doesn't exist
        
        return value
    
    def _emergency_fallback(self, game):
        """Emergency fallback when main AI logic fails"""
        self.fallback_used = True
        logger.warning(f"AI {self.wizard.color} using emergency fallback")
        
        # Try one simple random action
        self._quick_fallback_action(game)
    
    def _quick_fallback_action(self, game):
        """Perform one quick random valid action"""
        # Try actions in order of simplicity
        
        # Try to cast spell if ready
        if game.can_cast_spell(self.wizard):
            for spell_card in self.wizard.cards_laid_down:
                if spell_card.is_fully_charged():
                    enemies = game.get_adjacent_enemies(self.wizard)
                    if enemies:
                        game.cast_spell(self.wizard, spell_card)
                        return
        
        # Try to mine
        if game.can_mine(self.wizard):
            pos = self.wizard.location
            if (game.board.has_crystals_at_position(pos) and 
                not game.board.is_mine(pos) and 
                self.wizard.can_hold_more_crystals()):
                game.mine_white_crystal(self.wizard, pos)
                return
            elif game.board.is_healing_springs(pos) and self.wizard.health < 6:
                roll = random.randint(1, 3)
                game.resolve_mine_with_roll(self.wizard, pos, roll)
                return
            elif game.board.is_mine(pos) and self.wizard.can_hold_more_crystals():
                roll = random.randint(1, 6)
                game.resolve_mine_with_roll(self.wizard, pos, roll)
                return
        
        # Try to move randomly
        if game.can_move(self.wizard):
            adjacent = game.board.get_adjacent_positions(self.wizard.location)
            if adjacent:
                target = random.choice(adjacent)
                game.move_player(self.wizard, target)
                return
        
        # If all else fails, try to lay down a card or charge something
        if len(self.wizard.cards_laid_down) < 2 and self.wizard.hand:
            self.wizard.lay_down_spell_card(0)
            return
        
        # Try to charge a card
        for card in self.wizard.cards_laid_down:
            if not card.is_fully_charged():
                for color in ['white', 'red', 'blue', 'green', 'yellow']:
                    if self.wizard.crystals[color] > 0:
                        card.add_crystals(color, 1, self.wizard)
                        return
        
        # BUGFIX: Ultimate fallback - force end turn by setting action count to max
        # This ensures the AI never gets completely stuck with no valid actions
        logger.debug(f"AI {self.wizard.color} using ultimate fallback - ending turn")
        game.current_actions = game.max_actions_per_turn


class AIManager:
    """Factory class to create AI instances based on difficulty"""
    
    @staticmethod
    def create_ai(wizard, difficulty='easy'):
        """Create an AI instance of the specified difficulty"""
        difficulty = difficulty.lower()
        
        if difficulty in ['easy', 'medium', 'hard']:
            return SafeAI(wizard, difficulty)
        else:
            # Default to easy for unknown difficulties
            logger.warning(f"Unknown difficulty '{difficulty}', defaulting to easy")
            return SafeAI(wizard, 'easy')
    
    @staticmethod
    def get_available_difficulties():
        """Get list of available AI difficulties"""
        return ['easy', 'medium', 'hard']
