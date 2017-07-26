#!/usr/bin/env python3

import numpy as np
import pygame, sys
import random
from pygame.locals import *
from enum import Enum


BLACK  = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY   = (202, 207, 210)
CYAN   = (103, 183, 236)
YELLOW = (247, 220, 111)
PURPLE = (142, 68, 173)
GREEN  = (88, 214, 141)
RED    = (231, 76, 60)
BLUE   = (52, 152, 219)
ORANGE = (230, 126, 34)
COLORKEY = (255, 0, 255)

BACKGROUND_COLOR = BLACK
BORDER_COLOR = GRAY

BLOCK_COLOR = [BACKGROUND_COLOR, CYAN, YELLOW, PURPLE, GREEN, RED, BLUE, ORANGE, WHITE]

BLOCK_WIDTH = 30
BLOCK_HEIGHT = 30

pygame.init()
font = pygame.font.SysFont("arial", 16)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((600, 660))
        self.screen.set_colorkey(COLORKEY)
        self.clock = pygame.time.Clock()

        self.tetro = None
        self.hold  = HoldComponent(self)
        self.grid  = GridComponent(self)
        self.queue = QueueComponent(self)
        self.score = ScoreComponent(self)

    def tetro_step(self):
        if self.tetro == None:
            self.tetro = self.queue.pop_tetromino()

        grid = self.grid._grid
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.score.hard_drop(min(10 - self.tetro.y, 12))
                    self.tetro.try_fast_fall(grid)
                elif event.key == pygame.K_LEFT:
                    self.tetro.try_left(grid)
                elif event.key == pygame.K_RIGHT:
                    self.tetro.try_right(grid)
                elif event.key == pygame.K_z:
                    self.tetro.try_rotate(grid)
                elif event.key == pygame.K_x:
                    self.tetro = self.hold.push(self.tetro)
                    if not self.tetro:
                        return
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        if pygame.key.get_pressed()[pygame.K_DOWN]:
            self.tetro.fall_faster()

        if self.tetro.falling:
            self.tetro.fall(grid)
        else:
            self.grid.place_tetro(self.tetro)
            self.tetro = None
            return

        (left, top) = (self.grid._rect.left, self.grid._rect.top)
        self.tetro.draw(self.screen, self.grid._grid, left, top)

    def run(self):
        self.hold.reset()
        self.queue.reset()
        self.score.reset()
        self.grid.reset()
        while True:
            self.clock.tick(60)
            self.grid.update()
            self.tetro_step()
            pygame.display.flip()


class Component:
    def __init__(self, game, border=True):
        self._game = game
        self.border = border

    @property
    def left(self):
        return self._rect.left

    @property
    def top(self):
        return self._rect.top

    def reset(self):
        if self.border:
            self._game.screen.fill(BORDER_COLOR, rect=self._rect.inflate(4, 4))
        self._game.screen.fill(BACKGROUND_COLOR, rect=self._rect)

    def update(self):
        self.reset()
        self.draw()

    def draw(self):
        pass


def blit_center(source, dest, left, top, width, height):
    left_offset = left + (width - dest.get_width()) / 2
    top_offset = top + (height - dest.get_height()) / 2
    source.blit(dest, (left_offset, top_offset))


class QueueComponent(Component):
    BLOCK_WIDTH = 16
    BLOCK_HEIGHT = 16
    cell_width = BLOCK_WIDTH * 4 + 4
    cell_height = BLOCK_HEIGHT * 4 + 4
    def __init__(self, game):
        super().__init__(game, False)
        self._rect = pygame.Rect(480, 16,
                                 self.BLOCK_WIDTH * 4 + 10,
                                 self.BLOCK_HEIGHT * 4 * 3 + 10 + 28)
        self._queue = TetrominoShape.shuffle()
        self.next_title_top = self.top
        self.next_block_top = self.top + 18
        self.queue_block_top = self.next_block_top + 20 + self.cell_height

    def _populate(self):
        new_tetros = TetrominoShape.shuffle()
        self._queue.extend(new_tetros)

    def pop_tetromino(self):
        next_tetro = self._queue.pop(0)
        if len(self._queue) <= 3:
            self._populate()
        self.update()
        return Tetromino(next_tetro)

    def reset(self):
        screen = self._game.screen

        # Render next item
        next_title = font.render("NEXT", True, WHITE)
        screen.blit(next_title, (self.left, self.next_title_top))

        screen.fill(BORDER_COLOR, (self.left, self.next_block_top, self.cell_width + 4, self.cell_height + 4))
        screen.fill(BACKGROUND_COLOR, (self.left + 2, self.next_block_top + 2, self.cell_width, self.cell_height))

        screen.fill(BORDER_COLOR, (self.left, self.queue_block_top, self.cell_width + 4, self.cell_height * 2 + 6))
        screen.fill(BACKGROUND_COLOR, (self.left + 2, self.queue_block_top + 2, self.cell_width, self.cell_height * 2 + 2))

    def draw(self):
        bw = self.BLOCK_WIDTH
        bh = self.BLOCK_HEIGHT
        screen = self._game.screen

        next_tetro = self._queue[0]
        next_tetro_img = next_tetro.cropped_image(block_width=bw, block_height=bh)
        blit_center(screen, next_tetro_img, self.left + 4, self.next_block_top + 4, self.cell_width-4, self.cell_height-4)

        active_queue = self._queue[1:3]
        for i, shape in enumerate(active_queue):
            top = self.queue_block_top + 4 + (self.cell_height + 2) * i
            image = shape.cropped_image(block_width=bw, block_height=bh)
            blit_center(screen, image, self.left + 4, top, self.cell_width-4, self.cell_height-4)

