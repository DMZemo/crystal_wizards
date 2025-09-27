
"""
Crystal Wizards - Particle System and Visual Effects
Enhanced visual effects for spells, combat, mining, and other actions
"""

import pygame
import math
import random
from typing import List, Tuple, Optional

class Particle:
    """Base particle class for visual effects"""
    
    def __init__(self, x: float, y: float, vel_x: float = 0, vel_y: float = 0, 
                 color: Tuple[int, int, int] = (255, 255, 255), life: float = 1.0,
                 size: float = 3.0, fade: bool = True):
        self.x = x
        self.y = y
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.color = color
        self.life = life
        self.max_life = life
        self.size = size
        self.initial_size = size
        self.fade = fade
        self.gravity = 0.0
        self.friction = 0.98
        
    def update(self, dt: float):
        """Update particle position and properties"""
        self.x += self.vel_x * dt
        self.y += self.vel_y * dt
        self.vel_y += self.gravity * dt
        self.vel_x *= self.friction
        self.vel_y *= self.friction
        self.life -= dt
        
        if self.fade:
            life_ratio = max(0, self.life / self.max_life)
            self.size = self.initial_size * life_ratio
            
    def draw(self, screen: pygame.Surface):
        """Draw the particle"""
        if self.life <= 0 or self.size <= 0:
            return
            
        alpha = int(255 * (self.life / self.max_life)) if self.fade else 255
        color = (*self.color, alpha)
        
        # Create a surface with per-pixel alpha
        particle_surface = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(particle_surface, color, 
                         (int(self.size), int(self.size)), int(self.size))
        
        screen.blit(particle_surface, (int(self.x - self.size), int(self.y - self.size)))
        
    def is_alive(self) -> bool:
        """Check if particle is still alive"""
        return self.life > 0

