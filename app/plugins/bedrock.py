import click
import textwrap
from utils import (
    read_content_from_source,
    process_template_arguments,
    handle_interactive_chat,
    handle_single_prompt,
    read_stdin_if_empty,
)


def process_single_prompt(service_name, prompt, model):
    # Implement Bedrock specific code here
    return f"Bedrock response to: {prompt}"


def process_interactive_chat(service_name, user_input, chat_history, model):
    # Implement Bedrock specific interactive chat code here
    return "Bedrock response to: " + user_input


def register_cli_commands(cli_group):
    @cli_group.command(
        name="bedrock",
        help=textwrap.dedent(
            """
        Interact with Amazon Bedrock.

        Examples:
        ask bedrock "Tell me a fact" --model="claude-v2"
        ask bedrock "Translate '{text}' to French" --model="claude-v2" text="Hello, world"
        ask bedrock "How many {unit} in a mile?" unit=kilometers
        ask bedrock /path/to/fact_request.txt
        ask bedrock s3://mybucket/fact_request.txt
        ask bedrock https://example.com/fact_request.txt
        """
        ),
    )
    @click.argument("prompt", required=False)
    @click.argument("template_args", nargs=-1)
    @click.option("--model", default="claude-v2", help="Specify the model")
    @click.option("--chat", help="Filename of the chat session")
    def bedrock(prompt, model, chat, template_args):
        if chat:
            # Optional: process the prompt if it's provided
            initial_prompt = None
            if prompt:
                initial_prompt = read_content_from_source(prompt)
                initial_prompt = process_template_arguments(
                    initial_prompt, template_args
                )

            response = handle_interactive_chat("Bedrock", chat, initial_prompt, model)
        else:
            # For single prompt interaction
            prompt = read_content_from_source(read_stdin_if_empty(prompt))
            prompt = process_template_arguments(prompt, template_args)
            response = handle_single_prompt("Bedrock", prompt, model)
        print(response)
