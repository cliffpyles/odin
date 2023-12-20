#!/bin/bash

# Define the repository path and installation directory
REPO_PATH="https://github.com/cliffpyles/odin"
INSTALL_DIR="$HOME/.odin"

# Function to check if a command exists
command_exists() {
    command -v "$@" >/dev/null 2>&1
}

echo "Checking for necessary dependencies..."

# Check for Python and pip
if command_exists python && command_exists pip; then
    echo "Python and pip are installed."
else
    echo "Python or pip not found, please install them first."
    exit 1
fi

# Check for Git
if command_exists git; then
    echo "Git is installed."
else
    echo "Git not found, please install it first."
    exit 1
fi

# Clone the repository into the installation directory
echo "Cloning the Odin repository into $INSTALL_DIR..."
git clone $REPO_PATH $INSTALL_DIR

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r $INSTALL_DIR/requirements.txt --user

# Update PATH in the appropriate shell configuration file
update_path() {
    local shell_config="$1"
    if ! grep -q "$INSTALL_DIR" "$shell_config"; then
        echo "Updating PATH in the $shell_config file..."
        echo "export PATH=\"\$PATH:$INSTALL_DIR\"" >> "$shell_config"
    fi
}

# Detect the shell and update the configuration file
update_path "$HOME/.zshrc"
update_path "$HOME/.bashrc"

echo "Installation complete. Please restart your terminal or source your shell configuration file to use Odin."
