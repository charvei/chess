from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

import pyxel

from chess import Side, Position, ChessBoard, ChessPiece, InvalidMove
from pieces import MoveEffect


@dataclass
class MoveAnimation:
    piece: ChessPiece
    dst: Position
    progress: float = 0.0

    def update_progress(self):
        self.progress += 0.2


class GameEvent(Enum):
    OFFER_DRAW = 1
    RESIGN = 2
    RESTART_GAME = 3


class WinReason(Enum):
    CHECKMATE = "checkmate"
    RESIGNATION = "resignation"
    TIME = "time"


class DrawReason(Enum):
    STALEMATE = "stalemate"
    AGREEMENT = "agreement"


@dataclass
class Win:
    winner: Side
    reason: WinReason


@dataclass
class Draw:
    reason: DrawReason


class Game:
    def __init__(self) -> None:
        self.turn = Turn()
        self.player_perspective = Side.WHITE
        self.selected_position: Optional[Position] = None
        self.outcome: Optional[Win | Draw] = None
        self.board = ChessBoard()
        self.move_history = []
        self.animations: dict[Position, MoveAnimation] = {}

    def update(self) -> None:
        self.turn.update_timer()

    def move(self, src: Position, dst: Position) -> None:
        move = self.board.move(src, dst, self.turn.current_player)
        print(move.long_algebraic_notation)
        self.move_history.append(move)
        if MoveEffect.CHECKMATE in move.side_effects:
            self.outcome = Win(self.turn.current_player, WinReason.CHECKMATE)
        self.turn.toggle_current_player()

    def update_animations(self) -> None:
        completed = set()
        for position, animation in self.animations.items():
            animation.update_progress()
            if animation.progress > 1:
                completed.add(position)
        for pos in completed:
            self.animations.pop(pos)

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
                rank = int(pyxel.mouse_y / 16) - 1
                file = int(pyxel.mouse_x / 16) - 1
            else:
                rank = 7 - int(pyxel.mouse_y / 16) + 1
                file = 7 - int(pyxel.mouse_x / 16) + 1

            # Only return a position if a board tile was clicked
            if 0 <= rank < 8 and 0 <= file < 8:
                return Position(rank, file)


class Turn:
    def __init__(self):
        self.current_player = Side.WHITE
        # Currently hard coded for 10min games
        self.timer = {Side.WHITE: 10 * 60 * 100, Side.BLACK: 10 * 60 * 1000}
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
