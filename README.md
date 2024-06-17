
# Chess Analysis

Brief description:

ChessAnalysis is a flexible library designed to analyze chess games in-depth. It provides various functionalities to evaluate move error, opening strategies, time spent per move, and game results based on multiple criteria such as ELO ratings and specific opponents. The library is tailored for chess enthusiasts, researchers, and developers who want to gain insights from their chess games or build chess analysis tools.

Key Features:

Move Analysis:

Calculate average error and time spent per move.
Evaluate errors per move and track performance over time.
Opening Data:

Analyze different chess openings and their variations.
Track the performance of specific openings based on game results.
Game Statistics:

Retrieve game records filtered by date, opponent, ELO range, openings and more.
Analyze game results to identify strengths and weaknesses.
Visualization:

Generate plots to visualize statistical data for better insights.
Support for plotting average move error, time spent, and game results.
Export Functionality:

Export analyzed game data to CSV for further analysis or sharing.

Who It's For:

Chess Players: Improve your game by analyzing your moves, openings, and results to identify areas for improvement.
Coaches: Use the library to provide detailed feedback to students based on their game performance.
Developers: Integrate ChessAnalysis into chess applications or tools to provide advanced analysis features.

A few things to note: 

1) Throughout the entire library, the error is computed as the absolute difference between the Stockfish evaluation before your move and the evaluation after your move. This means that the closer the error is to zero, the better. Additionally, the evaluation may differ slightly from what you are familiar with in other apps, as it depends on the engine you use.

2) If given a small number of games to analyze, some of the functions may return values that are not meaningful.



## API Reference

#### getOpenings

