"""Top-level runner for experiments.

Allows choosing the protocol (pastry|chord). For now, pastry is the default
and calls into `src.experiments.run_pastry.main()`.
"""
from __future__ import annotations

import argparse
from typing import Optional


def main(argv: Optional[list] = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", choices=["pastry", "chord"], default="pastry")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode (no plotting)")

    args = parser.parse_args(argv)

    if args.protocol == "pastry":
        from src.experiments import run_pastry

        run_pastry.main()
        return

    if args.protocol == "chord":
        # Simple demo runner for Chord if/when implemented
        from src.chord.chord_network import ChordNetwork

        print("Running simple Chord demo (small network)")
        net = ChordNetwork()
        net.build(20)
        # insert a few dummy values
        nid, _ = net.insert("0" * 32, "zero", {"msg": "hello"})
        print(f"Inserted at: {nid}")
        vals, hops = net.get_values("0" * 32, "zero")
        print(f"Lookup returned {len(vals)} values, hops={hops}")
        return


if __name__ == "__main__":
    main()