class HoldComponent(Component):
    def __init__(self, game):
        super().__init__(game)
        self._rect = pygame.Rect(20, 20, 120, 120)
        self._hold = None

    def draw(self):
        (left, top) = (self._rect.left + 2, self._rect.top + 2)
        image = self._hold.cropped_image(block_width=29, block_height=29)
        screen = self._game.screen
        blit_center(screen, image, left, top, 116, 116)

    def push(self, tetro):
        old = self._hold
        self._hold = tetro._shape
        self.update()
        return Tetromino(old) if old else None

class GridComponent(Component):
    def __init__(self, game):
        super().__init__(game)
        self._rect = pygame.Rect(160, 20, 300, 600)
        self._grid = np.zeros((10, 22), dtype='int32')
        self._tetro = None

    def draw(self):
        (left, top) = (self._rect.left, self._rect.top)
        screen = self._game.screen
        for i in range(10):
            for j in range(20):
                color = self._grid[i, j]
                if color:
                    block = pygame.Rect(left + i * 30, top + j * 30, 30, 30)
                    screen.fill(BLOCK_COLOR[color], rect=block)

    def place_tetro(self, t):
        b = t.get_b()
        (x, y) = (t.x, t.y)
        for i in range(b.shape[0]):
            for j in range(b.shape[1]):
                if b[i, j]:
                    self._grid[x + i, y + j] = t.color_value
        self.check_line()

    def check_line(self):
        num_lines = 0
        for j in range(self._grid.shape[1]):
            if np.all(self._grid[:,j]):
                num_lines += 1
                self._grid[:,1:(j+1)] = self._grid[:,:j]
                self._grid[:,0] = 0
        self._game.score.clear(num_lines)


class ScoreComponent(Component):
    def __init__(self, game):
        super().__init__(game)
        self._rect = pygame.Rect(20, 180, 120, 30)
        self._score = 0
        self._combo = []

    def clear(self, num_lines):
        if num_lines <= 0:
            self._combo = []
            return
        self._combo += [num_lines]
        score = 0
        if num_lines == 1:
            score = 200
        elif num_lines == 2:
            score = 400
        elif num_lines == 3:
            score = 800
        elif num_lines == 4:
            score = 1200
        score += int(sum(self._combo[:-1]) / 2)
        self._score += score
        self.update()

    def hard_drop(self, y):
        self._score += y * 5
        self.update()

    def reset(self):
        title_txt = font.render("Score", True, WHITE)
        self._game.screen.blit(title_txt, (self._rect.left + 5, self._rect.top - 20))
        super().reset()

    def draw(self):
        score_txt = font.render("{:012d}".format(self._score), True, WHITE)
        self._game.screen.blit(score_txt, (self._rect.left + 5, self._rect.top + 5))


def draw_mat(b, c, w, h):
    image = pygame.Surface((b.shape[0] * w, b.shape[1] * h))
    image.set_colorkey(COLORKEY)
    image.fill(COLORKEY)
    for i in range(b.shape[0]):
        for j in range(b.shape[1]):
            if b[i,j]:
                image.fill(c, pygame.Rect(i * w, j * h, w, h))
    return image

