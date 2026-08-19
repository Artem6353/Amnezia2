"""
Block Blast Clone - Optimized for Mobile (Pydroid3)
Designed for devices like HUAWEI P20 Lite
Controls: Touch and drag to move blocks, tap to rotate (optional auto-rotate)
"""

import pygame
import random
import sys
import math

# Initialize Pygame
pygame.init()

# Get display info for fullscreen
display_info = pygame.display.Info()
SCREEN_WIDTH = display_info.current_w
SCREEN_HEIGHT = display_info.current_h

# Force a reasonable resolution for performance on older devices
# HUAWEI P20 Lite is 1080x2160, but we'll use a scaled approach for better performance
TARGET_WIDTH = min(SCREEN_WIDTH, 540)  # Half resolution for performance
TARGET_HEIGHT = min(SCREEN_HEIGHT, 960)

# Create screen with scaling
screen = pygame.display.set_mode((TARGET_WIDTH, TARGET_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Block Blast")

# Clock for FPS control (limit to 30 FPS for battery/performance)
clock = pygame.time.Clock()
MAX_FPS = 30

# Colors
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
GRAY = (60, 60, 60)
LIGHT_GRAY = (100, 100, 100)
RED = (231, 76, 60)
GREEN = (46, 204, 113)
BLUE = (52, 152, 219)
YELLOW = (241, 196, 15)
ORANGE = (230, 126, 34)
PURPLE = (142, 68, 173)
CYAN = (0, 192, 255)
PINK = (255, 105, 180)

BLOCK_COLORS = [RED, GREEN, BLUE, YELLOW, ORANGE, PURPLE, CYAN, PINK]

# Game constants
GRID_SIZE = 8
CELL_SIZE = min(TARGET_WIDTH, TARGET_HEIGHT) // 12  # Dynamic cell size
GRID_OFFSET_X = (TARGET_WIDTH - GRID_SIZE * CELL_SIZE) // 2
GRID_OFFSET_Y = TARGET_HEIGHT // 4

# Block shapes definitions (each shape is a list of relative coordinates)
SHAPES = [
    [(0, 0)],  # Single block
    [(0, 0), (1, 0)],  # 2-block horizontal
    [(0, 0), (0, 1)],  # 2-block vertical
    [(0, 0), (1, 0), (2, 0)],  # 3-block horizontal
    [(0, 0), (0, 1), (0, 2)],  # 3-block vertical
    [(0, 0), (1, 0), (0, 1)],  # L-shape small
    [(0, 0), (1, 0), (2, 0), (0, 1)],  # L-shape
    [(0, 0), (1, 0), (2, 0), (2, 1)],  # L-shape mirrored
    [(0, 0), (1, 0), (0, 1), (1, 1)],  # Square 2x2
    [(0, 0), (1, 0), (2, 0), (1, 1)],  # T-shape
    [(0, 0), (1, 0), (2, 0), (3, 0)],  # 4-block horizontal
    [(0, 0), (0, 1), (0, 2), (0, 3)],  # 4-block vertical
    [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1)],  # 2x3 rectangle minus one
]

class Block:
    def __init__(self, shape, color, x, y, cell_size):
        self.shape = shape  # List of (dx, dy) tuples
        self.color = color
        self.x = x  # Screen position
        self.y = y
        self.cell_size = cell_size
        self.original_shape = shape[:]
        
    def draw(self, surface, offset_x=0, offset_y=0, alpha=None):
        for dx, dy in self.shape:
            rect = pygame.Rect(
                self.x + dx * self.cell_size + offset_x,
                self.y + dy * self.cell_size + offset_y,
                self.cell_size - 2,
                self.cell_size - 2
            )
            if alpha:
                s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                s.fill((*self.color, alpha))
                pygame.draw.rect(s, WHITE, s.get_rect(), 2)
                surface.blit(s, rect)
            else:
                pygame.draw.rect(surface, self.color, rect)
                pygame.draw.rect(surface, WHITE, rect, 2)
    
    def get_rects(self, offset_x=0, offset_y=0):
        rects = []
        for dx, dy in self.shape:
            rect = pygame.Rect(
                self.x + dx * self.cell_size + offset_x,
                self.y + dy * self.cell_size + offset_y,
                self.cell_size - 2,
                self.cell_size - 2
            )
            rects.append(rect)
        return rects
    
    def rotate(self):
        """Rotate the shape 90 degrees clockwise"""
        new_shape = []
        for dx, dy in self.shape:
            new_shape.append((-dy, dx))
        self.shape = new_shape
    
    def copy(self):
        return Block(self.original_shape[:], self.color, self.x, self.y, self.cell_size)


class Game:
    def __init__(self):
        self.grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.score = 0
        self.high_score = 0
        self.available_blocks = []
        self.dragged_block = None
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.game_over = False
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 36)
        self.spawn_blocks()
        self.last_clear_time = 0
        self.clear_animation = []
        
    def spawn_blocks(self):
        """Spawn 3 random blocks at the bottom"""
        self.available_blocks = []
        spawn_area_width = TARGET_WIDTH // 3
        spawn_y = GRID_OFFSET_Y + GRID_SIZE * CELL_SIZE + 50
        
        for i in range(3):
            shape = random.choice(SHAPES)
            color = random.choice(BLOCK_COLORS)
            block_x = spawn_area_width * i + spawn_area_width // 2
            block_y = spawn_y
            
            # Center the block
            shape_width = max(dx for dx, dy in shape) + 1
            shape_height = max(dy for dx, dy in shape) + 1
            block_x -= shape_width * CELL_SIZE // 2
            block_y -= shape_height * CELL_SIZE // 2
            
            block = Block(shape, color, block_x, block_y, CELL_SIZE // 1.5)
            self.available_blocks.append(block)
    
    def can_place(self, block, grid_x, grid_y):
        """Check if block can be placed at grid position"""
        for dx, dy in block.shape:
            nx, ny = grid_x + dx, grid_y + dy
            if nx < 0 or nx >= GRID_SIZE or ny < 0 or ny >= GRID_SIZE:
                return False
            if self.grid[ny][nx] is not None:
                return False
        return True
    
    def place_block(self, block, grid_x, grid_y):
        """Place block on the grid"""
        for dx, dy in block.shape:
            self.grid[grid_y + dy][grid_x + dx] = block.color
        self.check_lines()
    
    def check_lines(self):
        """Check and clear completed lines"""
        lines_to_clear = []
        
        # Check rows
        for y in range(GRID_SIZE):
            if all(self.grid[y][x] is not None for x in range(GRID_SIZE)):
                lines_to_clear.append(('row', y))
        
        # Check columns
        for x in range(GRID_SIZE):
            if all(self.grid[y][x] is not None for y in range(GRID_SIZE)):
                lines_to_clear.append(('col', x))
        
        if lines_to_clear:
            # Clear lines
            for line_type, index in lines_to_clear:
                if line_type == 'row':
                    for x in range(GRID_SIZE):
                        self.grid[index][x] = None
                else:
                    for y in range(GRID_SIZE):
                        self.grid[y][index] = None
            
            # Calculate score
            num_lines = len(lines_to_clear)
            self.score += num_lines * 10 * num_lines  # Bonus for multiple lines
            
            if self.score > self.high_score:
                self.high_score = self.score
    
    def is_game_over(self):
        """Check if no more moves are possible"""
        for block in self.available_blocks:
            for gy in range(GRID_SIZE):
                for gx in range(GRID_SIZE):
                    if self.can_place(block, gx, gy):
                        return False
        return True
    
    def handle_touch(self, pos):
        """Handle touch input"""
        if self.game_over:
            # Restart game on touch
            self.__init__()
            return
        
        x, y = pos
        
        # Check if touching any available block
        for i, block in enumerate(self.available_blocks):
            block_rects = block.get_rects()
            for rect in block_rects:
                if rect.collidepoint(x, y):
                    self.dragged_block = block
                    self.dragged_block_index = i
                    # Calculate offset to grab from touch point
                    self.drag_offset_x = block.x - x
                    self.drag_offset_y = block.y - y
                    # Scale up block when dragging
                    block.cell_size = CELL_SIZE
                    return
    
    def handle_drag(self, pos):
        """Handle drag movement"""
        if self.dragged_block:
            x, y = pos
            self.dragged_block.x = x + self.drag_offset_x
            self.dragged_block.y = y + self.drag_offset_y
    
    def handle_release(self):
        """Handle touch release"""
        if self.dragged_block:
            # Calculate grid position
            block_screen_x = self.dragged_block.x
            block_screen_y = self.dragged_block.y
            
            # Convert to grid coordinates
            grid_x = round((block_screen_x - GRID_OFFSET_X) / CELL_SIZE)
            grid_y = round((block_screen_y - GRID_OFFSET_Y) / CELL_SIZE)
            
            # Try to place
            if self.can_place(self.dragged_block, grid_x, grid_y):
                self.place_block(self.dragged_block, grid_x, grid_y)
                self.available_blocks.pop(self.dragged_block_index)
                
                # Spawn new blocks if all used
                if not self.available_blocks:
                    self.spawn_blocks()
                
                # Check game over
                if self.is_game_over():
                    self.game_over = True
            else:
                # Return block to original position
                self.return_block_to_spawn()
            
            self.dragged_block = None
    
    def return_block_to_spawn(self):
        """Return dragged block to spawn area"""
        if self.dragged_block:
            spawn_area_width = TARGET_WIDTH // 3
            spawn_y = GRID_OFFSET_Y + GRID_SIZE * CELL_SIZE + 50
            i = self.dragged_block_index
            
            block = self.dragged_block
            block.cell_size = CELL_SIZE // 1.5
            
            shape_width = max(dx for dx, dy in block.shape) + 1
            shape_height = max(dy for dx, dy in block.shape) + 1
            
            block.x = spawn_area_width * i + spawn_area_width // 2 - shape_width * block.cell_size // 2
            block.y = spawn_y - shape_height * block.cell_size // 2
    
    def draw_grid(self):
        """Draw the game grid"""
        # Draw background
        grid_rect = pygame.Rect(
            GRID_OFFSET_X - 10,
            GRID_OFFSET_Y - 10,
            GRID_SIZE * CELL_SIZE + 20,
            GRID_SIZE * CELL_SIZE + 20
        )
        pygame.draw.rect(screen, GRAY, grid_rect, border_radius=10)
        pygame.draw.rect(screen, LIGHT_GRAY, grid_rect, 3, border_radius=10)
        
        # Draw cells
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                rect = pygame.Rect(
                    GRID_OFFSET_X + x * CELL_SIZE,
                    GRID_OFFSET_Y + y * CELL_SIZE,
                    CELL_SIZE - 2,
                    CELL_SIZE - 2
                )
                
                if self.grid[y][x]:
                    pygame.draw.rect(screen, self.grid[y][x], rect)
                    pygame.draw.rect(screen, WHITE, rect, 2)
                else:
                    pygame.draw.rect(screen, BLACK, rect)
                    pygame.draw.rect(screen, GRAY, rect, 1)
    
    def draw_ui(self):
        """Draw UI elements"""
        # Score
        score_text = self.font_medium.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (20, 20))
        
        # High Score
        high_score_text = self.font_small.render(f"Best: {self.high_score}", True, LIGHT_GRAY)
        screen.blit(high_score_text, (20, 70))
        
        # Title
        title_text = self.font_large.render("BLOCK BLAST", True, WHITE)
        title_rect = title_text.get_rect(center=(TARGET_WIDTH // 2, 50))
        screen.blit(title_text, title_rect)
    
    def draw_game_over(self):
        """Draw game over screen"""
        overlay = pygame.Surface((TARGET_WIDTH, TARGET_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        game_over_text = self.font_large.render("GAME OVER", True, RED)
        go_rect = game_over_text.get_rect(center=(TARGET_WIDTH // 2, TARGET_HEIGHT // 2 - 50))
        screen.blit(game_over_text, go_rect)
        
        final_score_text = self.font_medium.render(f"Score: {self.score}", True, WHITE)
        fs_rect = final_score_text.get_rect(center=(TARGET_WIDTH // 2, TARGET_HEIGHT // 2 + 20))
        screen.blit(final_score_text, fs_rect)
        
        restart_text = self.font_small.render("Touch to restart", True, LIGHT_GRAY)
        r_rect = restart_text.get_rect(center=(TARGET_WIDTH // 2, TARGET_HEIGHT // 2 + 80))
        screen.blit(restart_text, r_rect)
    
    def update(self):
        """Update game state"""
        pass  # Game logic is event-driven
    
    def draw(self):
        """Draw everything"""
        screen.fill(BLACK)
        
        self.draw_grid()
        self.draw_ui()
        
        # Draw available blocks
        for i, block in enumerate(self.available_blocks):
            if block != self.dragged_block:
                block.draw(screen)
        
        # Draw dragged block on top
        if self.dragged_block:
            # Draw shadow
            self.dragged_block.draw(screen, 5, 5, alpha=100)
            self.dragged_block.draw(screen)
            
            # Show ghost placement
            grid_x = round((self.dragged_block.x - GRID_OFFSET_X) / CELL_SIZE)
            grid_y = round((self.dragged_block.y - GRID_OFFSET_Y) / CELL_SIZE)
            
            if self.can_place(self.dragged_block, grid_x, grid_y):
                for dx, dy in self.dragged_block.shape:
                    ghost_rect = pygame.Rect(
                        GRID_OFFSET_X + (grid_x + dx) * CELL_SIZE,
                        GRID_OFFSET_Y + (grid_y + dy) * CELL_SIZE,
                        CELL_SIZE - 2,
                        CELL_SIZE - 2
                    )
                    pygame.draw.rect(screen, WHITE, ghost_rect, 3)
        
        if self.game_over:
            self.draw_game_over()
        
        pygame.display.flip()


def main():
    game = Game()
    running = True
    dragging = False
    
    while running:
        clock.tick(MAX_FPS)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r and game.game_over:
                    game = Game()
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click / touch
                    game.handle_touch(event.pos)
                    if game.dragged_block:
                        dragging = True
            
            elif event.type == pygame.MOUSEMOTION:
                if dragging and game.dragged_block:
                    game.handle_drag(event.pos)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if dragging:
                        game.handle_release()
                        dragging = False
        
        game.update()
        game.draw()
    
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