class SparkParticle(Particle):
    """Spark particle for magical effects"""
    
    def __init__(self, x: float, y: float, **kwargs):
        super().__init__(x, y, **kwargs)
        self.sparkle_timer = 0
        
    def update(self, dt: float):
        super().update(dt)
        self.sparkle_timer += dt * 10
        
    def draw(self, screen: pygame.Surface):
        if self.life <= 0:
            return
            
        # Draw sparkle effect
        sparkle_size = int(self.size * (1 + 0.3 * math.sin(self.sparkle_timer)))
        alpha = int(255 * (self.life / self.max_life))
        color = (*self.color, alpha)
        
        particle_surface = pygame.Surface((sparkle_size * 2, sparkle_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(particle_surface, color, (sparkle_size, sparkle_size), sparkle_size)
        
        # Add cross sparkle
        pygame.draw.line(particle_surface, color, 
                        (sparkle_size - sparkle_size//2, sparkle_size),
                        (sparkle_size + sparkle_size//2, sparkle_size), 2)
        pygame.draw.line(particle_surface, color,
                        (sparkle_size, sparkle_size - sparkle_size//2),
                        (sparkle_size, sparkle_size + sparkle_size//2), 2)
        
        screen.blit(particle_surface, (int(self.x - sparkle_size), int(self.y - sparkle_size)))

class MagicTrailParticle(Particle):
    """Trail particle for spell casting"""
    
    def __init__(self, x: float, y: float, target_x: float, target_y: float, **kwargs):
        super().__init__(x, y, **kwargs)
        self.target_x = target_x
        self.target_y = target_y
        self.trail_length = 20
        self.positions = [(x, y)]
        
    def update(self, dt: float):
        # Move towards target
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > 5:
            speed = 300 * dt
            self.x += (dx / distance) * speed
            self.y += (dy / distance) * speed
        
        # Update trail
        self.positions.append((self.x, self.y))
        if len(self.positions) > self.trail_length:
            self.positions.pop(0)
            
        self.life -= dt
        
    def draw(self, screen: pygame.Surface):
        if self.life <= 0 or len(self.positions) < 2:
            return
            
        # Draw trail
        for i, (px, py) in enumerate(self.positions):
            alpha = int(255 * (i / len(self.positions)) * (self.life / self.max_life))
            size = int(self.size * (i / len(self.positions)))
            if alpha > 0 and size > 0:
                color = (*self.color, alpha)
                particle_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(particle_surface, color, (size, size), size)
                screen.blit(particle_surface, (int(px - size), int(py - size)))

class ExplosionParticle(Particle):
    """Explosion particle for combat effects"""
    
    def __init__(self, x: float, y: float, **kwargs):
        super().__init__(x, y, **kwargs)
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-180, 180)
        
    def update(self, dt: float):
        super().update(dt)
        self.rotation += self.rotation_speed * dt
        
    def draw(self, screen: pygame.Surface):
        if self.life <= 0:
            return
            
        alpha = int(255 * (self.life / self.max_life))
        color = (*self.color, alpha)
        
        # Draw rotating square for explosion effect
        size = int(self.size)
        particle_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        
        # Create rotated square
        points = []
        for angle in [45, 135, 225, 315]:
            rad = math.radians(angle + self.rotation)
            px = size + size * 0.7 * math.cos(rad)
            py = size + size * 0.7 * math.sin(rad)
            points.append((px, py))
            
        pygame.draw.polygon(particle_surface, color, points)
        screen.blit(particle_surface, (int(self.x - size), int(self.y - size)))

class ParticleSystem:
    """Manages all particle effects"""
    
    def __init__(self):
        self.particles: List[Particle] = []
        self.screen_shake_intensity = 0
        self.screen_shake_duration = 0
        self.screen_offset_x = 0
        self.screen_offset_y = 0
        
    def add_particle(self, particle: Particle):
        """Add a particle to the system"""
        self.particles.append(particle)
        
    def create_spell_cast_effect(self, x: float, y: float, spell_color: str, intensity: int = 20):
        """Create spell casting particle effect"""
        color_map = {
            'red': (255, 100, 100),
            'blue': (100, 100, 255),
            'green': (100, 255, 100),
            'yellow': (255, 255, 100),
            'white': (255, 255, 255),
            'wild': (255, 100, 255)
        }
        
        color = color_map.get(spell_color, (255, 255, 255))
        
        for _ in range(intensity):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 150)
            vel_x = math.cos(angle) * speed
            vel_y = math.sin(angle) * speed
            
            particle = SparkParticle(
                x + random.uniform(-10, 10),
                y + random.uniform(-10, 10),
                vel_x=vel_x,
                vel_y=vel_y,
                color=color,
                life=random.uniform(0.5, 1.5),
                size=random.uniform(2, 6)
            )
            self.add_particle(particle)
            
    def create_spell_trail_effect(self, start_x: float, start_y: float, 
                                 end_x: float, end_y: float, spell_color: str):
        """Create spell trail effect from caster to target"""
        color_map = {
            'red': (255, 50, 50),
            'blue': (50, 50, 255),
            'green': (50, 255, 50),
            'yellow': (255, 255, 50),
            'white': (255, 255, 255),
            'wild': (255, 50, 255)
        }
        
        color = color_map.get(spell_color, (255, 255, 255))
        
        for i in range(5):
            particle = MagicTrailParticle(
                start_x + random.uniform(-5, 5),
                start_y + random.uniform(-5, 5),
                end_x + random.uniform(-10, 10),
                end_y + random.uniform(-10, 10),
                color=color,
                life=1.0,
                size=random.uniform(3, 8)
            )
            self.add_particle(particle)
            
    def create_combat_hit_effect(self, x: float, y: float, damage: int):
        """Create combat hit particle effect"""
        intensity = min(damage * 5, 30)
        
        for _ in range(intensity):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(100, 200)
            vel_x = math.cos(angle) * speed
            vel_y = math.sin(angle) * speed
            
            particle = ExplosionParticle(
                x + random.uniform(-5, 5),
                y + random.uniform(-5, 5),
                vel_x=vel_x,
                vel_y=vel_y,
                color=(255, 100, 50),
                life=random.uniform(0.3, 0.8),
                size=random.uniform(3, 8)
            )
            particle.gravity = 50
            self.add_particle(particle)
            
        # Add screen shake for impact
        self.add_screen_shake(damage * 2, 0.3)
        
    def create_mining_effect(self, x: float, y: float, crystal_color: str):
        """Create mining particle effect"""
        color_map = {
            'red': (200, 50, 50),
            'blue': (50, 50, 200),
            'green': (50, 200, 50),
            'yellow': (200, 200, 50),
            'white': (200, 200, 200)
        }
        
        color = color_map.get(crystal_color, (150, 150, 150))
        
        # Create crystal fragments
        for _ in range(15):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(30, 100)
            vel_x = math.cos(angle) * speed
            vel_y = math.sin(angle) * speed - random.uniform(20, 50)  # Upward bias
            
            particle = Particle(
                x + random.uniform(-10, 10),
                y + random.uniform(-10, 10),
                vel_x=vel_x,
                vel_y=vel_y,
                color=color,
                life=random.uniform(0.8, 1.5),
                size=random.uniform(2, 5)
            )
            particle.gravity = 100
            particle.friction = 0.95
            self.add_particle(particle)
            
    def create_crystal_pickup_effect(self, x: float, y: float, crystal_color: str):
        """Create crystal pickup particle effect"""
        color_map = {
            'red': (255, 100, 100),
            'blue': (100, 100, 255),
            'green': (100, 255, 100),
            'yellow': (255, 255, 100),
            'white': (255, 255, 255)
        }
        
        color = color_map.get(crystal_color, (255, 255, 255))
        
        # Create upward floating sparkles
        for _ in range(10):
            vel_x = random.uniform(-20, 20)
            vel_y = random.uniform(-80, -40)
            
            particle = SparkParticle(
                x + random.uniform(-5, 5),
                y + random.uniform(-5, 5),
                vel_x=vel_x,
                vel_y=vel_y,
                color=color,
                life=random.uniform(1.0, 2.0),
                size=random.uniform(2, 4)
            )
            self.add_particle(particle)
            
    def add_screen_shake(self, intensity: float, duration: float):
        """Add screen shake effect"""
        self.screen_shake_intensity = max(self.screen_shake_intensity, intensity)
        self.screen_shake_duration = max(self.screen_shake_duration, duration)
        
    def update(self, dt: float):
        """Update all particles and effects"""
        # Update particles
        self.particles = [p for p in self.particles if p.is_alive()]
        for particle in self.particles:
            particle.update(dt)
            
        # Update screen shake
        if self.screen_shake_duration > 0:
            self.screen_shake_duration -= dt
            if self.screen_shake_duration <= 0:
                self.screen_offset_x = 0
                self.screen_offset_y = 0
            else:
                shake_amount = self.screen_shake_intensity * (self.screen_shake_duration / 0.3)
                self.screen_offset_x = random.uniform(-shake_amount, shake_amount)
                self.screen_offset_y = random.uniform(-shake_amount, shake_amount)
                
    def draw(self, screen: pygame.Surface):
        """Draw all particles"""
        for particle in self.particles:
            particle.draw(screen)
            
    def get_screen_offset(self) -> Tuple[float, float]:
        """Get current screen shake offset"""
        return self.screen_offset_x, self.screen_offset_y
        
    def clear(self):
        """Clear all particles"""
        self.particles.clear()
        self.screen_shake_intensity = 0
        self.screen_shake_duration = 0
        self.screen_offset_x = 0
        self.screen_offset_y = 0

# Global particle system instance
particle_system = ParticleSystem()
