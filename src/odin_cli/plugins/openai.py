import click
import textwrap
from openai import OpenAI
from utils import (
    read_content_from_source,
    process_template_arguments,
    handle_interactive_chat,
    handle_single_prompt,
    read_stdin_if_empty,
)

client = OpenAI()


def process_single_prompt(service_name, prompt, model="gpt-4"):
    """Process a single prompt using OpenAI."""
    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ]
        response = client.chat.completions.create(model=model, messages=messages)
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"


def process_interactive_chat(service_name, user_input, chat_history, model="gpt-4"):
    """Process interactive chat using OpenAI ChatCompletion."""
    try:
        # Create a list of messages for the chat history
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        messages += [
            {
                "role": "user" if entry["prompt"] else "assistant",
                "content": entry["prompt"] or entry["response"],
            }
            for entry in chat_history
        ]
        messages.append({"role": "user", "content": user_input})
        response = client.chat.completions.create(
            model=model,
            messages=messages,
        )

        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"


def register_cli_commands(cli_group):
    @cli_group.command(
        name="openai",
        help=textwrap.dedent(
            """ 
        Interact with OpenAI.

        Examples:
        ask openai "Tell me a fact" --model="gpt-4"
        ask openai "Translate '{text}' to French" text="Hello, world" --model="gpt-4"
        ask openai "How many {unit} in a mile?" unit=kilometers
        ask openai /path/to/fact_request.txt
        ask openai s3://mybucket/fact_request.txt
        ask openai https://example.com/fact_request.txt
        """
        ),
    )
    @click.argument("prompt", required=False)
    @click.argument("template_args", nargs=-1)
    @click.option("--model", default="gpt-4", help="Specify the model")
    @click.option("--chat", help="Filename of the chat session")
    def openai(prompt, model, chat, template_args):
        if chat:
            # Optional: process the prompt if it's provided
            initial_prompt = None
            if prompt:
                initial_prompt = read_content_from_source(prompt)
                initial_prompt = process_template_arguments(
                    initial_prompt, template_args
                )

            response = handle_interactive_chat("openai", chat, initial_prompt, model)
        else:
            # For single prompt interaction
            prompt = read_content_from_source(read_stdin_if_empty(prompt))
            prompt = process_template_arguments(prompt, template_args)
            response = handle_single_prompt("openai", prompt, model)

        print(response)
