from openai import OpenAI
from odin_cli.utils import (
    read_content_from_source,
    process_template_arguments,
    handle_interactive_chat,
    handle_single_prompt,
    read_stdin_if_piped,
)
import json

client = OpenAI()


def process_single_prompt(service_name, prompt, model="gpt-4"):
    """Process a single prompt using OpenAI and log the request and response."""
    log_entry = {"service_name": service_name, "model": model, "prompt": prompt}

    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ]
        max_tokens = None
        temperature = 0
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        log_entry["response"] = response.choices[0].message.content
    except Exception as e:
        error_message = f"Error: {str(e)}"
        log_entry["response"] = error_message
        return error_message

    # Append log entry to file
    with open(f"{service_name}_log.json", "a") as log_file:
        log_file.write(json.dumps(log_entry) + "\n")

    return log_entry["response"]


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


def openai_command(args, config):
    prompt = args.prompt
    model = args.model
    chat = args.chat
    piped = args.piped
    pipe_key = args.pipe_key
    template_args = args.template_args

    if chat:
        initial_prompt = None
        if prompt:
            initial_prompt = read_content_from_source(prompt)
            initial_prompt = process_template_arguments(initial_prompt, template_args)

        response = handle_interactive_chat("openai", chat, initial_prompt, model)
    else:
        prompt = read_content_from_source(read_stdin_if_piped(prompt, piped, pipe_key))
        prompt = process_template_arguments(prompt, template_args)
        response = handle_single_prompt("openai", prompt, model)

    print(response)


def register_ask_args(subparsers, config):
    # set default values for arguments
    default_model = config.get("openai", {}).get("model", "gpt-4")

    # register arguments
    parser_openai = subparsers.add_parser("openai", help="Interact with OpenAI")
    parser_openai.add_argument("prompt", nargs="?", help="Prompt for the command")
    parser_openai.add_argument("template_args", nargs="*", help="Template arguments")
    parser_openai.add_argument(
        "--model", default=default_model, help="Specify the model"
    )
    parser_openai.add_argument("--chat", help="Filename of the chat session")
    parser_openai.add_argument(
        "--piped",
        action="store_true",
        help="Specifies the prompt is receiving input from a piped command",
    )
    parser_openai.add_argument(
        "--pipe-key",
        default="",
        help="Specifies the prompt is receiving input from a piped command",
    )
    parser_openai.set_defaults(func=openai_command)
