# Nemo Agent

[![PyPI - Version](https://img.shields.io/pypi/v/nemo-agent)](https://pypi.org/project/nemo-agent/)

Nemo Agent is a local fast AI Agent Python coding CLI. It creates project structures, writes code, writes tests, runs tests, and performs development tasks based on natural language prompts. Now with support for refactoring existing projects and Poetry integration!

## Features
* Runs completely local and very fast
* Generates Python project structures automatically
* Writes Python code based on task descriptions
* Executes development tasks using AI-generated commands
* Utilizes the Mistral-Nemo language model for intelligent code generation
* Implements best practices in Python development automatically
* Refactors existing Python projects
* Writes and runs tests
* Integrates Poetry for dependency management and virtual environments

## Installation
You can install Nemo Agent using pip:

`pip install nemo-agent`

## Usage
After installation, you can use NemoAgent from the command line:

For creating a new project:
`nemo-agent "Your task description here"`

For refactoring an existing project:
`nemo-agent "Your refactoring task description" --refactor /path/to/existing/project`

If you run nemo-agent without any arguments, it will prompt you to enter a task.

## Examples
Create a simple calculator with Poetry:

`nemo-agent "Create a simple calculator with add, subtract, multiply, and divide functions with tests"`

Generate a web scraper:

`nemo-agent "Build a web scraper to extract headlines from a news website with tests"`

Develop a basic API:

`nemo-agent "Create a Flask API with endpoints for user registration and login with tests"`

Refactor an existing project:

`nemo-agent "Refactor the code to improve performance and add type hints" --refactor /path/to/existing/project`

## How It Works

1. NemoAgent uses the Mistral-Nemo language model to interpret your task description.
2. For new projects:
   - It generates a project structure and necessary files based on the task.
   - The AI writes Python code to implement the requested functionality.
   - It initializes a Poetry project and manages dependencies.
3. For existing projects:
   - It analyzes the current project structure and code.
   - The AI suggests and implements refactoring changes based on the task.
4. NemoAgent can execute various development tasks like creating virtual environments, installing dependencies, and running tests.

## Requirements
* Python 3.12.4 or higher
* Ollama running mistral-nemo
* Linux with a minimum of an RTX 4070 or;
* Mac M2 Pro with 16GB RAM
* Poetry (automatically used for dependency management)

## Contributing
Contributions to Nemo Agent are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer
Nemo Agent generates code using AI. While it strives for accuracy and best practices, the generated code should be reviewed and tested before use in production environments.
