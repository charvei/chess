from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from functools import cached_property
from time import sleep
from typing import Optional

import pyxel

from chess import Side, Position, ChessBoard, ChessPiece, InvalidMove
from pieces import MoveEffect
from src.lichess_client import LiChess


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


class PlayerInput(Enum):
    CLIENT = "client"
    LICHESS = "lichess"


@dataclass
class Win:
    winner: Side
    reason: WinReason


@dataclass
class Draw:
    reason: DrawReason


@dataclass(frozen=True)
class Player:
    side: Side
    type: PlayerInput


class Game:
    def __init__(self) -> None:
        self.player_1 = Player(Side.WHITE, PlayerInput.LICHESS)
        self.player_2 = Player(Side.BLACK, PlayerInput.LICHESS)
        self._maybe_create_lichess_game()
        self.turn = Turn(self.player_1, self.player_2)
        self.player_perspective = Side.WHITE
        self.selected_position: Optional[Position] = None
        self.outcome: Optional[Win | Draw] = None
        self.board = ChessBoard()
        self.move_history = []
        self.animations: dict[Position, MoveAnimation] = {}

    @cached_property
    def lichess(self):
        return LiChess()

    def _maybe_create_lichess_game(self):
        if PlayerInput.LICHESS in (self.player_1.type, self.player_2.type):
            self.lichess.new_game()

    def update(self) -> None:
        self.turn.update_timer()
        for event in self.lichess.pop_events():
            print(event)
            if event["type"] == "gameState":
                moves = event["moves"].split(" ")
                move_for = Side.WHITE if bool(len(moves) % 2) else Side.BLACK
                if move_for == self.turn.current_player.side and self.turn.current_player.type == PlayerInput.LICHESS:
                    latest_move_src = Position.position_for_alg_coord(moves[-1][0:2])
                    latest_move_dst = Position.position_for_alg_coord(moves[-1][2:4])
                    self.move(latest_move_src, latest_move_dst)

    def move(self, src: Position, dst: Position) -> None:
        move = self.board.move(src, dst, self.turn.current_player.side)
        print(move.long_algebraic_notation)
        self.move_history.append(move)
        if MoveEffect.CHECKMATE in move.side_effects:
            self.outcome = Win(self.turn.current_player.side, WinReason.CHECKMATE)
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
        if (piece := self.board.get_piece(clicked_position)) and piece.side == self.turn.current_player.side:
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
    def __init__(self, player_1: Player, player_2: Player):
        self.current_player, self.waiting_player = (player_1, player_2) if player_1.side == Side.WHITE else (player_2, player_1)
        # Currently hard coded for 10min games
        self.timer = {self.current_player: 10 * 60 * 1000, self.waiting_player: 10 * 60 * 1000}
        self.last_update_time = datetime.now()

    def toggle_current_player(self):
        self.current_player, self.waiting_player = self.waiting_player, self.current_player

    def get_mins_seconds_left(self, side: Side):
        player = self.current_player if side == self.current_player.side else self.waiting_player
        return divmod(self.timer[player] / 1000, 60)

    def update_timer(self):
        self.timer[self.current_player] -= int((datetime.now() - self.last_update_time).microseconds / 1000)
        if self.timer[self.current_player] < 0:
            self.timer[self.current_player] = 0
        self.last_update_time = datetime.now()
