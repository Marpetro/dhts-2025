"""Run the full experiment as described in README.md.

This is a thin wrapper calling the pastry experiment runner.
"""
from __future__ import annotations

from src.experiments.run_pastry import main as run_pastry_main


if __name__ == "__main__":
    run_pastry_main()
