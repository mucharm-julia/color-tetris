from __future__ import annotations

import random
from dataclasses import dataclass

import pygame

BOARD_WIDTH = 10
BOARD_HEIGHT = 20
CELL_SIZE = 30
MARGIN_X = 36
MARGIN_Y = 30
SIDEBAR_GAP = 44
SIDEBAR_WIDTH = 280

BOARD_PIXEL_WIDTH = BOARD_WIDTH * CELL_SIZE
BOARD_PIXEL_HEIGHT = BOARD_HEIGHT * CELL_SIZE
BOARD_ORIGIN_X = MARGIN_X
BOARD_ORIGIN_Y = MARGIN_Y
SIDEBAR_X = BOARD_ORIGIN_X + BOARD_PIXEL_WIDTH + SIDEBAR_GAP
WINDOW_WIDTH = SIDEBAR_X + SIDEBAR_WIDTH + MARGIN_X
WINDOW_HEIGHT = BOARD_ORIGIN_Y + BOARD_PIXEL_HEIGHT + MARGIN_Y

FPS = 60
BASE_FALL_INTERVAL = 0.40
MIN_FALL_INTERVAL = 0.05

BACKGROUND_COLOR = (16, 22, 33)
BOARD_COLOR = (8, 12, 20)
GRID_COLOR = (34, 46, 66)
TEXT_COLOR = (235, 239, 247)
OVERLAY_COLOR = (5, 8, 14, 180)
GHOST_LINE_COLOR = (224, 240, 255)
GHOST_FILL_ALPHA = 105

PIECE_COLORS = {
    "I": (76, 195, 247),
    "O": (246, 212, 88),
    "T": (191, 120, 255),
    "S": (96, 211, 123),
    "Z": (247, 112, 123),
    "J": (98, 129, 255),
    "L": (255, 166, 91),
}

SHAPES = {
    "I": [[1, 1, 1, 1]],
    "O": [[1, 1], [1, 1]],
    "T": [[0, 1, 0], [1, 1, 1]],
    "S": [[0, 1, 1], [1, 1, 0]],
    "Z": [[1, 1, 0], [0, 1, 1]],
    "J": [[1, 0, 0], [1, 1, 1]],
    "L": [[0, 0, 1], [1, 1, 1]],
}


@dataclass
class Piece:
    kind: str
    matrix: list[list[int]]
    x: int
    y: int


def rotate_clockwise(matrix: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*matrix[::-1])]


