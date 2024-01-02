import json
import re
from datetime import datetime
import logging
import time
from openai import OpenAI
import frontmatter
import odin_cli.tools as tools


class MessagePrinter:
    def __init__(self, verbosity_level):
        self.verbosity_level = verbosity_level

    def print_header(self, role, message_number, total_messages, model):
        timestamp = datetime.now().strftime("%m-%d-%Y %H:%M:%S")
        role = role.upper()
        progress = f"Message {message_number} of {total_messages}"
        content = f"{role} [{timestamp}] | {progress} [{model}]"
        divider = "▓" * int(((120 - len(content)) / 2) - 2)

        print(f"\n{divider} {content} {divider}\n")

    def print_content(self, message, role=""):
        colors = {
            "info": "\033[94m",
            "assistant": "\033[94m",
            "user": "\033[95m",
            "warning": "\033[93m",
            "error": "\033[91m",
            "default": "\033[0m",
        }
        if role in colors:
            colored_msg = f"{colors[role]}{message}{colors['default']}"
        else:
            colored_msg = message

        print(colored_msg)

    def print_footer(self, response_time, model, token_metrics):
        content = (
            f"Model: {model} | "
            + f"Duration: {int(response_time)}s | "
            + f"Prompt: {token_metrics['prompt_tokens']} tokens | "
            + f"Completion: {token_metrics['completion_tokens']} tokens"
        )
        divider = "░" * int(((120 - len(content)) / 2) - 2)

        print(f"\n{divider} {content} {divider}\n")


# Initialize logger
logger = logging.getLogger(__name__)

# Initialize the OpenAI client
client = OpenAI()

IMAGE_MODELS = ["dall-e-2", "dall-e-3"]


# Function to execute a tool from the tools module
def execute_tool(tool_call):
    try:
        # Extract function name and arguments from the tool call
        func_name = tool_call["function"]["name"]
        arguments = json.loads(tool_call["function"]["arguments"])

        # Get the function from the tools module
        func = getattr(tools, func_name, None)
        if not func:
            # Raise an error if the function is not found
            raise ValueError(f"Function '{func_name}' not found in tools module.")

        # Execute the function with the provided arguments
        return func(**arguments)
    except KeyError as e:
        # Handle missing keys in the tool call object
        raise ValueError(f"Key error in the object structure: {e}")
    except json.JSONDecodeError as e:
        # Handle JSON parsing errors
        raise ValueError(f"Error in parsing arguments: {e}")


# Function to process template variables in a string
def process_template(template, template_variables):
    for variable in template_variables:
        key, value = variable.split("=")
        template = template.replace(f"{{{key}}}", value)
    return template


# Function to open a YAML file and parse its contents
def open_chat(file_path):
    with open(file_path, "r") as file:
        content = file.read()

    # Define regex pattern to extract frontmatter and content
    pattern = r"(---\n(?:.*?:.*?\n)+---)([\s\S]*?)(?=\n---|$)"

    # Find all sections in the file that match the pattern
    matches = re.findall(pattern, content)
    parsed_documents = {}

    # Parse each section and extract its frontmatter and content
    for frontmatter_str, content_str in matches:
        parsed_doc = frontmatter.loads(frontmatter_str + "\n" + content_str)
        doc_id = parsed_doc.metadata.get("id", None)
        if doc_id:
            # Store the parsed document using its ID
            parsed_documents[doc_id] = {
                "metadata": parsed_doc.metadata,
                "content": parsed_doc.content.strip(),
            }

    return parsed_documents


# Function to filter and sort chat items based on metadata
def get_chat_items(chat, sort=None, **filters):
    items = [
        doc
        for doc in chat.values()
        if all(doc["metadata"].get(key) == value for key, value in filters.items())
    ]

    # Sort the items if a sort key is provided
    if sort:
        items.sort(key=lambda x: x["metadata"].get(sort, float("inf")))

    return items


# Function to append logs to a log file
def log_event(event_type="INFO", message="", context=None):
    # Map event_type to logging levels
    event_type = event_type.upper()
    # inline_message = message.encode("unicode_escape").decode("utf-8")

    log_level = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }.get(event_type, logging.INFO)
    log_message = {
        "event_type": event_type,
        "message": message,
        "context": context,
    }

    # Log the message at the appropriate level
    logger.log(log_level, json.dumps(log_message))


# Function to save a response to a file
def save_response(file_path, content):
    with open(file_path, "w") as file:
        file.write(content)


