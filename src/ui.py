from typing import Callable, Optional, Protocol

import pyxel

from chess import ChessBoard, Move
from game import Turn, Game, MoveAnimation, GameEvent
from pieces import Position, Side


TILE_WIDTH = 16
TILE_HEIGHT = 16

BOARD_WIDTH = TILE_WIDTH * 10
BOARD_HEIGHT = TILE_HEIGHT * 10

GAME_INFO_WIDTH = TILE_WIDTH * 4
GAME_INFO_HEIGHT = TILE_HEIGHT * 10

IMAGE_LOCATION_FOR_PIECE = {
    "pawn": 0,
    "rook": 1,
    "bishop": 2,
    "knight": 3,
    "queen": 4,
    "king": 5,
}

FILE_LABELS = ["a", "b", "c", "d", "e", "f", "g", "h"]
RANK_LABELS = ["8", "7", "6", "5", "4", "3", "2", "1"]


class UIComponent:
    x: float
    y: float
    width: float
    height: float
    background_colour: int
    subcomponents: list["UIComponent"] = []
    hidden: bool = False

    def draw(self, *args, **kwargs) -> None:
        raise NotImplementedError

    def coords_are_within_element(self, x: int, y: int) -> bool:
        return self.x <= x < self.x + self.width and self.y <= y < self.y + self.height


class Clickable(Protocol):
    def on_click(self, *args: Optional[list], **kwargs: Optional[dict]) -> None:
        pass


class Board(UIComponent):
    def __init__(self) -> None:
        self.x = 0
        self.y = 0
        self.width = TILE_WIDTH * 10
        self.height = TILE_HEIGHT * 10
        self.background_colour = 5
        self.player_perspective = Side.WHITE

    def draw(
        self,
        game: Game,
    ) -> None:
        pyxel.rect(0, 0, TILE_WIDTH * 10, TILE_HEIGHT * 10, 5)

        # Draw file labels
        for file in range(8):
            for y in (0, 9):
                pyxel.text(
                    self._x_index_for_file(file) * TILE_WIDTH + TILE_WIDTH / 2 - 2,
                    y * TILE_HEIGHT + TILE_HEIGHT / 2 - 2,
                    FILE_LABELS[file],
                    col=7,
                )

        # Draw rank labels
        for rank in range(8):
            for x in (0, 9):
                pyxel.text(
                    x * TILE_WIDTH + TILE_WIDTH / 2 - 1,
                    (self._y_index_for_rank(rank) * TILE_HEIGHT) + TILE_HEIGHT / 2 - 2,
                    RANK_LABELS[rank],
                    col=7,
                )

        # Draw board tiles
        for file in range(8):
            for rank in range(8):
                colour = 4 if (rank + file) % 2 else 15
                pyxel.rect(
                    (file + 1) * TILE_WIDTH,
                    (rank + 1) * TILE_HEIGHT,
                    TILE_WIDTH,
                    TILE_HEIGHT,
                    colour,
                )

        # Draw selected border
        if game.selected_position:
            pyxel.blt(
                self._x_index_for_file(game.selected_position.file) * TILE_WIDTH,
                self._y_index_for_rank(game.selected_position.rank) * TILE_HEIGHT,
                2,
                0,
                0,
                TILE_WIDTH,
                TILE_HEIGHT,
                colkey=2,
            )

        self.draw_pieces(game.board, game.animations)

    def draw_pieces(self, board: ChessBoard, animations: dict[Position, MoveAnimation]) -> None:
        for file in range(8):
            for rank in range(8):
                if animation := animations.get(Position(rank, file)):
                    draw_file = animation.dst.file + ((file - animation.dst.file) * animation.progress)
                    draw_rank = animation.dst.rank + ((rank - animation.dst.rank) * animation.progress)
                else:
                    draw_file = file
                    draw_rank = rank

                if piece := board.get_piece(Position(rank, file)):
                    pyxel.blt(
                        self._x_index_for_file(draw_file) * TILE_WIDTH,
                        self._y_index_for_rank(draw_rank) * TILE_HEIGHT,
                        0,
                        0 if piece.side == Side.WHITE else 1 * TILE_WIDTH,
                        IMAGE_LOCATION_FOR_PIECE[piece.__class__.__name__.lower()] * TILE_HEIGHT,
                        TILE_WIDTH,
                        TILE_HEIGHT,
                        colkey=2,
                    )

    def _x_index_for_file(self, file) -> int:
        """
        Get the x / horizontal index for a file, i.e. 0th corresponds to the first file in the board and so on.

        This translates a tile to the appropriate screen coordinate.
        """
        return file + 1 if self.player_perspective == Side.WHITE else 7 - file + 1

    def _y_index_for_rank(self, rank) -> int:
        """
        Get the y / vertical index for a rank, i.e. 0th corresponds to the first rank in the board and so on.

        This translates a tile to the appropriate screen coordinate.
        """
        return rank + 1 if self.player_perspective == Side.WHITE else 7 - rank + 1


