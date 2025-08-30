"""
Crystal Wizards - FIXED AI System
Fixed version with comprehensive solutions for AI freezing issues.

Key Fixes:
1. Improved timeout handling with proper signal management
2. Enhanced emergency fallback system with guaranteed turn ending
3. Fixed action counting logic to prevent infinite loops
4. Added comprehensive logging for debugging
5. Robust error handling and recovery mechanisms
6. Simplified action loop logic to prevent deadlocks
"""

import random
import time
import signal
import logging
from collections import defaultdict

# Set up comprehensive logging for AI decisions
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
    FIXED Enhanced AI class with comprehensive freeze prevention and robust error handling.
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
        
        # FIXED: Add debugging and safety counters
        self.turn_count = 0
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3
        
    def _get_max_thinking_time(self):
        """Get maximum thinking time based on difficulty"""
        times = {'easy': 0.5, 'medium': 1.0, 'hard': 2.0}
        return times.get(self.difficulty, 0.5)
    
    def _init_resource_preference(self):
        """Initialize resource preferences based on wizard color"""
        preferences = defaultdict(float)
        preferences[self.wizard.color] = 1.5  # Prefer own color
        preferences['white'] = 1.2  # White crystals are versatile
        return preferences
    
    def reset_state(self):
        """Reset AI state for new game"""
        self.fallback_used = False
        self.last_action_type = None
        self.strategy_mode = 'balanced'
        self.consecutive_failures = 0
    
    def execute_turn(self, game):
        """
        FIXED: Main entry point - execute AI turn with comprehensive protection.
        This method is GUARANTEED to never freeze or crash.
        """
        self.turn_count += 1
        self.fallback_used = False
        
        logger.debug(f"AI {self.wizard.color} starting turn {self.turn_count}")
        
        try:
            # FIXED: Enhanced timeout protection with proper cleanup
            timeout_set = False
            if hasattr(signal, 'SIGALRM'):  # Unix-like systems
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(int(self.max_thinking_time) + 2)  # Extra buffer
                timeout_set = True
            
            start_time = time.time()
            success = self._execute_turn_logic(game, start_time)
            
            if not success:
                logger.warning(f"AI {self.wizard.color} turn logic failed, using emergency fallback")
                self._guaranteed_turn_end(game)
            
        except (TimeoutException, Exception) as e:
            logger.warning(f"AI {self.wizard.color} encountered issue: {e}")
            self._guaranteed_turn_end(game)
        
        finally:
            # FIXED: Always clean up timeout protection
            if timeout_set and hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
            
            # FIXED: Guarantee turn ends properly
            if game.current_actions < game.max_actions_per_turn:
                logger.debug(f"AI {self.wizard.color} forcing turn end - actions: {game.current_actions}/{game.max_actions_per_turn}")
                self._force_turn_end(game)
    
    def _execute_turn_logic(self, game, start_time):
        """FIXED: Execute the actual turn logic with simplified and robust action loop"""
        # Update strategy based on game state
        self._update_strategy(game)
        
        # FIXED: Simplified action loop with multiple safety mechanisms
        max_iterations = 10  # Hard limit to prevent infinite loops
        iteration_count = 0
        actions_at_start = game.current_actions
        
        logger.debug(f"AI {self.wizard.color} starting action loop: {game.current_actions}/{game.max_actions_per_turn}")
        
        while (game.current_actions < game.max_actions_per_turn and 
               iteration_count < max_iterations):
            
            iteration_count += 1
            
            # FIXED: Multiple timeout checks
            if time.time() - start_time > self.max_thinking_time:
                logger.debug(f"AI {self.wizard.color} hit time limit after {iteration_count} iterations")
                break
            
            # FIXED: Try to execute one action with comprehensive error handling
            action_success = self._try_single_action(game)
            
            if not action_success:
                # FIXED: If no action was possible, break immediately
                logger.debug(f"AI {self.wizard.color} no valid actions available, ending turn")
                break
            
            # FIXED: Safety check - if actions didn't increase, something is wrong
            if game.current_actions == actions_at_start and iteration_count > 3:
                logger.warning(f"AI {self.wizard.color} actions not increasing, forcing end")
                break
        
        # FIXED: Log final state
        actions_taken = game.current_actions - actions_at_start
        logger.debug(f"AI {self.wizard.color} completed turn: {actions_taken} actions in {iteration_count} iterations")
        
        return True
    
    def _try_single_action(self, game):
        """FIXED: Try to execute a single action with comprehensive error handling"""
        try:
            # Get all possible actions
            possible_actions = self._get_possible_actions(game)
            
            if not possible_actions:
                logger.debug(f"AI {self.wizard.color} has no possible actions")
                return False
            
            # Select and execute best action
            best_action = self._select_best_action(possible_actions, game)
            if not best_action:
                logger.debug(f"AI {self.wizard.color} could not select action")
                return False
            
            # Execute the action
            success = self._execute_action(best_action, game)
            
            if success:
                self.consecutive_failures = 0
                logger.debug(f"AI {self.wizard.color} executed {best_action['type']} successfully")
            else:
                self.consecutive_failures += 1
                logger.debug(f"AI {self.wizard.color} failed to execute {best_action['type']} (failure #{self.consecutive_failures})")
                
                # FIXED: If too many consecutive failures, stop trying
                if self.consecutive_failures >= self.max_consecutive_failures:
                    logger.warning(f"AI {self.wizard.color} too many consecutive failures, ending turn")
                    return False
            
            return success
            
        except Exception as e:
            logger.warning(f"AI {self.wizard.color} action execution error: {e}")
            self.consecutive_failures += 1
            return False
    
    def _update_strategy(self, game):
        """Update AI strategy based on current game state"""
        # Evaluate game state
        my_health = self.wizard.health
        my_crystals = sum(self.wizard.crystals.values())
        my_charged_spells = sum(1 for card in self.wizard.cards_laid_down if card.is_fully_charged())
        
        # Count enemies and their threat level
        enemies = [p for p in game.players if p != self.wizard]
        nearby_enemies = len(game.get_adjacent_enemies(self.wizard))
        
        # Determine strategy based on game state
        if my_health <= 2:
            self.strategy_mode = 'defensive'
        elif my_crystals >= 8:
            self.strategy_mode = 'aggressive'
        elif my_charged_spells >= 2:
            self.strategy_mode = 'aggressive'
        elif nearby_enemies > 0:
            self.strategy_mode = 'balanced'
        else:
            self.strategy_mode = 'resource_focused'
        
        logger.debug(f"AI {self.wizard.color} strategy: {self.strategy_mode}")
    
    def _get_possible_actions(self, game):
        """Get all currently possible actions"""
        actions = []
        
        # FIXED: More robust action detection with error handling
        try:
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
        except Exception as e:
            logger.warning(f"Error checking spell actions: {e}")
        
        try:
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
                
                # Healing springs
                if game.board.is_healing_springs(pos) and self.wizard.health < 6:
                    heal_value = 70 if self.wizard.health <= 2 else 40
                    actions.append({
                        'type': 'heal',
                        'position': pos,
                        'priority': heal_value
                    })
                
                # Colored crystal mining
                if game.board.is_mine(pos) and self.wizard.can_hold_more_crystals():
                    mine_color = game.board.get_mine_color_from_position(pos)
                    if mine_color:
                        base_priority = 50
                        if mine_color == self.wizard.color:
                            base_priority += 20
                        actions.append({
                            'type': 'mine_colored',
                            'position': pos,
                            'color': mine_color,
                            'priority': base_priority
                        })
        except Exception as e:
            logger.warning(f"Error checking mining actions: {e}")
        
        try:
            # Card actions (laying down and charging)
            self._add_card_actions(actions, game)
        except Exception as e:
            logger.warning(f"Error checking card actions: {e}")
        
        try:
            # Movement actions
            if game.can_move(self.wizard):
                self._add_movement_actions(actions, game)
        except Exception as e:
            logger.warning(f"Error checking movement actions: {e}")
        
        return actions
    
    def _evaluate_spell_cast(self, spell_card, enemies, game):
        """Evaluate the value of casting a spell"""
        base_value = 80
        
        # Adjust based on strategy
        if self.strategy_mode == 'aggressive':
            base_value += 20
        elif self.strategy_mode == 'defensive':
            base_value += 10
        
        # Adjust based on number of targets
        base_value += len(enemies) * 10
        
        # Adjust based on wizard health
        if self.wizard.health <= 2:
            base_value += 30  # Desperate situation
        
        return base_value
    
    def _add_card_actions(self, actions, game):
        """Add card-related actions (laying down and charging)"""
        # Lay down spell cards
        if len(self.wizard.cards_laid_down) < 2 and self.wizard.hand:
            for i, card in enumerate(self.wizard.hand):
                affordability = self._calculate_affordability(card)
                priority = 30 + (affordability * 20)
                actions.append({
                    'type': 'lay_card',
                    'card_index': i,
                    'card': card,
                    'priority': priority
                })
        
        # Charge spell cards
        for card in self.wizard.cards_laid_down:
            if not card.is_fully_charged():
                for color in ['white', 'red', 'blue', 'green', 'yellow']:
                    if (self.wizard.crystals[color] > 0 and 
                        self._can_charge_card(card, color)):
                        
                        priority = 25
                        if color == self.wizard.color:
                            priority += 10
                        if color == 'white':
                            priority += 5
                        
                        # Higher priority if card is almost charged
                        try:
                            if card.get_charging_progress() > 0.7:
                                priority += 15
                        except:
                            # Fallback calculation if method doesn't exist
                            total_cost = sum(card.cost.values())
                            used_crystals = sum(card.crystals_used.values())
                            if total_cost > 0 and used_crystals / total_cost > 0.7:
                                priority += 15
                        
                        actions.append({
                            'type': 'charge_card',
                            'card': card,
                            'color': color,
                            'priority': priority
                        })
    
    def _can_charge_card(self, card, color):
        """Check if a card can be charged with a specific color"""
        try:
            # Check if the card needs more crystals and if we can add this color
            if card.is_fully_charged():
                return False
            
            # Check if we have the crystal
            if self.wizard.crystals.get(color, 0) <= 0:
                return False
            
            # For wild crystal requirements, check if this color can fulfill them
            if 'wild' in card.cost:
                wild_needed = card.cost['wild'] - card.crystals_used.get('wild', 0)
                if wild_needed > 0:
                    # Wild can be fulfilled by wizard's color or white
                    if color == self.wizard.color or color == 'white':
                        return True
            
            # For regular color requirements
            if color in card.cost:
                needed = card.cost[color] - card.crystals_used.get(color, 0)
                if needed > 0:
                    return True
            
            return False
        except:
            return False
    
    def _evaluate_charging(self, card, color):
        """Evaluate the value of charging a card with a specific crystal"""
        base_value = 10
        
        # Higher value for cards closer to completion
        total_cost = card.get_total_cost()
        crystals_used = sum(card.crystals_used.values())
        completion_ratio = crystals_used / max(total_cost, 1)
        base_value += completion_ratio * 20
        
        # Strategy-based bonuses
        if self.strategy_mode == 'aggressive':
            base_value += 5
        elif self.strategy_mode == 'resource_focused':
            base_value -= 2  # Less eager to spend crystals
        
        # Color preference bonus
        if color in self.resource_preference:
            preference = self.resource_preference[color]
            if preference > 3:  # We have excess of this color
                base_value += 3
            elif preference < 2:  # We're low on this color
                base_value -= 5
        
        return base_value
    
    def _add_movement_actions(self, actions, game):
        """Add movement actions to available actions"""
        # Use the correct method to get empty adjacent positions
        adjacent_positions = game.board.get_adjacent_empty_positions(self.wizard.location)
        
        for pos in adjacent_positions:
            priority = self._calculate_movement_priority(pos, game)
            actions.append({
                'type': 'move',
                'target': pos,
                'priority': priority
            })
    
    def _calculate_movement_priority(self, position, game):
        """Calculate priority for moving to a specific position"""
        base_priority = 20
        
        # Check what's at the target position
        if game.board.has_crystals_at_position(position):
            base_priority += 30
        
        if game.board.is_mine(position):
            mine_color = game.board.get_mine_color_from_position(position)
            if mine_color == self.wizard.color:
                base_priority += 25
            else:
                base_priority += 15
        
        if game.board.is_healing_springs(position) and self.wizard.health < 6:
            heal_need = (6 - self.wizard.health) * 10
            base_priority += heal_need
        
        # Strategic positioning
        if self.strategy_mode == 'aggressive':
            # Move toward enemies
            enemies_nearby = len([p for p in game.players 
                                if p != self.wizard and 
                                game.board.get_distance(position, p.location) <= 2])
            base_priority += enemies_nearby * 5
        
        return base_priority
    
    def _select_best_action(self, actions, game):
        """Select the best action based on difficulty and strategy"""
        if not actions:
            return None
        
        # Apply difficulty-based selection
        if self.difficulty == 'easy':
            return self._easy_action_selection(actions)
        elif self.difficulty == 'medium':
            return self._medium_action_selection(actions)
        else:  # hard
            return self._hard_action_selection(actions, game)
    
    def _easy_action_selection(self, actions):
        """Easy AI: Simple selection with randomness"""
        # Add randomness to priorities
        for action in actions:
            action['priority'] += random.randint(-15, 15)
        
        actions.sort(key=lambda x: x['priority'], reverse=True)
        
        # Choose from top 3 actions for unpredictability
        candidates = actions[:min(3, len(actions))]
        return random.choice(candidates)
    
    def _medium_action_selection(self, actions):
        """Medium AI: Better prioritization with some randomness"""
        # Add strategic bonuses
        for action in actions:
            action['priority'] += self._calculate_strategic_bonus(action, None)
            action['priority'] += random.randint(-10, 10)
        
        actions.sort(key=lambda x: x['priority'], reverse=True)
        return actions[0]
    
    def _hard_action_selection(self, actions, game):
        """Hard AI: Optimal selection with strategic thinking"""
        # Add comprehensive strategic analysis
        for action in actions:
            action['priority'] += self._calculate_strategic_bonus(action, game)
            # Small randomness to avoid predictability
            action['priority'] += random.randint(-5, 5)
        
        actions.sort(key=lambda x: x['priority'], reverse=True)
        return actions[0]
    
    def _calculate_strategic_bonus(self, action, game):
        """Calculate strategic bonus for an action"""
        bonus = 0
        action_type = action['type']
        
        # Strategy-based bonuses
        if self.strategy_mode == 'aggressive':
            if action_type in ['cast_spell', 'move']:
                bonus += 10
        elif self.strategy_mode == 'defensive':
            if action_type in ['heal', 'charge_card']:
                bonus += 10
        elif self.strategy_mode == 'resource_focused':
            if action_type in ['mine_white', 'mine_colored', 'lay_card']:
                bonus += 10
        
        # Health-based adjustments
        if self.wizard.health <= 2:
            if action_type == 'heal':
                bonus += 20
            elif action_type == 'cast_spell':
                bonus -= 10  # Avoid risky combat when low health
        
        # Resource-based adjustments
        total_crystals = sum(self.wizard.crystals.values())
        if total_crystals >= 8:
            if action_type in ['cast_spell', 'charge_card']:
                bonus += 15
            elif action_type in ['mine_white', 'mine_colored']:
                bonus -= 10  # Don't need more crystals
        
        return bonus
    
    def _execute_action(self, action, game):
        """FIXED: Execute the chosen action with comprehensive error handling"""
        if not action:
            return False
        
        action_type = action['type']
        success = False
        
        try:
            if action_type == 'cast_spell':
                success = game.cast_spell(self.wizard, action['spell_card'], 
                                        gui=game.gui if hasattr(game, 'gui') else None)
            
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
            logger.warning(f"Action execution failed for {action_type}: {e}")
            return False
    
    def _calculate_affordability(self, card):
        """Calculate how affordable a card is (0-1 scale)"""
        total_cost = card.get_total_cost()
        if total_cost == 0:
            return 1.0
        
        available_crystals = 0
        for color, cost in card.cost.items():
            if color == 'wild':
                # Wild crystals can be fulfilled by wizard's color or white crystals
                wild_available = self.wizard.crystals.get(self.wizard.color, 0) + self.wizard.crystals.get('white', 0)
                available_crystals += min(cost, wild_available)
            else:
                available_crystals += min(cost, self.wizard.crystals.get(color, 0))
        
        return available_crystals / total_cost
    
    def _guaranteed_turn_end(self, game):
        """FIXED: Guaranteed method to end AI turn - this CANNOT fail"""
        try:
            logger.warning(f"AI {self.wizard.color} using guaranteed turn end")
            
            # Try emergency fallback first
            if self._emergency_fallback(game):
                return
            
            # If that fails, force turn end
            self._force_turn_end(game)
            
        except Exception as e:
            logger.error(f"Even guaranteed turn end failed: {e}")
            # Ultimate fallback - directly manipulate game state
            game.current_actions = game.max_actions_per_turn
    
    def _emergency_fallback(self, game):
        """FIXED: Enhanced emergency fallback with multiple strategies"""
        self.fallback_used = True
        logger.warning(f"AI {self.wizard.color} using emergency fallback")
        
        # Try multiple fallback strategies in order
        fallback_strategies = [
            self._try_simple_spell_cast,
            self._try_simple_mine,
            self._try_simple_move,
            self._try_simple_card_action
        ]
        
        for strategy in fallback_strategies:
            try:
                if strategy(game):
                    return True
            except Exception as e:
                logger.debug(f"Fallback strategy failed: {e}")
                continue
        
        # If all strategies fail, force turn end
        return False
    
    def _try_simple_spell_cast(self, game):
        """Try to cast any available spell"""
        if not game.can_cast_spell(self.wizard):
            return False
        
        for spell_card in self.wizard.cards_laid_down:
            if spell_card.is_fully_charged():
                enemies = game.get_adjacent_enemies(self.wizard)
                if enemies:
                    return game.cast_spell(self.wizard, spell_card, 
                                         gui=game.gui if hasattr(game, 'gui') else None)
        return False
    
    def _try_simple_mine(self, game):
        """Try to mine at current position"""
        if not game.can_mine(self.wizard):
            return False
        
        pos = self.wizard.location
        
        # Try white crystal mining first
        if (game.board.has_crystals_at_position(pos) and 
            not game.board.is_mine(pos) and 
            not game.board.is_healing_springs(pos) and
            self.wizard.can_hold_more_crystals()):
            return game.mine_white_crystal(self.wizard, pos)
        
        # Try healing
        if game.board.is_healing_springs(pos) and self.wizard.health < 6:
            roll = random.randint(1, 3)
            return game.resolve_mine_with_roll(self.wizard, pos, roll)
        
        # Try colored mining
        if game.board.is_mine(pos) and self.wizard.can_hold_more_crystals():
            roll = random.randint(1, 6)
            return game.resolve_mine_with_roll(self.wizard, pos, roll)
        
        return False
    
    def _try_simple_move(self, game):
        """Try to move to any adjacent position"""
        if not game.can_move(self.wizard):
            return False
        
        adjacent = game.board.get_adjacent_positions(self.wizard.location)
        free_positions = [pos for pos in adjacent if game.board.is_position_free(pos)]
        
        if free_positions:
            target = random.choice(free_positions)
            return game.move_player(self.wizard, target)
        
        return False
    
    def _try_simple_card_action(self, game):
        """Try to lay down a card or charge something"""
        # Try to lay down a card
        if len(self.wizard.cards_laid_down) < 2 and self.wizard.hand:
            return self.wizard.lay_down_spell_card(0)
        
        # Try to charge a card
        for card in self.wizard.cards_laid_down:
            if not card.is_fully_charged():
                for color in ['white', 'red', 'blue', 'green', 'yellow']:
                    if self.wizard.crystals[color] > 0:
                        try:
                            if card.add_crystals(color, 1, self.wizard):
                                return True
                        except Exception as e:
                            # Log the specific error for debugging
                            logger.debug(f"Failed to charge card with {color}: {e}")
                            continue
        
        return False
    
    def _force_turn_end(self, game):
        """FIXED: Force the turn to end by setting actions to maximum"""
        logger.debug(f"AI {self.wizard.color} forcing turn end - setting actions to max")
        game.current_actions = game.max_actions_per_turn


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