# Function to send messages and handle responses
def send_messages(messages, thread, template_variables, output_dir, printer):
    thread_metadata = thread.get("metadata", {})
    thread_id = thread_metadata.get("id")
    log_event(
        message="chat started",
        context={
            "thread_id": thread_id,
        },
    )
    log_event(
        message="received template variables",
        context={"thread_id": thread_id, "template_variables": template_variables},
    )
    try:
        system_context = thread.get("content", "").strip()
        system_context = process_template(system_context, template_variables)

        log_event(
            message="system context processed",
            context={"thread_id": thread_id, "system_context": system_context},
        )
        chat_start_time = time.time()
        current_chat = [{"role": "system", "content": system_context}]
        total_messages = len(messages)
        for index, message in enumerate(messages):
            message_start_time = time.time()
            metadata = message.get("metadata", {})
            disabled = metadata.get("disabled", False)
            id = metadata.get("id")
            thread_id = metadata.get("thread_id")
            model = metadata.get("model", "gpt-4")
            max_tokens = metadata.get("max_tokens", None)
            temperature = metadata.get("temperature", 0)
            response_handler = metadata.get("response_handler")
            output_file = metadata.get("output_file", f"{thread_id}/{id}.md")
            content = message.get("content", "").strip()

            if disabled:
                log_event(
                    message="message skipped",
                    context={"thread_id": thread_id, "message_id": id},
                )
                continue
            log_event(
                message="message started",
                context={
                    "thread_id": thread_id,
                    "message_id": id,
                    "model": model,
                    "temperature": temperature,
                    "content": content,
                },
            )
            content = process_template(content, template_variables)
            log_event(
                message="message content processed",
                context={
                    "thread_id": thread_id,
                    "message_id": id,
                    "content": content,
                },
            )
            current_chat.append({"role": "user", "content": content})
            printer.print_header(
                role="user",
                message_number=index + 1,
                total_messages=total_messages,
                model=model,
            )
            printer.print_content(content, role="user")

            tool_args = {}
            if response_handler:
                tool_args = {
                    "tools": [tools.tool_schemas.get(response_handler)],
                    "tool_choice": "auto",
                }

            response = client.chat.completions.create(
                model=model,
                messages=current_chat,
                temperature=temperature,
                max_tokens=max_tokens,
                **tool_args,
            )
            response_model = response.model_dump(exclude_unset=True)

            log_event(
                message="message response received",
                context={
                    "thread_id": thread_id,
                    "message_id": id,
                    "model": model,
                    "temperature": temperature,
                    "content": content,
                    "response": response_model,
                },
            )

            if response_handler:
                tool_calls = response_model["choices"][0]["message"]["tool_calls"]
                for tool_call in tool_calls:
                    tool_response = execute_tool(tool_call)
                    chat_item = {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": tool_call["function"]["name"],
                        "content": tool_response,
                    }
                    current_chat.append(chat_item)
                    log_event(
                        message="message tool executed",
                        context={
                            "thread_id": thread_id,
                            "message_id": id,
                            "tool": chat_item,
                        },
                    )
                message_end_time = time.time()
                response_time = message_end_time - message_start_time
                token_metrics = response_model["usage"]
                printer.print_footer(response_time, model, token_metrics)
            else:
                response_content = response.choices[0].message.content
                current_chat.append({"role": "assistant", "content": response_content})
                save_response(f"{output_dir}/{output_file}", response_content)
                log_event(
                    message="message output saved",
                    context={
                        "thread_id": thread_id,
                        "message_id": id,
                        "output_path": f"{output_dir}/{output_file}",
                    },
                )
                message_end_time = time.time()
                response_time = message_end_time - message_start_time
                token_metrics = response_model["usage"]
                printer.print_content(response_content, role="assistant")
                printer.print_footer(response_time, model, token_metrics)

        chat_end_time = time.time()
        log_event(
            message="chat completed",
            context={"thread_id": thread_id},
        )
        print(f"\nTotal Duration: {int(chat_end_time - chat_start_time)}s\n")
        return response
    except Exception as e:
        error_message = f"Error: {str(e)}"
        print(error_message)
        log_event(
            event_type="ERROR",
            message="chat errored",
            context={"thread_id": thread_id, "error_message": error_message},
        )

        return error_message


# Main function to run the chat process
def run_chat(args, config):
    file_path = args.file_path
    template_variables = args.template_variables
    output = args.output
    log_level = args.log_level.upper() if args.log_level else "INFO"
    log_file = args.log_file
    verbosity_level = (
        "silent" if args.silent else ("verbose" if args.verbose else "standard")
    )

    logging.basicConfig(
        level=log_level,
        filename=log_file,
        filemode="a",
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    printer = MessagePrinter(verbosity_level)
    chat = open_chat(file_path)
    thread = get_chat_items(chat, type="thread")[0]
    messages = get_chat_items(chat, type="message", sort="order")
    response = send_messages(messages, thread, template_variables, output, printer)


# Function to set up the 'run' command in a CLI environment
def setup_run_command(subparsers, config, plugins):
    run_parser = subparsers.add_parser("run", help="Execute a specification")
    run_parser.add_argument("file_path", nargs="?", help="File path for chat to invoke")
    run_parser.add_argument(
        "template_variables", nargs="*", help="Template variable values"
    )
    run_parser.add_argument(
        "--output", default=".", help="Directory path for the output"
    )
    run_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output in the standard output.",
    )
    run_parser.add_argument(
        "--silent",
        action="store_true",
        help="Disable all output to the standard output.",
    )

    run_parser.set_defaults(func=run_chat)
