from enum import Enum
from typing import Union
from . import Constants


class ChessColor(Enum):
    WHITE = Constants.ENUM_WHITE_KEY
    BLACK = Constants.ENUM_BLACK_KEY


class ChessResult(Enum):
    LOSS = Constants.ENUM_LOSS_KEY
    DRAW = Constants.ENUM_DRAW_KEY
    WIN = Constants.ENUM_WIN_KEY

    @staticmethod
    def chessResultToStr(result) -> str:
        if result == ChessResult.WIN:
            return Constants.WIN_KEY
        elif result == ChessResult.DRAW:
            return Constants.DRAW_KEY
        elif result == ChessResult.LOSS:
            return Constants.LOSS_KEY
        else:
            raise ValueError("Invalid ChessResult value")

    @staticmethod
    def numToChessResult(result: Union[float, int, list[Union[float, int], ...]]):
        chessResTranslator = {Constants.ENUM_WIN_KEY: ChessResult.WIN, Constants.ENUM_DRAW_KEY: ChessResult.DRAW,
                              Constants.ENUM_LOSS_KEY: ChessResult.LOSS}
        if isinstance(result, (float, int)):
            return (chessResTranslator[result],)
        else:
            return tuple(chessResTranslator[r] for r in result if r in chessResTranslator)
