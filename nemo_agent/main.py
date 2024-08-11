import ast
import os
import re
import subprocess
from phi.assistant import Assistant
from phi.llm.ollama import Ollama
from phi.tools.file import FileTools
import click

SYSTEM_PROMPT = """
You are Nemo Agent, an expert Python developer. Follow these rules strictly:

1. The project has been created using `poetry new {project_name}`. Use this layout to write code in the proper directories.
2. Only use the `json` module for reading and writing JSON files. Never use `jsonify` or `json.dumps`.
3. Always use `cat` with heredoc syntax to create files. Example:
   cat > filename.py << EOL
   # File content here
   EOL
4. Use `sed` for making specific modifications to existing files:
   sed -i 's/old_text/new_text/g' filename.py
5. Provide complete, fully functional code when creating or editing files.
6. Use markdown and include language specifiers in code blocks.
7. If a library is required, add it to the pyproject.toml and run `poetry update`.
8. CRITICAL: Never execute the code you created other than tests.
9. Always use Poetry for project setup and dependency management - never use requirements.txt.
10. Include proper error handling, comments, and follow Python best practices.
11. IMPORTANT: Write to disk after EVERY step, no matter how small.
12. Always use type hints in your Python code.
13. Always use pytest for testing.
14. Keep the project structure simple with 1-2 files in the code directory and 1-2 files in the tests directory.
15. Always run the tests using `poetry run pytest` with no options.

Current working directory: {cwd}
Project name: {project_name}
Code directory: {project_name}/{project_name}
Test directory: {project_name}/tests
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
        self.project_name = self.generate_project_name()
        self.assistant = self.setup_assistant()

    def setup_assistant(self):
        system_prompt = SYSTEM_PROMPT.format(
            cwd=self.cwd,
            project_name=self.project_name,
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

    def generate_project_name(self):
        temp_assistant = Assistant(
            llm=Ollama(model="mistral-nemo"),
            system_prompt="You are a helpful assistant.",
            show_tool_calls=True,
            markdown=True,
        )
        prompt = f"""
        Generate a two-word snake_case project name based on the following task:
        {self.task}

        The project name should be descriptive and relevant to the task.
        Return only the project name, nothing else.
        """
        response = self.get_response(prompt, assistant=temp_assistant)
        return response.strip().lower().replace(" ", "_")

    def update_system_prompt(self):
        updated_prompt = SYSTEM_PROMPT.format(
            cwd=self.cwd,
            project_name=self.project_name,
            os_name=os.uname().sysname,
            default_shell=os.environ.get("SHELL", "/bin/sh"),
            home_dir=os.path.expanduser("~")
        )
        self.assistant.system_prompt = updated_prompt

    def run_task(self):
        self.create_project_with_poetry()
        self.implement_solution()
        self.run_tests()

    def create_project_with_poetry(self):
        print(f"Creating new Poetry project: {self.project_name}")
        try:
            result = subprocess.run(
                ["poetry", "new", self.project_name],
                capture_output=True,
                text=True,
                cwd=self.cwd,
                check=True
            )
            print(result.stdout)

            # Change to the newly created project directory
            project_path = os.path.join(self.cwd, self.project_name)
            os.chdir(project_path)
            self.cwd = project_path

            # Update the system prompt with the new working directory
            self.update_system_prompt()

            print(f"Created and moved to project folder: {project_path}")
            print(f"Current working directory: {os.getcwd()}")
            print("Contents of the directory:")
            print(os.listdir(self.cwd))
        except subprocess.CalledProcessError as e:
            print(f"Error creating Poetry project: {e.stderr}")
        except Exception as e:
            print(f"Error: {str(e)}")

    def implement_solution(self):
        prompt = f"""
        Provide a complete solution for the task: {self.task}
        Follow the rules strictly:
        1. The project has been created using `poetry new {self.project_name}`.
        2. Always write code to the code directory.
        3. Always write tests to the tests directory.
        4. CRITICAL: Never use `jsonify` or `json.dumps` in your code.
        5. Provide complete, fully functional code when creating or editing files.
        6. Use markdown and include language specifiers in code blocks.
        7. Include proper error handling, comments, and follow Python best practices.
        8. Use absolute paths when referring to files and directories especially in tests.
        9. Always use type hints in your Python code.
        10. IMPORTANT: Provide all necessary commands to create and modify files, including `cat` commands for file creation and `sed` commands for modifications.
        11. After providing the implementation, include commands to install any necessary dependencies using Poetry.
        12. Keep the project structure simple with 1-2 files in the code directory and 1-2 files in the tests directory.

        Current working directory: {self.cwd}
        Code directory: {self.project_name}/{self.project_name}
        Test directory: {self.project_name}/tests
        """
        solution = self.get_response(prompt)
        print("Executing solution:")
        print(solution)
        self.validate_and_execute_commands(solution)

        # Install dependencies
        try:
            subprocess.run(["poetry", "install"], check=True, cwd=self.cwd)
            print("Dependencies installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error installing dependencies: {e}")

        # Update pyproject.toml if necessary
        pyproject_update = self.get_response(
            "Provide any necessary updates to pyproject.toml, including adding pytest as a dev dependency if it's not already there.")
        self.validate_and_execute_commands(pyproject_update)

        # Run poetry update to ensure all dependencies are installed
        try:
            subprocess.run(["poetry", "update"], check=True, cwd=self.cwd)
            print("Poetry update completed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error updating dependencies: {e}")

    def get_response(self, prompt, assistant=None):
        if assistant is None:
            assistant = self.assistant
        full_response = ""
        current_line = ""
        for response in assistant.run(prompt):
            if isinstance(response, str):
                full_response += response
                current_line += response
            elif isinstance(response, dict) and 'content' in response:
                content = response['content']
                full_response += content
                current_line += content
            else:
                full_response += str(response)
                print(str(response))

            if '\n' in current_line:
                lines = current_line.split('\n')
                for line in lines[:-1]:
                    print(line)
                current_line = lines[-1]

        if current_line:
            print(current_line)

        return full_response.strip()

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
        allowed_commands = ['cat', 'ls', 'cd', 'mkdir', 'sed',
                            'poetry', 'echo', 'python3', 'source', 'pytest', 'python']
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
                elif corrected_command.startswith(('ls', 'cd', 'mkdir', 'poetry', 'sed', 'cat', 'echo', 'python3', 'source', 'pytest', 'python')):
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
        match = re.search(r'cat > .*\.py << EOL\n(.*?)\nEOL',
                          command, re.DOTALL)
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

    def run_tests(self):
        print("Running tests...")
        try:
            result = subprocess.run(
                ["poetry", "run", "pytest"],
                capture_output=True,
                text=True,
                cwd=self.cwd,
                check=True
            )
            print(result.stdout)
            print("All tests passed successfully.")
        except subprocess.CalledProcessError as e:
            print("Some tests failed. Here's the output:")
            print(e.stdout)
            print(e.stderr)
            self.fix_failing_tests()

    def fix_failing_tests(self):
        prompt = f"""
        The tests for the project have failed. Please analyze the test output and provide fixes for the failing tests.
        Make sure to:
        1. Identify the specific tests that are failing.
        2. Analyze the error messages and stack traces.
        3. Propose changes to either the implementation or the tests to fix the failures.
        4. Provide the necessary commands to update the relevant files.
        """
        fixes = self.get_response(prompt)
        self.execute_solution(fixes)
        self.run_tests()  # Run tests again after applying fixes


@click.command()
@click.argument('task', required=False)
def cli(task: str = None):
    """
    Run Nemo Agent tasks to create Python projects using Poetry.
    If no task is provided, it will prompt the user for input.
    """
    if task is None:
        task = click.prompt("Please enter the task for Nemo Agent")

    nemo_agent = NemoAgent(task=task)
    nemo_agent.run_task()


if __name__ == "__main__":
    cli()
