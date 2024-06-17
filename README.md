
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



# ChessAnalysis Installation Guide

## Overview

ChessAnalysis is a Python library designed for analyzing chess games. It provides various functions to analyze game statistics, including errors per move, average time per move, records by openings, and more. This guide will help you install the library and its dependencies.

## Prerequisites

Before installing ChessAnalysis, ensure you have the following prerequisites:

1. **Python 3.6 or later**: Make sure you have Python 3.6 or a newer version installed on your system.
2. **pip**: The Python package installer should be available.

## Step-by-Step Installation

### 1. Clone the Repository

Clone the ChessAnalysis repository from GitHub to your local machine:

```sh
git clone https://github.com/tomerkeinan/ChessAnalysis.git
cd ChessAnalysis
```

### 2. Set Up a Virtual Environment

It is recommended to create a virtual environment to manage the dependencies for your project:

```sh
python3 -m venv venv
source venv/bin/activate
```

### 3. Create the Distribution Package

Create a source distribution package for ChessAnalysis:

```sh
python3 setup.py sdist
```

This will generate a `.tar.gz` file in the `dist` directory.

### 4. Install the Package

Install the ChessAnalysis package using `pip`:

```sh
pip install dist/ChessAnalysis-0.1.0.tar.gz
```

### 5. Verify the Installation

To ensure the library is installed correctly, open a Python interpreter and try importing the main classes:

```sh
python
```

```python
from ChessAnalysis import ChessAnalysis, SingleGame
```

If no errors occur, the installation is successful.

## Including Opening Book Data

ChessAnalysis requires opening book data stored in `.tsv` files located in the `OpeningBook` directory. The setup script is configured to include these files.

The `OpeningBook` directory should contain all necessary `.tsv` files.

## Uninstallation

If you need to uninstall the ChessAnalysis library, you can do so with pip:

```sh
pip uninstall ChessAnalysis
```

