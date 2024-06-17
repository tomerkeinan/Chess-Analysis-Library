from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="ChessAnalysis",
    version="0.1.0",
    author="Tomer Keinan",
    description="A library for analyzing chess games",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tomerkeinan",
    packages=find_packages(),
    package_data={
        "ChessAnalysis": ["OpeningBooks/*.tsv"],
    },
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "numpy",
        "matplotlib",
        "chess",
        "stockfish"
    ],
)
