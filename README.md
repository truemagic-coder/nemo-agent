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
* Utilizes the `Ollama`, `OpenAI`, `Claude`, or `Gemini` language models for intelligent code generation
* Ability to import reference documents to guide the task implementation
* Allows importing existing code projects in multiple languages to serve as a reference for the task
* Enables the importation of csv data files to populate databases or graphs
* Implements best practices in Python development automatically
* Writes and runs passing tests using `pytest` up to 80%+ test coverage 
* Automatically fixes and styles code using `pylint` up to 7+/10
* Calculates and improves the complexity score using `complexipy` to be under 15
* Auto-formats the code with `autopep8`
* Shows the token count used for the responses
* Run via UV (uvx)

## Coding Ability
* `leetcode` hards
* `fastapi` or `flask` APIs
* `flask` web apps
* `streamlit` apps
* `tkinter` apps
* `jupyter notebook`
* Note: Not all runs will be successful with all models

## Install 

### OpenAI, Claude, or Gemini Install

#### Requirements
* Python 3.9 or higher
* OpenAI, Claude, or Gemini API KEY
* Mac or Linux
* No GPU requirement

#### Requirements Installation
* Install OpenAI, Claude, or GEMINI API KEY for `zsh` shell
    * `echo 'export OPENAI_API_KEY="YOUR_API_KEY"' >> ~/.zshrc` or
    * `echo 'export ANTHROPIC_API_KEY="YOUR_API_KEY"' >> ~/.zshrc` or
    * `echo 'export GEMINI_API_KEY="YOUR_API_KEY"' >> ~/.zshrc`
* `pip install uv`
* `uvx nemo-agent` - to run nemo-agent

### OR

### Ollama Install

#### Requirements
* Python 3.9 or higher
* Ollama running `qwen2.5-coder:14b`
* Linux with minimum spec of Ubuntu 24.04 with RTX 4070 or;
* Mac with minimum spec of Mac Mini M2 Pro with 16MB 
  
#### Requirements Installation
* Ollama install instructions:
    * `curl -fsSL https://ollama.com/install.sh | sh`
    * `ollama pull qwen2.5-coder:14b`
* `pip install uv`
* `uvx nemo-agent` - to run nemo-agent

## Usage

### Providers
* `ollama`: `uvx nemo-agent --provider ollama`
* `openai`: `uvx nemo-agent --provider openai`
* `claude`: `uvx nemo-agent --provider claude`
* `gemini`: `uvx nemo-agent --provider gemini`

### Import Reference Documentation Into Prompt
* Documentation files must be either: .md (Markdown) or .txt (Text) and be located in a folder
* `uvx nemo-agent --docs example_folder`

### Import Existing Code Projects Into Prompt
* Code files must be either: .py (Python), .php (PHP), .rs (Rust), .js (JavaScript), .ts (TypeScript), .toml (TOML), .json (JSON), .rb (Ruby), or .yaml (YAML) and be located in a folder
* `uvx nemo-agent --code example_folder`

### Import Data Into Prompt
* Data files must be .csv (CSV) and be located in a folder
* `uvx nemo-agent --data example_folder`

### Prompting

#### CLI
* `uvx nemo-agent "create a fizzbuzz script"`

#### OR

#### File Prompt
* Prompt file must be markdown (.md) or text files (.txt)
* `uvx nemo-agent --file example.md` or 
* `uvx nemo-agent --file example.txt`

### Run Generated Program
* `cd generated_project_folder`
* `source .venv/bin/activate`
* `python main.py`

### Tests

Tests are automatically created and run.

### Skipping Tests

You many want to skip tests especially if you are generating a UI application.

* `uvx nemo-agent "create a fizzbuzz script" --tests False`

## Models

### Default Models 
* `ollama` is `qwen2.5-coder:14b`
* `openai` is `gpt-4o`
* `claude` is `claude-3-7-sonnet-20250219`
* `gemini` is `gemini-2.5-pro-exp-03-25`

### Select Models
* `uvx nemo-agent "my_prompt" --provider openai --model o3-mini`

### Supported Models

#### Ollama
* Supports any 128k input token models

#### OpenAI
* Supports `o3-mini`, `o1-mini`, `o1-preview`, `o1`, `gpt-4o`, and `gpt-4o-mini`

#### Claude
* Supports `claude-3-7-sonnet-20250219` and `claude-3-5-sonnet-20241022`

#### Gemini
* Supports `gemini-2.5-pro-exp-03-25`, `gemini-2.0-flash`, `gemini-1.5-pro`, `gemini-1.5-flash`

## Contributing
Contributions to Nemo Agent are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer
Nemo Agent generates code using an LLM. Every run is different as the LLM generated code is different. While it strives for accuracy and best practices, the generated code should be reviewed and tested before being used in a production environment.
