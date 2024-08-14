# Nemo Agent

[![PyPI - Version](https://img.shields.io/pypi/v/nemo-agent)](https://pypi.org/project/nemo-agent/)

[![Nemo Agent](https://cdn.cometheart.com/nemo-agent.png)](https://cdn.cometheart.com/nemo-agent.mp4)

Nemo Agent is a blazing fast local AI Agent for Python coding

## Features
* Runs blazing fast locally on an RTX 4070 or greater
* Generates Python project structures automatically using `poetry`
* Writes Python code based on task descriptions
* Executes development tasks using AI-generated commands
* Utilizes the `mistral-nemo` language model for intelligent code generation
* Implements best practices in Python development automatically
* Writes and runs passing tests up to 80%+ test coverage using `pytest`
* Automatically fixes and styles code using `pylint`

## Coding Ability
* Can solve a leetcode hard with a set time complexity constraint in less than a minute with full tests on an RTX 4090

## Installation
You can install Nemo Agent using pip:

`pip install nemo-agent`

## Usage
After installation, you can use NemoAgent from the command line:

`nemo-agent "Your task description here"`
If you run nemo-agent without any arguments, it will prompt you to enter a task.

## Examples
Create a simple calculator:

`nemo-agent "Create a simple calculator"`

Generate a fizzbuzz program:

`nemo-agent "Create a fizzbuzz script"`

## Cloud-Ready
* RunPod is the recommended hosting provider for RTX 4090 compute - [setup link](https://docs.runpod.io/tutorials/pods/run-ollama)

## Limitations

* LLM codegen issues mean that web APIs like Flask and FastAPI are not supported.

## How It Works

Nemo Agent leverages `mistral-nemo`, `Ollama`, `phidata`, `poetry`, `pytest`, `pylint`, and other libraries to build a complete working solution for your task.

## Requirements
* Python 3.9 or higher
* Ollama running `mistral-nemo`
* Linux with a minimum of an RTX 4070

## Contributing
Contributions to Nemo Agent are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer
Nemo Agent generates code using AI. While it strives for accuracy and best practices, the generated code should be reviewed and tested before being used in a production environment.
