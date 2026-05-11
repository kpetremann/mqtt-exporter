# Developer guide

## AI usage

Any AI usage must be disclosed in the Pull Request, including:
- Usage (e.g. minor suggestions, partial code, majority of implementation): 
- Estimated percentage of AI-generated content (e.g. everything, major part, minor part, none)

The contributor:
- Must ensure the quality of provided of the code is good, and must have been tested prior being pushed.
- Must be able to understand the code changes. **Purely vibe coded contribution without real developer experience is forbidden.**

This helps maintain transparency and review quality.

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

You can install invoke package on your system and then use it to install environment, run an autoformat or just run the exporter:

  * `invoke install`: to install virtualenv under .venv/ and install all dev requirements
  * `invoke reformat`: reformat using black and isort
  * `invoke start`: start the app
