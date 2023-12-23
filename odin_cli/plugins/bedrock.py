import json
import boto3
from odin_cli.utils import (
    read_content_from_source,
    process_template_arguments,
    handle_interactive_chat,
    handle_single_prompt,
    read_stdin_if_empty,
)

client = boto3.client("bedrock-runtime")


def process_single_prompt(service_name, prompt, model="anthropic.claude-v2"):
    """Process a single prompt using Bedrock."""
    try:
        response = client.invoke_model(
            modelId=model,  # Model name specified in the CLI command
            contentType="application/json",
            body=json.dumps({"prompt": prompt}),
        )
        return response["body"].read().decode()
    except Exception as e:
        return f"Error: {str(e)}"


def process_interactive_chat(
    service_name, user_input, chat_history, model="anthropic.claude-v2"
):
    """Process interactive chat using Bedrock."""
    try:
        chat_payload = {"user_input": user_input, "chat_history": chat_history}
        response = client.invoke_model(
            modelId=model,
            contentType="application/json",
            body=json.dumps(chat_payload),
        )
        return response["body"].read().decode()
    except Exception as e:
        return f"Error: {str(e)}"


def bedrock_command(args, config):
    prompt = args.prompt
    model = args.model
    chat = args.chat
    template_args = args.template_args

    if chat:
        initial_prompt = None
        if prompt:
            initial_prompt = read_content_from_source(prompt)
            initial_prompt = process_template_arguments(initial_prompt, template_args)

        response = handle_interactive_chat("bedrock", chat, initial_prompt, model)
    else:
        prompt = read_content_from_source(read_stdin_if_empty(prompt))
        prompt = process_template_arguments(prompt, template_args)
        response = handle_single_prompt("bedrock", prompt, model)

    print(response)


def register_ask_args(subparsers, config):
    # set default values for arguments
    default_model = config.get("bedrock", {}).get("model", "anthropic.claude-v2")

    # register arguments
    parser_bedrock = subparsers.add_parser(
        "bedrock", help="Interact with Amazon Bedrock"
    )
    parser_bedrock.add_argument("prompt", nargs="?", help="Prompt for the command")
    parser_bedrock.add_argument("template_args", nargs="*", help="Template arguments")
    parser_bedrock.add_argument(
        "--model", default=default_model, help="Specify the model"
    )
    parser_bedrock.add_argument("--chat", help="Filename of the chat session")
    parser_bedrock.set_defaults(func=bedrock_command)
