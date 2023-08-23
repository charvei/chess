from dataclasses import dataclass
from enum import Enum
from typing import Optional, Literal

from chess import Side, Position, ChessBoard, ChessPiece, Turn
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
