import ast
import os
import re
import subprocess
from phi.assistant import Assistant
from phi.llm.ollama import Ollama
from phi.tools.file import FileTools
import click

SYSTEM_PROMPT = """
You are NemoAgent, a skilled software developer in Python. Follow these rules strictly:

1. Always use your tools to get file and directory context before executing commands and writing code.
2. Always use `cat` with heredoc syntax to create or modify files:
   cat > filename.py << EOL
   # File content here
   EOL

3. You only use the latest version of Python 3.
4. You only use poetry for Python package management.
5. You only use pytest for testing.
7. You only use ruff for linting and code formatting.
8. Verify file creation and content after each step using `ls` and `cat`.
9. Use absolute paths when necessary.
10. Break complex tasks into smaller, verifiable steps.
11. Provide complete file content when creating or editing files.
12. Use markdown and include language specifiers in code blocks.
13. If a library is required, install it using `pip` as needed.

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


SYSTEM_PROMPT = """
You are NemoAgent, a skilled software developer in Python using the STaR (Self-Taught Reasoner) approach and Chain of Thought (COT) reasoning. Follow these rules strictly:

1. Use the STaR method: First, attempt to solve the problem. Then, critically analyze your solution, identify areas for improvement, and refine your approach.
2. Employ Chain of Thought reasoning: Explain your thought process step-by-step for each decision and action you take.
3. Always use your tools to get file and directory context before executing commands and writing code.
4. Only use `cat` with heredoc syntax to create or modify files:
   cat > filename.py << EOL
   # File content here
   EOL
5. Use `sed` for making specific modifications to existing files:
   sed -i 's/old_text/new_text/g' filename.py
6. You only use the latest version of Python 3.
7. Use absolute paths when necessary.
8. Break complex tasks into smaller, verifiable steps.
9. Provide complete file content when creating or editing files.
10. Use markdown and include language specifiers in code blocks.
11. Create a new folder based on the new project requested - like if a "snake" project is requested, create a folder named "snake" and work inside it.
12. If a library is required, install it using `pip` as needed.

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
        initial_solution = self.get_initial_solution()
        refined_solution = self.refine_solution(initial_solution)
        self.execute_solution(refined_solution)

    def get_initial_solution(self):
        prompt = f"""
        Task: {self.task}

        Provide an initial solution to this task using your Python development skills.
        Use Chain of Thought reasoning to explain your thought process for each step.
        Format your response as follows:

        Thought: [Your reasoning for the next step]
        Action: [The action you're taking, such as writing code or executing a command]
        Code/Command: [The actual code or command]

        Repeat this format for each step in your solution.
        Limit your response to 1-2 steps at a time.
        """
        return self.get_incremental_response(prompt)

    def refine_solution(self, initial_solution):
        prompt = f"""
        Initial solution:
        {initial_solution}

        Critically analyze the initial solution. Identify areas for improvement in terms of:
        1. Code efficiency
        2. Readability
        3. Best practices
        4. Potential edge cases
        5. Error handling
        6. Testing

        Then, provide a refined and improved solution addressing these aspects.
        Use Chain of Thought reasoning to explain your thought process for each improvement.
        Format your response as follows:

        Analysis: [Your analysis of the initial solution]

        Improvement 1:
        Thought: [Your reasoning for this improvement]
        Action: [The action you're taking to improve the solution]
        Code/Command: [The actual improved code or command]

        Limit your response to 1-2 improvements at a time.
        """
        return self.get_incremental_response(prompt)

    def get_incremental_response(self, prompt):
        full_response = ""
        continue_prompt = "Continue with the next steps or improvements."
        
        while True:
            partial_response = self.get_response(prompt)
            full_response += partial_response

            # Check if the response is complete
            if "Next steps:" not in partial_response and "Improvement" not in partial_response:
                break

            prompt = continue_prompt

        return full_response

    def execute_solution(self, solution):
        print("Executing refined solution:")
        print(solution)
        self.validate_and_execute_commands(solution)

    def execute_solution(self, solution):
        print("Executing refined solution:")
        print(solution)
        self.validate_and_execute_commands(solution)

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

        # Print any remaining content in the last line
        if current_line:
            print(current_line)

        return full_response

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
        # Add common typo corrections here
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
        # Check if the command uses cat with heredoc for file creation
        if command.strip().startswith('cat >'):
            return True
        # Allow other common commands
        elif command.startswith(('ls', 'cd', 'mkdir', 'python', 'pip', 'sed')):
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

                # Handle heredoc commands separately
                if '<<' in corrected_command:
                    self.execute_heredoc_command(corrected_command)
                else:
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

    def execute_heredoc_command(self, command):
        # Split the command into the file path and content
        try:
            file_path, content = command.split('<<', 1)
            file_path = file_path.split('>', 1)[1].strip()
        except IndexError:
            print(f"Error: Invalid heredoc command format. Command: {command}")
            return

        if not file_path:
            print("Error: File path is empty. Please provide a valid file path.")
            return

        content = content.strip()

        # Remove the EOL markers
        content_lines = content.split('\n')
        if content_lines[0] == content_lines[-1] == 'EOL':
            content = '\n'.join(content_lines[1:-1])

        # Ensure the directory exists
        try:
            directory = os.path.dirname(file_path)
            if directory:
                os.makedirs(directory, exist_ok=True)
        except OSError as e:
            print(f"Error creating directory: {e}")
            return

        # Write the content to the file
        try:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"File created: {file_path}")
        except IOError as e:
            print(f"Error writing to file: {e}")



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
    Run Nemo Agent tasks using the STaR approach and Chain of Thought reasoning.
    If no task is provided, it will prompt the user for input.
    """
    if task is None:
        task = click.prompt("Please enter the task for Nemo Agent")

    nemo_agent = NemoAgent(task=task)
    nemo_agent.run_task()


if __name__ == "__main__":
    cli()
