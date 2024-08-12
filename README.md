# Nemo Agent

[![PyPI - Version](https://img.shields.io/pypi/v/nemo-agent)](https://pypi.org/project/nemo-agent/)

Nemo Agent is a blazing fast local AI Agent for Python coding

## Features
* Runs blazing fast locally
* Generates Python project structures automatically using Poetry
* Writes Python code based on task descriptions
* Executes development tasks using AI-generated commands
* Utilizes the mistral-nemo language model for intelligent code generation
* Implements best practices in Python development automatically
* Writes and runs tests up to 80%+ test coverage using pytest
* Automatically fixes and styles code using pylint

## Installation
You can install Nemo Agent using pip:

`pip install nemo-agent`

## Usage
After installation, you can use NemoAgent from the command line:

`nemo-agent "Your task description here"`
If you run nemo-agent without any arguments, it will prompt you to enter a task.

## Examples
Create a simple calculator:

`nemo-agent "Create a simple calculator with add, subtract, multiply, and divide functions with tests"`

Generate a web scraper:

`nemo-agent "Build a web scraper to extract headlines from a news website with tests"`

Develop a basic API:

`nemo-agent "Create a Flask API with endpoints for user registration and login with tests"`

## How It Works

Nemo Agent uses the mistral-nemo LLM to interpret your task description.
It generates a project structure and necessary files based on the task.
The AI writes Python code to implement the requested functionality.
Nemo Agent can execute various development tasks like creating virtual environments, installing dependencies, and running tests.

## Requirements
* Python 3.12.4 or higher
* Ollama running mistral-nemo
* Linux with a minimum of an RTX 4090

## Contributing
Contributions to Nemo Agent are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer
Nemo Agent generates code using AI. While it strives for accuracy and best practices, the generated code should be reviewed and tested before being used in a production environment.
