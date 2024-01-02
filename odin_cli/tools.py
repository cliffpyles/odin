from openai import OpenAI
from pathlib import Path
import json
import requests

# Initialize the OpenAI client
client = OpenAI()


# Function to save content to a file
def save_file(path: str, content: str):
    file_path = Path(path)

    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open("w") as f:
        f.write(content)

    return json.dumps({"path": path, "content": content})


def generate_image(path: str, prompt: str):
    file_path = Path(path)

    file_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\npath: {path}\n")
    print(f"\nprompt: {prompt}\n")
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        style="vivid",
        n=1,
    )

    image_url = response.data[0].url
    image_response = requests.get(image_url)
    image_response.raise_for_status()

    # Write the image content to the file
    with file_path.open("wb") as f:
        f.write(image_response.content)

    return json.dumps({"path": path, "image_url": image_url, "prompt": prompt})


tool_schemas = {
    "save_file": {
        "type": "function",
        "function": {
            "name": "save_file",
            "description": "Saves a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Filepath of the file"},
                    "content": {"type": "string", "description": "Content of the file"},
                },
                "required": ["path", "content"],
            },
        },
    },
    "generate_image": {
        "type": "function",
        "function": {
            "name": "generate_image",
            "description": "Generates an image",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Filepath to save the image",
                    },
                    "prompt": {
                        "type": "string",
                        "description": "Prompt to use for creating the image",
                    },
                },
                "required": ["path", "prompt"],
            },
        },
    },
}
