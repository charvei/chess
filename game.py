from datetime import datetime
from typing import Optional

import pyxel

from chess import Side, Position, ChessBoard, InvalidMove, ChessPiece, Move
from pieces import MoveEffect

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


class Turn:
    def __init__(self):
        self.current_player = Side.WHITE
        # Currently hard coded for 10min games
        self.timer = {Side.WHITE: 10 * 60 * 1000, Side.BLACK: 10 * 60 * 1000}
        self.last_update_time = datetime.now()

    def toggle_current_player(self):
        self.current_player = Side.BLACK if self.current_player == Side.WHITE else Side.WHITE

    def get_mins_seconds_left(self, player: Side):
        return divmod(self.timer[player] / 1000, 60)

    def update_timer(self):
        self.timer[self.current_player] -= int((datetime.now() - self.last_update_time).microseconds / 1000)
        if self.timer[self.current_player] < 0:
            self.timer[self.current_player] = 0
        self.last_update_time = datetime.now()


class Game:
    def __init__(self):
        self.turn = Turn()
        self.player_perspective = Side.BLACK
        self.selected_position: Optional[Position] = None
        self.winner: Optional[Side] = None
        self.move_history = []
        self.board = ChessBoard()

    def maybe_handle_left_click(self):
        if clicked_position := self._get_clicked_position():
            if self.selected_position:
                try:
                    self.move(self.selected_position, clicked_position)
                    self.selected_position = None
                    return
                except InvalidMove as im:
                    print(im)
                    self.selected_position = None
        if (piece := self.board.get_piece(clicked_position)) and piece.side == self.turn.current_player:
            # Only allow for selecting position corresponding to a piece of a current players
            self.selected_position = clicked_position

    def _get_clicked_position(self) -> Optional[Position]:
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            # convert screen position to board position
            if self.player_perspective == Side.WHITE:
                rank = int(pyxel.mouse_y / TILE_HEIGHT) - 1
                file = int(pyxel.mouse_x / TILE_WIDTH) - 1
            else:
                rank = 7 - int(pyxel.mouse_y / TILE_HEIGHT) + 1
                file = 7 - int(pyxel.mouse_x / TILE_WIDTH) + 1

            # Only return a position if a board tile was clicked
            if 0 <= rank < 8 and 0 <= file < 8:
                return Position(rank, file)

    def maybe_handle_right_click(self):
        if pyxel.btnp(pyxel.MOUSE_BUTTON_RIGHT):
            self.selected_position = None

    def maybe_handle_run_out_of_time(self):
        if self.turn.timer[self.turn.current_player] <= 0:
            self.winner = Side.WHITE if self.turn.current_player == Side.BLACK else Side.BLACK

    def maybe_handle_winner_found(self):
        if self.winner:
            print(f"Winner: {self.winner.name.title()}")

    def move(self, src: Position, dst: Position):
        move = self.board.move(src, dst, self.turn.current_player)
        print(move.long_algebraic_notation)
        self.move_history.append(move)
        if MoveEffect.CHECKMATE in move.side_effects:
            self.winner = self.turn.current_player
        self.turn.toggle_current_player()

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


    def draw_board(self):
        # Initial background
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
        if self.selected_position:
            pyxel.blt(
                self._x_index_for_file(self.selected_position.file) * TILE_WIDTH,
                self._y_index_for_rank(self.selected_position.rank) * TILE_HEIGHT,
                2,
                0,
                0,
                TILE_WIDTH,
                TILE_HEIGHT,
                colkey=2,
            )

    def draw_pieces(self):
        for file in range(8):
            for rank in range(8):
                if piece := self.board.get_piece(Position(rank, file)):
                    pyxel.blt(
                        self._x_index_for_file(file) * TILE_WIDTH,
                        self._y_index_for_rank(rank) * TILE_HEIGHT,
                        0,
                        0 if piece.side == Side.WHITE else 1 * TILE_WIDTH,
                        IMAGE_LOCATION_FOR_PIECE[piece.__class__.__name__.lower()] * TILE_HEIGHT,
                        TILE_WIDTH,
                        TILE_HEIGHT,
                        colkey=2,
                    )

    def draw_game_info(self):
        # Draw background for game info area
        pyxel.rect(BOARD_WIDTH, 0, GAME_INFO_WIDTH, GAME_INFO_HEIGHT, 6)

        # White timer
        pyxel.rect(BOARD_WIDTH, 0, GAME_INFO_WIDTH / 2, 1 * TILE_HEIGHT, 15)
        white_mins, white_secs = self.turn.get_mins_seconds_left(Side.WHITE)
        pyxel.text(BOARD_WIDTH + 5, 5, f"{int(white_mins):02d}:{int(white_secs):02d}", 0)

        # Black timer
        pyxel.rect(BOARD_WIDTH + 2 * TILE_WIDTH, 0, GAME_INFO_WIDTH, 1 * TILE_HEIGHT, 4)
        black_mins, black_secs = self.turn.get_mins_seconds_left(Side.BLACK)
        pyxel.text(
            BOARD_WIDTH + 5 + 2 * TILE_WIDTH,
            5,
            f"{int(black_mins):02d}:{int(black_secs):02d}",
            0,
        )

        # Move history
        pyxel.rect(
            BOARD_WIDTH,
            TILE_HEIGHT * 1,
            GAME_INFO_WIDTH,
            GAME_INFO_HEIGHT - 1 * TILE_HEIGHT,
            0,
        )
        for i, move in enumerate(self.move_history):
            label = f"{int(i/2) + 1}. " if not i % 2 else "   "
            pyxel.text(
                BOARD_WIDTH + 4,
                TILE_HEIGHT * 1 + (i * (TILE_HEIGHT / 2)) + 6,
                f"{label}{move.long_algebraic_notation}",
                7,
            )
