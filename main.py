import pyxel
from game import Game, BOARD_WIDTH, GAME_INFO_WIDTH, BOARD_HEIGHT


class App:
    def __init__(self):
        pyxel.init(BOARD_WIDTH + GAME_INFO_WIDTH, BOARD_HEIGHT, title="chess", fps=40)
        pyxel.load("./assets/PIECES.pyxres")
        pyxel.mouse(visible=True)
        self.game = Game()
        pyxel.run(self.update, self.draw)

    def update(self):
        """"""
        if not self.game.winner:
            self.game.maybe_handle_left_click()
            self.game.maybe_handle_right_click()
            self.game.turn.update_timer()
            self.game.maybe_handle_run_out_of_time()
            self.game.maybe_handle_winner_found()

    def draw(self):
        pyxel.cls(0)
        self.game.draw_board()
        self.game.draw_pieces()
        self.game.draw_game_info()


App()
