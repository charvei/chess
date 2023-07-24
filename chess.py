from dataclasses import dataclass
from enum import Enum
from typing import Literal, Optional


FILE_LABELS = ["a", "b", "c", "d", "e", "f", "g", "h"]
RANK_LABELS = ["8", "7", "6", "5", "4", "3", "2", "1"]


class InvalidMove(Exception):
    """Raise when an invalid move is requested"""


class Side(Enum):
    WHITE = 0
    BLACK = 1


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
    def special_moves(self) -> list[Vector]:
        return []

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
    def special_moves(self) -> list[Vector]:
        return [Vector(rank=0, file=2, magnitude=1), Vector(rank=0, file=-2, magnitude=1)]


class MoveType(Enum):
    MOVE = "-"
    ATTACK = "x"
    CASTLE = "O"


@dataclass(frozen=True)
class Move:
    piece: ChessPiece
    src: Position
    dst: Position
    type: MoveType

    @property
    def long_algebraic_notation(self) -> str:
        if self.type == MoveType.CASTLE:
            return "O-O" if self.dst.file == 6 else "O-O-O"
        return f"{self.piece.algebraic_notation_name}{self.src.algebraic_notation_name}{self.type.value}{self.dst.algebraic_notation_name}"


class ChessBoard:
    def __init__(self, pieces: Optional[list[ChessPiece]] = None):
        self.pieces = pieces if pieces else self.default_pieces()
        self.board: dict[Position, ChessPiece] = {piece.position: piece for piece in self.pieces}

    def get_piece(self, position: Position) -> ChessPiece:
        return self.board.get(position)

    def get_possible_moves(self, piece: ChessPiece, move_type: Literal["move", "attack"]) -> list[Position]:
        """"""
        moves = []
        move_set = piece.move_set + piece.special_moves if move_type == "move" else piece.attack_set
        for vector in move_set:
            for step in range(vector.magnitude):
                move = piece.position + Position((1 + step) * vector.rank, (1 + step) * vector.file)
                if not (0 <= move.rank < 8 and 0 <= move.file < 8):
                    # we have reached the end of the board so stop following the vector
                    break
                else:
                    moves.append(move)
                    if self.get_piece(move) or not (0 <= move.rank < 8 and 0 <= move.file < 8):
                        # A piece is blocking us so don't follow the vector anymore
                        break
        return moves

    def validate_move(self, src: Position, dst: Position, player: Side) -> Move:
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
                if dst in self.get_possible_moves(src_piece, "attack"):
                    return Move(src_piece, src, dst, MoveType.ATTACK)
                else:
                    raise InvalidMove("Attack is not in src piece's attack set")
        else:
            # Attempting to move to an empty square
            if dst in self.get_possible_moves(src_piece, "move"):
                if (
                    src_piece.__class__ == King
                    and src.rank == dst.rank
                    and (dst.file == src.file + 2 or dst.file == src.file - 2)
                ):
                    # player is trying to castle
                    self._validate_castle(src_piece, src, dst)
                    return Move(src_piece, src, dst, MoveType.CASTLE)

                return Move(src_piece, src, dst, MoveType.MOVE)
            else:
                raise InvalidMove("Move is not in src piece's move set")

    def _validate_castle(self, piece: ChessPiece, src: Position, dst: Position):
        """
        Requirements for castling:
        - King has not been previously moved
        - Rook has not been previously moved
        - There are no pieces between King and Rook
        - None of the tiles the King moves through is under attacked
        - King is not currently in check
        """
        if piece.has_been_moved:
            raise InvalidMove("Cannot castle a King that has been previously moved.")

        # Depending on whether we are castling kingside or queenside we have different positions to check
        positions_to_be_clear, position_to_have_rook = (
            ([Position(piece.position.rank, 5), Position(piece.position.rank, 6)], Position(piece.position.rank, 7))
            if dst.file == src.file + 2
            else (
                [Position(piece.position.rank, 1), Position(piece.position.rank, 2), Position(piece.position.rank, 3)],
                Position(piece.position.rank, 0),
            )
        )

        if not (
            (maybe_rook := self.get_piece(position_to_have_rook))
            and maybe_rook.__class__ == Rook
            and not maybe_rook.has_been_moved
        ):
            raise InvalidMove("Cannot castle when rook has been moved from default position.")

        for position in positions_to_be_clear:
            if self.get_piece(position) is not None:
                raise InvalidMove("Cannot castle when pieces are in between King and Rook.")
            # if self.is_position_attacked(position):
            #     raise InvalidMove("Cannot castle through positions that are currently attacked.")

        # if piece.is_in_check:
        #     raise InvalidMove("Cannot castle with a King that is currently in check.")

    def move(self, src: Position, dst: Position, player: Side):
        """Move a piece"""
        move = self.validate_move(src, dst, player)
        piece_to_move = self.get_piece(src)

        if move.type == MoveType.CASTLE:
            rook_src, rook_dst = (
                (Position(src.rank, 7), Position(src.rank, 5))
                if dst.file == 6
                else (Position(src.rank, 0), Position(src.rank, 3))
            )
            rook = self.get_piece(rook_src)
            self.board[rook_dst] = rook
            self.board[rook_src] = None
            rook.has_been_moved = True

        self.board[src] = None
        self.board[dst] = piece_to_move
        piece_to_move.position = dst
        piece_to_move.has_been_moved = True
        return move

    def default_pieces(self) -> list[ChessPiece]:
        pawns = []
        for file in [0, 1, 2, 3, 4, 5, 6, 7, 8]:
            pawns.append(Pawn(position=Position(1, file), side=Side.BLACK))
            pawns.append(Pawn(position=Position(6, file), side=Side.WHITE))
        return pawns + [
            Rook(position=Position(0, 0), side=Side.BLACK),
            Rook(position=Position(0, 7), side=Side.BLACK),
            Rook(position=Position(7, 0), side=Side.WHITE),
            Rook(position=Position(7, 7), side=Side.WHITE),
            Bishop(position=Position(0, 2), side=Side.BLACK),
            Bishop(position=Position(0, 5), side=Side.BLACK),
            Bishop(position=Position(7, 2), side=Side.WHITE),
            Bishop(position=Position(7, 5), side=Side.WHITE),
            Knight(position=Position(0, 1), side=Side.BLACK),
            Knight(position=Position(0, 6), side=Side.BLACK),
            Knight(position=Position(7, 1), side=Side.WHITE),
            Knight(position=Position(7, 6), side=Side.WHITE),
            Queen(position=Position(7, 3), side=Side.WHITE),
            Queen(position=Position(0, 3), side=Side.BLACK),
            King(position=Position(7, 4), side=Side.WHITE),
            King(position=Position(0, 4), side=Side.BLACK),
        ]
