from dataclasses import dataclass
from enum import Flag, auto, Enum

FILE_LABELS = ["a", "b", "c", "d", "e", "f", "g", "h"]
RANK_LABELS = ["8", "7", "6", "5", "4", "3", "2", "1"]


class Side(Flag):
    WHITE = auto()
    BLACK = auto()


class MoveType(Enum):
    MOVE = "-"
    ATTACK = "x"
    CASTLE = "O"


class MoveEffect(Enum):
    CHECK = "+"
    CHECKMATE = "#"
    PROMOTION = "=Q"


@dataclass(eq=True, frozen=True)
class Position:
    rank: int
    file: int

    @property
    def algebraic_notation_name(self):
        return f"{FILE_LABELS[self.file]}{RANK_LABELS[self.rank]}"

    def __add__(self, x: "Position") -> "Position":
        return Position(self.rank + x.rank, self.file + x.file)

    def __str__(self) -> str:
        return f"{FILE_LABELS[self.file]}{RANK_LABELS[self.rank]}"


@dataclass
class Vector:
    rank: int
    file: int
    magnitude: int


class ChessPiece:
    def __init__(self, position: Position, side: Side):
        self.position = position
        self.side = side
        self.has_been_moved = False

    @property
    def algebraic_notation_name(self):
        return self.__class__.__name__[0].upper()

    @property
    def move_set(self) -> list[Vector]:
        raise NotImplemented()

    @property
    def attack_set(self) -> list[Vector]:
        """Unless overridden this will be the same as the move set"""
        return self.move_set

    @property
    def special_moves(self) -> dict[MoveType, list[Position]]:
        return {}

    def __str__(self) -> str:
        return f"{{{self.side.name.title()} {self.__class__.__name__} at {str(self.position)}}}"


class Pawn(ChessPiece):
    """Pawn"""

    @property
    def algebraic_notation_name(self):
        """Pawns are identified by the lack of a name"""
        return ""

    @property
    def direction_of_movement(self):
        return -1 if self.side == Side.WHITE else 1

    @property
    def default_rank(self):
        return 6 if self.side == Side.WHITE else 1

    @property
    def promotion_rank(self):
        return 0 if self.side == Side.WHITE else 7

    @property
    def move_set(self) -> list[Vector]:
        """Get relative positions that are possible for this piece, not considering the state of the board"""
        magnitude = 2 if self.position.rank == self.default_rank else 1
        moves = [Vector(rank=1 * self.direction_of_movement, file=0, magnitude=magnitude)]
        return moves

    @property
    def attack_set(self) -> list[Vector]:
        return [
            Vector(rank=1 * self.direction_of_movement, file=1, magnitude=1),
            Vector(rank=1 * self.direction_of_movement, file=-1, magnitude=1),
        ]



class Rook(ChessPiece):
    """"""

    @property
    def move_set(self) -> list[Vector]:
        """Get relative positions that are possible for this piece, not considering the state of the board"""
        return [
            Vector(rank=1, file=0, magnitude=8),
            Vector(rank=-1, file=0, magnitude=8),
            Vector(rank=0, file=1, magnitude=8),
            Vector(rank=0, file=-1, magnitude=8),
        ]


class Bishop(ChessPiece):
    """"""

    @property
    def move_set(self) -> list[Vector]:
        return [
            Vector(rank=1, file=1, magnitude=8),
            Vector(rank=1, file=-1, magnitude=8),
            Vector(rank=-1, file=1, magnitude=8),
            Vector(rank=-1, file=-1, magnitude=8),
        ]


class Knight(ChessPiece):
    """"""

    @property
    def algebraic_notation_name(self):
        return "N"

    @property
    def move_set(self) -> list[Vector]:
        return [
            Vector(rank=2, file=1, magnitude=1),
            Vector(rank=2, file=-1, magnitude=1),
            Vector(rank=-2, file=1, magnitude=1),
            Vector(rank=-2, file=-1, magnitude=1),
            Vector(rank=1, file=2, magnitude=1),
            Vector(rank=1, file=-2, magnitude=1),
            Vector(rank=-1, file=2, magnitude=1),
            Vector(rank=-1, file=-2, magnitude=1),
        ]


class Queen(ChessPiece):
    """"""

    @property
    def move_set(self) -> list[Vector]:
        return [
            Vector(rank=1, file=1, magnitude=8),
            Vector(rank=1, file=-1, magnitude=8),
            Vector(rank=-1, file=1, magnitude=8),
            Vector(rank=-1, file=-1, magnitude=8),
            Vector(rank=1, file=0, magnitude=8),
            Vector(rank=-1, file=0, magnitude=8),
            Vector(rank=0, file=1, magnitude=8),
            Vector(rank=0, file=-1, magnitude=8),
        ]


class King(ChessPiece):
    @property
    def starting_position(self):
        return Position(7, 4) if self.side == Side.WHITE else Position(0, 4)

    @property
    def move_set(self) -> list[Vector]:
        return [
            Vector(rank=1, file=1, magnitude=1),
            Vector(rank=1, file=-1, magnitude=1),
            Vector(rank=-1, file=1, magnitude=1),
            Vector(rank=-1, file=-1, magnitude=1),
            Vector(rank=1, file=0, magnitude=1),
            Vector(rank=-1, file=0, magnitude=1),
            Vector(rank=0, file=1, magnitude=1),
            Vector(rank=0, file=-1, magnitude=1),
        ]

    @property
    def special_moves(self) -> dict[MoveType, list[Position]]:
        if not self.has_been_moved:
            return {
                MoveType.CASTLE: [Position(rank=self.position.rank, file=2), Position(rank=self.position.rank, file=6)]
            }
        return {}