class GameInfo(UIComponent):
    """"""

    def __init__(self, ui_events: list[GameEvent]) -> None:
        self.x = BOARD_WIDTH
        self.y = 0
        self.width = GAME_INFO_WIDTH
        self.height = GAME_INFO_HEIGHT
        self.background_colour = 6
        # self.subcomponents = [PlayerTimers(), GameHistory()]
        self.subcomponents = [PlayerTimers(), MoveHistory(), GameControls(ui_events)]

    def draw(self, turn: Turn, move_history: list[Move]) -> None:
        pyxel.rect(self.x, self.y, self.width, self.height, self.background_colour)
        self.subcomponents[0].draw(turn)
        self.subcomponents[1].draw(move_history)
        self.subcomponents[2].draw()
        # for component in self.subcomponents:
        #     component.draw(turn)


class PlayerTimers(UIComponent):
    def __init__(self) -> None:
        self.x = BOARD_WIDTH
        self.y = 0
        self.width = GAME_INFO_WIDTH
        self.height = 1 * TILE_HEIGHT
        self.background_colour = 0

    def draw(self, turn: Turn) -> None:
        # White timer
        pyxel.rect(self.x, 0, self.width / 2, self.height, 15)
        white_mins, white_secs = turn.get_mins_seconds_left(Side.WHITE)
        pyxel.text(self.x + 5, 5, f"{int(white_mins):02d}:{int(white_secs):02d}", 0)

        # Black timer
        pyxel.rect(self.x + (2 * TILE_WIDTH), 0, self.width, self.height, 4)
        black_mins, black_secs = turn.get_mins_seconds_left(Side.BLACK)
        pyxel.text(
            BOARD_WIDTH + 5 + 2 * TILE_WIDTH,
            5,
            f"{int(black_mins):02d}:{int(black_secs):02d}",
            0,
        )


class MoveHistory(UIComponent):
    def __init__(self) -> None:
        self.x = BOARD_WIDTH
        self.y = TILE_HEIGHT * 1
        self.width = GAME_INFO_WIDTH
        self.height = 8 * TILE_HEIGHT
        self.background_colour = 0
        self.subcomponents = [
            ScrollUpButton(self._decrement_move_history_frame),
            ScrollDownButton(self._increment_move_history_frame),
        ]
        self.move_history_window_size = int(8 - 1) * 2 + 1
        self.move_history_frame = 0
        self.prev_move_history: list = []

    def _increment_move_history_frame(self, move_history: list) -> None:
        if self.move_history_frame < max(len(move_history) - self.move_history_window_size, 0):
            self.move_history_frame += 1
            print(self.move_history_frame)

    def _decrement_move_history_frame(self, move_history: list) -> None:
        if self.move_history_frame > 0:
            self.move_history_frame -= 1
            print(self.move_history_frame)

    def draw(self, move_history: list[Move]) -> None:
        move_history_height_tiles = (GAME_INFO_HEIGHT / TILE_HEIGHT) - 2
        pyxel.rect(
            BOARD_WIDTH,
            TILE_HEIGHT * 1,
            GAME_INFO_WIDTH,
            move_history_height_tiles * TILE_HEIGHT,
            0,
        )

        if len(self.prev_move_history) < len(move_history):
            if self.move_history_frame == max(len(self.prev_move_history) - self.move_history_window_size, 0):
                for _ in range(0, len(move_history) - self.move_history_window_size):
                    self._increment_move_history_frame(move_history)

        if len(move_history):
            for draw_pos, move_index in enumerate(
                range(
                    self.move_history_frame,
                    min(len(move_history), self.move_history_frame + self.move_history_window_size),
                )
            ):
                label = f"{int(move_index / 2) + 1}. " if not move_index % 2 else "   "
                pyxel.text(
                    BOARD_WIDTH + 4,
                    (TILE_HEIGHT * 1 + 6) + (draw_pos * (TILE_HEIGHT / 2)),
                    f"{label}{move_history[move_index].long_algebraic_notation}",
                    7,
                )

        self.prev_move_history = move_history

        for component in self.subcomponents:
            component.draw()


