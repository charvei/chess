from dataclasses import dataclass
from typing import Optional

from chess import Side, Position, ChessBoard, ChessPiece, Move, Turn
from pieces import MoveEffect, MoveType


@dataclass
class MoveAnimation:
    piece: ChessPiece
    dst: Position
    progress: float = 0.0

    def update_progress(self):
        self.progress += 0.2


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

    def update(self):
        self.turn.update_timer()
        self.update_animations()

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
