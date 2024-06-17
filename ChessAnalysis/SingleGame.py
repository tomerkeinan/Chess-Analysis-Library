from functools import wraps
import importlib.resources as pkg_resources
from .Enums import ChessColor, ChessResult
from . import Constants
from typing import Tuple, Union
from stockfish import Stockfish
from datetime import datetime
from copy import deepcopy
import chess
import re
import os


def _changeTurn(turn) -> ChessColor:
    if turn == ChessColor.WHITE:
        turn = ChessColor.BLACK
    else:
        turn = ChessColor.WHITE
    return turn


def _openingBookInit() -> dict[str, str]:
    """
    Initialize the opening book by reading from TSV files in the specified directory.

    Returns:
        dict[str, str]: A dictionary mapping openings to their descriptions.
    """
    
    openingBook = {}
    opening_book_dir = pkg_resources.files(__package__) / Constants.OPENING_BOOK_DIR
    for file_name in os.listdir(opening_book_dir):
        input_file = os.path.join(opening_book_dir, file_name)
        if not file_name.endswith(Constants.VALID_OPENING_BOOK_EXTENSION):
            continue
        with open(input_file, 'r') as f:
            content = f.read()
            start_index = content.find(Constants.OPENING_START_MARKER) + len(Constants.OPENING_START_MARKER)
            end_index = content.find(Constants.OPENING_END_MARKER)
            relevant_section = content[start_index:end_index]
            pattern = re.compile(Constants.OPENING_PATTERN)
            matches = pattern.findall(relevant_section)
            openingBook.update({match[2]: match[1] for match in matches})
    return openingBook


def _addMoveOrder(moveNum: int, move: str) -> str:
    """
    Add move numbering to the move string for proper game notation.

    Args:
        moveNum (int): The move number.
        move (str): The move string.

    Returns:
        str: The move string with move numbering.
    """
    
    cur_move = ""
    if moveNum % 2 == 0:
        cur_move += str(int((moveNum / 2) + 1)) + ". "  # Move numbering pattern as the key in the
        # openingBook dictionary.
    cur_move += move
    return cur_move


def _parseTime(time: str) -> int:
    """
    Parse a time string and return the total time in seconds.

    Args:
        time (str): The time string in the format "hh:mm:ss".

    Returns:
        int: The total time in seconds.
    """
    
    pattern = Constants.TIME_PATTERN
    match = re.match(pattern, time)
    hours = int(match.group(1))
    minutes = int(match.group(2))
    seconds = int(match.group(3))
    fractional = float(match.group(4)) if match.group(4) else 0
    return (hours * Constants.NORMALIZED_HOURS + minutes *
            Constants.NORMALIZED_MINUTES + seconds * Constants.NORMALIZED_SECONDS + fractional)


def extractTimeControl(timeControl: str) -> Tuple[int, int]:
    """
    Extract the main time control and bonus time from the time control string.

    Args:
        timeControl (str): The time control string in the format "main+bonus".

    Returns:
        Tuple[int, int]: The main time control and bonus time in seconds.
    """
    
    assert isinstance(timeControl, str), Constants.INVALID_TIME_CONTROL
    parts = timeControl.split(Constants.TIME_CONTROL_SEPERATOR, 1)

    timeControl = parts[0]

    assert timeControl.isdigit(), Constants.INVALID_TIME_CONTROL

    if len(parts) > 1:
        timeBonus = parts[1]
        assert timeBonus.isdigit(), Constants.INVALID_TIME_CONTROL
        return int(timeControl), int(timeBonus)

    return int(timeControl), Constants.NO_TIME_BONUS


def validateAnalysis(method):
    """
    Decorator to ensure that the game is analyzed before accessing certain properties.

    Args:
        method (Callable): The method to wrap.

    Returns:
        Callable: The wrapped method.
    """
    
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.isAnalyzed():
            self.analyzeGame()
        return method(self, **kwargs)
    return wrapper


def parseDate(date: str) -> datetime:
    """
    Parse a date string and return a datetime object.

    Args:
        date (str): The date string in the format "yyyy-mm-dd".

    Returns:
        datetime: The parsed datetime object.
    """
    
    if date is None:
        return datetime.today()
    date = date.split(Constants.DATE_SEPERATOR)
    for i in range(1, 3):
        if date[i].startswith("0"):
            date[i] = date[i][1]
    return datetime(int(date[0]), int(date[1]), int(date[2]))


