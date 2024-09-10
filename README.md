# Nemo Agent

[![PyPI - Version](https://img.shields.io/pypi/v/nemo-agent)](https://pypi.org/project/nemo-agent/)

[![Nemo Agent](https://cdn.cometheart.com/nemo-agent-2.png)](https://cdn.cometheart.com/nemo-agent.mp4)

## Nemo Agent is your Python AI Coder!


https://github.com/user-attachments/assets/51cf6ad1-196c-44ab-99ba-0035365f1bbd


## Features
* Runs blazing fast
* Generates Python project structures automatically using `uv`
* Writes Python code based on task descriptions
* Executes development tasks using AI-generated commands
* Utilizes `Ollama` or `OpenAI` language models for intelligent code generation
* Implements best practices in Python development automatically
* Writes and runs passing tests using `pytest` up to 80%+ test coverage 
* Automatically fixes and styles code using `pylint` up to 7+/10
* Calculates and improves the complexity score using `complexipy` to be under 15
* Auto-formats the code with `autopep8`

## Community
* Join our community - [Nemo Agent Telegram Group](https://t.me/+f-6nu2mUpgtiOGUx)

## Coding Ability
* `leetcode` hards (app works - tests pass)
* `fastapi` or `flask` APIs (app works - tests pass)
* `flask` web apps (app works - tests pass)
* `streamlit` apps (app works - tests fail)  
* `tkinter` apps (app works - tests fail)
* Note: `OpenAI` succeeds more often the `Ollama` in their runs
* Note: Not all runs will be successful

## Install 

### OpenAI Install

#### Requirements
* Python 3.9 or higher
* OpenAI API KEY
* Mac or Linux

#### Requirements Installation
* Install OpenAI API KEY for `zsh` shell
    * `echo 'export OPENAI_API_KEY="YOUR_API_KEY"' >> ~/.zshrc`
* `pip install nemo-agent`
* You are ready to use `nemo-agent`

### OR

### Ollama Install

#### Requirements
* Python 3.9 or higher
* Ollama running `yi-coder`
* Linux with minimum specs of Ubuntu 24.04 with RTX 4070 or;
* Mac with M2 Pro with 16GB
  
#### Requirements Installation
* Ollama install instructions:
    * `curl -fsSL https://ollama.com/install.sh | sh`
    * `ollama pull yi-coder`
* `pip install nemo-agent`
* You are ready to use `nemo-agent`

## Usage

### Prompt
* `ollama`: `nemo-agent "create a fizzbuzz script"`
* `openai`: `nemo-agent "create a fizzbuzz script" --provider openai`

### Markdown File
* `ollama`: `nemo-agent --file example.md`
* `openai`: `nemo-agent --file example.md --provider openai`

## Model overrides

* You can pass the `--model` flag to override the default model for the provider.
* The default model for `openai` is `gpt-4o-2024-08-06`
* The default model for `ollama` is `yi-coder`

## Contributing
Contributions to Nemo Agent are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer
Nemo Agent generates code using an LLM. Every run is different as the LLM generated code is different. While it strives for accuracy and best practices, the generated code should be reviewed and tested before being used in a production environment.
