from pathlib import Path
import json


# Function to save content to a file
def save_file(path: str, content: str):
    file_path = Path(path)

    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open("w") as f:
        f.write(content)

    return json.dumps({"path": path, "content": content})


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
    }
}
