# Nemo Agent

[![PyPI - Version](https://img.shields.io/pypi/v/nemo-agent)](https://pypi.org/project/nemo-agent/)

Nemo Agent is a blazing fast local AI Agent for Python coding.

## Features
* Runs completely local and very fast
* Generates Python project structures automatically
* Writes Python code based on task descriptions
* Executes development tasks using AI-generated commands
* Utilizes the Mistral-Nemo language model for intelligent code generation
* Implements best practices in Python development automatically
* Writes and runs tests

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

Nemo Agent uses the Mistral-Nemo language model to interpret your task description.
It generates a project structure and necessary files based on the task.
The AI writes Python code to implement the requested functionality.
Nemo Agent can execute various development tasks like creating virtual environments, installing dependencies, and running tests.

## Requirements
* Python 3.12.4 or higher
* Ollama running mistral-nemo
* Linux with a minimum of an RTX 4070 or;
* Mac with a minimum of an M2 Pro with 16GB RAM

## Contributing
Contributions to Nemo Agent are welcome! Please feel free to submit a Pull Request.

## Roadmap
* Support current folder structure of projects for refactoring []
* Support poetry []
* Get all files in a folder recursive and put them into context for analysis []
* Conversational interface with history [] 

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer
Nemo Agent generates code using AI. While it strives for accuracy and best practices, the generated code should be reviewed and tested before use in production environments.
