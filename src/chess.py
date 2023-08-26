from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional

from pieces import ChessPiece, Position, Vector, Bishop, Rook, Knight, Queen, King, Side, Pawn, MoveType, MoveEffect


class InvalidMove(Exception):
    """Raise when an invalid move is requested"""


@dataclass
class Move:
    piece: ChessPiece
    src: Position
    dst: Position
    type: Optional[MoveType] = None
    side_effects: set[MoveEffect] = field(default_factory=set)

    @property
    def long_algebraic_notation(self) -> str:
        if self.type == MoveType.CASTLE:
            return "O-O" if self.dst.file == 6 else "O-O-O"

        suffix = ""
        if self.side_effects:
            if MoveEffect.PROMOTION in self.side_effects:
                suffix += MoveEffect.PROMOTION.value
            if MoveEffect.CHECKMATE in self.side_effects:
                suffix += MoveEffect.CHECKMATE.value
            elif MoveEffect.CHECK in self.side_effects:
                suffix += MoveEffect.CHECK.value

        return f"{self.piece.algebraic_notation_name}{self.src.algebraic_notation_name}{self.type.value}{self.dst.algebraic_notation_name}{suffix}"


class ChessBoard:
    def __init__(self, pieces: Optional[list[ChessPiece]] = None):
        self.pieces = pieces if pieces else self.default_pieces()
        self.board: dict[Position, Optional[ChessPiece]] = {piece.position: piece for piece in self.pieces}

    def get_piece(self, position: Position) -> ChessPiece:
        return self.board.get(position)

    def get_possible_moves(self, piece: ChessPiece, move_type: Literal["move", "attack"]) -> list[Position]:
        """"""
        moves = []
        move_set = piece.move_set if move_type == "move" else piece.attack_set
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

    def validate_move(self, move: Move, player: Side) -> MoveType:
        if not move.piece:
            raise InvalidMove("There is no piece at the provided src position")

        if move.piece.side != player:
            raise InvalidMove("Cannot move another player's piece")

        if dst_piece := self.board.get(move.dst):
            # there is another piece at the destination
            if dst_piece.side == move.piece.side:
                raise InvalidMove("Cannot move two pieces of the same side to same square")
            else:
                # piece is taking an opponent piece
                if move.dst in self.get_possible_moves(move.piece, "attack"):
                    return MoveType.ATTACK
                else:
                    raise InvalidMove("Attack is not in src piece's attack set")
        else:
            # Attempting to move to an empty square
            # Check if a special move for the piece we are moving
            for move_type, positions in move.piece.special_moves.items():
                if move.dst in positions:
                    if (
                        move.piece.__class__ == King
                        and move.piece.position.rank == move.dst.rank
                        and (
                            move.dst.file == move.piece.position.file + 2
                            or move.dst.file == move.piece.position.file - 2
                        )
                    ):
                        return self._validate_castle(move.piece, move.piece.position, move.dst)
                    return move_type

            # it's a normal move
            if move.dst in self.get_possible_moves(move.piece, "move"):
                return MoveType.MOVE
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
            if self.get_pieces_attacking_position(position, ~piece.side):
                raise InvalidMove("Cannot castle through positions that are currently attacked.")

        if self.get_pieces_attacking_position(piece.position, ~piece.side):
            raise InvalidMove("Cannot castle when King is in check.")

        return MoveType.CASTLE

    def move(self, src: Position, dst: Position, player: Side):
        """Move a piece"""
        with ProvisionalMove(src, dst, player, self) as pm:
            # Raise an invalid move if new position results in ourselves being in check, provisional move will then
            # handle rolling back
            if self._get_pieces_checking_king(player):
                raise InvalidMove("King would be in check.")

            if pm.move.type == MoveType.CASTLE:
                self._move_castling_rook(src, dst)

            # Is a pawn promotion
            if isinstance(pm.move.piece, Pawn) and pm.move.dst.rank == pm.move.piece.promotion_rank:
                # prompt user for promotion piece
                self.board[dst] = Queen(dst, player)
                pm.move.side_effects.add(MoveEffect.PROMOTION)

            # Does this move check the opponent?
            if checking_pieces := self._get_pieces_checking_king(~player):
                pm.move.side_effects.add(MoveEffect.CHECK)
                if self._is_checkmate(checking_pieces, ~player):
                    print(f"checkmate: {self._is_checkmate(checking_pieces, ~player)}")
                    pm.move.side_effects.add(MoveEffect.CHECKMATE)

            pm.commit()

        return pm.move

    def _is_checkmate(self, checking_pieces: list[ChessPiece], player_in_check: Side) -> bool:
        """
        Determine if opponent has any possible moves to get themselves out of check, if not then it is checkmate.

        Solutions to get out of check are:
        - Moving king
        - Taking pieces that are attacking king
        - Blocking pieces attacking king

        :param checking_pieces:
        :return:
        """
        king = self._get_king(player_in_check)
        for dst in [dst for dst in self.get_possible_moves(king, "move")]:
            try:
                with ProvisionalMove(king.position, dst, player_in_check, self):
                    if not self._get_pieces_checking_king(player_in_check):
                        print("Player can move or attack with King out of check.")
                        return False
            except InvalidMove:
                continue

        # Determine if checking piece can be taken. Only a possible way out of check if there is one attacking piece
        if len(checking_pieces) == 1 and (
            counter_pieces := self.get_pieces_attacking_position(checking_pieces[0].position, player_in_check)
        ):
            # Check that this attack doesn't expose another check
            for counter_piece in counter_pieces:
                with ProvisionalMove(counter_piece.position, checking_pieces[0].position, player_in_check, self):
                    if not self._get_pieces_checking_king(player_in_check):
                        return False

            # Check if any of the player in check's pieces can move to an in between position and get king out of check.
            # Only a possible way out of check if there is only one attacking piece.
            if len(checking_pieces) == 1:
                rank_difference = checking_pieces[0].position.rank - king.position.rank
                file_difference = checking_pieces[0].position.file - king.position.file
                lower_abs_diff, higher_abs_diff = min(abs(rank_difference), abs(file_difference)), max(
                    abs(rank_difference), abs(file_difference)
                )
                if lower_abs_diff == 0:
                    vector = Vector(
                        rank=int(rank_difference / higher_abs_diff),
                        file=int(file_difference / higher_abs_diff),
                        magnitude=higher_abs_diff,
                    )
                else:
                    vector = Vector(
                        rank=int(rank_difference / lower_abs_diff),
                        file=int(file_difference / lower_abs_diff),
                        magnitude=lower_abs_diff,
                    )

                inbetween_positions = [
                    king.position + Position(rank=vector.rank * step, file=vector.file * step)
                    for step in range(1, vector.magnitude)
                ]

                for dst in inbetween_positions:
                    for blocking_pieces in self.get_pieces_attacking_position(dst, player_in_check, "move"):
                        with ProvisionalMove(blocking_pieces.position, dst, player_in_check, self):
                            if not self._get_pieces_checking_king(player_in_check):
                                return False

        # There are no solutions to getting out of check; checkmate.
        return True

    def _move_castling_rook(self, src: Position, dst: Position):
        rook_src, rook_dst = (
            (Position(src.rank, 7), Position(src.rank, 5))
            if dst.file == 6
            else (Position(src.rank, 0), Position(src.rank, 3))
        )
        self.board[rook_dst] = self.get_piece(rook_src)
        self.board[rook_src] = None

    def _get_pieces_checking_king(self, player: Side) -> list[ChessPiece]:
        return self.get_pieces_attacking_position(self._get_king(player).position, ~player)

    def _get_king(self, player: Side) -> ChessPiece:
        for piece in self.pieces:
            if piece.__class__ == King and piece.side == player:
                return piece

    def get_pieces_attacking_position(
        self, position: Position, player: Side, move_type: Literal["attack", "move"] = "attack"
    ) -> list[ChessPiece]:
        # Queen and knight attacks cover all attack vectors
        all_possible_attack_vectors = [
            # queen
            Vector(rank=1, file=1, magnitude=8),
            Vector(rank=1, file=-1, magnitude=8),
            Vector(rank=-1, file=1, magnitude=8),
            Vector(rank=-1, file=-1, magnitude=8),
            Vector(rank=1, file=0, magnitude=8),
            Vector(rank=-1, file=0, magnitude=8),
            Vector(rank=0, file=1, magnitude=8),
            Vector(rank=0, file=-1, magnitude=8),
            # knight
            Vector(rank=2, file=1, magnitude=1),
            Vector(rank=2, file=-1, magnitude=1),
            Vector(rank=-2, file=1, magnitude=1),
            Vector(rank=-2, file=-1, magnitude=1),
            Vector(rank=1, file=2, magnitude=1),
            Vector(rank=1, file=-2, magnitude=1),
            Vector(rank=-1, file=2, magnitude=1),
            Vector(rank=-1, file=-2, magnitude=1),
        ]
        pieces_attacking_position = []
        for vector in all_possible_attack_vectors:
            for step in range(vector.magnitude):
                move = position + Position((1 + step) * vector.rank, (1 + step) * vector.file)
                if not (0 <= move.rank < 8 and 0 <= move.file < 8):
                    # we have reached the end of the board so stop following the vector
                    break
                else:
                    if (piece := self.get_piece(move)) and piece.side == player:
                        # We have found a piece, now to determine if it is attacking where we started
                        if position in self.get_possible_moves(piece, move_type):
                            pieces_attacking_position.append(piece)
        return pieces_attacking_position

    def default_pieces(self) -> list[ChessPiece]:
        pawns = []
        for file in [0, 1, 2, 3, 4, 5, 6, 7, 8]:
            pawns.append(Pawn(position=Position(1, file), side=Side.BLACK))
            pawns.append(Pawn(position=Position(6, file), side=Side.WHITE))
            pass
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


class ProvisionalMove:
    """"""

    def __init__(self, src: Position, dst: Position, player: Side, board: ChessBoard):
        self.player = player
        self.chess_board = board
        self._committed = False
        self.original_dst_piece = None
        self.src_piece = self.chess_board.get_piece(src)
        self.move = Move(self.src_piece, src, dst)
        self._was_piece_moved_before = self.src_piece.has_been_moved

    def __enter__(self):
        self.move.type = self.chess_board.validate_move(self.move, self.player)
        self.original_dst_piece = self.chess_board.get_piece(self.move.dst)
        self.chess_board.board[self.move.src] = None
        self.chess_board.board[self.move.dst] = self.move.piece
        self.move.piece.position = self.move.dst
        self.src_piece.has_been_moved = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type or not self._committed:
            # rollback
            self.chess_board.board[self.move.src] = self.move.piece
            self.chess_board.board[self.move.dst] = self.original_dst_piece
            self.move.piece.position = self.move.src
            self.move.piece.has_been_moved = self._was_piece_moved_before

    def commit(self):
        self._committed = True
