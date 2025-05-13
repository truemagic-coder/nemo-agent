# Nemo Agent

[![PyPI - Version](https://img.shields.io/pypi/v/nemo-agent)](https://pypi.org/project/nemo-agent/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/nemo-agent)](https://pypi.org/project/nemo-agent/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Libraries.io dependency status for GitHub repo](https://img.shields.io/librariesio/github/truemagic-coder/nemo-agent)](https://libraries.io/pypi/nemo-agent)

[![Nemo Agent](https://cdn.cometheart.com/nemo-agent-2.png)](https://cdn.cometheart.com/nemo-agent.mp4)

## Features
* Runs blazing fast
* Generates Python project structures automatically using `uv`
* Writes Python code based on task descriptions
* Executes development tasks using AI-generated commands
* Utilizes the `OpenAI` or `Gemini` language models for intelligent code generation
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

## Install 

### Requirements
* Python 3.10 or higher
* OpenAI or Gemini API key
* Mac or Linux
* No GPU requirement

### Requirements Installation
* Install OpenAI or Gemini for `zsh` shell
    * `echo 'export OPENAI_API_KEY="YOUR_API_KEY"' >> ~/.zshrc` or
    * `echo 'export GEMINI_API_KEY="YOUR_API_KEY"' >> ~/.zshrc`
* `pip install uv`
* `uvx nemo-agent` - to run nemo-agent

## Usage

### Providers
* `openai`: `uvx nemo-agent` (default)
* `gemini`: `uvx nemo-agent --provider gemini`

### Supported Models 
* `openai` is `gpt-4.1` (default), `o4-mini`, and `o3` (requires organization verification)
* `gemini` is `gemini-2.5-pro-preview-05-06`(default) and `gemini-2.5-flash-preview-04-17`

### Calling Non-Default Models
* `uvx nemo-agent --model o4-mini`

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

## Contributing
Contributions to Nemo Agent are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer
Nemo Agent generates code using an LLM. Every run is different as the LLM generated code is different. While it strives for accuracy and best practices, the generated code should be reviewed and tested before being used in a production environment.
