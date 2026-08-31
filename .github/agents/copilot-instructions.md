<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [bsbingo Development Guidelines](#bsbingo-development-guidelines)
  - [Active Technologies](#active-technologies)
  - [Project Structure](#project-structure)
  - [Commands](#commands)
  - [Code Style](#code-style)
  - [Recent Changes](#recent-changes)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# bsbingo Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-08-30

## Active Technologies

- Python 3.14 (per repo-root `pyproject.toml`) + Django ≥6.0.7, `django-htmx` (already wired in `002-buzzword-bingo-game`), no new dependencies (004-buzzword-categories)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.14 (per repo-root `pyproject.toml`): Follow standard conventions

## Recent Changes

- 004-buzzword-categories: Added Python 3.14 (per repo-root `pyproject.toml`) + Django ≥6.0.7, `django-htmx` (already wired in `002-buzzword-bingo-game`), no new dependencies

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
