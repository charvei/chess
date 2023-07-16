from time import sleep
from typing import Optional

import pyxel
from chess import ChessBoard, Position, Side, InvalidMove

PIECE_WIDTH = 16
PIECE_HEIGHT = 16

IMAGE_LOCATION_FOR_PIECE = {
    "pawn": 0,
    "rook": 1,
    "bishop": 2,
    "knight": 3
}


class App:
    def __init__(self):
        pyxel.init(PIECE_WIDTH*10, PIECE_HEIGHT*10, title="chess", fps=40)
        pyxel.load("./assets/PIECES.pyxres")
        pyxel.mouse(visible=True)
        self.cb = ChessBoard()
        self.selected_position: Optional[Position] = None

        # Initial background
        pyxel.rect(0, 0, PIECE_WIDTH*10, PIECE_HEIGHT*10, 5)

        self._test_moves()

        pyxel.run(self.update, self.draw)


    def update(self):
        """"""
        if pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
            # convert screen position to board position
            rank, file = int(pyxel.mouse_y / PIECE_HEIGHT), int(pyxel.mouse_x / PIECE_WIDTH)
            print(rank, file, pyxel.mouse_x, pyxel.mouse_y)

            if not self.selected_position:
                self.selected_position = Position(rank, file)
            else:
                try:
                    self.cb.move(self.selected_position, Position(rank, file), Side.WHITE)
                    self.selected_position = None
                except InvalidMove as im:
                    print(im)


        if pyxel.btn(pyxel.MOUSE_BUTTON_RIGHT):
            self.selected_position = None



            # print(pyxel.mouse_x, pyxel.mouse_y)
        # self.cb.move(Position(self.x, 5), Position(self.x+1, 5), Side.WHITE)

    def draw(self):
        pyxel.cls(0)
        self._draw_board()
        self._draw_pieces()

    def _draw_board(self):
        # Initial background
        pyxel.rect(0, 0, PIECE_WIDTH * 10, PIECE_HEIGHT * 10, 5)

        # Draw file labels
        for file in range(1, 9):
            for y in (0, 9):
                pyxel.blt(file * PIECE_WIDTH, y * PIECE_HEIGHT, 1, 0, (file - 1) * PIECE_HEIGHT, PIECE_WIDTH, PIECE_HEIGHT, colkey=2)

        # Draw rank labels
        for rank in range(1, 9):
            for x in (0, 9):
                pyxel.blt(x * PIECE_WIDTH, rank * PIECE_HEIGHT, 1, PIECE_WIDTH, (8 - rank) * PIECE_HEIGHT, PIECE_WIDTH,
                          PIECE_HEIGHT, colkey=2)

        # Draw board
        for file in range(1,9):
            for rank in range(1, 9):
                colour = 4 if (rank + file) % 2 else 15
                pyxel.rect(file * PIECE_WIDTH, rank * PIECE_HEIGHT, PIECE_WIDTH, PIECE_HEIGHT, colour)

        # Draw selected
        if self.selected_position:
            pyxel.blt(self.selected_position.file * PIECE_WIDTH, self.selected_position.rank * PIECE_HEIGHT, 2, 0, 0,PIECE_WIDTH,
                          PIECE_HEIGHT, colkey=2)

    def _draw_pieces(self):
        for file in (range(8)):
            for rank in (range(8)):
                if piece := self.cb.get_piece(Position(rank + 1, file + 1)):
                    pyxel.blt(
                        (file + 1) * PIECE_WIDTH,
                        (rank + 1) * PIECE_HEIGHT,
                        0,
                        piece.side.value*PIECE_WIDTH,
                        IMAGE_LOCATION_FOR_PIECE[piece.__class__.__name__.lower()]*PIECE_HEIGHT,
                        PIECE_WIDTH,
                        PIECE_HEIGHT,
                        colkey=2
                    )

    def _test_moves(self):
        # Pawn movement
        self.cb.move(Position(2, 5), Position(4, 5), Side.BLACK)
        self.cb.move(Position(4, 5), Position(5, 5), Side.BLACK)
        self.cb.move(Position(5, 5), Position(6, 5), Side.BLACK)
        self.cb.move(Position(6, 5), Position(7, 6), Side.BLACK)

        # Bishop movement
        self.cb.move(Position(3, 3), Position(3, 5), Side.BLACK)
        self.cb.move(Position(3, 5), Position(7, 5), Side.BLACK)
        self.cb.move(Position(7, 5), Position(3, 5), Side.BLACK)
        self.cb.move(Position(3, 5), Position(3, 3), Side.BLACK)
        self.cb.move(Position(3, 3), Position(7, 3), Side.BLACK)

        self.cb.move(Position(1, 6), Position(6, 1), Side.BLACK)
        self.cb.move(Position(7, 2), Position(6, 1), Side.WHITE)
        # self.cb.move(Position(6, 1), Position(7, 2), Side.BLACK)


App()
