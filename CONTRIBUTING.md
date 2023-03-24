# Developer guide

## Requirements

Please add/adapt **unit tests** for new features or bug fixes.

Please ensure you have run the following before pushing a commit:
  * `black` and `isort` (or `invoke reformat`)
  * `pylama` to run all linters

## Coding style

Follow usual best practices:
  * document your code (inline and docstrings)
  * constants are in upper case
  * use comprehensible variable name
  * one function = one purpose
  * function name should perfectly define its purpose

## Dev environment

You can install invoke package on your system and then use it to install environement, run an autoformat or just run the exporter:

  * `invoke install`: to install virtualenv under .venv/ and install all dev requirements
  * `invoke reformat`: reformat using black and isort
  * `invoke start`: start the app
