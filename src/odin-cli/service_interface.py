def process_single_prompt(service_name, prompt, model):
    raise NotImplementedError


def process_interactive_chat(service_name, user_input, chat_history, model):
    raise NotImplementedError


def register_cli_commands(cli_group):
    """Function to register CLI commands for the plugin."""
    raise NotImplementedError
