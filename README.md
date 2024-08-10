# NemoAgent

[![PyPI - Version](https://img.shields.io/pypi/v/nemo-agent)](https://pypi.org/project/nemo-agent/)

NemoAgent is an AI Agent for Python codegen using the Mistral-Nemo Ollama framework. It creates project structures, writes code, writes tests, runs tests, and performs development tasks based on natural language prompts.

## Features
* Runs completely local
* Generate Python project structures automatically
* Write Python code based on task descriptions
* Execute development tasks using AI-generated commands
* Utilize the Mistral-Nemo language model for intelligent code generation and testing
* Implement best practices in Python development automatically

## Installation
You can install NemoAgent using pip:

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

NemoAgent uses the Mistral-Nemo language model to interpret your task description.
It generates a project structure and necessary files based on the task.
The AI writes Python code to implement the requested functionality.
NemoAgent can execute various development tasks like creating virtual environments, installing dependencies, and running tests.

## Requirements
* Python 3.12.4 or higher
* Ollama running mistral-nemo
* Linux
* Minimum of an RTX 4070

## Contributing
Contributions to NemoAgent are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer
NemoAgent generates code using AI. While it strives for accuracy and best practices, the generated code should be reviewed and tested before use in production environments.
