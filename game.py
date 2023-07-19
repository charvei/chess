from typing import Optional

import pyxel

from chess import Side, Position, ChessBoard, InvalidMove

PIECE_WIDTH = 16
PIECE_HEIGHT = 16

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


class Game:
    def __init__(self):
        self.current_player_turn = Side.WHITE
        self.player_perspective = Side.WHITE
        self.selected_position: Optional[Position] = None
        self.board = ChessBoard()
        # self.timer

    def maybe_handle_left_click(self):
        if clicked_position := self._get_clicked_position():
            if self.selected_position:
                try:
                    self.move(self.selected_position, clicked_position)
                    self.selected_position = None
                except InvalidMove as im:
                    print(im)
            else:
                self.selected_position = clicked_position

    def _get_clicked_position(self) -> Optional[Position]:
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            # convert screen position to board position
            rank, file = int(pyxel.mouse_y / PIECE_HEIGHT), int(pyxel.mouse_x / PIECE_WIDTH)

            # Only return a position if a board tile was clicked
            if 0 < rank < 9 and 0 < file < 9:
                return Position(rank, file)

    def maybe_handle_right_click(self):
        if pyxel.btnp(pyxel.MOUSE_BUTTON_RIGHT):
            self.selected_position = None

    def move(self, src: Position, dst: Position):
        self.board.move(src, dst, self.current_player_turn)
        self.toggle_turn()

    def draw_board(self):
        # Initial background
        pyxel.rect(0, 0, PIECE_WIDTH * 10, PIECE_HEIGHT * 10, 5)

        # Draw file labels
        for file in range(1, 9):
            for y in (0, 9):
                pyxel.text(file * PIECE_WIDTH + PIECE_WIDTH / 2 - 2, y * PIECE_HEIGHT + PIECE_HEIGHT / 2 - 2, LABEL_FOR_FILE_POSITION[file],
                           col=7)

        # Draw rank labels
        for rank in range(1, 9):
            for x in (0, 9):
                pyxel.text(x * PIECE_WIDTH + PIECE_WIDTH / 2 - 1, rank * PIECE_HEIGHT + PIECE_HEIGHT / 2 - 1, str(rank), col=7)

        # Draw board tiles
        for file in range(1,9):
            for rank in range(1, 9):
                colour = 4 if (rank + file) % 2 else 15
                pyxel.rect(file * PIECE_WIDTH, rank * PIECE_HEIGHT, PIECE_WIDTH, PIECE_HEIGHT, colour)

        # Draw selected border
        if self.selected_position:
            pyxel.blt(self.selected_position.file * PIECE_WIDTH, self.selected_position.rank * PIECE_HEIGHT, 2, 0, 0,PIECE_WIDTH,
                          PIECE_HEIGHT, colkey=2)

    def draw_pieces(self):
        for file in (range(8)):
            for rank in (range(8)):
                if piece := self.board.get_piece(Position(rank + 1, file + 1)):
                    pyxel.blt(
                        (file + 1) * PIECE_WIDTH,
                        (rank + 1) * PIECE_HEIGHT,
                        0,
                        piece.side.value * PIECE_WIDTH,
                        IMAGE_LOCATION_FOR_PIECE[piece.__class__.__name__.lower()] * PIECE_HEIGHT,
                        PIECE_WIDTH,
                        PIECE_HEIGHT,
                        colkey=2
                    )

    def toggle_turn(self) -> None:
        self.current_player_turn = Side.BLACK if self.current_player_turn == Side.WHITE else Side.WHITE

