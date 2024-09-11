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
* Utilizes the `Ollama`, `OpenAI`, or `Claude` language models for intelligent code generation
* Implements best practices in Python development automatically
* Writes and runs passing tests using `pytest` up to 80%+ test coverage 
* Automatically fixes and styles code using `pylint` up to 7+/10
* Calculates and improves the complexity score using `complexipy` to be under 15
* Auto-formats the code with `autopep8`
* Shows the token count used for the responses

## Community
* Join our community - [Nemo Agent Telegram Group](https://t.me/+f-6nu2mUpgtiOGUx)

## Coding Ability
* `leetcode` hards (app works - tests pass)
* `fastapi` or `flask` APIs (app works - tests pass)
* `flask` web apps (app works - tests pass)
* `streamlit` apps (app works - tests fail)  
* `tkinter` apps (app works - tests fail)
* Note: `OpenAI` or `Claude` succeed more often the `mistral-nemo` in their runs
* Note: Not all runs will be successful

## Install 

### OpenAI or Claude Install

#### Requirements
* Python 3.9 or higher
* OpenAI or Claude API KEY
* Mac or Linux

#### Requirements Installation
* Install OpenAI or Claude API KEY for `zsh` shell
    * `echo 'export OPENAI_API_KEY="YOUR_API_KEY"' >> ~/.zshrc` or
    * `echo 'export ANTHROPIC_API_KEY="YOUR_API_KEY"' >> ~/.zshrc`
* `pip install nemo-agent`
* You are ready to use `nemo-agent`

### OR

### Mistral-Nemo Install

#### Requirements
* Python 3.9 or higher
* Ollama running `mistral-nemo`
* Linux with minimum specs of Ubuntu 24.04 with RTX 4070
  
#### Requirements Installation
* Ollama install instructions:
    * `curl -fsSL https://ollama.com/install.sh | sh`
    * `ollama pull mistral-nemo`
* `pip install nemo-agent`
* You are ready to use `nemo-agent`

## Usage

### Prompt
* `mistral-nemo`: `nemo-agent "create a fizzbuzz script"`
* `openai`: `nemo-agent "create a fizzbuzz script" --provider openai`
* `claude`: `nemo-agent "create a fizzbuzz script" --provider claude`

### Markdown File
* `mistral-nemo`: `nemo-agent --file example.md`
* `openai`: `nemo-agent --file example.md --provider openai`
* `claude`: `nemo-agent --file example.md --provider claude`

## Model overrides

* You can pass the `--model` flag to override the default model for the provider.
* The default model for `ollama` is `mistral-nemo`
* The default model for `openai` is `gpt-4o-2024-08-06`
* The default model for `claude` is `claude-3-5-sonnet-20240620`

## Contributing
Contributions to Nemo Agent are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer
Nemo Agent generates code using an LLM. Every run is different as the LLM generated code is different. While it strives for accuracy and best practices, the generated code should be reviewed and tested before being used in a production environment.
