from dataclasses import dataclass
from typing import Optional

import pyxel

from chess import Side, Position, ChessBoard, InvalidMove, ChessPiece, Move, Turn
from pieces import MoveEffect, MoveType
from ui import Board, TILE_HEIGHT, TILE_WIDTH, GameInfo, UIComponent


@dataclass
class MoveAnimation:
    piece: ChessPiece
    dst: Position
    progress: float = 0.0

    def update_progress(self):
        self.progress += 0.25


class Game:
    def __init__(self):
        self.turn = Turn()
        self.player_perspective = Side.WHITE
        self.selected_position: Optional[Position] = None
        self.winner: Optional[Side] = None

        self.board = ChessBoard()

        # For ongoing dev purposes
        self.move_history = [
            Move(self.board.get_piece(Position(1, 1)), Position(1, 1), Position(2, 2), MoveType.MOVE)
            for _ in range(20)
        ]
        # self.move_history = []

        self.animations: dict[Position, MoveAnimation] = {}
        self.board_ui = Board()
        self.game_info_ui = GameInfo()

    def draw(self):
        # self.ui_components[0].draw(self.board, self.selected_position)
        self.board_ui.draw(self.board, self.animations, self.selected_position)
        self.game_info_ui.draw(self.turn, self.move_history)

    def maybe_handle_left_click(self):
        if component := self._get_clicked_ui_component():
            if component.__class__ == Board:
                self.handle_board_left_click()

    def _get_clicked_ui_component(self) -> UIComponent:
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            ui_components = [self.board_ui, self.game_info_ui]
            for component in ui_components:
                if component.coords_are_within_element(pyxel.mouse_x, pyxel.mouse_y):
                    for subcomponent in component.subcomponents:
                        if subcomponent.coords_are_within_element(pyxel.mouse_x, pyxel.mouse_y):
                            return subcomponent
                    return component

    def handle_board_left_click(self):
        if clicked_position := self._get_clicked_position():
            if self.selected_position:
                try:
                    self.move(self.selected_position, clicked_position)
                except InvalidMove as im:
                    print(im)
                else:
                    self.animations[clicked_position] = MoveAnimation(
                        self.board.get_piece(clicked_position), self.selected_position
                    )
                    return
                finally:
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

    def update_animations(self):
        completed = set()
        for position, animation in self.animations.items():
            animation.update_progress()
            if animation.progress > 1:
                completed.add(position)
        for pos in completed:
            self.animations.pop(pos)
