import ast
import os
import re
import subprocess
from phi.assistant import Assistant
from phi.llm.ollama import Ollama
from phi.tools.file import FileTools
import click

SYSTEM_PROMPT = """
You are NemoAgent, a skilled software developer. Follow these rules strictly:

1. Always use your tools to get file and directory context before executing commands and writing code.
2. Always use `cat` with heredoc syntax to create or modify files:
   cat > filename.py << EOL
   # File content here
   EOL

3. Verify file creation and content after each step using `ls` and `cat`.
4. Use absolute paths when necessary.
5. Break complex tasks into smaller, verifiable steps.
6. Provide complete file content when creating or editing files.
7. Use markdown and include language specifiers in code blocks.
8. If a library is required, install it using `pip` as needed.

Current working directory: {cwd}
"""

class CustomSystemTools:
    def __init__(self):
        self.cwd = os.getcwd()

    def execute_command(self, command: str) -> str:
        try:
            result = subprocess.run(
                command, shell=True, check=True, capture_output=True, text=True, cwd=self.cwd)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error executing command: {e.stderr}"


class NemoAgent:
    def __init__(self, task: str):
        self.cwd = os.getcwd()
        self.task = task
        self.assistant = self.setup_assistant()

    def setup_assistant(self):
        system_prompt = SYSTEM_PROMPT.format(
            cwd=self.cwd,
            os_name=os.uname().sysname,
            default_shell=os.environ.get("SHELL", "/bin/sh"),
            home_dir=os.path.expanduser("~")
        )
        custom_system_tools = CustomSystemTools()
        return Assistant(
            llm=Ollama(model="mistral-nemo"),
            system_prompt=system_prompt,
            tools=[
                custom_system_tools.execute_command,
                FileTools(),
            ],
            show_tool_calls=True,
            markdown=True,
        )

    def run_task(self):
        full_response = ""
        for response in self.assistant.run(self.task):
            if isinstance(response, str):
                full_response += response
            elif isinstance(response, dict):
                if 'content' in response:
                    full_response += response['content']
                else:
                    full_response += str(response)

        print(full_response)

        # Validate and execute the generated commands
        self.validate_and_execute_commands(full_response)

    def extract_commands(self, response):
        commands = []
        lines = response.split('\n')
        in_bash_block = False
        current_command = ""
        in_heredoc = False
        heredoc_delimiter = ""

        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith('```bash'):
                in_bash_block = True
            elif stripped_line.startswith('```') and in_bash_block:
                in_bash_block = False
                if current_command:
                    commands.append(current_command.strip())
                    current_command = ""
            elif in_bash_block:
                if not in_heredoc and '<<' in stripped_line:
                    heredoc_delimiter = stripped_line.split('<<')[1].strip()
                    in_heredoc = True
                    current_command += line + '\n'
                elif in_heredoc and stripped_line == heredoc_delimiter:
                    in_heredoc = False
                    current_command += line + '\n'
                elif in_heredoc:
                    current_command += line + '\n'
                else:
                    current_command += stripped_line + '; '

        if current_command:
            commands.append(current_command.strip())

        return commands
    
    def validate_command(self, command):
        # Check if the command uses cat with heredoc for file creation
        if 'cat >' in command and '<<' in command:
            return True
        # Allow other common commands
        elif command.startswith(('ls', 'cd', 'mkdir', 'python', 'pip')):
            return True
        # Allow verification commands
        elif command.startswith(('cat ', 'ls ')):
            return True
        return False

    def validate_and_execute_commands(self, response):
        commands = self.extract_commands(response)

        for command in commands:
            if not self.validate_command(command):
                print(f"Invalid command: {command}")
                continue

            print(f"Executing: {command}")
            try:
                # Attempt to auto-correct common typos
                corrected_command = self.auto_correct_command(command)
                
                # For Python code, validate syntax before execution
                if command.startswith('cat > ') and command.endswith('.py'):
                    python_code = self.extract_python_code(corrected_command)
                    if not self.validate_python_syntax(python_code):
                        raise ValueError("Invalid Python syntax")

                result = subprocess.run(
                    corrected_command, shell=True, check=True, capture_output=True, text=True)
                print(result.stdout)
            except (subprocess.CalledProcessError, ValueError) as e:
                print(f"Error: {str(e)}")
                # Implement feedback loop here
                corrected_command = self.get_correction(command, str(e))
                if corrected_command:
                    print(f"Attempting correction: {corrected_command}")
                    self.validate_and_execute_commands(corrected_command)

    def auto_correct_command(self, command):
        # Add common typo corrections here
        corrections = {
            'pyhton': 'python',
            'pirnt': 'print',
            'impotr': 'import',
            'defien': 'define',
            'fucntion': 'function',
        }
        for typo, correction in corrections.items():
            command = command.replace(typo, correction)
        return command

    def extract_python_code(self, command):
        match = re.search(r'cat > .*\.py << EOL\n(.*?)\nEOL', command, re.DOTALL)
        if match:
            return match.group(1)
        return ""

    def validate_python_syntax(self, code):
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def get_correction(self, command, error_message):
        correction_prompt = f"""
        The following command resulted in an error:
        {command}

        Error message:
        {error_message}

        Please provide a corrected version of the command that addresses this error.
        """
        correction_response = ""
        for response in self.assistant.run(correction_prompt):
            if isinstance(response, str):
                correction_response += response
            elif isinstance(response, dict):
                if 'content' in response:
                    correction_response += response['content']
                else:
                    correction_response += str(response)

        corrected_commands = self.extract_commands(correction_response)
        return corrected_commands[0] if corrected_commands else None

@click.command()
@click.argument('task', required=False)
def cli(task: str = None):
    """
    Run Nemo Agent tasks.
    If no task is provided, it will prompt the user for input.
    """
    if task is None:
        task = click.prompt("Please enter the task for Nemo Agent")

    nemo_agent = NemoAgent(task=task)
    nemo_agent.run_task()


if __name__ == "__main__":
    cli()
