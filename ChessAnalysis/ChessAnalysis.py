from collections import defaultdict
import os
import re
from .SingleGame import SingleGame, parseDate, extractTimeControl
from .Enums import ChessColor, ChessResult
from .MoveStats import MoveStatistics
from .OpeningData import OpeningData
from .PlotFactory import PlotFactory
from . import Constants
from functools import wraps
from typing import Callable, Tuple, Any, Union
import inspect
import csv
from stockfish import Stockfish


def _extractMetaData(content: str, extractionPara: str) -> str:
    extractionPara += ' "'
    start_index = content.find(extractionPara) + len(extractionPara)
    end_index = content.find('"', start_index)
    return content[start_index:end_index]


def _preProcessPGN(game_pgn: str, result: str) -> str:
    # removing the final result from the end of the pgn
    end_index = game_pgn.find(result)
    game_pgn = game_pgn[:end_index]

    # removing the move number of both black and white
    game_pgn = _removeMoveNumbering(game_pgn)

    # All the game data in one line, so data will not get cut at the middle of line
    game_pgn = re.sub(Constants.ONE_LINE_PATTERN, ' ', game_pgn)

    # Converting the format of MOVE {[%clk TIME]} to MOVE TIME format(incase there is clk format in the pgn)
    game_pgn = _removeClockPattern(game_pgn)

    return game_pgn


def _removeMoveNumbering(game_pgn: str) -> str:
    game_pgn = re.sub(Constants.BLACK_MOVE_NUMBER_PATTERN, '', game_pgn)
    game_pgn = re.sub(Constants.WHITE_MOVE_NUMBER_PATTERN_NO_END_LINE, '', game_pgn)
    game_pgn = re.sub(Constants.WHITE_MOVE_NUMBER_PATTERN_END_OF_LINE, '\n', game_pgn)
    return game_pgn


def _removeClockPattern(game_pgn: str) -> str:
    game_pgn = re.sub(Constants.CLK_PATTERN_1, Constants.CLK_PATTERN_GROUP, game_pgn)
    game_pgn = re.sub(Constants.CLK_PATTERN_2, Constants.CLK_PATTERN_GROUP, game_pgn)
    game_pgn = re.sub(Constants.CLK_PATTERN_3, Constants.CLK_PATTERN_GROUP, game_pgn)
    game_pgn = re.sub(Constants.CLK_PATTERN_4, Constants.CLK_PATTERN_GROUP, game_pgn)
    return game_pgn


def _sortTop(openings: list[OpeningData], reverse: bool, attribute_func: Callable[[OpeningData], Any],
             sorting_key: Callable[[Tuple[str, Any]], Any]) -> list[Tuple[str, Any]]:
    """
    Sorts the given list of openings based on a specific attribute and sorting key.

    Args:
        openings (list[OpeningData]): List of OpeningData instances to sort.
        reverse (bool): Whether to sort in reverse order.
        attribute_func (Callable[[OpeningData], Any]): Function to extract the attribute to sort by from each opening.
        sorting_key (Callable[[Tuple[str, Any]], Any]): Function to extract the sorting key from the attribute.

    Returns:
        list[Tuple[str, Any]]: Sorted list of tuples, each containing the opening name and the attribute value.
    """
    topPicks = []
    for opening in openings:  # openings types list[OpeningData]
        topPicks.append((opening.getName(), attribute_func(opening)))

    topPicks.sort(key=sorting_key, reverse=reverse)
    return topPicks


def _checkMoveOverBound(openings: list[OpeningData], bound: int):
    """
    Finds the index of the first move that has been played less than the specified bound across all openings.

    Args:
        openings (list[OpeningData]): List of OpeningData instances to check.
        bound (int): The minimum number of times a move must be played to be considered.

    Returns:
        int: The index of the first move that has been played less than the bound, or the longest move played if all
         moves meet the bound.
    """
    longestMovePlayed = max((len(opening.getTotalTimesPlayedMove()) for opening in openings), default=0)

    totalTimesPlayedMove: list[int] = _initTotalTimesPlayed(longestMovePlayed, openings)

    for i, num in enumerate(totalTimesPlayedMove):
        if num < bound:
            return i
    return longestMovePlayed


def _initTotalTimesPlayed(longestMovePlayed: int, openings: list[OpeningData]) -> list[int]:
    """
    Initializes a list of total times each move has been played across all openings.

    Args:
        longestMovePlayed (int): The length of the longest move sequence played.
        openings (list[OpeningData]): List of OpeningData instances to aggregate move counts from.

    Returns:
        list[int]: List where each index represents the total times the corresponding move has been played.
    """
    totalTimesPlayedMove: list[int] = [0] * longestMovePlayed
    for opening in openings:
        for idx, totalTimesPlayedMoveInOpening in enumerate(opening.getTotalTimesPlayedMove()):
            totalTimesPlayedMove[idx] += totalTimesPlayedMoveInOpening

    return totalTimesPlayedMove


def _calculateAvgPerMove(openings: list[OpeningData], attributeFunc: Callable[[OpeningData], list[float]], bound: int) \
        -> list[Tuple[str, float]]:
    """
    Calculates the average value of a specified attribute for each move up to the bound across all openings.

    Args:
        openings (list[OpeningData]): List of OpeningData instances to process.
        attributeFunc (Callable[[OpeningData], list[float]]): Func to extract the attribute values from each opening.
        bound (int): Minimum number of times a move must be played to be included in the calculation.

    Returns:
        list[Tuple[str, float]]: List of tuples where each tuple contains the move index (as a string) and the average
         value of the attribute for that move.
    """
    longestMoveOverBound: int = _checkMoveOverBound(openings, bound)
    summed, counter = [0] * longestMoveOverBound, [0] * longestMoveOverBound

    for opening in openings:
        for i, val in enumerate(attributeFunc(opening)):
            summed[i] += val
            counter[i] += 1

    avg_per_move = [(str(i), summed[i] / counter[i]) for i in range(longestMoveOverBound) if counter[i] != 0]
    return avg_per_move


def _initResult(top_records: list[Tuple[str, Any]]):
    """
    Initializes a result dictionary from a list of top records.

    Args:
        top_records (list[Tuple[str, Any]]): List of tuples where each tuple contains an opening name and a value.
            The value can be a dictionary, list, float, or int.

    Returns:
        dict: A dictionary where the keys are opening names and the values are either:
            - Tuples containing win, draw, and loss counts if the value was a dictionary.
            - The value itself if it was a float or int.
            - A tuple of values if the value was a list or other iterable.
    """
    result = {}
    for opening, value in top_records:
        if isinstance(value, dict):
            result[opening] = (
                value.get(Constants.WIN_KEY),
                value.get(Constants.DRAW_KEY),
                value.get(Constants.LOSS_KEY))

        elif isinstance(value, list):
            validateListType(opening, result, value)

        elif isinstance(value, (float, int)):
            result[opening] = value
        else:
            result[opening] = tuple(value, )
    return result


def validateListType(opening, result, value):
    if (len(value)) == 1 and isinstance(value[0], (float, int)):
        result[opening] = value[0]
    elif len(value) > 1 and all(isinstance(val, (float, int)) for val in value):
        result[opening] = tuple(val for val in value)
    elif all(isinstance(val, SingleGame) for val in value):
        result[opening] = tuple(val for val in value)


