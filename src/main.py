from typing import Optional

import pyxel

from chess import InvalidMove
from game import Game, MoveAnimation, GameEvent
from pieces import Position, Side
from ui import (
    Board,
    TILE_HEIGHT,
    TILE_WIDTH,
    GameInfo,
    UIComponent,
    ScrollUpButton,
    ScrollDownButton,
    BOARD_WIDTH,
    GAME_INFO_WIDTH,
    BOARD_HEIGHT,
    Button,
)


class App:
    def __init__(self):
        pyxel.init(BOARD_WIDTH + GAME_INFO_WIDTH, BOARD_HEIGHT, title="chess", fps=60)
        pyxel.load("../assets/PIECES.pyxres")
        pyxel.mouse(visible=True)
        self.game = Game()
        self.ui_events = list()
        self.board_ui = Board()
        self.game_info_ui = GameInfo(self.ui_events)
        pyxel.run(self.update, self.draw)

    def update(self):
        """"""
        if not self.game.winner:
            self.maybe_handle_left_click()
            self.maybe_handle_right_click()
            self.game.update()
            self.handle_game_events()
            self.maybe_handle_run_out_of_time()
            self.maybe_handle_winner_found()
        self.game.update_animations()

    def draw(self):
        pyxel.cls(0)
        self.board_ui.draw(self.game)
        # We copy() this list so the ui gets the value not reference, so it can react to state changes better
        self.game_info_ui.draw(self.game.turn, self.game.move_history.copy())

    def handle_game_events(self):
        while self.ui_events:
            event = self.ui_events.pop()
            if event == GameEvent.RESIGN:
                print("handling resign")
                self.game.winner = ~self.game.turn.current_player
            if event == GameEvent.OFFER_DRAW:
                print("handling draw offer")

    def maybe_handle_left_click(self):
        if component := self._get_clicked_ui_component():
            print(component)
            if component.__class__ == Board:
                self.handle_board_left_click()
            elif isinstance(component, ScrollUpButton) or isinstance(component, ScrollDownButton):
                component.on_click(self.game.move_history)
            elif isinstance(component, Button):
                component.on_click()

    def _get_clicked_ui_component(self) -> UIComponent:
        # todo: this is just a quick implementation, needs to handle any level of depth
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            ui_components = [self.board_ui, self.game_info_ui]
            for component in ui_components:
                if component.coords_are_within_element(pyxel.mouse_x, pyxel.mouse_y):
                    for subcomponent in component.subcomponents:
                        if subcomponent.coords_are_within_element(pyxel.mouse_x, pyxel.mouse_y):
                            for subsubcomponent in subcomponent.subcomponents:
                                if subsubcomponent.coords_are_within_element(pyxel.mouse_x, pyxel.mouse_y):
                                    return subsubcomponent
                            return subcomponent
                    return component

    def handle_board_left_click(self):
        if clicked_position := self._get_clicked_position():
            if self.game.selected_position:
                try:
                    self.game.move(self.game.selected_position, clicked_position)
                except InvalidMove as im:
                    print(im)
                else:
                    self.game.animations[clicked_position] = MoveAnimation(
                        self.game.board.get_piece(clicked_position), self.game.selected_position
                    )
                    return
                finally:
                    self.game.selected_position = None
        if (piece := self.game.board.get_piece(clicked_position)) and piece.side == self.game.turn.current_player:
            # Only allow for selecting position corresponding to a piece of a current players
            self.game.selected_position = clicked_position

    def _get_clicked_position(self) -> Optional[Position]:
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            # convert screen position to board position
            if self.game.player_perspective == Side.WHITE:
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
            self.game.selected_position = None

    def maybe_handle_run_out_of_time(self):
        if self.game.turn.timer[self.game.turn.current_player] <= 0:
            self.game.winner = Side.WHITE if self.game.turn.current_player == Side.BLACK else Side.BLACK

    def maybe_handle_winner_found(self):
        if self.game.winner:
            print(f"Winner: {self.game.winner.name.title()}")


App()

# todo:
#  inprogress:
#   - game over handling / forfeit / starting new games,
#  backlog
#   - en passant,
#   - dragging / dropping pieces
#   - connect to chess engine / api
#   - short form algebraic notation
#   - reverse & forward board through move history
#   - auto chess variant
#   - export game move history
#   - playback from exported move history
#  done:
#   - fix rank labels (wrong order),
#   - long algebraic notation
#   - castling
#   - check
#   - check shows in move history
#   - checkmate
#   - swapping player perspective
#   - pawn promotion
#   - animation
#   - scrolling move history - polish,
#   - checkmate  on edge rank bug
