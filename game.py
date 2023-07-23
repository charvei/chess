from datetime import datetime
from typing import Optional

import pyxel

from chess import Side, Position, ChessBoard, InvalidMove, ChessPiece, Move

TILE_WIDTH = 16
TILE_HEIGHT = 16

BOARD_WIDTH = TILE_WIDTH*10
BOARD_HEIGHT = TILE_HEIGHT*10

GAME_INFO_WIDTH = TILE_WIDTH*4
GAME_INFO_HEIGHT = TILE_HEIGHT*10

IMAGE_LOCATION_FOR_PIECE = {
    "pawn": 0,
    "rook": 1,
    "bishop": 2,
    "knight": 3,
    "queen": 4,
    "king": 5
}

LABEL_FOR_FILE_POSITION = {
    1: "a",
    2: "b",
    3: "c",
    4: "d",
    5: "e",
    6: "f",
    7: "g",
    8: "h"
}


class Turn:
    def __init__(self):
        self.current_player = Side.WHITE
        # Currently hard coded for 10min games
        self.timer = {
            Side.WHITE: 10*60*1000,
            Side.BLACK: 10*60*1000
        }
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


class MoveTracker:
    def __init__(self):
        self.moves: list[Move] = []

    def add_move(self, move: Move):
        """"""
        print(move.as_long_algebraic_notation)
        self.moves.append(move)


class Game:
    def __init__(self):
        self.turn = Turn()
        self.player_perspective = Side.WHITE
        self.selected_position: Optional[Position] = None
        self.winner: Optional[Side] = None
        self.move_tracker = MoveTracker()
        self.board = ChessBoard()

    def maybe_handle_left_click(self):
        if clicked_position := self._get_clicked_position():
            if self.selected_position:
                try:
                    self.move(self.selected_position, clicked_position)
                    self.selected_position = None
                except InvalidMove as im:
                    print(im)
                    self.selected_position = clicked_position
            else:
                if (piece := self.board.get_piece(clicked_position)) and piece.side == self.turn.current_player:
                    # Only allow for selecting position corresponding to a piece of a current players
                    self.selected_position = clicked_position

    def _get_clicked_position(self) -> Optional[Position]:
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            # convert screen position to board position
            rank, file = int(pyxel.mouse_y / TILE_HEIGHT), int(pyxel.mouse_x / TILE_WIDTH)

            # Only return a position if a board tile was clicked
            if 0 < rank < 9 and 0 < file < 9:
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
        self.move_tracker.add_move(move)
        self.turn.toggle_current_player()

    def draw_board(self):
        # Initial background
        pyxel.rect(0, 0, TILE_WIDTH * 10, TILE_HEIGHT * 10, 5)

        # Draw file labels
        for file in range(1, 9):
            for y in (0, 9):
                pyxel.text(file * TILE_WIDTH + TILE_WIDTH / 2 - 2, y * TILE_HEIGHT + TILE_HEIGHT / 2 - 2, LABEL_FOR_FILE_POSITION[file],
                           col=7)

        # Draw rank labels
        for rank in range(1, 9):
            for x in (0, 9):
                pyxel.text(x * TILE_WIDTH + TILE_WIDTH / 2 - 1, rank * TILE_HEIGHT + TILE_HEIGHT / 2 - 1, str(rank), col=7)

        # Draw board tiles
        for file in range(1,9):
            for rank in range(1, 9):
                colour = 4 if (rank + file) % 2 else 15
                pyxel.rect(file * TILE_WIDTH, rank * TILE_HEIGHT, TILE_WIDTH, TILE_HEIGHT, colour)

        # Draw selected border
        if self.selected_position:
            pyxel.blt(self.selected_position.file * TILE_WIDTH, self.selected_position.rank * TILE_HEIGHT, 2, 0, 0,TILE_WIDTH,
                          TILE_HEIGHT, colkey=2)

    def draw_pieces(self):
        for file in (range(8)):
            for rank in (range(8)):
                if piece := self.board.get_piece(Position(rank + 1, file + 1)):
                    pyxel.blt(
                        (file + 1) * TILE_WIDTH,
                        (rank + 1) * TILE_HEIGHT,
                        0,
                        piece.side.value * TILE_WIDTH,
                        IMAGE_LOCATION_FOR_PIECE[piece.__class__.__name__.lower()] * TILE_HEIGHT,
                        TILE_WIDTH,
                        TILE_HEIGHT,
                        colkey=2
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
        pyxel.text(BOARD_WIDTH + 5 + 2 * TILE_WIDTH, 5, f"{int(black_mins):02d}:{int(black_secs):02d}", 0)

        # Move history
        # todo handle scrolling
        pyxel.rect(BOARD_WIDTH, TILE_HEIGHT * 1, GAME_INFO_WIDTH, GAME_INFO_HEIGHT - 2 * TILE_HEIGHT, 0)
        for i, move in enumerate(self.move_tracker.moves):
            label = f"{int(i/2) + 1}. " if not i % 2 else "   "
            pyxel.text(BOARD_WIDTH, TILE_HEIGHT * 1 + (i * (TILE_HEIGHT / 2)) + 7, f"{label}{move.as_long_algebraic_notation}", 7)