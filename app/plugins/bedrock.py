def process_single_prompt(service_name, prompt, model):
    # Implement Bedrock specific code here
    return f"Bedrock response to: {prompt}"


def process_interactive_chat(service_name, user_input, chat_history, model):
    # Implement Bedrock specific interactive chat code here
    return "Bedrock response to: " + user_input
