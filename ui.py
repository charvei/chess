from dataclasses import dataclass
from typing import Optional

import pyxel

from chess import ChessBoard, Move
from game import Turn
from pieces import ChessPiece, Position, Side


TILE_WIDTH = 16
TILE_HEIGHT = 16

BOARD_WIDTH = TILE_WIDTH * 10
BOARD_HEIGHT = TILE_HEIGHT * 10

GAME_INFO_WIDTH = TILE_WIDTH * 4
GAME_INFO_HEIGHT = TILE_HEIGHT * 10

IMAGE_LOCATION_FOR_PIECE = {
    "pawn": 0,
    "rook": 1,
    "bishop": 2,
    "knight": 3,
    "queen": 4,
    "king": 5,
}

FILE_LABELS = ["a", "b", "c", "d", "e", "f", "g", "h"]
RANK_LABELS = ["8", "7", "6", "5", "4", "3", "2", "1"]


class UIComponent:
    x: float
    y: float
    width: float
    height: float
    background_colour: int
    subcomponents: list["UIComponent"] = []

    def draw(self, *args, **kwargs) -> None:
        raise NotImplementedError

    def coords_are_within_element(self, x: int, y: int):
        print(x, y)
        return self.x <= x < self.x + self.width and self.y <= y < self.y + self.height


@dataclass
class MoveAnimation:
    piece: ChessPiece
    dst: Position
    progress: float = 0.0

    def update_progress(self):
        self.progress += 0.25


class Board(UIComponent):
    def __init__(self):
        self.x = 0
        self.y = 0
        self.width = TILE_WIDTH * 10
        self.height = TILE_HEIGHT * 10
        self.background_colour = 5
        # self.animations: dict[Position, MoveAnimation] = {}
        self.player_perspective = Side.WHITE

    def draw(
        self,
        board: ChessBoard,
        animations: dict[Position, MoveAnimation],
        selected_position: Optional[Position] = None,
    ) -> None:
        pyxel.rect(0, 0, TILE_WIDTH * 10, TILE_HEIGHT * 10, 5)

        # Draw file labels
        for file in range(8):
            for y in (0, 9):
                pyxel.text(
                    self._x_index_for_file(file) * TILE_WIDTH + TILE_WIDTH / 2 - 2,
                    y * TILE_HEIGHT + TILE_HEIGHT / 2 - 2,
                    FILE_LABELS[file],
                    col=7,
                )

        # Draw rank labels
        for rank in range(8):
            for x in (0, 9):
                pyxel.text(
                    x * TILE_WIDTH + TILE_WIDTH / 2 - 1,
                    (self._y_index_for_rank(rank) * TILE_HEIGHT) + TILE_HEIGHT / 2 - 2,
                    RANK_LABELS[rank],
                    col=7,
                )

        # Draw board tiles
        for file in range(8):
            for rank in range(8):
                colour = 4 if (rank + file) % 2 else 15
                pyxel.rect(
                    (file + 1) * TILE_WIDTH,
                    (rank + 1) * TILE_HEIGHT,
                    TILE_WIDTH,
                    TILE_HEIGHT,
                    colour,
                )

        # Draw selected border
        if selected_position:
            pyxel.blt(
                self._x_index_for_file(selected_position.file) * TILE_WIDTH,
                self._y_index_for_rank(selected_position.rank) * TILE_HEIGHT,
                2,
                0,
                0,
                TILE_WIDTH,
                TILE_HEIGHT,
                colkey=2,
            )

        self.draw_pieces(board, animations)

    def draw_pieces(self, board: ChessBoard, animations: dict[Position, MoveAnimation]):
        for file in range(8):
            for rank in range(8):
                if animation := animations.get(Position(rank, file)):
                    draw_file = animation.dst.file + ((file - animation.dst.file) * animation.progress)
                    draw_rank = animation.dst.rank + ((rank - animation.dst.rank) * animation.progress)
                else:
                    draw_file = file
                    draw_rank = rank

                if piece := board.get_piece(Position(rank, file)):
                    pyxel.blt(
                        self._x_index_for_file(draw_file) * TILE_WIDTH,
                        self._y_index_for_rank(draw_rank) * TILE_HEIGHT,
                        0,
                        0 if piece.side == Side.WHITE else 1 * TILE_WIDTH,
                        IMAGE_LOCATION_FOR_PIECE[piece.__class__.__name__.lower()] * TILE_HEIGHT,
                        TILE_WIDTH,
                        TILE_HEIGHT,
                        colkey=2,
                    )

    def _x_index_for_file(self, file):
        """
        Get the x / horizontal index for a file, i.e. 0th corresponds to the first file in the board and so on.

        This translates a tile to the appropriate screen coordinate.
        """
        return file + 1 if self.player_perspective == Side.WHITE else 7 - file + 1

    def _y_index_for_rank(self, rank):
        """
        Get the y / vertical index for a rank, i.e. 0th corresponds to the first rank in the board and so on.

        This translates a tile to the appropriate screen coordinate.
        """
        return rank + 1 if self.player_perspective == Side.WHITE else 7 - rank + 1