class SingleGame:
    def __init__(self, pgn: str, whiteElo: int, blackElo: int, result: str, time_control: str,
                 userColor: ChessColor, stockfish: Stockfish, opponent: str, date: str) -> None:
        """
        Initialize a SingleGame instance with the provided parameters.

        Args:
            pgn (str): The PGN string of the game.
            whiteElo (int): The ELO rating of the white player.
            blackElo (int): The ELO rating of the black player.
            result (str): The result of the game.
            time_control (str): The time control for the game.
            userColor (ChessColor): The color of the user.
            stockfish (Stockfish): The Stockfish engine instance.
            opponent (str): The opponent's name.
            date (str): The date of the game.
        """

        self._isAnalyzed: bool = False

        self._pgn = pgn
        self._openingBook = _openingBookInit()
        self._pgnWithClockFormat: bool = self._isThereClk()

        self._board = chess.Board()
        self._stockfish = stockfish
        self._stockfish.set_fen_position(self._board.fen())
        self._opponent = opponent

        self._date = parseDate(date)

        self._errorPerMove: list[float] = []
        self._timeSpentPerMove: list[float] = []

        self._whiteElo: int = whiteElo
        self._blackElo: int = blackElo
        self._timeControl, self._bonusTime = extractTimeControl(time_control)
        self._userColor: ChessColor = userColor
        self._gameResult: ChessResult = self._extractGameResult(result)
        self._mainOpening: str = Constants.UNKNOWN_OPENING
        self._openingVariation: Union[str, type[None]] = None
        self._moveLeavingOpening: int = 0

        self._initOpenings()

        self._validate_pgn()

    def __copy__(self):
        return self.__deepcopy__({})

    def __deepcopy__(self, memo):
        """
        Create a deep copy of the instance.

        Args:
            memo (dict): A dictionary to keep track of already copied objects.

        Returns:
            SingleGame: A deep copy of the instance.
        """
        
        new_instance = SingleGame(
            self._pgn,
            self._whiteElo,
            self._blackElo,
            ChessResult.chessResultToStr(self._gameResult),
            Constants.DEFAULT_TIME_CONTROL,
            self._userColor,
            self._stockfish,
            self._opponent,
            Constants.DEFAULT_FROM_DATE_VALUE
        )

        new_instance._timeControl, new_instance._time_control_bonus = self._timeControl, self._bonusTime
        new_instance.date = self._date

        new_instance.errorPerMove = deepcopy(self._errorPerMove)
        new_instance.timeSpentPerMove = deepcopy(self._timeSpentPerMove)

        new_instance._mainOpening = self._mainOpening
        new_instance._openingVariation = self._openingVariation

        return new_instance

    def _extractGameResult(self, result: str) -> ChessResult:
        """
        Extract the game result from the result string.

        Args:
            result (str): The result string.

        Returns:
            ChessResult: The extracted game result.
        """
        
        result = result.split(Constants.RESULT_SEPERATOR)[0]
        if result == Constants.DRAW:
            return ChessResult.DRAW
        elif result == Constants.LOSS:
            return ChessResult.LOSS if self._userColor == ChessColor.WHITE else ChessResult.WIN
        return ChessResult.WIN if self._userColor == ChessColor.WHITE else ChessResult.LOSS

    def _isThereClk(self) -> bool:
        """
        Check if the PGN contains clock format.

        Returns:
            bool: True if the PGN contains clock format, False otherwise.
        """
        
        clock_pattern = re.compile(Constants.CLOCK_PATTERN)

        # Split the content by spaces and check each part
        parts = self._pgn.split()

        for part in parts:
            if clock_pattern.match(part):
                return True

        return False

    def _initOpenings(self) -> None:
        """Initialize the main opening and variation from the PGN."""
        
        pgn: list[str] = self._sanitize_pgn()
        gameplay = []
        turn = ChessColor.WHITE
        board = chess.Board()
        for moveNum, move in enumerate(pgn):
            gameplay.append(_addMoveOrder(moveNum, move))
            board.push_san(move)
            if self._updateOpeningAndVariation(' '.join(gameplay)) and turn == self._userColor:
                self._increaseMoveLeavingOpening()

            turn = _changeTurn(turn)

    def analyzeGame(self) -> bool:
        """
        Analyze the game and calculate move errors.

        Returns:
            bool: True if the game was successfully analyzed, False otherwise.
        """

        if self._isAnalyzed:
            return False

        pgn: list[str] = self._sanitize_pgn()
        turn = ChessColor.WHITE
        beforeTurnEval: int = self._calculateEval()
        for moveNum, move in enumerate(pgn):

            self._board.push_san(move)
            afterTurnEval: int = self._calculateEval()

            if turn == self._userColor:
                self._calculateMoveError(beforeTurnEval, afterTurnEval)
            beforeTurnEval = afterTurnEval

            turn = _changeTurn(turn)
        self._isAnalyzed = True
        return True

    def _sanitize_pgn(self) -> list[str]:
        """
        Sanitize the PGN string and extract the moves.

        Returns:
            list[str]: The list of moves.
        """
        
        pgn = self._pgn.strip().split(' ')
        if self._pgnWithClockFormat:
            pgn = self._extractTimeManagement(pgn)  # Cutting out the time control
        return pgn

    def _extractTimeManagement(self, pgn: list[str]) -> list[str]:
        """
        Extract time management information from the PGN.

        Args:
            pgn (list[str]): The list of moves with time information.

        Returns:
            list[str]: The list of moves without time information.
        """
        
        prev_time, starting_ind = self._initTimeControl(pgn)
        bonusTime = self._bonusTime * Constants.NORMALIZED_SECONDS
        prev_time += bonusTime
        for i in range(starting_ind, len(pgn), Constants.NEXT_MOVE_JUMP):
            cur_time = _parseTime(pgn[i])
            normalized_seconds = round((prev_time - cur_time) / Constants.NORMALIZED_SECONDS,
                                       Constants.ROUNDING_ERROR)
            self._timeSpentPerMove.append(normalized_seconds)
            prev_time = cur_time + bonusTime

        return [pgn[idx] for idx in range(len(pgn)) if idx % 2 == 0]

    def _initTimeControl(self, pgn: list[str]) -> Tuple[int, int]:
        """
        Initialize the time control values.

        Args:
            pgn (str): The PGN string.

        Returns:
            Tuple[int, int]: The previous time and the starting index.
        """
        
        if self._userColor == ChessColor.WHITE:
            prev_time = self._timeControl * Constants.NORMALIZED_SECONDS
            starting_ind = Constants.WHITE_FIRST_MOVE_IND
        else:
            prev_time = _parseTime(pgn[1])
            starting_ind = Constants.BLACK_FIRST_MOVE_IND
        return prev_time, starting_ind

    def _validate_pgn(self) -> None:
        """Validate the PGN string to ensure it meets the minimum move requirements."""
        
        pgn = self._pgn.split(' ')
        if self._isThereClk() and len(pgn) < Constants.MINIMUM_NUMBER_OF_MOVES_WITH_CLOCK_FORMAT:
            raise ValueError(Constants.MINIMUM_MOVES_ERR)
        if not self._isThereClk() and len(pgn) < Constants.MINIMUM_NUMBER_OF_MOVES_WITHOUT_CLOCK_FORMAT:
            raise ValueError(Constants.MINIMUM_MOVES_ERR)

    def _calculateEval(self) -> int:
        """
        Calculate the evaluation of the current board position using Stockfish.

        Returns:
            int: The evaluation value.
        """
        
        StockEval = self._stockfish.get_evaluation()
        mateDetector = StockEval['type']
        value = StockEval['value']

        if mateDetector == Constants.STOCKFISH_MATE_ANNOUNCEMENT:
            if value > 0:
                return Constants.WHITE_FORCED_MATE_EVAL - (value - 1) * Constants.LONG_MATE_PUNISHMENT
            return Constants.BLACK_FORCED_MATE_EVAL + (value + 1) * Constants.LONG_MATE_PUNISHMENT
        else:
            return value

    def _calculateMoveError(self, beforeTurnEval: int, afterTurnEval: int) -> None:
        """
        Calculate the error for a move based on the change in evaluation.

        Args:
            beforeTurnEval (int): The evaluation before the move.
            afterTurnEval (int): The evaluation after the move.
        """
        
        self._errorPerMove.append(abs(beforeTurnEval - afterTurnEval) / Constants.NORMALIZED_ERROR)

    def _updateOpeningAndVariation(self, gameplay: str) -> bool:
        """
        Update the main opening and variation based on the gameplay.

        Args:
            gameplay (str): The gameplay string.

        Returns:
            bool: True if the opening or variation was updated, False otherwise.
        """
        
        if gameplay not in self._openingBook:
            return False

        opening_info = self._openingBook[gameplay]
        parts = opening_info.split(Constants.OPENING_SEPERATOR, 1)
        self._mainOpening = parts[0].strip()
        if len(parts) > 1:
            self._openingVariation = parts[1].strip()
        return True

    def _increaseMoveLeavingOpening(self) -> None:
        """Increase the move count when leaving the opening."""

        self._moveLeavingOpening += 1

    def isAnalyzed(self) -> bool:
        """
        Check if the game has been analyzed.

        Returns:
            bool: True if the game has been analyzed, False otherwise.
        """
        
        return self._isAnalyzed

    def getElo(self) -> int:
        """
        Get the ELO rating of the user.

        Returns:
            int: The ELO rating of the user.
        """
        
        if self._userColor == ChessColor.WHITE:
            return self._whiteElo
        return self._blackElo

    def getOpponentElo(self) -> int:
        """
        Get the ELO rating of the opponent.

        Returns:
            int: The ELO rating of the opponent.
        """
        
        if self._userColor == ChessColor.WHITE:
            return self._blackElo
        return self._whiteElo

    def getGameResult(self) -> ChessResult:
        """
        Get the result of the game.

        Returns:
            ChessResult: The result of the game.
        """
        
        return self._gameResult

    def getStrGameResult(self) -> str:
        """
        Get the result of the game as a string.

        Returns:
            str: The result of the game as a string ("win", "loss", "draw").
        """
        
        if self._gameResult == ChessResult.WIN:
            return "win"
        elif self._gameResult == ChessResult.LOSS:
            return "loss"
        else:
            return "draw"

    @validateAnalysis
    def getMainOpening(self) -> str:
        """
        Get the main opening of the game.

        Returns:
            str: The main opening of the game.
        """
        
        return self._mainOpening

    @validateAnalysis
    def getVariation(self) -> str:
        """
        Get the variation of the game.

        Returns:
            str: The variation of the game.
        """
        
        return self._openingVariation

    @validateAnalysis
    def getMoveLeavingOpening(self) -> int:
        """
        Get the move number when leaving the opening.

        Returns:
            int: The move number when leaving the opening.
        """
        
        return self._moveLeavingOpening

    def getTimeControl(self) -> int:
        """
        Get the main time control of the game.

        Returns:
            int: The main time control in seconds.
        """
        
        return self._timeControl

    def getTimeBonus(self) -> int:
        """
        Get the bonus time of the game.

        Returns:
            int: The bonus time in seconds.
        """
        
        return self._bonusTime

    def getTotalTimeControl(self) -> str:
        """
        Get the total time control as a string.

        Returns:
            str: The total time control in the format "main+bonus".
        """
        
        return str(self._timeControl) + Constants.TIME_CONTROL_SEPERATOR + str(self._bonusTime)

    @validateAnalysis
    def getTimeSpent(self) -> list[float]:
        """
        Get the time spent per move.

        Returns:
            list[float]: The list of time spent per move.
        """
        
        return self._timeSpentPerMove

    @validateAnalysis
    def getErrorPerMove(self) -> list[float]:
        """
        Get the error per move.

        Returns:
            list[float]: The list of error per move.
        """
        
        return self._errorPerMove

    def getOpeningBook(self) -> dict[str, str]:
        """
        Get the opening book.

        Returns:
            dict[str, str]: The opening book dictionary.
        """
        
        return self._openingBook

    @validateAnalysis
    def getGameError(self) -> float:
        """
        Get the average error of the game.

        Returns:
            float: The average error of the game.
        """
        
        return sum(self._errorPerMove) / len(self._errorPerMove)

    def getOpponent(self) -> str:
        """
        Get the opponent's name.

        Returns:
            str: The opponent's name.
        """
        
        return self._opponent

    def getDate(self) -> datetime:
        """
        Get the date of the game.

        Returns:
            datetime: The date of the game.
        """
        
        return self._date

    @validateAnalysis
    def getName(self) -> str:
        """
        Get the name of the game.

        Returns:
            str: The name of the game, including the main opening and variation.
        """
        
        if self._openingVariation is not None:
            return self._mainOpening + Constants.OPENING_SEPERATOR + " " + self._openingVariation
        return self._mainOpening
