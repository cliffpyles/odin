#!/usr/bin/env python

import click
import sys
import os
import requests
import boto3
import json
import textwrap
from urllib.parse import urlparse
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory


# Function to determine if a string is a valid URL
def is_url(string):
    try:
        result = urlparse(string)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


# Function to check if a string is an S3 path
def is_s3_path(string):
    return string.startswith("s3://")


# Function to read content from a file, URL, or S3 path
def read_content_from_source(source):
    # Check if source is a URL
    if is_url(source):
        response = requests.get(source)
        return response.text

    # Check if source is an S3 path
    if is_s3_path(source):
        s3 = boto3.client("s3")
        bucket, key = source[5:].split("/", 1)
        response = s3.get_object(Bucket=bucket, Key=key)
        return response["Body"].read().decode("utf-8")

    # Otherwise, treat it as a file path
    if os.path.isfile(source):
        with open(source, "r") as file:
            return file.read()

    return source


# Function to read from stdin if prompt is empty
def read_stdin_if_empty(prompt):
    if not prompt:
        return sys.stdin.read().strip()
    return prompt


# Function to process template arguments
def process_template_arguments(prompt, template_args):
    for arg in template_args:
        key, value = arg.split("=")
        prompt = prompt.replace(f"{{{key}}}", value)
    return prompt


# Function to handle interactive chat
def handle_interactive_chat(service_name, chat_file, initial_prompt):
    session = PromptSession(history=FileHistory(chat_file) if chat_file else None)

    chat_history = []
    if chat_file:
        if os.path.exists(chat_file):
            with open(chat_file, "r") as file:
                chat_history = json.load(file)
        else:
            print(f"Chat file '{chat_file}' not found. A new file will be created.")

    if initial_prompt:
        # Process initial prompt (if provided)
        # Placeholder for AI interaction code
        chat_history.append({"prompt": initial_prompt, "response": "AI response here"})

    while True:
        try:
            user_input = session.prompt("> ")
            if user_input.lower() in ["exit", "quit", "q"]:
                break

            # Placeholder for AI interaction code
            ai_response = "AI response to: " + user_input
            chat_history.append({"prompt": user_input, "response": ai_response})
            print(ai_response)
        except KeyboardInterrupt:
            continue
        except EOFError:
            break

    if chat_file:
        with open(chat_file, "w") as file:
            json.dump(chat_history, file)

    return "Chat session ended."


# Function to handle single prompt interaction
def handle_single_prompt(service_name, prompt):
    # Placeholder for AI interaction code
    # Replace the following line with AI service interaction code
    return f"{service_name} response to: {prompt}"


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


# Define the Bedrock command with examples
@ask.command(
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
    )
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
            initial_prompt = process_template_arguments(initial_prompt, template_args)

        response = handle_interactive_chat("Bedrock", chat, initial_prompt)
    else:
        # For single prompt interaction
        prompt = read_content_from_source(read_stdin_if_empty(prompt))
        prompt = process_template_arguments(prompt, template_args)
        response = handle_single_prompt("Bedrock", prompt)
    print(response)


# Define the OpenAI command with examples
@ask.command(
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
    )
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
            initial_prompt = process_template_arguments(initial_prompt, template_args)

        response = handle_interactive_chat("OpenAI", chat, initial_prompt)
    else:
        # For single prompt interaction
        prompt = read_content_from_source(read_stdin_if_empty(prompt))
        prompt = process_template_arguments(prompt, template_args)
        response = handle_single_prompt("OpenAI", prompt)

    print(response)


if __name__ == "__main__":
    ask()
