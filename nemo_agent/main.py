import ast
import os
import re
import subprocess
from phi.assistant import Assistant
from phi.llm.ollama import Ollama
from phi.tools.file import FileTools
import click

SYSTEM_PROMPT = """
You are NemoAgent, an expert Python developer. Follow these rules strictly:

1. Always use your tools to get file and directory context before executing commands and writing code.
2. Always use `cat` with heredoc syntax to create files. Example:
   cat > filename.py << EOL
   # File content here
   EOL
3. Use `sed` for making specific modifications to existing files:
   sed -i 's/old_text/new_text/g' filename.py
4. Provide complete, fully functional code when creating or editing files.
5. Use markdown and include language specifiers in code blocks.
6. If a library is required, install it using `pip` as needed.
7. CRITICAL: Never execute the code you created.
8. Always create an venv for the Python project.
9. Include proper error handling, comments, and follow Python best practices.
10. IMPORTANT: Write to disk after EVERY step, no matter how small.
11. Never override the user requirements including library choices. Always follow the user's instructions.
12. Always use absolute paths when referring to files and directories.

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
        project_name = self.task.split()[0].lower()
        self.create_project_folder(project_name)
        self.get_initial_solution()

    def get_initial_solution(self):
        prompt = f"""
        Provide a complete solution for the task: {self.task}
        Include all necessary code and commands.
        Remember to write all files within the project directory: {self.cwd}
        After creating each file, verify its contents using the `cat` command.
        """
        initial_solution = self.get_response(prompt)
        self.execute_solution(initial_solution)
        return initial_solution

    def get_response(self, prompt):
        full_response = ""
        current_line = ""
        for response in self.assistant.run(prompt):
            if isinstance(response, str):
                full_response += response
                current_line += response
                if '\n' in current_line:
                    lines = current_line.split('\n')
                    for line in lines[:-1]:
                        print(line)
                    current_line = lines[-1]
            elif isinstance(response, dict):
                if 'content' in response:
                    content = response['content']
                    full_response += content
                    current_line += content
                    if '\n' in current_line:
                        lines = current_line.split('\n')
                        for line in lines[:-1]:
                            print(line)
                        current_line = lines[-1]
                else:
                    full_response += str(response)
                    print(str(response))

        if current_line:
            print(current_line)

        return full_response

    def execute_solution(self, solution):
        print("Executing solution:")
        print(solution)
        self.validate_and_execute_commands(solution)

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
                    heredoc_delimiter = stripped_line.split('<<', 1)[1].strip()
                    in_heredoc = True
                    current_command += line + '\n'
                elif in_heredoc and stripped_line == heredoc_delimiter:
                    in_heredoc = False
                    current_command += line + '\n'
                elif in_heredoc:
                    current_command += line + '\n'
                else:
                    if current_command:
                        commands.append(current_command.strip())
                    current_command = stripped_line

        if current_command:
            commands.append(current_command.strip())

        return commands

    def auto_correct_command(self, command):
        corrections = {
            'pyhton': 'python',
            'pirnt': 'print',
            'impotr': 'import',
            'defien': 'define',
            'fucntion': 'function',
            'retrun': 'return',
            'flase': 'false',
            'ture': 'true',
            'elif': 'elif',
            'esle': 'else',
        }
        for typo, correction in corrections.items():
            command = command.replace(typo, correction)
        return command

    def validate_command(self, command):
        allowed_commands = ['cat', 'ls', 'cd', 'mkdir', 'sed', 'pip', 'echo', 'venv', 'python3', 'source']
        command_parts = command.strip().split()
        if command_parts:
            return command_parts[0] in allowed_commands
        return False

    def validate_and_execute_commands(self, response):
        commands = self.extract_commands(response)

        for command in commands:
            if not self.validate_command(command):
                print(f"Invalid command: {command}")
                continue

            print(f"Executing: {command}")
            try:
                corrected_command = self.auto_correct_command(command)

                if corrected_command.strip().startswith('cat >'):
                    self.execute_heredoc_command(corrected_command)
                elif corrected_command.startswith(('ls', 'cd', 'mkdir', 'sed', 'cat', 'echo', 'venv', 'python3', 'source')):
                    result = subprocess.run(
                        corrected_command, shell=True, check=True, capture_output=True, text=True, cwd=self.cwd)
                    print(result.stdout)
                else:
                    print(f"Command not allowed: {corrected_command}")

                os.sync()

            except subprocess.CalledProcessError as e:
                print(f"Error: {e.stderr}")
            except Exception as e:
                print(f"Error: {str(e)}")

    def create_project_folder(self, project_name):
        project_name = "snake_game"  # Use a fixed name for this specific task
        project_path = os.path.join(self.cwd, project_name)
        try:
            os.makedirs(project_path, exist_ok=True)
            os.chdir(project_path)
            self.cwd = project_path
            print(f"Created and moved to project folder: {project_path}")
            print(f"Current working directory: {os.getcwd()}")
            print(f"Contents of the directory:")
            print(os.listdir(self.cwd))
        except Exception as e:
            print(f"Error creating project folder: {e}")

    def file_exists_and_has_content(self, file_path):
        return os.path.exists(file_path) and os.path.getsize(file_path) > 0

    def verify_file_contents(self, file_path):
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            print(f"Contents of {file_path}:")
            print(content)
            print(f"File size: {os.path.getsize(file_path)} bytes")
        except Exception as e:
            print(f"Error verifying file contents: {e}")

    def execute_heredoc_command(self, command):
        try:
            file_path, content = command.split('<<', 1)
            file_path = file_path.split('>', 1)[1].strip()
            content = content.strip()

            # Remove the EOL markers
            content_lines = content.split('\n')
            if len(content_lines) >= 2 and content_lines[0] == content_lines[-1]:
                content = '\n'.join(content_lines[1:-1])

            # Ensure the file path is within the project directory
            full_file_path = os.path.join(self.cwd, file_path)

            # Ensure the directory exists
            os.makedirs(os.path.dirname(full_file_path), exist_ok=True)

            # Write the content to the file
            with open(full_file_path, 'w') as f:
                f.write(content)

            # Force sync to disk
            os.fsync(f.fileno())

            if self.file_exists_and_has_content(full_file_path):
                print(f"File successfully created/updated: {full_file_path}")
                self.verify_file_contents(full_file_path)
            else:
                print(f"Failed to create/update file: {full_file_path}")

        except Exception as e:
            print(f"Error executing heredoc command: {e}")
            print(f"Command that caused the error: {command}")

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
        correction_response = self.get_response(correction_prompt)
        corrected_commands = self.extract_commands(correction_response)
        return corrected_commands[0] if corrected_commands else None

@click.command()
@click.argument('task', required=False)
def cli(task: str = None):
    """
    Run Nemo Agent tasks to create Python projects without executing scripts.
    If no task is provided, it will prompt the user for input.
    """
    if task is None:
        task = click.prompt("Please enter the task for Nemo Agent")

    nemo_agent = NemoAgent(task=task)
    nemo_agent.run_task()

if __name__ == "__main__":
    cli()

