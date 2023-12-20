#!/usr/bin/env python

import click
import textwrap
from utils import load_plugins


# Define the main CLI group with examples
@click.group(
    epilog=textwrap.dedent(
        """
        Examples:
        ask bedrock "Tell me a joke"
        ask openai "Tell me a fact"
        """
    )
)
def ask():
    """This tool allows interaction with AI services such as OpenAI and Amazon Bedrock."""
    pass


load_plugins(ask)


def main():
    ask()


if __name__ == "__main__":
    main()
