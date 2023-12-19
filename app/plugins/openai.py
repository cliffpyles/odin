from openai import OpenAI

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
