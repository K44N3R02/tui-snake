#!/usr/bin/python3

from dataclasses import dataclass
from collections import deque
from enum import IntEnum, auto
from random import randint
import sys
from typing import Protocol, Self

import curses


class Direction(IntEnum):
    UP = auto()
    DOWN = auto()
    RIGHT = auto()
    LEFT = auto()

    def opposite(self, other: Self) -> bool:
        return (self == Direction.UP and other == Direction.DOWN
                or self == Direction.DOWN and other == Direction.UP
                or self == Direction.RIGHT and other == Direction.LEFT
                or self == Direction.LEFT and other == Direction.RIGHT)

@dataclass
class Point:
    x: int
    y: int

    def __add__(self, other: Self) -> 'Point':
        return Point(self.x + other.x, self.y + other.y)

units = {
    Direction.UP: Point(0, -1),
    Direction.DOWN: Point(0, 1),
    Direction.RIGHT: Point(1, 0),
    Direction.LEFT: Point(-1, 0),
}

@dataclass
class BodyPart:
    point: Point
    direction: Direction

@dataclass
class Snake:
    body: deque[BodyPart]

    def body_points(self) -> list[Point]:
        return list(map(lambda part: part.point, self.body))

@dataclass
class Board:
    width: int
    height: int
    obstacles: list[Point]
    snake: Snake
    apples: list[Point]
    score: int

    def within_borders(self: Self, point: Point) -> bool:
        return (
            0 <= point.x < self.width and
            0 <= point.y < self.height
        )

    def update(self, direction: Direction, shifted: bool) -> bool:
        if self.snake.body[-1].direction.opposite(direction):
            return True

        head_pos = self.snake.body[-1].point
        next_pos = head_pos + units[direction]

        if next_pos in self.apples:
            self.apples.remove(next_pos)
            self.new_apple()
            self.score += 1
        else:
            _ = self.snake.body.popleft()

        if next_pos in self.obstacles or next_pos in self.snake.body_points():
            return False

        self.snake.body[-1].direction = direction
        self.snake.body.append(BodyPart(next_pos, direction))

        return True

    def new_apple(self) -> None:
        new_x = randint(0, self.width - 1)
        new_y = randint(0, self.height - 1)
        apple = Point(new_x, new_y)
        if apple in self.obstacles or apple in self.apples or apple in self.snake.body_points():
            self.new_apple()
        else:
            self.apples.append(apple)


class Renderer(Protocol):
    def render(self: Self, board: Board, scr: curses.window) -> None:
        ...

class TerminalRenderer(Renderer):
    def render(self, board, scr) -> None:
        scr.clear()      # Clear the screen

        scr.addstr(0, 0, str(board.score))

        for y in range(board.height):
            for x in range(board.width):
                scr.addstr(y + 1, x, ".")

        for obstacle in board.obstacles:
            if board.within_borders(obstacle):
                scr.addstr(obstacle.y + 1, obstacle.x, "#")

        for apple in board.apples:
            if board.within_borders(apple):
                scr.addstr(apple.y + 1, apple.x, "@")

        for part in board.snake.body:
            if board.within_borders(part.point):
                if part.direction == Direction.UP:
                    char = 'A'
                if part.direction == Direction.DOWN:
                    char = 'V'
                if part.direction == Direction.RIGHT:
                    char = '>'
                if part.direction == Direction.LEFT:
                    char = '<'
                scr.addstr(part.point.y + 1, part.point.x, char)

        scr.refresh()  # Refresh the screen to show changes

@dataclass
class Game:
    renderer: Renderer

    def __post_init__(self):
        self.replay = True

    def init(self, height: int, width: int):
        snake = Snake(deque())
        for i in range(1,4):
            snake.body.append(BodyPart(Point(x=i, y=1), Direction.RIGHT))

        self.board = Board(width, height, [], snake, [Point(width//2,height//2)], 0)
        for i in range(self.board.height):
            for j in range(self.board.width):
                if i == 0 or i == self.board.height - 1 or j == 0 or j == self.board.width - 1:
                    self.board.obstacles.append(Point(j, i))

        self.scr = curses.initscr()
        curses.curs_set(0)
        curses.noecho()

    def loop(self) -> bool:
        self.renderer.render(self.board, self.scr)
        char = self.scr.getch()
        match chr(char):
            case 'a' | 'h':
                direction = Direction.LEFT
            case 's' | 'j':
                direction = Direction.DOWN
            case 'w' | 'k':
                direction = Direction.UP
            case 'd' | 'l':
                direction = Direction.RIGHT
            case 'q':
                self.replay = False
                return False
            case _:
                return True

        is_alive = self.board.update(direction, False)
        if not is_alive:
            self.lost_scene()
            return False

        return True

    def help_scene(self):
        self.scr.clear()
        self.scr.addstr(0, 0, "Welcome to TUI Snake.\nUse wasd or hjkl to move.\nPress `q` to exit.\nTap any key to continue.")
        char = chr(self.scr.getch())
        if char == 'q':
            self.deinit()
            sys.exit(0)

    def lost_scene(self):
        self.scr.addstr(self.board.height + 2, 0, "You lost. Press `q` to quit or `r` to restart")
        char = chr(self.scr.getch())
        if char == 'q':
            self.replay = False
        elif char == 'r':
            self.replay = True
        else:
            self.lost_scene()

    def deinit(self):
        curses.endwin()

def main():
    renderer = TerminalRenderer()
    game = Game(renderer)
    while game.replay:
        game.init(20, 30)
        game.help_scene()
        while game.loop():
            pass
    game.deinit()


if __name__ == '__main__':
    main()
