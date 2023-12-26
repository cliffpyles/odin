import json
import re
from datetime import datetime
from openai import OpenAI
import frontmatter
import odin_cli.tools as tools

# Initialize the OpenAI client
client = OpenAI()


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
def append_log(file_path, event_type="INFO", message=""):
    current_timestamp = str(datetime.now())
    event_type = event_type.upper()
    inline_message = message.encode("unicode_escape").decode("utf-8")
    with open(file_path, "a") as log_file:
        log_file.write(f"{current_timestamp} {event_type} {inline_message}\n")


# Function to save a response to a file
def save_response(file_path, content):
    with open(file_path, "w") as file:
        file.write(content)


# Function to send messages and handle responses
def send_messages(messages, thread, template_variables, output_dir):
    # This function is quite long and contains multiple sub-functions and complex logic.
    # It handles the logic of processing messages, sending them to the OpenAI API,
    # processing responses, and saving logs and outputs.
    thread_metadata = thread.get("metadata", {})
    thread_id = thread_metadata.get("id")
    thread_log = thread_metadata.get("log_file")
    append_log(thread_log, "CHAT_STARTED", thread_id)
    append_log(
        thread_log, "CHAT_RECEIVED_TEMPLATE_VARIABLES", json.dumps(template_variables)
    )
    try:
        system_context = thread.get("content", "").strip()
        system_context = process_template(system_context, template_variables)

        append_log(thread_log, "CHAT_SYSTEM_CONTEXT_PROCESSED", system_context)

        current_chat = [{"role": "system", "content": system_context}]

        for message in messages:
            metadata = message.get("metadata", {})
            disabled = metadata.get("disabled", False)
            id = metadata.get("id")
            thread_id = metadata.get("thread_id")
            model = metadata.get("model", "gpt-4")
            temperature = metadata.get("temperature", 0)
            response_handler = metadata.get("response_handler")
            output_file = metadata.get("output_file", f"{thread_id}/{id}.md")
            content = message.get("content", "").strip()
            if disabled:
                append_log(
                    thread_log,
                    "CHAT_MESSAGE_SKIPPED",
                    f"Thread: {thread_id} Message: {id}",
                )
                continue
            append_log(
                thread_log,
                "CHAT_MESSAGE_STARTED",
                f"Thread: {thread_id} Message: {id} Model: {model} Temperature: {temperature} Content: {content}",
            )
            content = process_template(content, template_variables)
            append_log(thread_log, "CHAT_MESSAGE_CONTENT_PROCESSED", content)
            current_chat.append({"role": "user", "content": content})
            print(f"\nMessage:\n\n{content}")

            tool_args = {}
            if response_handler:
                tool_args = {
                    "tools": [tools.tool_schemas.get(response_handler)],
                    "tool_choice": "auto",
                }

            response = client.chat.completions.create(
                max_tokens=None,
                model=model,
                messages=current_chat,
                temperature=temperature,
                **tool_args,
            )

            append_log(
                thread_log,
                "CHAT_MESSAGE_RESPONSE_RECEIVED",
                response.model_dump_json(exclude_unset=True),
            )

            if response_handler:
                print(f"\nExecuting: {response_handler}\n\n---\n")
                response_model = response.model_dump(exclude_unset=True)
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
                    append_log(
                        thread_log, "CHAT_MESSAGE_TOOL_EXECUTED", json.dumps(chat_item)
                    )
            else:
                response_content = response.choices[0].message.content
                print(f"\nResponse:\n\n{response_content}\n\n---\n")
                current_chat.append({"role": "assistant", "content": response_content})
                save_response(f"{output_dir}/{output_file}", response_content)
                append_log(
                    thread_log,
                    "CHAT_MESSAGE_OUTPUT_SAVED",
                    f"{output_dir}/{output_file}",
                )

        append_log(thread_log, "CHAT_COMPLETED", thread_id)
        return response
    except Exception as e:
        error_message = f"Error: {str(e)}"

        append_log(
            thread_log,
            "CHAT_ERRORED",
            f"{thread_id} {error_message}",
        )
        return error_message


# Main function to run the chat process
def run_chat(args, config):
    file_path = args.file_path
    template_variables = args.template_variables
    output = args.output

    chat = open_chat(file_path)
    thread = get_chat_items(chat, type="thread")[0]
    messages = get_chat_items(chat, type="message", sort="order")
    response = send_messages(messages, thread, template_variables, output)


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

    run_parser.set_defaults(func=run_chat)