def _extractData(data) -> Tuple[str, int, str, str, str, int, str]:
    date = _extractMetaData(data, Constants.DATE_METADATA)
    white = _extractMetaData(data, Constants.WHITE_METADATA)
    whiteElo = int(_extractMetaData(data, Constants.WHITE_ELO_METADATA))
    black = _extractMetaData(data, Constants.BLACK_METADATA)
    blackElo = int(_extractMetaData(data, Constants.BLACK_ELO_METADATA))
    result = _extractMetaData(data, Constants.RESULT_METADATA)
    time_control = _extractMetaData(data, Constants.TIME_CONTROL_METADATA)
    return black, blackElo, result, time_control, white, whiteElo, date


def _validateBound(argValue: int, minBound: int, errMsg: str) -> None:
    if not argValue or argValue < minBound:
        raise ValueError(errMsg)


def adjustAndValidateParams(method):
    """
    Decorator that adjusts and validates parameters for the given method.

    It binds the method's signature to the provided arguments, applies default values,
    validates and updates the arguments, and then calls the method with the updated arguments.

    Args:
        method (Callable): The method to be wrapped and validated.

    Returns:
        Callable: The wrapped method with validated and updated parameters.
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        bound_param = self._initBoundParam(method, args, kwargs)
        self._clear()
        self._validateThenUpdateArgs(bound_param)

        self._validateClass()

        kwargs.update(bound_param)
        return method(self, **kwargs)

    return wrapper


def _isAtrophiedGame(game_pgn: str, gameNum: int) -> bool:
    """
     Checks if a game is atrophied based on its PGN.

     A game is considered atrophied if it contains a specific flag indicating that both
     players have played only once.

     Args:
         game_pgn (str): The PGN string of the game.
         gameNum (int): The game number for reference.

     Returns:
         bool: True if the game is atrophied, False otherwise.
     """
    if game_pgn.partition(Constants.WHITE_AND_BLACK_PLAYED_ONCE_FLAG)[1] != "":
        return False
    print(Constants.ATROPHIED_GAME_MSG.format(str(gameNum)))
    return True


def _removeGamesUnderBound(bound: int, openings: list[OpeningData]) -> None:
    openings[:] = [opening for opening in openings if opening.getTotalGames() >= bound]


def _validateOpponent(opponent: Union[str, Tuple[str]]):
    """
    Validates the opponent parameter to ensure it is either a string or a tuple of strings.

    If the opponent is None, the function returns without any checks.
    If the opponent is not a string or a tuple of strings, a ValueError is raised.

    Args:
        opponent (Union[str, Tuple[str]]): The opponent(s) to be validated.

    Raises:
        ValueError: If the opponent is of an invalid type or contains invalid values.
    """
    if opponent is None:
        return
    if not isinstance(opponent, str):
        if not isinstance(opponent, tuple):
            raise ValueError(Constants.INVALID_OPPONENT_TYPE)
        for item in opponent:
            if not isinstance(item, str):
                raise ValueError(Constants.INVALID_OPPONENT_TYPE)


def _validateSetGap(setGap: int) -> None:
    if not setGap or setGap < Constants.MIN_VAL_FOR_SET_GAP:
        raise ValueError(Constants.VALUE_VALIDITY_ERR_SET_GAP)


def _validateResult(result):
    """
    Validates the result parameter to ensure it is of the correct type and value.

    The result can be a float, an int, or a tuple of floats/ints. If the result is invalid,
    a ValueError is raised.

    Args:
        result (Union[float, int, Tuple[float, int]]): The result to be validated.

    Raises:
        ValueError: If the result is of an invalid type or contains invalid values.
    """
    if result is None:
        return
    if isinstance(result, (float, int)):
        if result not in result:
            raise ValueError(Constants.INVALID_RESULT_ERR)
    elif isinstance(result, tuple) and all(isinstance(r, (float, int)) for r in result):
        if any(r not in result for r in result):
            raise ValueError(Constants.INVALID_RESULT_ERR)
    else:
        raise ValueError(Constants.INVALID_RESULT_TYPE)


def _findKeyInterval(result: dict, opponentElo: int) -> tuple[int, int]:
    for key in result.keys():
        if key[0] <= opponentElo <= key[1]:
            return key


def _averagePoints(record: dict[str, int]) -> float:
    total_games = record[Constants.WIN_KEY] + record[Constants.DRAW_KEY] + record[Constants.LOSS_KEY]
    points = record[Constants.WIN_KEY] + Constants.DRAW_POINTS * record[Constants.DRAW_KEY]
    return points / total_games if total_games > 0 else 0


def _updateResult(result: dict, game: SingleGame) -> None:
    key = _findKeyInterval(result, game.getOpponentElo())
    if game.getGameResult() == ChessResult.WIN:
        subKey = Constants.WIN_KEY
    elif game.getGameResult() == ChessResult.LOSS:
        subKey = Constants.LOSS_KEY
    else:
        subKey = Constants.DRAW_KEY

    result[key][subKey] += 1


def _initEloDict(openings: list[OpeningData], setGap: int) -> dict[tuple[int, int], dict[str, int]]:
    """
    Initializes a dictionary to store the game results grouped by Elo rating ranges.

    This function calculates the lowest and highest Elo ratings from the given openings.
    It then creates ranges of Elo ratings with a specified gap and initializes a dictionary
    with these ranges as keys and dictionaries to store win, draw, and loss counts as values.

    Args:
        openings (list[OpeningData]): A list of OpeningData objects containing game information.
        setGap (int): The range gap for grouping Elo ratings.

    Returns:
        dict[tuple[int, int], dict[str, int]]: A dictionary where keys are tuples representing
        Elo rating ranges and values are dictionaries with keys for win, draw, and loss counts.
    """
    lowestEloPlayed = min(game.getOpponentElo() for opening in openings for game in opening.getGames())
    maxEloPlayed = max(game.getOpponentElo() for opening in openings for game in opening.getGames())
    left, right = lowestEloPlayed, lowestEloPlayed + setGap

    result = {}
    while right < maxEloPlayed:
        result[(left, right)] = {Constants.WIN_KEY: Constants.DEFAULT_WIN_VAL,
                                 Constants.DRAW_KEY: Constants.DEFAULT_DRAW_VAL,
                                 Constants.LOSS_KEY: Constants.DEFAULT_LOSS_VAL}

        left, right = right, right + setGap

    result[(left, right)] = {Constants.WIN_KEY: Constants.DEFAULT_WIN_VAL,
                             Constants.DRAW_KEY: Constants.DEFAULT_DRAW_VAL,
                             Constants.LOSS_KEY: Constants.DEFAULT_LOSS_VAL}  # handles final iteration

    return result


def _initGamesAgainstPlayer(gamesBound: int, openings: list[OpeningData]) -> list[Tuple[str, list[SingleGame]]]:
    games = defaultdict(list)
    for opening in openings:
        for game in opening.getGames():
            games[game.getOpponent()].append(game)
    games = {opponentName: gamesAgainstOpponent for opponentName, gamesAgainstOpponent in games.items()
             if len(gamesAgainstOpponent) >= gamesBound}
    return [(key, val) for key, val in games.items()]


def _initGamesFilteredTimeControl(gamesBound: int, openings: list[OpeningData]) -> list[Tuple[str, list[SingleGame]]]:
    games = defaultdict(list)
    for opening in openings:
        for game in opening.getGames():
            games[game.getTotalTimeControl()].append(game)
    games = {timeControl: gamesAtTimeControl for timeControl, gamesAtTimeControl in games.items()
             if len(gamesAtTimeControl) >= gamesBound}

    return [(key, val) for key, val in games.items()]


def _slicedTopRecords(topRecord: list[Tuple[Any, dict[str, int]]], takeTop: int) -> list[Tuple[Any, dict[str, int]]]:
    """
    Slices the top records based on average points until the takeTop limit is reached.

    Args:
        topRecord (list[Tuple[Any, dict[str, int]]]): A list of tuples containing records.
        takeTop (int): The number of top records to take.

    Returns:
        list[Tuple[Any, dict[str, int]]]: The sliced top records.
    """
    slicedItems = []
    takeTopCounter = 0
    topItemVal = _averagePoints(topRecord[0][1])
    for tup in topRecord:
        candidate = _averagePoints(tup[1])
        parts = _updateSlicedItems(candidate, topItemVal, takeTopCounter, takeTop, slicedItems, tup)
        topItemVal, takeTopCounter = parts[0], parts[1]
    return slicedItems


def _slicedTopItems(topItem: list[Tuple[str, float]], takeTop: int) -> list[Tuple[str, float]]:
    """
    Slices the top items based on their values until the takeTop limit is reached.

    Args:
        topItem (list[Tuple[str, float]]): A list of tuples containing items.
        takeTop (int): The number of top items to take.

    Returns:
        list[Tuple[str, float]]: The sliced top items.
    """
    slicedItems = []
    takeTopCounter = 0
    topItemVal = topItem[0][1]
    for tup in topItem:
        candidate = tup[1]
        parts = _updateSlicedItems(candidate, topItemVal, takeTopCounter, takeTop, slicedItems, tup)
        topItemVal, takeTopCounter = parts[0], parts[1]
    return slicedItems


def _updateSlicedItems(candidate, topItemVal, takeTopCounter: int, takeTop: int,
                       slicedItems: list[Tuple[Any, dict[str, int]]], tup):
    """
    Updates the sliced items list based on the candidate value and the top item value.

    Args:
        candidate: The candidate value to compare.
        topItemVal: The current top item value.
        takeTopCounter (int): The counter for the number of items taken.
        takeTop (int): The number of top items to take.
        slicedItems (list[Tuple[Any, dict[str, int]]]): The list of sliced items.
        tup: The current tuple being processed.

    Returns:
        tuple: Updated top item value and take top counter.
    """
    if candidate < topItemVal and takeTopCounter >= takeTop:
        return topItemVal, takeTopCounter
    elif candidate < topItemVal and takeTopCounter < takeTop:
        slicedItems.append((tup[0], tup[1]))
        takeTopCounter += 1
        topItemVal = candidate
    else:
        slicedItems.append((tup[0], tup[1]))
    return topItemVal, takeTopCounter


def _updateTopGamesList(candidate, topItemVal, takeTopCounter, takeTop, topGamesAgainstSpecificOpponent, game):
    """
    Updates the top games list based on the candidate value and the top item value.

    Args:
        candidate: The candidate value to compare.
        topItemVal: The current top item value.
        takeTopCounter: The counter for the number of items taken.
        takeTop: The number of top items to take.
        topGamesAgainstSpecificOpponent: The list of top games against a specific opponent.
        game: The current game being processed.

    Returns:
        Updated top item value and take top counter.
    """
    if candidate < topItemVal and takeTopCounter >= takeTop:
        return topItemVal
    elif candidate < topItemVal and takeTopCounter < takeTop:
        topGamesAgainstSpecificOpponent.append(game)
        takeTopCounter += 1
        topItemVal = candidate
    else:
        topGamesAgainstSpecificOpponent.append(game)
    return topItemVal, takeTopCounter


def _slicedTopSingleGames(sortedGames: list[Tuple[str, list[SingleGame]]], takeTop: int):
    """
    Slices the top single games based on their errors until the takeTop limit is reached.

    Args:
        sortedGames (list[Tuple[str, list[SingleGame]]]): A list of tuples containing games.
        takeTop (int): The number of top games to take.

    Returns:
        The sliced top single games.
    """
    slicedItems = []
    gameCounter = 0
    topItemVal = sortedGames[0][1][0].getGameError()
    for tup in sortedGames:
        topGamesSpecificOpponent = []
        for game in tup[1]:
            candidate = game.getGameError()
            parts = _updateTopGamesList(candidate, topItemVal, gameCounter, takeTop, topGamesSpecificOpponent, game)
            topItemVal, gameCounter = parts[0], parts[1]

        slicedItems.append((tup[0], topGamesSpecificOpponent))
    return slicedItems


def _updateResultGames(games: dict[str, list[SingleGame]], opening: OpeningData, gamesBound: int, ) -> None:
    if opening.getTotalGames() >= gamesBound:
        for game in opening.getGames():
            games[ChessResult.chessResultToStr(game.getGameResult())].append(game)


def _updateDateGames(games: dict[str, list[SingleGame]], opening: OpeningData, gamesBound: int, eloBound: int) -> None:
    if opening.getTotalGames() >= gamesBound:
        for game in opening.getGames():
            if game.getOpponentElo() <= eloBound:
                games[game.getDate().date().__str__()].append(game)


def _validateReverse(argValue):
    assert isinstance(argValue, bool), Constants.INVALID_REVERSE_TYPE


def _validateTakeTop(argValue):
    assert isinstance(argValue, int), Constants.INVALID_TAKE_TOP
    assert argValue >= 0, Constants.INVALID_TAKE_TOP


def _validatePlotArg(argValue):
    assert isinstance(argValue, bool), Constants.INVALID_PLOT_TYPE


def _validateThenUpdateTakeTop(argValue, bound_param):
    _validateTakeTop(argValue)
    takeTop = Constants.MAX_TAKE_TOP if argValue == Constants.MIN_VAL_FOR_TAKE_TOP else argValue
    bound_param.update(takeTop=takeTop)


def _printAnalyzeProcess(i: int, numOfGamesToAnalyze: int) -> None:
    if numOfGamesToAnalyze > 0:
        print(Constants.PROCESS_ANALYZE_MSG.format(i + 1, numOfGamesToAnalyze))


def _totalGames(record: dict[str, int]) -> int:
    return record[Constants.WIN_KEY] + record[Constants.LOSS_KEY] + record[Constants.DRAW_KEY]


def _validateEloBound(argValue):
    assert isinstance(argValue, int), Constants.ELO_BOUND_ERR
    assert argValue >= Constants.MIN_ELO_BOUND, Constants.ELO_BOUND_ERR


def _calculateRecord(games: tuple[SingleGame, ...]) -> float:
    avgRecord: float = 0
    for game in games:
        avgRecord += game.getGameResult().value
    return avgRecord / len(games)


def _checkIfMostCommon(opening, result, topScore):
    if opening.getTotalGames() > topScore:
        topScore = opening.getTotalGames()
        result = [opening]
    elif opening.getTotalGames() == topScore:
        result.append(opening)
    return topScore, result


def _sanitizeResult(result):
    if len(result) == 0:
        return []
    elif len(result) == 1:
        return result[0]
    else:
        return tuple(result)


def _sliceAndPlot(games, plot, reverse, takeTop):
    for game in games:
        game[1].sort(key=lambda item: item.getGameError(), reverse=reverse)
    slicedTop = _slicedTopSingleGames(games, takeTop)
    result = _initResult(slicedTop)
    PlotFactory(result, plot, Constants.AGAINST_PLAYER_TITLE, Constants.AGAINST_PLAYER_X_LABEL,
                Constants.AGAINST_PLAYER_Y_LABEL)
    return result


class ChessAnalysis:
    def __init__(self, dataset, username, stockfish: Stockfish) -> None:
        """
        Initializes the ChessAnalysis class with the provided dataset, username, and Stockfish instance.

        Args:
            dataset: The path to the dataset (directory or file).
            username: The username of the player.
            stockfish (Stockfish): The Stockfish instance for chess analysis.

        Raises:
            FileNotFoundError: If the dataset is neither a directory nor a file.
        """
        self._allGames: set[SingleGame] = set()
        self._gamesToAnalyze: set[SingleGame] = set()
        self._stockfish = stockfish
        self._username = username
        self._dataset = dataset
        self._moveStats = MoveStatistics()
        self._openingsStats: dict[str, OpeningData] = {}

        if os.path.isdir(self._dataset):
            self._process_directory()
        elif os.path.isfile(self._dataset):
            self._process_file()
        else:
            raise FileNotFoundError

    def _clear(self) -> None:
        """
        Clears the internal data structures.
        """
        self._openingsStats.clear()
        self._gamesToAnalyze.clear()
        self._moveStats.clear()

    def _validateOpeningNames(self, openings: list[str]) -> None:
        """
        Validates the provided opening names.

        Args:
            openings (list[str]): The list of opening names to validate.

        Raises:
            ValueError: If the opening name is not found or similar names are suggested.
        """
        for opening in openings:
            parts = opening.partition(Constants.OPENING_SEPERATOR)
            opening, variation = parts[0], parts[2]
            if opening not in self._openingsStats:
                self._LookForSimilarOpenings(opening)
            if variation != '' and not self._openingsStats[opening].getVariation(variation):
                self._LookForSimilarOpenings(variation)

    def _validateClass(self) -> None:
        """
        Validates that there are openings to analyze.

        Raises:
            ValueError: If no openings are found for analysis.
        """
        if not self._openingsStats:
            raise ValueError(Constants.NO_GAMES_ANALYZE_ERR)

    def _LookForSimilarOpenings(self, opening):
        """
        Looks for similar opening names if the provided name is not found.

        Args:
            opening: The opening name to search for.

        Raises:
            ValueError: If no similar openings are found.
        """
        similar_openings = [o for o in self._openingsStats if opening in o]
        if similar_openings:
            similar_openings_str = ", ".join(similar_openings)
            raise ValueError(Constants.NO_OPENING_BUT_THERE_IS_SIMILAR_ERR.format(similar_openings_str))
        else:
            raise ValueError(Constants.NO_OPENING_ERR.format(opening))

    def _process_directory(self) -> None:
        """
        Processes all PGN files in the provided directory.
        """
        noPgnFound = True
        for file_name in os.listdir(self._dataset):
            if file_name.endswith(Constants.VALID_GAME_EXTENSION):
                noPgnFound = False
                file_path = os.path.join(self._dataset, file_name)
                with open(file_path, 'r') as f:
                    self._processPgnFile(f.read())
        if noPgnFound:
            raise ValueError(Constants.NO_PGN_FILES_ERR)

    def _process_file(self) -> None:
        """
        Processes the provided PGN file.
        """
        if not self._dataset.endswith(Constants.VALID_EXTENSION):
            raise ValueError(Constants.FILE_NOT_PGN_ERR)
        with open(self._dataset, 'r') as f:
            self._processPgnFile(f.read())

    def _processPgnFile(self, file: str) -> None:
        """
        Processes the content of a PGN file, extracting game data and metadata.

        Args:
            file (str): The content of the PGN file.
        """
        file_data = file.split(Constants.PGN_META_DATA_TO_GAME_SEPERATOR)
        # Even numbers := the metadata of the next odd number game. Odd := the actual game moves.
        for i in range(0, len(file_data), 2):
            metaData, game = file_data[i], file_data[i + 1]
            black, blackElo, result, time_control, white, whiteElo, date = _extractData(metaData)

            if white != self._username and black != self._username:
                raise ValueError(Constants.USERNAME_NOT_MATCH_ERR)

            if _isAtrophiedGame(game, int((i / 2) + 1)):
                continue

            pgn = _preProcessPGN(game, result)

            userColor = ChessColor.WHITE if self._username == white else ChessColor.BLACK
            opponent = black if self._username == white else white

            game = SingleGame(pgn, whiteElo, blackElo, result, time_control, userColor, self._stockfish, opponent, date)
            self._allGames.add(game)

    def _initOpening(self) -> list[OpeningData]:
        """
        Initializes the openings' data.

        Returns:
            list[OpeningData]: The list of initialized openings.
        """
        numOfGameToAnalyze = sum(1 for game in self._gamesToAnalyze if not game.isAnalyzed())
        for i, game in enumerate(self._gamesToAnalyze):
            _printAnalyzeProcess(i, numOfGameToAnalyze)

            game.analyzeGame()

            self._moveStats.update(game)
            opening, variation = game.getMainOpening(), game.getVariation()

            self._updateOpening(game, opening, variation)

        sanitizedOpenings: list[OpeningData] = [opening for opening in self._openingsStats.values()]
        return sanitizedOpenings

    def _updateOpening(self, game, opening, variation):
        self._updateMainOpening(opening, game)
        if variation is not None:
            self._updateVariation(opening, game.getName(), game)

    def _filterOpponents(self, filteredOpponents: set[SingleGame], opponent: list[str]) -> None:
        """
        Filters opponents based on the provided list.

        Args:
            filteredOpponents (set[SingleGame]): The set to store filtered opponents.
            opponent (list[str]): The list of opponent names to filter by.
        """
        for game in self._allGames:
            if game.getOpponent() in opponent:
                filteredOpponents.add(game)

    def _filterResults(self, filteredResults: set[SingleGame], result: Tuple[ChessResult, ...]) -> None:
        """
        Filters results based on the provided tuple of results.

        Args:
            filteredResults (set[SingleGame]): The set to store filtered results.
            result (Tuple[ChessResult, ...]): The tuple of results to filter by.
        """
        for game in self._allGames:
            if game.getGameResult() in result:
                filteredResults.add(game)

    def _filterOpenings(self, filteredOpenings: set[SingleGame], openings: Union[list[str], type[None]]) -> None:
        """
        Filters openings based on the provided list.

        Args:
            filteredOpenings (set[SingleGame]): The set to store filtered openings.
            openings (Union[list[str], type[None]]): The list of opening names to filter by.
        """
        if openings is None:
            filteredOpenings.update(self._allGames)
            return
        for game in self._allGames:
            if game.getName() in openings or game.getMainOpening() in openings:
                filteredOpenings.add(game)

    def _initBoundParam(self, method, args, kwargs) -> dict[str, Any]:
        """
        Initializes bound parameters for the provided method and arguments.

        Args:
            method: The method to bind parameters to.
            args: The positional arguments.
            kwargs: The keyword arguments.

        Returns:
            dict[str, Any]: The bound parameters.
        """
        signature = inspect.signature(method)
        bound_arguments = signature.bind(self, *args, **kwargs)
        bound_arguments.apply_defaults()
        bound_param = bound_arguments.arguments

        bound_param.pop(Constants.REMOVE_DUPLICATE)
        return bound_param

    def _updateMainOpening(self, opening: str, game: SingleGame) -> None:
        """
        Updates the statistics for the provided opening with the given game.

        Args:
            opening (str): The name of the opening.
            game (SingleGame): The game to update statistics with.
        """
        if opening not in self._openingsStats:
            self._openingsStats[opening] = OpeningData(opening)
        self._openingsStats[opening].addGame(game)

    def _validateThenUpdateArgs(self, bound_param) -> None:
        """
        Validates and updates arguments for the bound parameters.

        Args:
            bound_param: The bound parameters.
        """
        filteredToDate, filteredFromDate, filteredOpponents, filteredResult, filteredEloBound, filteredOpenings, \
            filteredTimeControl = \
            (set(), set(), set(), set(), set(), set(), set())
        presentArgs: list[set] = []

        for argName, argValue in bound_param.items():
            if argName == Constants.OPENINGS_ARG:
                self._filterOpenings(filteredOpenings, argValue)
                presentArgs.append(filteredOpenings)

            if argName == Constants.OPPONENT_ARG:
                self._validateThenUpdateOpponents(argValue, bound_param, filteredOpponents)
                presentArgs.append(filteredOpponents)

            if argName == Constants.RESULT_ARG:
                self._validateThenUpdateResult(argValue, bound_param, filteredResult)
                presentArgs.append(filteredResult)

            if argName == Constants.FROM_DATE_ARG:
                self._validateThenUpdateFromDate(argValue, bound_param, filteredFromDate)
                presentArgs.append(filteredFromDate)

            if argName == Constants.TO_DATE_ARG:
                self._validateThenUpdateToDate(argValue, bound_param, filteredToDate)
                presentArgs.append(filteredToDate)

            if argName == Constants.ELO_BOUND_ARG:
                self._validateThenUpdateEloBound(argValue, filteredEloBound)
                presentArgs.append(filteredEloBound)

            if argName == Constants.TIME_CONTROL_ARG:
                self._validateThenUpdateTimeControl(argValue, filteredTimeControl)
                presentArgs.append(filteredTimeControl)

            if argName == Constants.TAKE_TOP_ARG:
                _validateThenUpdateTakeTop(argValue, bound_param)

            if argName == Constants.REVERSE_ARG:
                _validateReverse(argValue)

            if argName == Constants.PLOT_ARG:
                _validatePlotArg(argValue)

            if argName == Constants.SET_GAP_ARG:
                _validateSetGap(argValue)

        self._gamesToAnalyze = set.intersection(*presentArgs)
        openings = self._initOpening()
        bound_param.update(openings=openings)

    def _validateThenUpdateOpponents(self, argValue, bound_param, filteredOpponents):
        _validateOpponent(argValue)
        opponent = self._getAllOpponents() if argValue is None else argValue
        self._filterOpponents(filteredOpponents, opponent)
        bound_param.update(opponent=opponent)

    def _validateThenUpdateToDate(self, argValue, bound_param, toDateSet: set) -> None:
        toDate = parseDate(argValue)
        toDateSet.update(game for game in self._allGames if game.getDate() <= toDate)
        bound_param.update(toDate=toDate)

    def _validateThenUpdateFromDate(self, argValue, bound_param, fromDateSet: set) -> None:
        fromDate = parseDate(argValue)
        fromDateSet.update(game for game in self._allGames if game.getDate() >= fromDate)
        bound_param.update(fromDate=fromDate)

    def _validateThenUpdateResult(self, argValue, bound_param, games):
        _validateResult(argValue)
        result = ChessResult.numToChessResult(argValue)
        self._filterResults(games, result)
        bound_param.update(result=result)

    def _validateThenUpdateEloBound(self, argValue, filteredEloBound):
        _validateEloBound(argValue)
        filteredEloBound.update(game for game in self._allGames if game.getOpponentElo() <= argValue)

    def _validateThenUpdateTimeControl(self, argValue, filteredTimeControl: set) -> None:
        if argValue is None:
            filteredTimeControl.update(game for game in self._allGames)
        else:
            timeControl, bonusTime = extractTimeControl(argValue)
            for game in self._allGames:
                if game.getTimeControl() == timeControl and game.getTimeBonus() == bonusTime:
                    filteredTimeControl.add(game)

    def _updateVariation(self, opening: str, variation: str, game: SingleGame) -> None:
        self._openingsStats[opening].addVariation(game, variation)

    def _extractOpeningInstance(self, openings: Union[str, list[str]]) -> Union[Tuple[OpeningData, ...], OpeningData]:
        """
        Extracts instances of OpeningData based on the provided opening names.

        Args:
            openings (Union[str, list[str]]): The opening name(s) to extract instances for.

        Returns:
            Union[Tuple[OpeningData, ...], OpeningData]: The extracted OpeningData instance(s).
        """
        if isinstance(openings, list):
            self._validateOpeningNames(openings)
            return tuple(self._openingsStats[opening] for opening in openings)
        elif isinstance(openings, str):
            self._validateOpeningNames([openings])
            return self._openingsStats[openings]

    def _getMostCommon(self, openings: list[OpeningData] = None) -> Union[OpeningData, Tuple[OpeningData, ...], list]:
        """
        Gets the most common opening(s) based on the number of games.

        Args:
            openings (list[OpeningData], optional): The list of openings to consider. Defaults to None.

        Returns:
            Union[OpeningData, Tuple[OpeningData, ...], list]: The most common opening(s).
        """
        topScore = 0
        result = []
        openings = list(self._openingsStats.values()) if openings is None else openings
        for opening in openings:
            topScore, result = _checkIfMostCommon(opening, result, topScore)

        return _sanitizeResult(result)

    def _getAllOpponents(self) -> list[str]:
        """
        Gets a list of all opponents from the games.

        Returns:
            list[str]: The list of opponent names.
        """
        opponents = set()
        for game in self._allGames:
            opponents.add(game.getOpponent())
        return list(opponents)

    def getOpenings(self) -> dict[str, OpeningData]:
        """
        Gets the openings statistics.

        Returns:
            dict[str, OpeningData]: The openings' statistics.
        """
        return self._openingsStats

    @adjustAndValidateParams
    def getErrorPerMove(self, openings=Constants.DEFAULT_OPENING_ARGUMENT,
                        takeTop: int = Constants.DEFAULT_TAKE_TOP, moveBound=Constants.DEFAULT_MOVE_BOUND,
                        reverse: bool = Constants.DEFAULT_REVERSE, plot: bool = Constants.DEFAULT_PLOT,
                        fromDate=Constants.DEFAULT_FROM_DATE_VALUE, toDate=Constants.DEFAULT_TO_DATE_VALUE,
                        timeControl=Constants.DEFAULT_TIME_CONTROL) \
            -> dict[str, float]:
        """
        Gets the error per move for the given openings.

        Args:
            openings: The openings to analyze.
            takeTop (int): The number of top openings to return.
            moveBound: The move bound.
            reverse (bool): Whether to reverse the sorting.
            plot (bool): Whether to plot the results.
            fromDate: The start date for the analysis.
            toDate: The end date for the analysis.
            timeControl: The time control for the analysis.

        Returns:
            dict[str, float]: The error per move for the given openings.
        """

        attributeFunc = lambda opening: opening.getErrorPerMove()
        avgErrorPerMove = _calculateAvgPerMove(openings, attributeFunc, moveBound)

        avgErrorPerMove.sort(key=lambda x: -x[1], reverse=reverse)
        slicedTop = _slicedTopItems(avgErrorPerMove, takeTop)
        result = _initResult(slicedTop)

        PlotFactory(result, plot, Constants.ERROR_PER_MOVE_TITLE, Constants.ERROR_PER_MOVE_X_LABEL,
                    Constants.ERROR_PER_MOVE_Y_LABEL)

        return result

    @adjustAndValidateParams
    def getAvgError(self, openings=Constants.DEFAULT_OPENING_ARGUMENT, takeTop: int = Constants.DEFAULT_TAKE_TOP,
                    gamesBound: int = Constants.DEFAULT_GAMES_BOUND,
                    reverse: bool = Constants.DEFAULT_REVERSE, plot: bool = Constants.DEFAULT_PLOT,
                    fromDate=Constants.DEFAULT_FROM_DATE_VALUE, toDate=Constants.DEFAULT_TO_DATE_VALUE,
                    timeControl=Constants.DEFAULT_TIME_CONTROL) \
            -> dict[str, float]:

        """
        Gets the average error for the given openings.

        Args:
            openings: The openings to analyze.
            takeTop (int): The number of top openings to return.
            gamesBound (int): The games bound.
            reverse (bool): Whether to reverse the sorting.
            plot (bool): Whether to plot the results.
            fromDate: The start date for the analysis.
            toDate: The end date for the analysis.
            timeControl: The time control for the analysis.

        Returns:
            dict[str, float]: The average error for the given openings.
        """

        _removeGamesUnderBound(gamesBound, openings)

        attributeFunc, sortingKey = lambda opening: opening.getOpeningAvgError(), lambda x: -x[1]
        topError = _sortTop(openings, reverse, attributeFunc, sortingKey)
        slicedTop = _slicedTopItems(topError, takeTop)
        result = _initResult(slicedTop)

        PlotFactory(result, plot, Constants.AVG_ERROR_TITLE, Constants.AVG_ERROR_X_LABEL, Constants.AVG_ERROR_Y_LABEL)

        return result

    @adjustAndValidateParams
    def getAvgTimePerMove(self, openings=Constants.DEFAULT_OPENING_ARGUMENT, takeTop: int = Constants.DEFAULT_TAKE_TOP,
                          moveBound: int = Constants.DEFAULT_MOVE_BOUND,
                          reverse: bool = Constants.DEFAULT_REVERSE, plot: bool = Constants.DEFAULT_PLOT,
                          fromDate=Constants.DEFAULT_FROM_DATE_VALUE, toDate=Constants.DEFAULT_TO_DATE_VALUE,
                          timeControl=Constants.DEFAULT_TIME_CONTROL) \
            -> dict[str, float]:
        """
        Gets the average time per move for the given openings.

        Args:
            openings: The openings to analyze.
            takeTop (int): The number of top openings to return.
            moveBound: The move bound.
            reverse (bool): Whether to reverse the sorting.
            plot (bool): Whether to plot the results.
            fromDate: The start date for the analysis.
            toDate: The end date for the analysis.
            timeControl: The time control for the analysis.

        Returns:
            dict[str, float]: The average time per move for the given openings.
        """
        attribute_func = lambda opening: opening.getTimeSpent()
        avgTimePerMove = _calculateAvgPerMove(openings, attribute_func, moveBound)

        topTime = sorted(avgTimePerMove, key=lambda x: -x[1], reverse=reverse)
        slicedTop = _slicedTopItems(topTime, takeTop)
        result = _initResult(slicedTop)

        PlotFactory(result, plot, Constants.TIME_SPENT_TITLE, Constants.TIME_SPENT_X_LABEL,
                    Constants.TIME_SPENT_Y_LABEL)

        return result

    @adjustAndValidateParams
    def getRecord(self, openings=Constants.DEFAULT_OPENING_ARGUMENT, takeTop: int = Constants.DEFAULT_TAKE_TOP,
                  gamesBound: int = Constants.DEFAULT_GAMES_BOUND,
                  reverse: bool = Constants.DEFAULT_REVERSE, plot: bool = Constants.DEFAULT_PLOT,
                  fromDate=Constants.DEFAULT_FROM_DATE_VALUE, toDate=Constants.DEFAULT_TO_DATE_VALUE,
                  timeControl=Constants.DEFAULT_TIME_CONTROL) \
            -> dict[str, tuple[int, int, int]]:
        """
        Gets the record (wins, draws, losses) for the given openings.

        Args:
            openings: The openings to analyze.
            takeTop (int): The number of top openings to return.
            gamesBound (int): The games bound.
            reverse (bool): Whether to reverse the sorting.
            plot (bool): Whether to plot the results.
            fromDate: The start date for the analysis.
            toDate: The end date for the analysis.
            timeControl: The time control for the analysis.

        Returns:
            dict[str, tuple[int, int, int]]: The record (wins, draws, losses) for the given openings.
        """
        _removeGamesUnderBound(gamesBound, openings)

        attributeFunc, sortingKey = lambda opening: opening.getRecord(), lambda x: _averagePoints(x[1])
        topRecords = _sortTop(openings, reverse, attributeFunc, sortingKey)
        topSlicedRecords = _slicedTopRecords(topRecords, takeTop)

        result = _initResult(topSlicedRecords)

        PlotFactory(result, plot, Constants.RECORD_TITLE, Constants.RECORD_X_LABEL, Constants.RECORD_Y_LABEL)

        return result

    @adjustAndValidateParams
    def getAvgMoveLeavingOpening(self, openings=Constants.DEFAULT_OPENING_ARGUMENT,
                                 takeTop: int = Constants.DEFAULT_TAKE_TOP,
                                 gamesBound: int = Constants.DEFAULT_GAMES_BOUND,
                                 reverse: bool = Constants.DEFAULT_REVERSE, plot: bool = Constants.DEFAULT_PLOT,
                                 fromDate=Constants.DEFAULT_FROM_DATE_VALUE, toDate=Constants.DEFAULT_TO_DATE_VALUE,
                                 timeControl=Constants.DEFAULT_TIME_CONTROL) \
            -> dict[str, float]:
        """
        Gets the average move number leaving the opening for the given openings.

        Args:
            openings: The openings to analyze.
            takeTop (int): The number of top openings to return.
            gamesBound (int): The games bound.
            reverse (bool): Whether to reverse the sorting.
            plot (bool): Whether to plot the results.
            fromDate: The start date for the analysis.
            toDate: The end date for the analysis.
            timeControl: The time control for the analysis.

        Returns:
            dict[str, float]: The average move number leaving the opening for the given openings.
        """
        _removeGamesUnderBound(gamesBound, openings)

        attributeFunc, sortingKey = lambda opening: opening.getAvgMoveLeavingOpening(), lambda x: -x[1]
        topAvgMove = _sortTop(openings, reverse, attributeFunc, sortingKey)
        slicedTop = _slicedTopItems(topAvgMove, takeTop)

        result = _initResult(slicedTop)

        PlotFactory(result, plot, Constants.LEAVING_OPENING_TITLE, Constants.LEAVING_OPENING_X_LABEL,
                    Constants.LEAVING_OPENING_Y_LABEL)

        return result

    @adjustAndValidateParams
    def getRecordByElo(self, openings=Constants.DEFAULT_OPENING_ARGUMENT,
                       takeTop: int = Constants.DEFAULT_TAKE_TOP,
                       gamesBound: int = Constants.DEFAULT_GAMES_BOUND,
                       reverse: bool = Constants.DEFAULT_REVERSE, plot: bool = Constants.DEFAULT_PLOT,
                       eloBound: int = Constants.DEFAULT_ELO_BOUND, setGap: int = Constants.DEFAULT_SET_GAP,
                       fromDate=Constants.DEFAULT_FROM_DATE_VALUE, toDate=Constants.DEFAULT_TO_DATE_VALUE,
                       timeControl=Constants.DEFAULT_TIME_CONTROL) \
            -> dict[tuple[int, int], [tuple[int, int, int]]]:
        """
        Gets the record (wins, draws, losses) by Elo rating range for the given openings.

        Args:
            openings: The openings to analyze.
            takeTop (int): The number of top openings to return.
            gamesBound (int): The games bound.
            reverse (bool): Whether to reverse the sorting.
            plot (bool): Whether to plot the results.
            eloBound (int): The Elo rating bound.
            setGap (int): The gap for Elo rating ranges.
            fromDate: The start date for the analysis.
            toDate: The end date for the analysis.
            timeControl: The time control for the analysis.

        Returns:
            dict[tuple[int, int], [tuple[int, int, int]]]: The record (wins, draws, losses) by Elo rating range for the given openings.
        """
        result = _initEloDict(openings, setGap)

        for opening in openings:
            for game in opening.getGames():
                _updateResult(result, game)

        sorted_items = sorted(result.items(), key=lambda item: _averagePoints(item[1]), reverse=reverse)
        sorted_items = [(elo, record) for elo, record in sorted_items if _totalGames(record) >= gamesBound]

        result = {key: (value[Constants.WIN_KEY], value[Constants.DRAW_KEY], value[Constants.LOSS_KEY])
                  for key, value in sorted_items}

        PlotFactory(result, plot, Constants.RESULT_BY_ELO_TITLE, Constants.RESULT_BY_ELO_X_LABEL,
                    Constants.RESULT_BY_ELO_Y_LABEL)

        return result

    @adjustAndValidateParams
    def getGamesAgainstPlayer(self, opponent: Union[str, Tuple[str]] = Constants.DEFAULT_OPPONENT_VALUE,
                              result=Constants.DEFAULT_RESULT,
                              openings=Constants.DEFAULT_OPENING_ARGUMENT, takeTop: int = Constants.DEFAULT_TAKE_TOP,
                              gamesBound: int = Constants.DEFAULT_GAMES_BOUND,
                              eloBound: int = Constants.DEFAULT_ELO_BOUND, reverse: bool = Constants.DEFAULT_REVERSE,
                              plot: bool = Constants.DEFAULT_PLOT,
                              fromDate=Constants.DEFAULT_FROM_DATE_VALUE, toDate=Constants.DEFAULT_TO_DATE_VALUE,
                              timeControl=Constants.DEFAULT_TIME_CONTROL) \
            -> dict[str, tuple[SingleGame, ...]]:
        """
                Gets the games against a specific player for the given openings.

                Args:
                    opponent: The opponent to filter games by.
                    result: The result to filter games by.
                    openings: The openings to analyze.
                    takeTop (int): The number of top openings to return.
                    gamesBound (int): The games bound.
                    eloBound (int): The Elo rating bound.
                    reverse (bool): Whether to reverse the sorting.
                    plot (bool): Whether to plot the results.
                    fromDate: The start date for the analysis.
                    toDate: The end date for the analysis.
                    timeControl: The time control for the analysis.

                Returns:
                    dict[str, tuple[SingleGame, ...]]: The games against the specific player for the given openings."""

        games = _initGamesAgainstPlayer(gamesBound, openings)
        return _sliceAndPlot(games, plot, reverse, takeTop)

    @adjustAndValidateParams
    def getGamesByTimeControl(self, opponent: Union[str, Tuple[str]] = Constants.DEFAULT_OPPONENT_VALUE,
                              result=Constants.DEFAULT_RESULT,
                              openings=Constants.DEFAULT_OPENING_ARGUMENT, takeTop: int = Constants.DEFAULT_TAKE_TOP,
                              gamesBound: int = Constants.DEFAULT_GAMES_BOUND,
                              eloBound: int = Constants.DEFAULT_ELO_BOUND, reverse: bool = Constants.DEFAULT_REVERSE,
                              plot: bool = Constants.DEFAULT_PLOT, fromDate=Constants.DEFAULT_FROM_DATE_VALUE,
                              toDate=Constants.DEFAULT_TO_DATE_VALUE, timeControl=Constants.DEFAULT_TIME_CONTROL) \
            -> dict[str, tuple[SingleGame, ...]]:

        games = _initGamesFilteredTimeControl(gamesBound, openings)
        return _sliceAndPlot(games, plot, reverse, takeTop)

    @adjustAndValidateParams
    def getGamesByDate(self, opponent: Union[str, Tuple[str]] = Constants.DEFAULT_OPPONENT_VALUE,
                       result=Constants.DEFAULT_RESULT,
                       openings=Constants.DEFAULT_OPENING_ARGUMENT, takeTop: int = Constants.DEFAULT_TAKE_TOP,
                       gamesBound: int = Constants.DEFAULT_GAMES_BOUND,
                       eloBound: int = Constants.DEFAULT_ELO_BOUND, reverse: bool = Constants.DEFAULT_REVERSE,
                       plot: bool = Constants.DEFAULT_PLOT, fromDate=Constants.DEFAULT_FROM_DATE_VALUE,
                       toDate=Constants.DEFAULT_TO_DATE_VALUE, timeControl=Constants.DEFAULT_TIME_CONTROL) \
            -> dict[str, tuple[SingleGame, ...]]:
        """
        Gets the games filtered by time control for the given openings.

        Args:
            opponent: The opponent to filter games by.
            result: The result to filter games by.
            openings: The openings to analyze.
            takeTop (int): The number of top openings to return.
            gamesBound (int): The games bound.
            eloBound (int): The Elo rating bound.
            reverse (bool): Whether to reverse the sorting.
            plot (bool): Whether to plot the results.
            fromDate: The start date for the analysis.
            toDate: The end date for the analysis.
            timeControl: The time control for the analysis.

        Returns:
            dict[str, tuple[SingleGame, ...]]: The games filtered by time control for the given openings.
        """
        games = defaultdict(list)
        for opening in openings:
            _updateDateGames(games, opening, gamesBound, eloBound)

        for date, game_list in games.items():
            game_list.sort(key=lambda game: game.getGameError(), reverse=reverse)
        sortedGames = [(date, games) for date, games in games.items()]
        _slicedTopSingleGames(sortedGames, takeTop)

        result = _initResult(sortedGames)
        PlotFactory(result, plot, Constants.AVG_ERROR_TITLE, Constants.AVG_ERROR_X_LABEL, Constants.AVG_ERROR_Y_LABEL)

        return result

    @adjustAndValidateParams
    def getGamesByResult(self, openings=Constants.DEFAULT_OPENING_ARGUMENT, result=Constants.DEFAULT_RESULT,
                         gamesBound: int = Constants.DEFAULT_GAMES_BOUND, eloBound: int = Constants.DEFAULT_ELO_BOUND,
                         fromDate: str = Constants.DEFAULT_FROM_DATE_VALUE,
                         toDate: str = Constants.DEFAULT_TO_DATE_VALUE,
                         opponent: Union[str, Tuple[str]] = Constants.DEFAULT_OPPONENT_VALUE,
                         timeControl=Constants.DEFAULT_TIME_CONTROL) -> dict[str, Tuple[SingleGame, ...]]:
        """
        Gets the games filtered by result for the given openings.

        Args:
            openings: The openings to analyze.
            result: The result to filter games by.
            gamesBound (int): The games bound.
            eloBound (int): The Elo rating bound.
            fromDate (str): The start date for the analysis.
            toDate (str): The end date for the analysis.
            opponent: The opponent to filter games by.
            timeControl: The time control for the analysis.

        Returns:
            dict[str, Tuple[SingleGame, ...]]: The games filtered by result for the given openings.
        """
        games = defaultdict(list)

        for opening in openings:
            _updateResultGames(games, opening, gamesBound)

        return {key: tuple(value) for key, value in games.items()}

    def getMostCommonOpening(self, opening: str = None) -> Union[OpeningData, Tuple[OpeningData, ...]]:
        """
        Gets the most common opening(s).

        Args:
            opening (str, optional): The opening to consider. Defaults to None.

        Returns:
            Union[OpeningData, Tuple[OpeningData, ...]]: The most common opening(s).
        """
        if opening is None:
            return self._getMostCommon()
        else:
            if opening not in self._openingsStats:
                raise ValueError(Constants.NO_OPENING_ERR)
            return self._getMostCommon(self._openingsStats[opening].getVariation())

    def getOpeningStats(self, openingName: Union[str, list[str]]) -> Union[OpeningData, Tuple[OpeningData, ...]]:
        """
        Gets the statistics for the provided opening name(s).

        Args:
            openingName (Union[str, list[str]]): The opening name(s) to get statistics for.

        Returns:
            Union[OpeningData, Tuple[OpeningData, ...]]: The statistics for the provided opening name(s).
        """
        return self._extractOpeningInstance(openingName)

    def getMostAccurateOpening(self) -> Union[Tuple[OpeningData, ...], None]:
        """
        Gets the most accurate opening(s) based on the average error.

        Returns:
            Union[Tuple[OpeningData, ...], None]: The most accurate opening(s).
        """
        return tuple(self._extractOpeningInstance(list(self.getAvgError(takeTop=1).keys())))

    def getBestOpeningRecord(self) -> Union[Tuple[OpeningData, ...], None]:
        """
        Gets the opening(s) with the best record (wins, draws, losses).

        Returns:
            Union[Tuple[OpeningData, ...], None]: The opening(s) with the best record.
        """
        return tuple(self._extractOpeningInstance(list(self.getRecord(takeTop=1).keys())))

    def getLeastAccurateOpening(self) -> Union[Tuple[OpeningData, ...], None]:
        """
        Gets the least accurate opening(s) based on the average error.

        Returns:
            Union[Tuple[OpeningData, ...], None]: The least accurate opening(s).
        """
        return tuple(self._extractOpeningInstance(list(self.getAvgError(takeTop=1, reverse=False).keys())))

    def getWorstOpening(self) -> Union[Tuple[OpeningData, ...], None]:
        """
        Gets the worst opening(s) based on the record (wins, draws, losses).

        Returns:
            Union[Tuple[OpeningData, ...], None]: The worst opening(s).
        """
        return tuple(self._extractOpeningInstance(list(self.getRecord(takeTop=1, reverse=False).keys())))

    def getAllGames(self) -> list[SingleGame]:
        """
        Gets all games.

        Returns:
            list[SingleGame]: The list of all games.
        """
        return list(self._allGames)

    def exportCSV(self, output_file: str = 'exported_data.csv'):
        """
        Exports the game data to a CSV file.

        Args:
            output_file (str): The name of the output CSV file. Defaults to 'exported_data.csv'.

        """
        data_to_export = self._allGames  # or any other data structure you want to export

        # Define the headers for the CSV
        headers = Constants.CSV_HEADERS

        # Open the CSV file for writing
        with open(output_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers)  # Write the headers

            # Iterate over the data and write each row
            for game in data_to_export:
                row = [
                    game.getDate().strftime("%Y-%m-%d"),
                    game.getOpponent(),
                    ChessResult.chessResultToStr(game.getGameResult()),
                    game.getElo(),
                    game.getOpponentElo(),
                    game.getMainOpening(),
                    game.getVariation() or 'N/A',
                    game.getMoveLeavingOpening(),
                    game.getTimeControl(),
                    game.getTimeBonus(),
                    ';'.join(f'{x:.2f}' for x in game.getErrorPerMove()),  # Format floats to 2 decimal places
                    ';'.join(f'{x:.2f}' for x in game.getTimeSpent())  # Format floats to 2 decimal places
                ]
                writer.writerow(row)


if __name__ == '__main__':
    stockFish = Stockfish(Constants.STOCKFISH_DIR)
    stockFish.set_depth(20)
    # stockFish.set_elo_rating(3400)
    # stockFish.update_engine_parameters({"Min Split Depth": 20, "Hash": 2048})
    a = ChessAnalysis('Dataset/4GamesFrench.pgn', 'tomerkein', stockFish)
    # print(a.getGamesByTimeControl(plot=True))
    # print(a.getWorstOpening())
    # print(a.getLeastAccurateOpening())
    # print(a.getAvgTimePerMove(plot=True))
    # print(a.getMostCommonOpening())
    # print(a.getErrorPerMove(plot=True))
    # print(a.getAvgError(plot=True))
    # print(a.getRecordByElo(plot=True))
    # print(a.getAvgMoveLeavingOpening(plot=True))
    # print(a.getGamesAgainstPlayer(plot=True))
    # print(a.getMostAccurateOpening())
    # print(a.getGamesByResult(opponent="VRemo"))
    # print(a.getBestOpeningRecord())
    # print(a.getGamesByDate(plot=True))
    a.exportCSV()
