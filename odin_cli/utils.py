import sys
import os
import requests
import boto3
import json
import yaml
import re
from urllib.parse import urlparse
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
import importlib
import datetime
import glob
import frontmatter


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


def read_stdin_if_piped(prompt, piped, pipe_key):
    if piped:
        has_pipe_key = pipe_key != ""
        piped_content = sys.stdin.read()
        if has_pipe_key:
            prompt_key = "{" + pipe_key + "}"

            return prompt.replace(prompt_key, piped_content)
        else:
            return f"{piped_content}{prompt}"
    return prompt


# Function to process template arguments
def process_template_arguments(prompt, template_args):
    for arg in template_args:
        key, value = arg.split("=")
        prompt = prompt.replace(f"{{{key}}}", value)
    return prompt


def open_chat(file_path):
    with open(file_path, "r") as file:
        content = file.read()

    # Regex Pattern Explanation:
    # - (---\n(?:.*?:.*?\n)+---): Matches frontmatter enclosed in '---'.
    # - ([\s\S]*?): Non-greedy capture of content after frontmatter.
    # - (?=\n---|$): Stops at next frontmatter or end of file.
    pattern = r"(---\n(?:.*?:.*?\n)+---)([\s\S]*?)(?=\n---|$)"

    # Find all matches of the pattern in the content
    matches = re.findall(pattern, content)
    parsed_documents = {}

    # Iterate over the matches and parse them
    for frontmatter_str, content_str in matches:
        parsed_doc = frontmatter.loads(frontmatter_str + "\n" + content_str)
        doc_id = parsed_doc.metadata.get("id", None)
        if doc_id:
            parsed_documents[doc_id] = {
                "metadata": parsed_doc.metadata,
                "content": parsed_doc.content.strip(),
            }

    return parsed_documents


def get_chat_items(chat, sort=None, **filters):
    # Filter items based on provided keyword arguments
    items = [
        doc
        for doc in chat.values()
        if all(doc["metadata"].get(key) == value for key, value in filters.items())
    ]

    # Sort items by the specified field if provided
    if sort:
        items.sort(key=lambda x: x["metadata"].get(sort, float("inf")))

    return items


def create_chat_banner(service_name, chat_file):
    """Generate a banner for the chat session."""
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    banner_lines = [
        "==========================================================",
        f"      Chat Session with {service_name}",
        "==========================================================",
        f"Session Time: {current_time}",
    ]

    if chat_file:
        banner_lines.append(f"Chat File: {chat_file}")

    banner_lines.append("Type 'exit', 'quit', or 'q' to end the chat session.")
    banner_lines.append("==========================================================\n")

    return "\n".join(banner_lines)


# Function to handle interactive chat
def handle_interactive_chat(service_name, chat_file, initial_prompt, model):
    # Print the chat session banner
    print(create_chat_banner(service_name, chat_file))

    session = PromptSession(history=FileHistory(chat_file) if chat_file else None)

    chat_history = []
    if chat_file:
        if os.path.exists(chat_file):
            with open(chat_file, "r") as file:
                chat_history = json.load(file)

            # Display existing chat history
            for entry in chat_history:
                print(f"You: {entry['prompt']}")
                print(f"{service_name}: {entry['response']}")
        else:
            print(f"Chat file '{chat_file}' not found. A new file will be created.")

    if initial_prompt:
        # Process initial prompt (if provided)
        # Placeholder for AI interaction code
        chat_history.append({"prompt": initial_prompt, "response": "AI response here"})

    plugin = load_plugin(service_name)
    while True:
        try:
            user_input = session.prompt("> ")
            if user_input.lower() in ["exit", "quit", "q"]:
                break

            ai_response = plugin.process_interactive_chat(
                service_name, user_input, chat_history, model
            )
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
def handle_single_prompt(service_name, prompt, model):
    plugin = load_plugin(service_name.lower())

    return plugin.process_single_prompt(service_name, prompt, model)


def load_config():
    config_paths = [
        os.path.expanduser("~/.config/odin/odin.yaml"),
        os.path.expanduser("~/.config/odin/odin.yml"),
    ]

    for path in config_paths:
        if os.path.exists(path):
            with open(path, "r") as file:
                return yaml.safe_load(file)

    return {}  # Return an empty config if no file is found


def load_plugin(plugin_name):
    try:
        plugin = importlib.import_module(f".{plugin_name}", "odin_cli.plugins")

        return plugin
    except (ImportError, AssertionError):
        raise ImportError(
            f"Plugin for {plugin_name} not found or does not conform to the interface."
        )


def load_plugins(subparsers, config):
    package_directory = os.path.dirname(__file__)
    plugins_glob = f"{package_directory}/plugins/*.py"

    plugins = []
    for plugin_path in glob.glob(plugins_glob):
        plugin_name = os.path.basename(plugin_path)[:-3]
        if plugin_name != "__init__":
            plugin = load_plugin(plugin_name)
            plugins.append(plugin)
    return plugins