class ScrollUpButton(UIComponent, Clickable):
    def __init__(self, on_click: Callable) -> None:
        self.width = 8
        self.height = 8
        self.x = BOARD_WIDTH + GAME_INFO_WIDTH - self.width - 1
        self.y = TILE_HEIGHT + 4
        self.on_click = on_click

    def draw(self) -> None:
        pyxel.blt(
            self.x,
            self.y,
            1,
            0,
            0,
            self.width,
            self.height,
            colkey=2,
        )

    def on_click(self, move_history) -> None:
        self.on_click(move_history)


class ScrollDownButton(UIComponent, Clickable):
    def __init__(self, on_click: Callable) -> None:
        self.width = 8
        self.height = 8
        self.x = BOARD_WIDTH + GAME_INFO_WIDTH - self.width - 1
        self.y = BOARD_HEIGHT - TILE_HEIGHT - self.height - 3
        self.on_click = on_click

    def draw(self) -> None:
        pyxel.blt(
            self.x,
            self.y,
            1,
            0,
            self.height,
            self.width,
            self.height,
            colkey=2,
        )

    def on_click(self, move_history) -> None:
        self.on_click(move_history)


class GameControls(UIComponent, Clickable):
    def __init__(self, ui_events: list[GameEvent]) -> None:
        self.x = BOARD_WIDTH
        self.y = TILE_HEIGHT * 9
        self.width = GAME_INFO_WIDTH
        self.height = TILE_HEIGHT
        self.background_colour = 7
        self.subcomponents = [
            Button(BOARD_WIDTH, self.y, 0, 64, lambda: self.publish_resign(ui_events)),
            Button(BOARD_WIDTH + 2 * TILE_WIDTH, self.y, 0, 80, lambda: self.publish_draw_offer(ui_events)),
        ]

    def publish_draw_offer(self, ui_events: list[GameEvent]) -> None:
        ui_events.append(GameEvent.OFFER_DRAW)

    def publish_resign(self, ui_events: list[GameEvent]) -> None:
        ui_events.append(GameEvent.RESIGN)

    def draw(self) -> None:
        pyxel.rect(
            self.x,
            self.y,
            self.width,
            self.height,
            self.background_colour,
        )

        for component in self.subcomponents:
            component.draw()


class Button(UIComponent, Clickable):
    def __init__(self, x, y, u, v, on_click: Callable) -> None:
        self.x = x
        self.y = y
        self.width = TILE_WIDTH * 2
        self.height = TILE_HEIGHT
        self.background_colour = 0
        self.u = u
        self.v = v
        self.on_click = on_click

    def draw(self) -> None:
        pyxel.blt(self.x, self.y, 1, self.u, self.v, self.width, self.height, colkey=2)

    def on_click(self) -> None:
        self.on_click()


class GameOutcomeModal(UIComponent):
    def __init__(self, ui_events: list[GameEvent]) -> None:
        self.x = TILE_WIDTH * 2
        self.y = TILE_HEIGHT * 2
        self.width = BOARD_WIDTH - (TILE_WIDTH * 4)
        self.height = BOARD_HEIGHT - (TILE_HEIGHT * 4)
        self.background_colour = 0
        self.text_colour = 1
        self.subcomponents = [
            Button(
                self.x + TILE_WIDTH,
                self.y + self.height - TILE_HEIGHT * 2,
                0,
                96,
                lambda: self.publish_restart_game(ui_events),
            )
        ]
        self.hidden = True

    def publish_restart_game(self, ui_events: list[GameEvent]) -> None:
        ui_events.append(GameEvent.RESTART_GAME)

    def draw(self, game: Game) -> None:
        if self.hidden:
            return
        assert game.outcome

        if game.outcome.winner == Side.WHITE:
            self.background_colour = 0
            self.text_colour = 15
        else:
            self.background_colour = 0
            self.text_colour = 4

        pyxel.rect(self.x, self.y, self.width, self.height, self.background_colour)
        pyxel.text(
            self.x + 1 * TILE_WIDTH,
            self.y + 1 * TILE_HEIGHT,
            f"{game.outcome.winner.name.title()} wins\n\nby {game.outcome.reason.value}!",
            self.text_colour,
        )

        for component in self.subcomponents:
            component.draw()
