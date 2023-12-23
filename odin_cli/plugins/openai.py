import textwrap
from openai import OpenAI
from odin_cli.utils import (
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


def openai_command(args):
    prompt = args.prompt
    model = args.model
    chat = args.chat
    template_args = args.template_args

    if chat:
        initial_prompt = None
        if prompt:
            initial_prompt = read_content_from_source(prompt)
            initial_prompt = process_template_arguments(initial_prompt, template_args)

        response = handle_interactive_chat("openai", chat, initial_prompt, model)
    else:
        prompt = read_content_from_source(read_stdin_if_empty(prompt))
        prompt = process_template_arguments(prompt, template_args)
        response = handle_single_prompt("openai", prompt, model)

    print(response)


def register_argparse_commands(subparsers):
    parser_openai = subparsers.add_parser("openai", help="Interact with OpenAI")
    parser_openai.add_argument("prompt", nargs="?", help="Prompt for the command")
    parser_openai.add_argument("template_args", nargs="*", help="Template arguments")
    parser_openai.add_argument("--model", default="gpt-4", help="Specify the model")
    parser_openai.add_argument("--chat", help="Filename of the chat session")
    parser_openai.set_defaults(func=openai_command)