class TetrisGame:
    def __init__(self) -> None:
        self.board: list[list[tuple[int, int, int] | None]] = []
        self.bag: list[str] = []
        self.current_piece: Piece | None = None
        self.next_kind = ""
        self.score = 0
        self.lines = 0
        self.level = 1
        self.game_over = False
        self.paused = False
        self.drop_accumulator = 0.0
        self.reset()

    def reset(self) -> None:
        self.board = [[None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.bag = []
        self.score = 0
        self.lines = 0
        self.level = 1
        self.game_over = False
        self.paused = False
        self.drop_accumulator = 0.0
        self.next_kind = self._draw_from_bag()
        self.current_piece = self._spawn_next_piece()

    def _draw_from_bag(self) -> str:
        if not self.bag:
            self.bag = list(SHAPES.keys())
            random.shuffle(self.bag)
        return self.bag.pop()

    def _create_piece(self, kind: str) -> Piece:
        matrix = [row[:] for row in SHAPES[kind]]
        start_x = (BOARD_WIDTH // 2) - (len(matrix[0]) // 2)
        return Piece(kind=kind, matrix=matrix, x=start_x, y=0)

    def _spawn_next_piece(self) -> Piece:
        piece = self._create_piece(self.next_kind)
        self.next_kind = self._draw_from_bag()
        if not self._is_valid_position(piece):
            self.game_over = True
        return piece

    def _is_valid_position(
        self,
        piece: Piece,
        dx: int = 0,
        dy: int = 0,
        matrix: list[list[int]] | None = None,
    ) -> bool:
        shape = matrix if matrix is not None else piece.matrix
        for row_index, row in enumerate(shape):
            for col_index, filled in enumerate(row):
                if not filled:
                    continue
                board_x = piece.x + dx + col_index
                board_y = piece.y + dy + row_index
                if board_x < 0 or board_x >= BOARD_WIDTH or board_y >= BOARD_HEIGHT:
                    return False
                if board_y >= 0 and self.board[board_y][board_x] is not None:
                    return False
        return True

    def _lock_current_piece(self) -> None:
        if self.current_piece is None:
            return
        color = PIECE_COLORS[self.current_piece.kind]
        for row_index, row in enumerate(self.current_piece.matrix):
            for col_index, filled in enumerate(row):
                if not filled:
                    continue
                board_x = self.current_piece.x + col_index
                board_y = self.current_piece.y + row_index
                if board_y < 0:
                    self.game_over = True
                    return
                self.board[board_y][board_x] = color

        cleared = self._clear_lines()
        if cleared:
            self._add_score(cleared)
        self.current_piece = self._spawn_next_piece()

    def _clear_lines(self) -> int:
        remaining_rows = [row for row in self.board if any(cell is None for cell in row)]
        cleared = BOARD_HEIGHT - len(remaining_rows)
        if cleared:
            new_rows = [[None for _ in range(BOARD_WIDTH)] for _ in range(cleared)]
            self.board = new_rows + remaining_rows
        return cleared

    def _add_score(self, cleared: int) -> None:
        points = {1: 100, 2: 300, 3: 500, 4: 800}
        self.lines += cleared
        self.level = (self.lines // 10) + 1
        self.score += points.get(cleared, 0) * self.level

    def _fall_interval(self) -> float:
        interval = BASE_FALL_INTERVAL - ((self.level - 1) * 0.06)
        return max(MIN_FALL_INTERVAL, interval)

    def ghost_drop_distance(self) -> int:
        if self.current_piece is None:
            return 0
        distance = 0
        while self._is_valid_position(self.current_piece, dy=distance + 1):
            distance += 1
        return distance

    def move(self, dx: int, dy: int) -> bool:
        if self.game_over or self.paused or self.current_piece is None:
            return False
        if self._is_valid_position(self.current_piece, dx=dx, dy=dy):
            self.current_piece.x += dx
            self.current_piece.y += dy
            return True
        if dy == 1:
            self._lock_current_piece()
        return False

    def rotate(self) -> None:
        if self.game_over or self.paused or self.current_piece is None:
            return
        rotated = rotate_clockwise(self.current_piece.matrix)
        if self._is_valid_position(self.current_piece, matrix=rotated):
            self.current_piece.matrix = rotated
            return

        # Minimal wall-kick behavior keeps rotation usable around edges.
        for kick in (-1, 1, -2, 2):
            if self._is_valid_position(self.current_piece, dx=kick, matrix=rotated):
                self.current_piece.x += kick
                self.current_piece.matrix = rotated
                return

    def hard_drop(self) -> None:
        if self.game_over or self.paused:
            return
        while self.move(0, 1):
            continue

    def toggle_pause(self) -> None:
        if self.game_over:
            return
        self.paused = not self.paused

    def update(self, dt: float, fast_drop: bool = False) -> None:
        if self.game_over or self.paused:
            return
        interval = 0.04 if fast_drop else self._fall_interval()
        self.drop_accumulator += dt
        while self.drop_accumulator >= interval:
            self.drop_accumulator -= interval
            if not self.move(0, 1):
                break


def draw_block(
    surface: pygame.Surface,
    color: tuple[int, int, int],
    x: int,
    y: int,
    size: int = CELL_SIZE,
) -> None:
    rect = pygame.Rect(x, y, size, size)
    border = tuple(max(0, value - 45) for value in color)
    pygame.draw.rect(surface, border, rect, border_radius=5)
    pygame.draw.rect(surface, color, rect.inflate(-4, -4), border_radius=4)


def draw_board(surface: pygame.Surface, game: TetrisGame) -> None:
    board_rect = pygame.Rect(BOARD_ORIGIN_X, BOARD_ORIGIN_Y, BOARD_PIXEL_WIDTH, BOARD_PIXEL_HEIGHT)
    pygame.draw.rect(surface, BOARD_COLOR, board_rect, border_radius=8)

    for row_index, row in enumerate(game.board):
        for col_index, cell in enumerate(row):
            if cell is None:
                continue
            x = BOARD_ORIGIN_X + (col_index * CELL_SIZE)
            y = BOARD_ORIGIN_Y + (row_index * CELL_SIZE)
            draw_block(surface, cell, x, y)

    if not game.game_over and game.current_piece is not None:
        piece = game.current_piece
        ghost_distance = game.ghost_drop_distance()
        color = PIECE_COLORS[piece.kind]
        ghost_color = tuple(min(255, value + 95) for value in color)

        # Landing guide: a lightweight ghost projection + vertical reference lines.
        if ghost_distance > 0:
            for row_index, row in enumerate(piece.matrix):
                for col_index, filled in enumerate(row):
                    if not filled:
                        continue
                    board_x = piece.x + col_index
                    current_y = piece.y + row_index
                    ghost_y = current_y + ghost_distance
                    if ghost_y >= 0:
                        x = BOARD_ORIGIN_X + (board_x * CELL_SIZE)
                        y = BOARD_ORIGIN_Y + (ghost_y * CELL_SIZE)
                        guide_rect = pygame.Rect(x + 3, y + 3, CELL_SIZE - 6, CELL_SIZE - 6)
                        ghost_block = pygame.Surface((guide_rect.width, guide_rect.height), pygame.SRCALPHA)
                        pygame.draw.rect(
                            ghost_block,
                            (*ghost_color, GHOST_FILL_ALPHA),
                            ghost_block.get_rect(),
                            border_radius=4,
                        )
                        surface.blit(ghost_block, (guide_rect.x, guide_rect.y))
                    if current_y >= 0:
                        guide_x = BOARD_ORIGIN_X + (board_x * CELL_SIZE) + (CELL_SIZE // 2)
                        start_y = BOARD_ORIGIN_Y + (current_y * CELL_SIZE) + CELL_SIZE
                        end_y = BOARD_ORIGIN_Y + (ghost_y * CELL_SIZE)
                        if end_y > start_y:
                            pygame.draw.line(
                                surface,
                                GHOST_LINE_COLOR,
                                (guide_x, start_y),
                                (guide_x, end_y),
                                2,
                            )

        for row_index, row in enumerate(piece.matrix):
            for col_index, filled in enumerate(row):
                if not filled:
                    continue
                board_x = piece.x + col_index
                board_y = piece.y + row_index
                if board_y < 0:
                    continue
                x = BOARD_ORIGIN_X + (board_x * CELL_SIZE)
                y = BOARD_ORIGIN_Y + (board_y * CELL_SIZE)
                draw_block(surface, color, x, y)

    for line in range(BOARD_WIDTH + 1):
        x = BOARD_ORIGIN_X + (line * CELL_SIZE)
        pygame.draw.line(
            surface,
            GRID_COLOR,
            (x, BOARD_ORIGIN_Y),
            (x, BOARD_ORIGIN_Y + BOARD_PIXEL_HEIGHT),
            1,
        )
    for line in range(BOARD_HEIGHT + 1):
        y = BOARD_ORIGIN_Y + (line * CELL_SIZE)
        pygame.draw.line(
            surface,
            GRID_COLOR,
            (BOARD_ORIGIN_X, y),
            (BOARD_ORIGIN_X + BOARD_PIXEL_WIDTH, y),
            1,
        )


def draw_next_piece(surface: pygame.Surface, kind: str, x: int, y: int) -> None:
    matrix = SHAPES[kind]
    color = PIECE_COLORS[kind]
    preview_size = 22
    for row_index, row in enumerate(matrix):
        for col_index, filled in enumerate(row):
            if not filled:
                continue
            block_x = x + (col_index * preview_size)
            block_y = y + (row_index * preview_size)
            draw_block(surface, color, block_x, block_y, size=preview_size)


def draw_sidebar(
    surface: pygame.Surface,
    game: TetrisGame,
    title_font: pygame.font.Font,
    label_font: pygame.font.Font,
    body_font: pygame.font.Font,
) -> None:
    panel_x = SIDEBAR_X
    title = title_font.render("TETRIS", True, TEXT_COLOR)
    surface.blit(title, (panel_x, BOARD_ORIGIN_Y))

    stats = [
        f"Score: {game.score}",
        f"Lines: {game.lines}",
        f"Level: {game.level}",
    ]
    y = BOARD_ORIGIN_Y + 54
    for text in stats:
        label = label_font.render(text, True, TEXT_COLOR)
        surface.blit(label, (panel_x, y))
        y += 34

    next_label = label_font.render("Next", True, TEXT_COLOR)
    surface.blit(next_label, (panel_x, y + 6))
    draw_next_piece(surface, game.next_kind, panel_x, y + 42)

    controls = [
        "Controls:",
        "Arrow Left/Right: Move",
        "Arrow Up: Rotate",
        "Arrow Down: Soft Drop",
        "Space: Hard Drop",
        "P: Pause",
        "R: Restart",
        "Esc: Quit",
    ]
    y = BOARD_ORIGIN_Y + 280
    for index, text in enumerate(controls):
        font = label_font if index == 0 else body_font
        control_text = font.render(text, True, TEXT_COLOR)
        surface.blit(control_text, (panel_x, y))
        y += 26


def draw_overlay(
    surface: pygame.Surface,
    title_font: pygame.font.Font,
    body_font: pygame.font.Font,
    title_text: str,
    subtitle_text: str,
) -> None:
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill(OVERLAY_COLOR)
    surface.blit(overlay, (0, 0))

    title = title_font.render(title_text, True, TEXT_COLOR)
    subtitle = body_font.render(subtitle_text, True, TEXT_COLOR)

    title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, (WINDOW_HEIGHT // 2) - 20))
    subtitle_rect = subtitle.get_rect(center=(WINDOW_WIDTH // 2, (WINDOW_HEIGHT // 2) + 20))
    surface.blit(title, title_rect)
    surface.blit(subtitle, subtitle_rect)


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Color Tetris")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont("dejavusans", 36, bold=True)
    label_font = pygame.font.SysFont("dejavusans", 26, bold=True)
    body_font = pygame.font.SysFont("dejavusans", 19)

    game = TetrisGame()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        keys = pygame.key.get_pressed()
        fast_drop = keys[pygame.K_DOWN]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_p:
                    game.toggle_pause()
                elif event.key == pygame.K_r:
                    game.reset()
                elif game.game_over or game.paused:
                    continue
                elif event.key == pygame.K_LEFT:
                    game.move(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    game.move(1, 0)
                elif event.key == pygame.K_UP:
                    game.rotate()
                elif event.key == pygame.K_SPACE:
                    game.hard_drop()
                elif event.key == pygame.K_DOWN:
                    game.move(0, 1)

        game.update(dt, fast_drop=fast_drop)

        screen.fill(BACKGROUND_COLOR)
        draw_board(screen, game)
        draw_sidebar(screen, game, title_font, label_font, body_font)

        if game.paused:
            draw_overlay(screen, title_font, body_font, "Paused", "Press P to resume")
        elif game.game_over:
            draw_overlay(screen, title_font, body_font, "Game Over", "Press R to restart")

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