```http
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| None | --- | Gets the openings statistics. |

#### getErrorPerMove

```http
```

| Parameter | Type | Description |
| :-------- | :--- | :----------- |
| `openings` | `str, list[str]` | The openings to analyze. |
| `takeTop` | `int` | The number of top openings to return. |
| `moveBound` | `int` | The move bound. |
| `reverse` | `bool` | Whether to reverse the sorting. |
| `plot` | `bool` | Whether to plot the results. |
| `fromDate` | `str` | The start date for the analysis. |
| `toDate` | `str` | The end date for the analysis. |
| `timeControl` | `str` | The time control for the analysis. |


#### getAvgError

| Parameter | Type | Description |
| :-------- | :--- | :----------- |
| `openings` | `str, list[str]` | The openings to analyze. |
| `takeTop` | `int` | The number of top openings to return. |
| `gamesBound` | `int` | The games bound. |
| `reverse` | `bool` | Whether to reverse the sorting. |
| `plot` | `bool` | Whether to plot the results. |
| `fromDate` | `str` | The start date for the analysis. |
| `toDate` | `str` | The end date for the analysis. |
| `timeControl` | `str` | The time control for the analysis. |

#### getAvgTimePerMove

| Parameter | Type | Description |
| :-------- | :--- | :----------- |
| `openings` | `str, list[str]` | The openings to analyze. |
| `takeTop` | `int` | The number of top openings to return. |
| `moveBound` | `int` | The move bound. |
| `reverse` | `bool` | Whether to reverse the sorting. |
| `plot` | `bool` | Whether to plot the results. |
| `fromDate` | `str` | The start date for the analysis. |
| `toDate` | `str` | The end date for the analysis. |
| `timeControl` | `str` | The time control for the analysis. |

#### getRecord

| Parameter | Type | Description |
| :-------- | :--- | :----------- |
| `openings` | `str, list[str]` | The openings to analyze. |
| `takeTop` | `int` | The number of top openings to return. |
| `gamesBound` | `int` | The games bound. |
| `reverse` | `bool` | Whether to reverse the sorting. |
| `plot` | `bool` | Whether to plot the results. |
| `fromDate` | `str` | The start date for the analysis. |
| `toDate` | `str` | The end date for the analysis. |
| `timeControl` | `str` | The time control for the analysis. |

#### getAvgMoveLeavingOpening

| Parameter | Type | Description |
| :-------- | :--- | :----------- |
| `openings` | `str, list[str]` | The openings to analyze. |
| `takeTop` | `int` | The number of top openings to return. |
| `gamesBound` | `int` | The games bound. |
| `reverse` | `bool` | Whether to reverse the sorting. |
| `plot` | `bool` | Whether to plot the results. |
| `fromDate` | `str` | The start date for the analysis. |
| `toDate` | `str` | The end date for the analysis. |
| `timeControl` | `str` | The time control for the analysis. |

#### getRecordByElo

| Parameter | Type | Description |
| :-------- | :--- | :----------- |
| `openings` | `str, list[str]` | The openings to analyze. |
| `takeTop` | `int` | The number of top openings to return. |
| `gamesBound` | `int` | The games bound. |
| `reverse` | `bool` | Whether to reverse the sorting. |
| `plot` | `bool` | Whether to plot the results. |
| `eloBound` | `int` | The Elo rating bound. |
| `setGap` | `int` | The gap for Elo rating ranges. |
| `fromDate` | `str` | The start date for the analysis. |
| `toDate` | `str` | The end date for the analysis. |
| `timeControl` | `str` | The time control for the analysis. |

#### getGamesAgainstPlayer

| Parameter | Type | Description |
| :-------- | :--- | :----------- |
| `opponent` | `str, Tuple[str]` | The opponent to filter games by. |
| `result` | `str` | The result to filter games by. |
| `openings` | `str, list[str]` | The openings to analyze. |
| `takeTop` | `int` | The number of top openings to return. |
| `gamesBound` | `int` | The games bound. |
| `eloBound` | `int` | The Elo rating bound. |
| `reverse` | `bool` | Whether to reverse the sorting. |
| `plot` | `bool` | Whether to plot the results. |
| `fromDate` | `str` | The start date for the analysis. |
| `toDate` | `str` | The end date for the analysis. |
| `timeControl` | `str` | The time control for the analysis. |

#### getGamesByTimeControl

| Parameter | Type | Description |
| :-------- | :--- | :----------- |
| `opponent` | `str, Tuple[str]` | The opponent to filter games by. |
| `result` | `str` | The result to filter games by. |
| `openings` | `str, list[str]` | The openings to analyze. |
| `takeTop` | `int` | The number of top openings to return. |
| `gamesBound` | `int` | The games bound. |
| `eloBound` | `int` | The Elo rating bound. |
| `reverse` | `bool` | Whether to reverse the sorting. |
| `plot` | `bool` | Whether to plot the results. |
| `fromDate` | `str` | The start date for the analysis. |
| `toDate` | `str` | The end date for the analysis. |
| `timeControl` | `str` | The time control for the analysis. |

#### getGamesByDate

| Parameter | Type | Description |
| :-------- | :--- | :----------- |
| `opponent` | `str, Tuple[str]` | The opponent to filter games by. |
| `result` | `str` | The result to filter games by. |
| `openings` | `str, list[str]` | The openings to analyze. |
| `takeTop` | `int` | The number of top openings to return. |
| `gamesBound` | `int` | The games bound. |
| `eloBound` | `int` | The Elo rating bound. |
| `reverse` | `bool` | Whether to reverse the sorting. |
| `plot` | `bool` | Whether to plot the results. |
| `fromDate` | `str` | The start date for the analysis. |
| `toDate` | `str` | The end date for the analysis. |
| `timeControl` | `str` | The time control for the analysis. |

#### getGamesByResult

| Parameter | Type | Description |
| :-------- | :--- | :----------- |
| `openings` | `str, list[str]` | The openings to analyze. |
| `result` | `str` | The result to filter games by. |
| `gamesBound` | `int` | The games bound. |
| `eloBound` | `int` | The Elo rating bound. |
| `fromDate` | `str` | The start date for the analysis. |
| `toDate` | `str` | The end date for the analysis. |
| `opponent` | `str, Tuple[str]` | The opponent to filter games by. |
| `timeControl` | `str` | The time control for the analysis. |

#### getMostCommonOpening

| Parameter | Type | Description |
| :-------- | :--- | :----------- |
| `opening` | `str` | The opening to consider. Defaults to None. |

#### getOpeningStats

| Parameter | Type | Description |
| :-------- | :--- | :----------- |
| `openingName` | `str, list[str]` | The opening name(s) to get statistics for. |

#### getMostAccurateOpening

| Parameter | Type | Description |
| :-------- | :--- | :----------- |
| None | | Gets the most accurate opening(s) based on the average error. |

#### getBestOpeningRecord

| Parameter | Type | Description |
| :-------- | :--- | :----------- |
| None | | Gets the opening(s) with the best record (wins, draws, losses). |

#### getLeastAccurateOpening

| Parameter | Type | Description |
| :-------- | :--- | :----------- |
| None | | Gets the least accurate opening(s) based on the average error. |

#### getWorstOpening

| Parameter | Type | Description |
| :-------- | :--- | :----------- |
| None | | Gets the worst opening(s) based on the record (wins, draws, losses). |

#### getAllGames

| Parameter | Type | Description |
| :-------- | :--- | :----------- |
| None | | Gets all games. |

#### exportCSV

| Parameter | Type | Description |
| :-------- | :--- | :----------- |
| `output_file` | `str` | The name of the output CSV file. Defaults to 'exported_data.csv'. |


## License

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


## Authors

- [Tomer Keinan](https://github.com/tomerkeinan)