class TetrominoShape:
    def __init__(self, b, color):
        self._b = b
        self._color = color
        self._orient = []
        self._skirt = []
        for i in range(4):
            self._orient.append(np.rot90(self._b, i))

    def shuffle():
        return random.sample(TetrominoShape.ALL, len(TetrominoShape.ALL))

    def rotate(self, level):
        return self._orient[level % 4]

    @property
    def color(self):
        return BLOCK_COLOR[self._color]

    @property
    def width(self):
        return self._b.shape[0]

    @property
    def height(self):
        return self._b.shape[1]

    def image(self, orient=0, block_width=BLOCK_WIDTH, block_height=BLOCK_HEIGHT):
        b = self.rotate(orient)
        return draw_mat(b, self.color, block_width, block_height)

    def cropped_image(self, orient=0, block_width=BLOCK_WIDTH, block_height=BLOCK_HEIGHT):
        b = self.rotate(orient)
        b = b[~np.all(b == 0, axis=1)]
        b = b[:,~np.all(b == 0, axis=0)]
        return draw_mat(b, self.color, block_width, block_height)

    def draw(self, surf, dest, orient=0, block_width=BLOCK_WIDTH, block_height=BLOCK_HEIGHT):
        image = self.image(orient, block_width, block_height)
        surf.blit(image, dest)

TetrominoShape.I = TetrominoShape(np.array([[0,0,0,0], [1,1,1,1], [0,0,0,0], [0,0,0,0]]), 1)
TetrominoShape.O = TetrominoShape(np.array([[1,1], [1,1]]), 2)
TetrominoShape.T = TetrominoShape(np.array([[0,1,0], [1,1,1], [0,0,0]]), 3)
TetrominoShape.S = TetrominoShape(np.array([[0,1,1], [1,1,0], [0,0,0]]), 4)
TetrominoShape.Z = TetrominoShape(np.array([[1,1,0], [0,1,1], [0,0,0]]), 5)
TetrominoShape.J = TetrominoShape(np.array([[1,0,0], [1,1,1], [0,0,0]]), 6)
TetrominoShape.L = TetrominoShape(np.array([[0,0,1], [1,1,1], [0,0,0]]), 7)
TetrominoShape.ALL = [TetrominoShape.I, TetrominoShape.O, TetrominoShape.T, TetrominoShape.S, TetrominoShape.Z, TetrominoShape.J, TetrominoShape.L]


class Tetromino:
    GRAVITY_RATE = 30
    def __init__(self, shape):
        self._shape = shape
        self._rotate = 0
        self.x = 5
        self.y = -shape.height
        # Time before applying gravity
        self.gstep = 0
        self.falling = True

    def get_b(self):
        return self._shape.rotate(self._rotate)

    @property
    def color_value(self):
        return self._shape._color

    def fall(self, grid):
        if not self.falling:
            return
        self.gstep += 1
        if self.gstep > self.GRAVITY_RATE:
            self.gstep = 0
            if self.conflicts(grid, dy=1):
                self.falling = False
            else:
                self.y += 1

    def fall_faster(self):
        self.gstep += 3

    def try_left(self, grid):
        if not self.conflicts(grid, dx=-1):
            self.x -= 1

    def try_right(self, grid):
        if not self.conflicts(grid, dx=1):
            self.x += 1

    def try_rotate(self, grid):
        dx = 0
        ddx = -1 if self.x > 0 else 1
        conflict = self.conflicts(grid, dr=1, dx=dx)
        while conflict and abs(dx) < 1:
            dx += ddx
            conflict = self.conflicts(grid, dr=1, dx=dx)
        if not conflict:
            self._rotate += 1
            self.x += dx

    def try_fast_fall(self, grid):
        self.gstep = self.GRAVITY_RATE
        self.y += self.calc_fall_distance(grid)

    def calc_fall_distance(self, grid):
        dy = 0
        while not self.conflicts(grid, dy=dy):
            dy += 1
        return max(0, dy - 1)

    def conflicts(self, grid, dr=0, dx=0, dy=0):
        x = self.x + dx
        y = self.y + dy
        b = self._shape.rotate(self._rotate + dr)
        for i in range(b.shape[0]):
            for j in range(b.shape[1]):
                if b[i, j]:
                    if x + i < 0 or x + i >= 10 or y + j >= 20:
                        return True
                    if y+j >= 0 and grid[x + i, y + j]:
                        return True
        return False

    def image(self):
        return self._shape.image(orient=self._rotate)

    def draw(self, screen, grid, left, top):
        (x_px, y_px) = (self.x * 30, self.y * 30)
        image = self.image()
        nleft = left + x_px

        ## Draw where the tetro will fall.
        y_px_bot = (self.y + self.calc_fall_distance(grid)) * 30
        ntop = top + y_px_bot
        image_alpha = image.copy()
        image_alpha.set_alpha(50)
        if y_px_bot >= 0:
            screen.blit(image_alpha, (nleft, top + y_px_bot))

        ## Draw the tetro
        if y_px >= 0:
            screen.blit(image, (nleft, top + y_px))
        else:
            crop_y = abs(y_px)
            screen.blit(image, (nleft, top), (0, crop_y, image.get_width(), image.get_height() - ntop))


if __name__ == '__main__':
    game = Game()
    game.run()
