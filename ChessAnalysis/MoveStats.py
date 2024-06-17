from . import Constants
from .SingleGame import SingleGame
from copy import deepcopy
from typing import Literal, Union


class MoveStatistics:
    """
    A class to keep track of and manage move statistics for chess games.
    """
    def __init__(self) -> None:
        self._total_error: list[Union[int, float]] = []
        self._total_time: list[Union[int, float]] = []
        self._total_moves: list[Union[int, float]] = []
        self._avg_error: list[float] = []
        self._avg_time: list[float] = []

    def __copy__(self):
        return self.__deepcopy__({})

    def __deepcopy__(self, memo):
        """
        Create a deep copy of the instance.

        Args:
            memo (dict): Memoization dictionary to avoid infinite recursion in deep copy.

        Returns:
            MoveStatistics: A deep copy of the current instance.
        """

        new_instance = MoveStatistics()
        new_instance._total_error = deepcopy(self._total_error, memo)
        new_instance._total_time = deepcopy(self._total_time, memo)
        new_instance._total_moves = deepcopy(self._total_moves, memo)
        new_instance._avg_error = deepcopy(self._avg_error, memo)
        new_instance._avg_time = deepcopy(self._avg_time, memo)

        return new_instance

    def update(self, game: SingleGame, updateState: Literal[-1, 1] = Constants.APPEND)\
            -> None:
        """
        Update move statistics with data from a single game.

        Args:
            game (SingleGame): The game from which to extract move data.
            updateState (Literal[-1, 1]): The state to indicate whether to add (1) or remove (-1) data.
        """
        timeSpentPerMove, errorPerMove = game.getTimeSpent(), game.getErrorPerMove()
        moveNumbering = range(len(timeSpentPerMove))
        for idx, time, error in zip(moveNumbering, timeSpentPerMove, errorPerMove):
            time, idx = updateState * time, updateState * idx
            self._updateOneMove(idx, time, error, updateState)

    def _updateOneMove(self, moveNum, time, error, updateState: Literal[-1, 1]):
        """
        Update the statistics for a single move.

        Args:
            moveNum (int): The move number.
            time (float): The time spent on the move.
            error (float): The error for the move.
            updateState (Literal[-1, 1]): The state to indicate whether to add (1) or remove (-1) data.
        """
        if moveNum < 0:
            raise ValueError(Constants.INVALID_MOVE_NUMBER)

        if self._isThisMoveNumberEverPlayed(moveNum):
            self._updateTotalFields(moveNum, error, time, updateState)
            self._updateAvgFields(moveNum)
        else:
            self._initTotalFields(error, time)
            self._initAvgFields(error, time)

    def _isThisMoveNumberEverPlayed(self, moveNum):
        """
        Check if a move number has been played before.

        Args:
            moveNum (int): The move number to check.

        Returns:
            bool: True if the move number has been played before, False otherwise.
        """
        return len(self._avg_error) > moveNum

    def _initAvgFields(self, error, time):
        """
         Initialize the average fields for a move.

         Args:
             error (float): The error for the move.
             time (float): The time spent on the move.
         """
        self._avg_error.append(error)
        self._avg_time.append(time)

    def _initTotalFields(self, error, time):
        """
        Initialize the total fields for a move.

        Args:
            error (float): The error for the move.
            time (float): The time spent on the move.
        """
        self._total_error.append(error)
        self._total_time.append(time)
        self._total_moves.append(1)

    def _updateAvgFields(self, moveNum):
        """
        Update the average fields for a move number.

        Args:
            moveNum (int): The move number to update.
        """
        self._avg_error[moveNum] = self._total_error[moveNum] / self._total_moves[moveNum]
        self._avg_time[moveNum] = self._total_time[moveNum] / self._total_moves[moveNum]

    def _updateTotalFields(self, moveNum: int, error, time, updateState: Literal[1, -1]) -> None:
        """
        Update the total fields for a move number.

        Args:
            moveNum (int): The move number to update.
            error (float): The error for the move.
            time (float): The time spent on the move.
            updateState (Literal[1, -1]): The state to indicate whether to add (1) or remove (-1) data.
        """
        self._total_error[moveNum] += error
        self._total_time[moveNum] += time
        self._total_moves[moveNum] += updateState

    def clear(self) -> None:
        """
         Clear all the move statistics.
         """
        self._total_error.clear()
        self._total_time.clear()
        self._total_moves.clear()
        self._avg_error.clear()
        self._avg_time.clear()

    def get_avg_error(self) -> list[float]:
        """
        Get the average error for each move.

        Returns:
            list[float]: A list of average errors rounded to the specified precision.
        """
        return [round(error, Constants.ROUNDING_ERROR) for error in self._avg_error]

    def get_avg_time(self) -> list[float]:
        """
        Get the average time for each move.

        Returns:
            list[float]: A list of average times rounded to the specified precision.
        """
        return [round(avgTime, Constants.ROUNDING_TIME) for avgTime in self._avg_time]

    def get_total_moves(self) -> list[int]:
        """
        Get the total number of moves for each move number.

        Returns:
            list[int]: A list of total moves.
        """
        return self._total_moves
