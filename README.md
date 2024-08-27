# Nemo Agent

[![PyPI - Version](https://img.shields.io/pypi/v/nemo-agent)](https://pypi.org/project/nemo-agent/)

[![Nemo Agent](https://cdn.cometheart.com/nemo-agent-2.png)](https://cdn.cometheart.com/nemo-agent.mp4)

## Nemo Agent is your Python AI Coder!


https://github.com/user-attachments/assets/51cf6ad1-196c-44ab-99ba-0035365f1bbd


## Features
* Runs blazing fast
* Generates Python project structures automatically using `poetry`
* Writes Python code based on task descriptions
* Executes development tasks using AI-generated commands
* Utilizes the `mistral-nemo`, `OpenAI`, or `Claude` language models for intelligent code generation
* Implements best practices in Python development automatically
* Writes and runs passing tests using `pytest` up to 80%+ test coverage 
* Automatically fixes and styles code using `pylint` up to 8+/10
* Calculates and improves the complexity score using `complexipy` to be under 15
* Auto-formats to the code with `autopep8`
* Utilizes `git` to commit and track changes

## Coding Ability
* Can solve leetcode hards in 30 seconds using larger models and sometimes with `mistral-nemo`
* Can apply time complexity constraints in task requirements

## Install 

### Claude or OpenAI Local Install

#### Requirements
* Python 3.9 or higher
* git
* OpenAI or Claude API Key
* Linux or Mac

#### Requirements Installation
* Install Claude API Key for `zsh` shell
    * echo 'export ANTHROPIC_API_KEY="YOUR_API_KEY"' >> ~/.zshrc
* OR: Install OpenAI API Key for `zsh` shell
    * echo 'export OPENAI_API_KEY="YOUR_API_KEY"' >> ~/.zshrc
* `pip install nemo-agent`
* You are ready to use `nemo-agent`

### OR

### Mistral-Nemo Local Install

#### Requirements
* Python 3.9 or higher
* git
* curl
* Ollama running `mistral-nemo`
* Ubuntu (22.04 or 24.04) with a minimum of an RTX 4070

#### Requirements Installation
* Python, curl, git are pre-installed on Ubuntu
* Ollama install instructions:
    * `curl -fsSL https://ollama.com/install.sh | sh`
    * `ollama pull mistral-nemo`
* `pip install nemo-agent`
* You are ready to use `nemo-agent`

### OR

### Mistral-Nemo Cloud Install

#### Requirements
* [RunPod](https://runpod.io) account setup with your SSH and billing information

#### RunPod Setup
* Make sure you have setup your SSH keys
* Select a `4090` pod
* Select the `RunPod Pytorch 2.1.1` template
* Edit the template:
    * Set `Container Disk` to 60 GB
    * Set `Expose HTTP Ports` to `8888, 11434`
    * Add `environment variables` with `OLLAMA_HOST` key and `0.0.0.0` value
* Deploy your pod
* After deploying then login via SSH
* Run on the pod: `(curl -fsSL https://ollama.com/install.sh | sh && ollama serve > ollama.log 2>&1) &` and then press CTRL+C to exit
* Run on the pod: `ollama pull mistral-nemo`
* Run on the pod: `pip install nemo-agent`
* You are ready to use `nemo-agent`

## Usage

* `mistral-nemo`: `nemo-agent "create a fizzbuzz script"`
* `openai`: `nemo-agent "create a fizzbuzz script" --provider openai`
* `claude`: `nemo-agent "create a fizzbuzz script" --provider claude`

## Model overrides

* You can pass the `--model` flag to override the default model for the provider.
* The default model for `openai` is `gpt-4o-2024-08-06`
* The default model for `claude` is `claude-3-5-sonnet-20240620`
* The default model for `ollama` is `mistral-nemo`

## Contributing
Contributions to Nemo Agent are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer
Nemo Agent generates code using AI. While it strives for accuracy and best practices, the generated code should be reviewed and tested before being used in a production environment.
