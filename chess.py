from dataclasses import dataclass
from enum import Enum
from typing import Literal, Optional


class InvalidMove(Exception):
    """Raise when an invalid move is requested"""


class Side(Enum):
    WHITE = 0
    BLACK = 1


@dataclass(eq=True, frozen=True)
class Position:
    rank: int
    file: int

    def __add__(self, x: "Position") -> "Position":
        return Position(self.rank + x.rank, self.file + x.file)

    def __str__(self) -> str:
        return f"{{Pos:{self.rank},{self.file}}}"


@dataclass
class Vector:
    rank: int
    file: int
    magnitude: int


class ChessPiece:
    def __init__(self, position: Position, side: Side):
        self.position = position
        self.side = side

    @property
    def move_set(self) -> list[Vector]:
        raise NotImplemented()

    @property
    def attack_set(self) -> list[Vector]:
        """Unless overridden this will be the same as the move set"""
        return self.move_set

    def __str__(self) -> str:
        return f"{{{self.side.name.title()} {self.__class__.__name__} at {str(self.position)}}}"


class Pawn(ChessPiece):
    """Pawn"""
    @property
    def direction_of_movement(self):
        return -1 if self.side == Side.WHITE else 1

    @property
    def default_rank(self):
        return 7 if self.side == Side.WHITE else 2

    @property
    def move_set(self) -> list[Vector]:
        """Get relative positions that are possible for this piece, not considering the state of the board"""
        magnitude = 2 if self.position.rank == self.default_rank else 1
        moves = [Vector(rank=1*self.direction_of_movement, file=0, magnitude=magnitude)]
        return moves

    @property
    def attack_set(self) -> list[Vector]:
        return [
            Vector(rank=1*self.direction_of_movement, file=1, magnitude=1),
            Vector(rank=1*self.direction_of_movement, file=-1, magnitude=1)
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
            Vector(rank=0, file=-1, magnitude=8)
        ]


class Bishop(ChessPiece):
    """"""
    @property
    def move_set(self) -> list[Vector]:
        return [
            Vector(rank=1, file=1, magnitude=8),
            Vector(rank=1, file=-1, magnitude=8),
            Vector(rank=-1, file=1, magnitude=8),
            Vector(rank=-1, file=-1, magnitude=8)
        ]


class Knight(ChessPiece):
    """"""
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
            Vector(rank=-1, file=-2, magnitude=1)
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
            Vector(rank=0, file=-1, magnitude=8)
        ]


class King(ChessPiece):
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
            Vector(rank=0, file=-1, magnitude=1)
        ]


class ChessBoard:
    ranks = [1, 2, 3, 4, 5, 6, 7, 8]
    files = [1, 2, 3, 4, 5, 6, 7, 8]

    def __init__(self, pieces: Optional[list[ChessPiece]] = None):
        self.pieces = pieces if pieces else self.default_pieces()
        self.board: dict[Position, ChessPiece] = {piece.position: piece for piece in self.pieces}

    def get_piece(self, position: Position) -> ChessPiece:
        return self.board.get(position)

    def get_possible_moves(self, piece: ChessPiece, move_type: Literal["move", "attack"]) -> list[Position]:
        """"""
        moves = []
        move_set = piece.move_set if move_type == "move" else piece.attack_set
        for vector in move_set:
            for step in range(vector.magnitude):
                move = piece.position + Position((1 + step) * vector.rank, (1 + step) * vector.file)
                if not (0 < move.rank < 9 and 0 < move.file < 9):
                    # we have reached the end of the board so stop following the vector
                    break
                else:
                    moves.append(move)
                    if self.get_piece(move) or not (0 < move.rank < 9 and 0 < move.file < 9):
                        # A piece is blocking us so don't follow the vector anymore
                        break
        return moves

    def validate_move(self, src: Position, dst: Position, player: Side):
        if not (src_piece := self.get_piece(src)):
            raise InvalidMove("There is no piece at the provided src position")

        if src_piece.side != player:
            raise InvalidMove("Cannot move another player's piece")

        if dst_piece := self.board.get(dst):
            # there is another piece at the destination
            if dst_piece.side == src_piece.side:
                raise InvalidMove("Cannot move two pieces of the same side to same square")
            else:
                # piece is taking an opponent piece
                if dst not in self.get_possible_moves(src_piece, "attack"):
                    raise InvalidMove("Attack is not in src piece's attack set")
        else:
            # Attempting to move to an empty square
            if dst not in self.get_possible_moves(src_piece, "move"):
                raise InvalidMove("Move is not in src piece's move set")

    def move(self, src: Position, dst: Position, player: Side):
        """Move a piece"""
        self.validate_move(src, dst, player)
        piece_to_move = self.get_piece(src)
        self.board[src] = None
        self.board[dst] = piece_to_move
        piece_to_move.position = dst

    def default_pieces(self) -> list[ChessPiece]:
        pawns = []
        for file in self.files:
            pawns.append(Pawn(position=Position(2, file), side=Side.BLACK))
            pawns.append(Pawn(position=Position(7, file), side=Side.WHITE))

        return pawns + [
            Rook(position=Position(1, 1), side=Side.BLACK),
            Rook(position=Position(1, 8), side=Side.BLACK),
            Rook(position=Position(8, 1), side=Side.WHITE),
            Rook(position=Position(8, 8), side=Side.WHITE),
            Bishop(position=Position(1, 3), side=Side.BLACK),
            Bishop(position=Position(1, 6), side=Side.BLACK),
            Bishop(position=Position(8, 3), side=Side.WHITE),
            Bishop(position=Position(8, 6), side=Side.WHITE),
            Knight(position=Position(1, 2), side=Side.BLACK),
            Knight(position=Position(1, 7), side=Side.BLACK),
            Knight(position=Position(8, 2), side=Side.WHITE),
            Knight(position=Position(8, 7), side=Side.WHITE),
            Queen(position=Position(8, 4), side=Side.WHITE),
            Queen(position=Position(1, 4), side=Side.BLACK),
            King(position=Position(8, 5), side=Side.WHITE),
            King(position=Position(1, 5), side=Side.BLACK)
        ]