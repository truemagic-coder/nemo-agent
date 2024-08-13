# Nemo Agent

[![PyPI - Version](https://img.shields.io/pypi/v/nemo-agent)](https://pypi.org/project/nemo-agent/)

Nemo Agent is a blazing fast local AI Agent for Python coding

## Features
* Runs blazing fast locally
* Generates Python project structures automatically using poetry
* Writes Python code based on task descriptions
* Executes development tasks using AI-generated commands
* Utilizes the `mistral-nemo` language model for intelligent code generation
* Implements best practices in Python development automatically
* Writes and runs passing tests up to 80%+ test coverage using pytest
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

Generate a fizzbuzz program:

`nemo-agent "Create a fizzbuzz script"`

## Custom Ollama Model
* Nemo Agent allows running any Ollama model instead of `mistral-nemo`.
* Tested on RunPod RTX 4090 x1 (all fail or are too slow): 
    * gemma2:27b
    * codestral:22b
    * deepseek-coder-v2:16b
    * phi3:14b
    * command-r:35b
    * nous-hermes2:34b
    * nous-hermes2-mixtral:8x7b

`nemo-agent --model other_model_name "Create a fizzbuzz script"`

## Cloud Install
* RunPod is the recommended hosting provider for RTX 4090 compute - [setup link](https://docs.runpod.io/tutorials/pods/run-ollama)

## Limitations

* Currently due to `mistral-nemo` issues cannot codegen for APIs like Flask and FastAPI.
* Due to `mistral-nemo` model IQ limits keeping to simple tasks is required.

## How It Works

Nemo Agent uses the mistral-nemo LLM to interpret your task description.
It generates a project structure and necessary files based on the task.
The AI writes Python code to implement the requested functionality.
Nemo Agent can execute various development tasks like creating virtual environments, installing dependencies, and running tests.

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
