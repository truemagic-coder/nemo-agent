import ast
import os
import re
import subprocess
from phi.assistant import Assistant
from phi.llm.ollama import Ollama
from phi.tools.file import FileTools
import click

SYSTEM_PROMPT = """
You are Nemo Agent, an expert Python developer specializing in Flask applications. Follow these rules strictly:

1. Always use your tools to get file and directory context before executing commands and writing code.
2. Always use `cat` with heredoc syntax to create files. Example:
   cat > filename.py << EOL
   # File content here
   EOL
3. Use `sed` for making specific modifications to existing files:
   sed -i 's/old_text/new_text/g' filename.py
4. Provide complete, fully functional code when creating or editing files.
5. Always install packages using `pip` into the venv created for the project at the start.
6. CRITICAL: Never execute the code you created other than tests.
7. Always create a venv for the Python project.
8. Include proper error handling, comments, and follow Python best practices.
9. IMPORTANT: Write to disk after EVERY step, no matter how small.
10. Use absolute paths when referring to files and directories when required.
11. Always use type hints in your Python code.
12. Always use pytest for testing.
13. Follow the TDD red-green-refactor cycle:
    a. Write a failing test (red).
    b. Write the minimum code to make the test pass (green).
    c. Refactor the code if necessary.
14. Always write tests before implementing the actual code.
15. Keep modifying the code until all tests pass.
16. Run tests after each code change using the command: pytest test_filename.py
17. Use Pylint to check code quality before running tests.
18. Address any Pylint warnings or errors before proceeding with tests.

Current working directory: {{cwd}}
Operating System: {{os_name}}
Default Shell: {{default_shell}}
Home Directory: {{home_dir}}
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
        self.create_virtual_environment()
        self.install_pytest_and_pylint()
        self.tdd_cycle()

    def create_virtual_environment(self):
        venv_command = "python3 -m venv venv"
        self.validate_and_execute_commands(venv_command)
        activate_command = "source venv/bin/activate"
        self.validate_and_execute_commands(activate_command)
        self.venv_path = os.path.join(self.cwd, "venv")

    def install_pytest_and_pylint(self):
        install_command = "pip install pytest pylint"
        self.validate_and_execute_commands(install_command)

    def tdd_cycle(self):
        while True:
            # Write failing test
            self.write_test()
            
            # Run Pylint on test file
            if not self.run_pylint("test_*.py"):
                continue
            
            # Run test (should fail)
            if not self.run_tests():
                # Write code to make test pass
                self.write_code()
                
                # Run Pylint on implementation file
                if not self.run_pylint("*.py"):
                    continue
                
                # Run test again (should pass)
                if self.run_tests():
                    # Refactor if necessary
                    self.refactor()
                else:
                    print("Test still failing. Continuing TDD cycle.")
            else:
                print("All tests passing. TDD cycle complete.")
                break

    def run_pylint(self, file_pattern):
        pylint_command = f"{os.path.join(self.venv_path, 'bin', 'pylint')} --output-format=json {file_pattern}"
        result = subprocess.run(pylint_command, shell=True, capture_output=True, text=True, cwd=self.cwd)
        
        if result.returncode != 0:
            print("Pylint found issues. Attempting to fix them.")
            self.fix_pylint_issues(result.stdout, file_pattern)
            return False
        return True

    def fix_pylint_issues(self, pylint_output, file_pattern):
        import json
        
        try:
            issues = json.loads(pylint_output)
        except json.JSONDecodeError:
            print("Error parsing Pylint output. Skipping automatic fixes.")
            return

        files_to_fix = {}
        for issue in issues:
            filename = issue['path']
            if filename not in files_to_fix:
                with open(filename, 'r') as f:
                    files_to_fix[filename] = f.readlines()

            line = issue['line'] - 1  # Pylint uses 1-based line numbers
            message = issue['message']
            
            prompt = f"Fix the following Pylint issue in file {filename} at line {line + 1}:\n\n{message}\n\nCurrent line: {files_to_fix[filename][line].strip()}\n\nProvide the corrected line of code."
            corrected_line = self.get_response(prompt).strip()
            
            files_to_fix[filename][line] = corrected_line + '\n'

        for filename, lines in files_to_fix.items():
            with open(filename, 'w') as f:
                f.writelines(lines)
            print(f"Updated file: {filename}")

        print("Pylint issues have been addressed. Running Pylint again to verify.")
        self.run_pylint(file_pattern)

    def write_test(self):
        prompt = f"Write a failing test for the following task: {self.task}"
        test_code = self.get_response(prompt)
        self.validate_and_execute_commands(test_code)

    def write_code(self):
        prompt = f"Write the minimum code to make the test pass for the task: {self.task}"
        code = self.get_response(prompt)
        self.validate_and_execute_commands(code)

    def run_tests(self):
        test_command = "pytest"
        result = subprocess.run(test_command, shell=True, capture_output=True, text=True, cwd=self.cwd)
        print(result.stdout)
        return result.returncode == 0

    def refactor(self):
        prompt = f"Refactor the code if necessary for the task: {self.task}"
        refactored_code = self.get_response(prompt)
        self.validate_and_execute_commands(refactored_code)

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
        allowed_commands = ['cat', 'ls', 'cd', 'mkdir', 'sed', 'pip', 'echo', 'venv', 'python3', 'source', 'pytest', 'python', 'pylint', 'touch']
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
                elif corrected_command.startswith(('ls', 'cd', 'mkdir', 'pip', 'sed', 'cat', 'echo', 'venv', 'python3', 'source', 'pytest', 'python', 'pylint', 'touch')):
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
        # Generate a project name based on the task
        words = self.task.lower().split()
        clean_words = [word for word in words if word.isalnum()]
        
        if len(clean_words) == 0:
            project_name = "python_project"  # Fallback name if no valid words are found
        elif len(clean_words) == 1:
            project_name = clean_words[0]
        else:
            project_name = f"{clean_words[0]}_{clean_words[1]}"
        
        project_path = os.path.join(self.cwd, project_name)
        try:
            os.makedirs(project_path, exist_ok=True)
            os.chdir(project_path)
            self.cwd = project_path
            print(f"Created and moved to project folder: {project_path}")
            print(f"Current working directory: {os.getcwd()}")
            print("Contents of the directory:")
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

