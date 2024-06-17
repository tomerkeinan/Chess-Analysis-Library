from . import Constants
from .MoveStats import MoveStatistics
from .SingleGame import SingleGame
from .Enums import ChessResult
from typing import Callable, Any
from math import ceil
from copy import deepcopy


def increment_totalGames(method: Callable) -> Callable:
    """
    Decorator to increment the total games counter.

    Args:
        method (Callable): The method to be wrapped.

    Returns:
        Callable: The wrapped method.
    """
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        self._increaseTotalGames()
        return method(self, *args, **kwargs)
    return wrapper


class OpeningData:
    def __init__(self, openingName: str = Constants.DEFAULT_OPENING_DATA_NAME,
                 isVariation=Constants.DEFAULT_IS_VARIATION) -> None:
        """
        Initialize the OpeningData class.

        Args:
            openingName (str): The name of the opening.
            isVariation (bool): Flag indicating if the opening is a variation.
        """
        self._openingName = openingName
        self._variations: dict[str, OpeningData] = {}
        self._moveStats = MoveStatistics()
        self._totalGames = 0
        self._gameHistory: list[SingleGame] = []
        self._isVariation = isVariation

    def __copy__(self):
        return self.__deepcopy__({})

    def __deepcopy__(self, memo):
        new_instance = OpeningData(self._openingName, self._isVariation)
        new_instance._moveStats = deepcopy(self._moveStats, memo)
        new_instance._gameHistory = deepcopy(self._gameHistory, memo)
        new_instance._variations = {key: deepcopy(v, memo) for key, v in self._variations.items()}
        new_instance._totalGames = self._totalGames
        return new_instance

    def __iter__(self):
        """Return an iterator over the game history."""

        return iter(self._gameHistory)

    def __len__(self):
        """Return the number of games in the game history."""
        return len(self._gameHistory)

    @increment_totalGames
    def addGame(self, game: SingleGame) -> None:
        """
        Add a game to the opening data.

        Args:
            game (SingleGame): The game to be added.
        """
        self._gameHistory.append(game)
        self._moveStats.update(game)

    @increment_totalGames
    def addVariation(self, game: SingleGame, variation: str) -> None:
        """
        Add a variation to the opening data.

        Args:
            game (SingleGame): The game to be added.
            variation (str): The name of the variation.
        """
        if self._isVariation:
            raise ValueError(Constants.ADD_VARIATION_TO_VARIATION_ERR)
        if variation not in self._variations:
            self._variations[variation] = OpeningData(self._openingName + Constants.OPENING_SEPERATOR + variation,
                                                      True)
        self._variations[variation].addGame(game)

    def removeGame(self, game: SingleGame) -> None:
        """
        Remove a game from the opening data.

        Args:
            game (SingleGame): The game to be removed.

        Raises:
            ValueError: If the game is not found in the game history.
        """
        if game not in self._gameHistory:
            raise ValueError(Constants.GAME_NOT_FOUND_ERR)
        self._gameHistory.remove(game)
        self._moveStats.update(game, updateState=Constants.REMOVE)
        self._decreaseTotalGames()

        if game.getVariation() is not None and not self._isVariation:
            self._variations[game.getVariation()].removeGame(game)

    def getName(self) -> str:
        """
        Get the name of the opening.

        Returns:
            str: The name of the opening.
        """
        return self._openingName

    def getTimeSpent(self) -> list[float]:
        """
        Get the average time spent per move.

        Returns:
            list[float]: The average time spent per move.
        """
        return self._moveStats.get_avg_time()

    def getErrorPerMove(self) -> list[float]:
        """
        Get the average error per move.

        Returns:
            list[float]: The average error per move.
        """
        return self._moveStats.get_avg_error()

    def getOpeningAvgError(self) -> float:
        """
        Get the average error for the opening.

        Returns:
            float: The average error for the opening.
        """
        total_error = 0
        for game in self._gameHistory:
            total_error += game.getGameError()
        return total_error/len(self._gameHistory)

    def getTotalMoves(self) -> list[int]:
        """
        Get the total moves made in the opening.

        Returns:
            list[int]: The total moves made in the opening.
        """
        return self._moveStats.get_total_moves()

    def getRecord(self) -> dict[str, int]:
        """
        Get the record of wins, losses, and draws for the opening.

        Returns:
            dict[str, int]: The record of wins, losses, and draws.
        """
        loss, draws, wins = 0, 0, 0
        for game in self._gameHistory:
            if game.getGameResult() == ChessResult.WIN:
                wins += 1
            elif game.getGameResult() == ChessResult.LOSS:
                loss += 1
            else:
                draws += 1
        return {Constants.WIN_KEY: wins, Constants.LOSS_KEY: loss, Constants.DRAW_KEY: draws}

    def getAvgMoveLeavingOpening(self) -> int:
        """
        Get the average move number when leaving the opening.

        Returns:
            int: The average move number when leaving the opening.
        """
        totalMoveLeavingOpening = 0
        for game in self._gameHistory:
            totalMoveLeavingOpening += game.getMoveLeavingOpening()
        return ceil(totalMoveLeavingOpening / len(self._gameHistory))

    def _increaseTotalGames(self) -> None:
        self._totalGames += 1

    def _decreaseTotalGames(self) -> None:
        self._totalGames -= 1

    def getTotalGames(self) -> int:
        """
        Get the total number of games.

        Returns:
            int: The total number of games.
        """
        return self._totalGames

    def getVariation(self, variation: str = None):
        """
        Get the variation data.

        Args:
            variation (str, optional): The name of the variation. Defaults to None.

        Returns:
            Union[list[OpeningData], OpeningData, None]: The variation data.
        """
        if variation is None:
            return list(self._variations.values())
        if variation not in self._variations:
            return None
        return self._variations[variation]

    def getGames(self) -> list[SingleGame]:
        """
        Get the game history.

        Returns:
            list[SingleGame]: The game history.
        """
        return self._gameHistory

    def getTotalTimesPlayedMove(self) -> list[int]:
        """
        Get the total number of times each move was played.

        Returns:
            list[int]: The total number of times each move was played.
        """
        return self._moveStats.get_total_moves()