class GameInfo(UIComponent):
    """"""

    def __init__(self):
        self.x = BOARD_WIDTH
        self.y = 0
        self.width = GAME_INFO_WIDTH
        self.height = GAME_INFO_HEIGHT
        self.background_colour = 6
        # self.subcomponents = [PlayerTimers(), GameHistory()]
        self.subcomponents = [PlayerTimers(), MoveHistory()]

    def draw(self, turn: Turn, move_history: list[Move]):
        pyxel.rect(self.x, self.y, self.width, self.height, self.background_colour)
        self.subcomponents[0].draw(turn)
        self.subcomponents[1].draw(move_history)
        # for component in self.subcomponents:
        #     component.draw(turn)


class PlayerTimers(UIComponent):
    def __init__(self):
        self.x = BOARD_WIDTH
        self.y = 0
        self.width = GAME_INFO_WIDTH
        self.height = 1 * TILE_HEIGHT
        self.background_colour = 0

    def draw(self, turn: Turn):
        # White timer
        pyxel.rect(self.x, 0, self.width / 2, self.height, 15)
        white_mins, white_secs = turn.get_mins_seconds_left(Side.WHITE)
        pyxel.text(self.x + 5, 5, f"{int(white_mins):02d}:{int(white_secs):02d}", 0)

        # Black timer
        pyxel.rect(self.x + (2 * TILE_WIDTH), 0, self.width, self.height, 4)
        black_mins, black_secs = turn.get_mins_seconds_left(Side.BLACK)
        pyxel.text(
            BOARD_WIDTH + 5 + 2 * TILE_WIDTH,
            5,
            f"{int(black_mins):02d}:{int(black_secs):02d}",
            0,
        )


class MoveHistory(UIComponent):
    def __init__(self):
        self.x = BOARD_WIDTH
        self.y = TILE_HEIGHT * 1
        self.width = GAME_INFO_WIDTH
        self.height = 8 * TILE_HEIGHT
        self.background_colour = 0

    def draw(self, move_history: list[Move]):
        move_history_height_tiles = (GAME_INFO_HEIGHT / TILE_HEIGHT) - 2
        # Move history
        pyxel.rect(
            BOARD_WIDTH,
            TILE_HEIGHT * 1,
            GAME_INFO_WIDTH,
            move_history_height_tiles * TILE_HEIGHT,
            0,
        )

        # number of lines of text that can be presented at once in the move history box
        # There are 2 lines of text per tile
        move_history_window_size = int(move_history_height_tiles - 1) * 2 + 1
        move_history_frame_index = (
            int(-1 * move_history_window_size)
            if len(move_history) > move_history_window_size
            else -1 * len(move_history)
        )

        if len(move_history):
            for draw_pos, move_index in enumerate(
                range(len(move_history) + move_history_frame_index, len(move_history))
            ):
                label = f"{int(move_index / 2) + 1}. " if not move_index % 2 else "   "
                pyxel.text(
                    BOARD_WIDTH + 4,
                    (TILE_HEIGHT * 1 + 6) + (draw_pos * (TILE_HEIGHT / 2)),
                    f"{label}{move_history[move_index].long_algebraic_notation}",
                    7,
                )

        arrow_width = 8
        arrow_height = 8
        # top arrow
        pyxel.blt(
            BOARD_WIDTH + GAME_INFO_WIDTH - arrow_width - 1,
            TILE_HEIGHT + 4,
            1,
            0,
            0,
            arrow_width,
            arrow_height,
            colkey=2,
        )

        # bottom arrow
        pyxel.blt(
            BOARD_WIDTH + GAME_INFO_WIDTH - arrow_width - 1,
            BOARD_HEIGHT - TILE_HEIGHT - arrow_height - 3,
            1,
            0,
            arrow_height,
            arrow_width,
            arrow_height,
            colkey=2,
        )
