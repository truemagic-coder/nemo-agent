# Nemo Agent

[![PyPI - Version](https://img.shields.io/pypi/v/nemo-agent)](https://pypi.org/project/nemo-agent/)

[![Nemo Agent](https://cdn.cometheart.com/nemo-agent-2.png)](https://cdn.cometheart.com/nemo-agent.mp4)

Nemo Agent is an expert Python software developer that can build fully-tested Python programs for your task.

## Features
* Runs blazing fast locally on an RTX 4070 or greater
* Generates Python project structures automatically using `poetry`
* Writes Python code based on task descriptions
* Executes development tasks using AI-generated commands
* Utilizes the `mistral-nemo` language model for intelligent code generation
* Implements best practices in Python development automatically
* Writes and runs passing tests up to 80%+ test coverage using `pytest`
* Automatically fixes and styles code using `pylint`
* Utilizes `git` to commit and track changes

## Coding Ability
* Can solve some leetcode hards on some runs in about 30 seconds on an RTX 4090
* Can apply time complexity constraints in task requirements

## Demo Video

[Watch on Youtube](https://www.youtube.com/watch?v=i2Au5F4anME)

## Local Install

### Requirements
* Python 3.9 or higher
* git
* curl
* Ollama running `mistral-nemo`
* Ubuntu (22.04 or 24.04) with a minimum of an RTX 4070

### Requirements Installation
* Python, curl, git are pre-installed on Ubuntu
* Ollama install instructions:
    * `curl -fsSL https://ollama.com/install.sh | sh`
    * `ollama pull mistral-nemo`
* `nemo-agent` install:
    * `pip install nemo-agent`
* You are ready to use `nemo-agent`

## Cloud Install

### Requirements
* [RunPod](https://runpod.io) account setup with your SSH and billing information

### RunPod Setup
* Make sure you have setup your SSH keys
* Select a `4090` pod
* Select the `RunPod Pytorch 2.1.1` template
* Edit the template:
    * Set `Container Disk` to 60 GB
    * Set `Expose HTTP Ports` to `8888, 11434`
    * Add `environment variables` with `OLLAMA_HOST` key and `0.0.0.0` value
* Deploy your pod
* After deploying then login via SSH
* Run on the pod: `curl -fsSL https://ollama.com/install.sh | sh && ollama serve`
* Run on the pod: `ollama pull mistral-nemo`
* Run on the pod: `pip install nemo-agent`
* You are ready to use `nemo-agent`

## Usage
After installation, you can use Nemo Agent from the command line:

`nemo-agent "Your task description here"`
If you run nemo-agent without any arguments, it will prompt you to enter a task.

## Examples
Create a simple calculator:

`nemo-agent "Create a simple calculator"`

Generate a fizzbuzz program:

`nemo-agent "Create a fizzbuzz script"`

## Limitations

* LLM codegen issues mean that web APIs like Flask and FastAPI are not supported.
* Due to the LLM getting confused with paths and files - writing 1 code and 1 test file is only supported.

## Notes
* Tested all local models that can run on an RTX 4090 on Ollama other than `mistral-nemo` and none can be prompted to complete the task.
* Tested with Mistral Nemo hosted API - the local/API models are not the same and the API version is very buggy with prompting

## Contributing
Contributions to Nemo Agent are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer
Nemo Agent generates code using AI. While it strives for accuracy and best practices, the generated code should be reviewed and tested before being used in a production environment.
