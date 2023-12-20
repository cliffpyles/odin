# Odin CLI

Odin is a command-line interface (CLI) application designed to interact with various AI services, including OpenAI and Amazon Bedrock. It emphasizes simplicity, modularity, and extensibility.

## Disclaimer

Odin is in active development. Features and functionalities may change, and the tool is not yet fully stable. Users should be aware of potential risks in its use.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Basic Commands](#basic-commands)
  - [Detailed Usage Examples](#detailed-usage-examples)
  - [Passing Variables to Prompts](#passing-variables-to-prompts)
- [Command Arguments and Options](#command-arguments-and-options)
- [License](#license)
- [Support](#support)

## Features

- **Single Prompt Interactions**: Provide single prompts to AI services via text, URL, file path, or S3 path.
- **Interactive Chats**: Engage and persist interactive chats with AI services.
- **Persistent Conversations**: Save and resume chat histories.
- **Modular Architecture**: Integration with more AI services is straightforward.

## Installation

To install Odin:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/cliffpyles/odin/HEAD/dev_install.sh)"
```

### Prerequisites

- Python 3.x
- pip (Python package manager)
- Git

## Usage

### Basic Commands

After installation, use the `ask` binary to interact with AI services.

- Query Bedrock:
  ```bash
  ask bedrock "Tell me a joke"
  ```
- Query OpenAI:
  ```bash
  ask openai "Tell me a fact"
  ```

### Detailed Usage Examples

#### Interacting with Bedrock
- **Simple Prompt**:
  ```bash
  ask bedrock "Tell me a joke"
  ```
- **File Input**:
  ```bash
  ask bedrock /path/to/my_query.txt
  ```
- **URL Input**:
  ```bash
  ask bedrock https://example.com/my_query.txt
  ```
- **Interactive Chat**:
  ```bash
  ask bedrock --chat my_chat_history.json
  ```

#### Interacting with OpenAI
- **Simple Query**:
  ```bash
  ask openai "Tell me a fact"
  ```
- **Interactive Chat**:
  ```bash
  ask openai --chat session_history.json
  ```

### Passing Variables to Prompts

Odin CLI allows dynamic content generation in prompts using variables.

#### Usage of Variables in Prompts

- **Single Variable**:
  ```bash
  ask openai "Translate '{text}' to French" text="Hello, world"
  ```
- **Multiple Variables**:
  ```bash
  ask bedrock "What is the weather like in {city} on {date}?" city="Paris" date="2023-07-16"
  ```

#### Formatting and Constraints

- Enclose variables in `{}`.
- Replace each variable with its value using `variable_name="value"`.
- Variables can be repeated in a prompt.
- Avoid spaces in variable assignments.

## Command Arguments and Options

| Argument/Option   | Description                                           | Example                                                 |
|-------------------|-------------------------------------------------------|---------------------------------------------------------|
| `prompt`          | Text, file path, URL, or S3 path for the prompt.      | `ask openai "Translate '{text}' to French" text="Hello"`|
| `--model`         | Specifies the AI model.                               | `ask openai --model="gpt-4" "What is AI?"`              |
| `--chat`          | Initiates interactive chat and specifies history file.| `ask bedrock --chat chat_history.json`                  |
| `/path/to/file`   | Path to a text file with the prompt.                  | `ask openai /path/to/fact_request.txt`                  |
| `s3://bucket/file`| S3 path to a file with the prompt.                    | `ask openai s3://mybucket/fact_request.txt`             |
| `https://url`     | URL to a text file with the prompt.                   | `ask openai https://example.com/fact_request.txt`       |

## License

Odin is licensed under the [MIT License](LICENSE). See the LICENSE file for details.

## Support

For support, questions, or feedback, [open an issue](https://github.com/cliffpyles/odin/issues).
