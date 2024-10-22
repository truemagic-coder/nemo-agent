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
* Utilizes the `mistral-nemo`, `OpenAI`, or `Claude` language models for intelligent code generation
* Ability to import reference documents to guide the task implementation
* Allows importing existing code projects in multiple languages to serve as a reference for the task
* Enables the importation of csv data files to populate databases or graphs
* Implements best practices in Python development automatically
* Writes and runs passing tests using `pytest` up to 80%+ test coverage 
* Automatically fixes and styles code using `pylint` up to 7+/10
* Calculates and improves the complexity score using `complexipy` to be under 15
* Auto-formats the code with `autopep8`
* Shows the token count used for the responses

## Community
* Join our community - [Nemo Agent Telegram Group](https://t.me/+f-6nu2mUpgtiOGUx)

## Coding Ability
* `leetcode` hards
* `fastapi` or `flask` APIs
* `flask` web apps
* `streamlit` apps
* `tkinter` apps
* `jupyter notebook`
* Note: `OpenAI` > `Claude` > `mistral-nemo` for most coding projects
* Note: Not all runs will be successful with all models

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

### Providers
* `ollama`: `nemo-agent --provider ollama`
* `openai`: `nemo-agent --provider openai`
* `claude`: `nemo-agent --provider claude`

### Import Reference Documentation Into Prompt
* Documentation files must be either: .md (Markdown) or .txt (Text) and be located in a folder
* `nemo-agent --docs example_folder`

### Import Existing Code Projects Into Prompt
* Code files must be either: .py (Python), .php (PHP), .rs (Rust), .js (JavaScript), .ts (TypeScript), .toml (TOML), .json (JSON), .rb (Ruby), or .yaml (YAML) and be located in a folder
* `nemo-agent --code example_folder`

### Import Data Into Prompt
* Data files must be .csv (CSV) and be located in a folder
* `nemo-agent --data example_folder`

### Prompting

#### CLI
* `nemo-agent "create a fizzbuzz script"`

#### OR

#### File Prompt
* Prompt file must be markdown (.md) or text files (.txt)
* `nemo-agent --file example.md` or 
* `nemo-agent --file example.txt`

### Run Generated Program
* `cd generated_project_folder`
* `source .venv/bin/activate`
* `python main.py`

## Default Models 
* `ollama` is `mistral-nemo` (default model)
* `openai` is `gpt-4o`
* `claude` is `claude-3-5-sonnet-20241022`

## Select Models
* `nemo-agent "my_prompt" --provider ollama --model nemotron`

## OpenAI o1 Support
* Supports `o1-mini` and `o1-preview`
* `nemo-agent "my prompt" --provider openai --model o1-mini`

## Contributing
Contributions to Nemo Agent are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer
Nemo Agent generates code using an LLM. Every run is different as the LLM generated code is different. While it strives for accuracy and best practices, the generated code should be reviewed and tested before being used in a production environment.
