#!/usr/bin/env python

import argparse
from odin_cli.utils import load_plugins


def setup_ask_command(subparsers):
    # Subparser for the "ask" command
    parser_ask = subparsers.add_parser(
        "ask", help="Ask a question or interact with a service"
    )
    ask_subparsers = parser_ask.add_subparsers(help="Services")

    # Load plugins (for each service) and register their commands
    load_plugins(ask_subparsers)


def main():
    parser = argparse.ArgumentParser(prog="odin")
    subparsers = parser.add_subparsers(help="Commands")

    setup_ask_command(subparsers)

    # Parse the arguments
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
