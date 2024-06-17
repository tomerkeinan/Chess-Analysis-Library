from . import Constants
from .SingleGame import SingleGame
import matplotlib.pyplot as plt
from numpy import ceil


def calculateAvgPoints(record: list[float, int]) -> float:
    """
    Calculate the average points from a record.

    Args:
        record (list[float, int]): A list containing the win and draw points.

    Returns:
        float: The calculated average points.
    """
    return record[0] + record[1] * Constants.DRAW_POINTS


class PlotFactory:
    def __init__(self, dictToPlot: dict, plot: bool, title: str, xlabel: str, ylabel: str):
        """
        Initialize the PlotFactory class.

        Args:
            dictToPlot (dict): The dictionary to plot.
            plot (bool): Flag to indicate if plotting is needed.
            title (str): The title of the plot.
            xlabel (str): The label for the x-axis.
            ylabel (str): The label for the y-axis.
        """
        if not plot:
            return

        assert isinstance(dictToPlot, dict), Constants.DICT_TO_PLOT_ERR
        self._dictToPlot = dictToPlot
        self._title = title
        self._xlabel = xlabel
        self._ylabel = ylabel
        self._generate()

    def _generate(self) -> None:
        """Generate the plot based on the type of data in the dictionary."""

        if self._typeFloat():
            self._generateFloatPlot()

        elif self._isTuple():
            if self._isTupleFloat():
                if self._isKeysTupFloat():  # type tuple[int, int]: tuple[int, int int]
                    self._generateTupleFloatWithTupleIntKey()
                else:
                    self._generateTupleFloatWithKeyStr()
            else:  # type is tuple[SingleGame]
                self._generateTupleSingleGame()

    def _isTupleFloat(self) -> bool:
        """Check if the values in the dictionary are tuples of floats/integers."""

        return all(isinstance(val, (float, int)) for tup in self._dictToPlot.values() for val in tup)

    def _isKeysTupFloat(self):
        """Check if the keys in the dictionary are tuples and the values are floats/integers."""

        return all(isinstance(val, tuple) for val in self._dictToPlot.keys()) and all(
            isinstance(val, (float, int)) for tup in self._dictToPlot.keys() for val in tup)

    def _typeFloat(self) -> bool:
        """Check if the values in the dictionary are floats/integers."""

        return all(isinstance(key, (float, int)) for key in self._dictToPlot.values())

    def _generateFloatPlot(self) -> None:
        """Generate a plot for float values."""

        axis, yaxis = [key for key in self._dictToPlot.keys()], [val for val in self._dictToPlot.values()]
        self._generatePlot(axis, yaxis)

    def _generatePlot(self, axis, yaxis):
        """
        Generate the plot.

        Args:
            axis (list): The x-axis values.
            yaxis (list): The y-axis values.
        """
        for i in range(0, len(axis), Constants.JUMP_TO_MAKE_PLOT_MORE_SPARSE):
            x = axis[i: i + Constants.JUMP_TO_MAKE_PLOT_MORE_SPARSE]
            y = yaxis[i: i + Constants.JUMP_TO_MAKE_PLOT_MORE_SPARSE]
            plt.style.use(Constants.PLOT_STYLE)

            if len(x) < Constants.MAXIMUM_ITEMS_PER_BAR:
                plt.bar(x, y)
                plt.xlabel(self._xlabel)
                plt.ylabel(self._ylabel)

            else:
                plt.barh(x, y)
                plt.ylabel(self._xlabel)
                plt.xlabel(self._ylabel)

            plt.title(self._title)
            plt.tight_layout()
            plt.show()
        self._printSplitMsg(axis)

    def _printSplitMsg(self, axis: list) -> None:
        """
        Print a message indicating the number of split plots.

        Args:
            axis (list): The x-axis values.
        """
        numOfSplitPlots = int(ceil(len(axis) / Constants.JUMP_TO_MAKE_PLOT_MORE_SPARSE))
        if numOfSplitPlots > 1:
            print(Constants.NUM_OF_PLOT_PRINTED.format(self._title, numOfSplitPlots))

    def _isTuple(self) -> bool:
        """Check if the values in the dictionary are tuples."""
        return all(isinstance(val, tuple) for val in self._dictToPlot.values())

    def _generateTupleFloatWithKeyStr(self) -> None:
        """Generate a plot for tuples with string keys."""
        axis = [key for key in self._dictToPlot.keys()]
        yaxis = [calculateAvgPoints(record) for record in self._dictToPlot.values()]
        self._generatePlot(axis, yaxis)

    def _generateTupleFloatWithTupleIntKey(self) -> None:
        """Generate a plot for tuples with tuple integer keys."""
        axis = [f"{key[0]}-{key[1]}" for key in self._dictToPlot.keys()]
        yaxis = [calculateAvgPoints(record) for record in self._dictToPlot.values()]
        self._generatePlot(axis, yaxis)

    def _generateTupleSingleGame(self) -> None:
        """Generate a plot for tuples of SingleGame objects."""
        axis = [key for key in self._dictToPlot.keys()]
        yaxis = self._calculateAvgSingleGames()
        self._generatePlot(axis, yaxis)

    def _typeTupleSingleGame(self) -> bool:
        """Check if the values in the dictionary are tuples of SingleGame objects."""

        return all(isinstance(val, SingleGame) for val in self._dictToPlot.values())

    def _calculateAvgSingleGames(self) -> list[float]:
        """
        Calculate the average error for SingleGame tuples.

        Returns:
            list[float]: The average error for each tuple.
        """
        result = []
        for tup in self._dictToPlot.values():
            result.append(sum(game.getGameError() for game in tup))
        return result
