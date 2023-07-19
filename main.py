import pyxel
from game import Game

PIECE_WIDTH = 16
PIECE_HEIGHT = 16


class App:
    def __init__(self):
        pyxel.init(PIECE_WIDTH*10, PIECE_HEIGHT*10, title="chess", fps=40)
        pyxel.load("./assets/PIECES.pyxres")
        pyxel.mouse(visible=True)
        self.game = Game()
        pyxel.run(self.update, self.draw)


    def update(self):
        """"""
        self.game.maybe_handle_left_click()
        self.game.maybe_handle_right_click()


    def draw(self):
        pyxel.cls(0)
        self.game.draw_board()
        self.game.draw_pieces()

App()
