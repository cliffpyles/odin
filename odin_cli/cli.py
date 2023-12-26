#!/usr/bin/env python

import argparse
from odin_cli.utils import load_config, load_plugins
from odin_cli.commands.ask import setup_ask_command
from odin_cli.commands.config import setup_config_command
from odin_cli.commands.run import setup_run_command


def main():
    config = load_config()
    parser = argparse.ArgumentParser(prog="odin")
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    parser.add_argument(
        "--log-file",
        default="odin.log",
        help="Path to the log file.",
    )

    subparsers = parser.add_subparsers(help="Commands")
    plugins = load_plugins(subparsers, config)
    setup_config_command(subparsers, config, plugins)
    setup_ask_command(subparsers, config, plugins)
    setup_run_command(subparsers, config, plugins)

    # Parse the arguments
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args, config)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
