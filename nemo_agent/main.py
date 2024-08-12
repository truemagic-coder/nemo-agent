import ast
import os
import random
import re
import subprocess
import sys
import time
from phi.assistant import Assistant
from phi.llm.ollama import Ollama
from phi.tools.file import FileTools
import click

SYSTEM_PROMPT = """
You are Nemo Agent, an expert Python developer. Follow these rules strictly:

1. The project has been created using `poetry new {project_name}`. Use this layout to write code in the proper directories.
2. Always provide complete, fully functional code when creating or editing files.
3. Use markdown and include language specifiers in code blocks.
4. If a library is required, add it to the pyproject.toml and run `poetry update`.
5. CRITICAL: Never execute the code you created other than tests.
6. Always use Poetry for project setup and dependency management - never use requirements.txt.
7. Include proper error handling, comments, and follow Python best practices.
8. IMPORTANT: Write to disk after EVERY step, no matter how small.
9. Use type hints in your Python code when appropriate.
10. Only use pytest for testing - never use unittest.
11. Always run the tests using `poetry run pytest` with no options.
12. Always use module imports when referring to files in tests.
13. Use the following format for creating files:
    For code files with inline tests: cat > {project_name}/filename.py << EOL
14. IMPORTANT: Write to disk after EVERY step, no matter how small.
15. Always break up tests into multiple test functions for better organization.
16. Once the tests pass, the task is complete.
17. Always mock external services, database calls, and APIs.
18. Always include module docstrings at the beginning of Python files, unless they are test files or __init__.py files.
19. You use your tools like `ls` and `cat` to verify and understand the contents of files and directories.
20. Always use `cat` with heredoc syntax to create files. Example:
   cat > filename.py << EOL
   # File content here
   EOL
21. Use `sed` for making specific modifications to existing files:
   sed -i 's/old_text/new_text/g' filename.py
22. Use the following format for creating files:
            For code files: cat > {project_name}/filename.py << EOL
            For test files: cat > tests/test_filename.py << EOL
23. Only create an __init__.py file the project code directory {pwd}/{project_name}.
24. Never create an __init__.py file in the tests directory.
25. Create a simple test plan to ensure that all requirements are met.
26. Don't use print statements as return values.
27. Write testable code from the start.

Current working directory: {pwd}
"""


class CustomSystemTools:
    def __init__(self):
        self.pwd = os.getcwd()

    def execute_command(self, command: str) -> str:
        try:
            result = subprocess.run(
                command, shell=True, check=True, capture_output=True, text=True, cwd=self.pwd)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error executing command: {e.stderr}"


class NemoAgent:
    MAX_IMPROVEMENT_ATTEMPTS = 3

    def __init__(self, task: str):
        self.pwd = os.getcwd()
        self.task = task
        self.project_name = self.generate_project_name()
        self.assistant = self.setup_assistant()

    def setup_assistant(self):
        system_prompt = SYSTEM_PROMPT.format(
            pwd=self.pwd,
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
        It must be exactly two words in snake_case format.
        Return only the project name, nothing else.
        """
        response = self.get_response(prompt, assistant=temp_assistant)
        project_name = response.strip().lower().replace(" ", "_")

        # Ensure the project name has exactly two segments
        segments = project_name.split('_')
        if len(segments) != 2:
            # If not, generate a default name
            project_name = f"task_{
                segments[0]}" if segments else "default_project"

        # Add a random 3-digit number as the third segment
        random_number = random.randint(100, 999)
        project_name = f"{project_name}_{random_number}"

        return project_name

    def update_system_prompt(self):
        updated_prompt = SYSTEM_PROMPT.format(
            pwd=self.pwd,
            project_name=self.project_name,
            os_name=os.uname().sysname,
            default_shell=os.environ.get("SHELL", "/bin/sh"),
            home_dir=os.path.expanduser("~")
        )
        self.assistant.system_prompt = updated_prompt

    def run_task(self):
        self.ensure_poetry_installed()
        self.create_project_with_poetry()
        self.setup_init_files()
        self.implement_solution()
        tests_passed = self.run_tests()
        if not tests_passed:
            self.improve_test_coverage()

        print("Task completed. Please review the output and make any necessary manual adjustments.")

    def ensure_poetry_installed(self):
        try:
            subprocess.run(["poetry", "--version"], check=True,
                           capture_output=True, text=True)
            print("Poetry is already installed.")
        except FileNotFoundError:
            print("Poetry is not installed. Installing Poetry...")
            try:
                if sys.platform.startswith('win'):
                    subprocess.run(
                        ["powershell", "-Command", "(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -"], check=True, shell=True)
                else:
                    subprocess.run(["curl", "-sSL", "https://install.python-poetry.org",
                                   "|", "python3", "-"], check=True, shell=True)
                print("Poetry installed successfully.")
            except subprocess.CalledProcessError as e:
                print(f"Error installing Poetry: {e}")
                sys.exit(1)

    def create_project_with_poetry(self):
        print(f"Creating new Poetry project: {self.project_name}")
        try:
            result = subprocess.run(
                ["poetry", "new", self.project_name],
                capture_output=True,
                text=True,
                cwd=self.pwd,
                check=True
            )
            print(result.stdout)

            self.pwd = os.path.join(self.pwd, self.project_name)
            os.chdir(self.pwd)

            # Delete __init__.py from the tests folder
            tests_init_file = os.path.join(self.pwd, 'tests', '__init__.py')
            if os.path.exists(tests_init_file):
                os.remove(tests_init_file)
                print(f"Deleted {tests_init_file}")

            # Update the system prompt with the new working directory
            self.update_system_prompt()

            print(f"Current working directory: {os.getcwd()}")
            print("Contents of the directory:")
            print(os.listdir(self.pwd))

            subprocess.run(
                f"sed -i '/^\\[tool.poetry\\]/a packages = [{{include = \"{
                    self.project_name}\"}}]' pyproject.toml",
                shell=True,
                check=True,
                cwd=self.pwd
            )
            print("Added packages variable to pyproject.toml")

            # Add [tool.pytest.ini-options] section to pyproject.toml
            subprocess.run(
                "sed -i '$a\\[tool.pytest.ini-options]\\npython_paths = [\".\", \"tests\"]' pyproject.toml",
                shell=True,
                check=True,
                cwd=self.pwd
            )
            print("Added [tool.pytest.ini-options] section to pyproject.toml")

            try:
                subprocess.run(["poetry", "add", "--dev", "pytest@*", "pylint@*", "autopep8@*",
                                "pytest-cov@*", "pytest-flask@*", "httpx@*"], check=True, cwd=self.pwd)
                print("Added pytest, pylint, autopep8, pytest-cov, pytest-flask, and httpx as development dependencies with latest versions.")
            except subprocess.CalledProcessError as e:
                print(f"Error adding development dependencies: {e}")

        except subprocess.CalledProcessError as e:
            print(f"Error creating Poetry project: {e.stderr}")
        except Exception as e:
            print(f"Error: {str(e)}")

    def implement_solution(self):
        prompt = f"""
        Create a comprehensive test plan and implementation for the task: {self.task}

        Follow these guidelines:
        1. Use Object-Oriented Programming (OOP) principles.
        2. Apply SOLID principles:
        - Single Responsibility Principle (SRP)
        - Open-Closed Principle (OCP)
        - Liskov Substitution Principle (LSP)
        - Interface Segregation Principle (ISP)
        - Dependency Inversion Principle (DIP)
        3. Implement Dependency Injection (DI) where appropriate.
        4. Ensure each class and method has a single responsibility.
        5. Use abstract base classes or interfaces to define contracts.
        6. Implement a simple Dependency Injection Container if needed.
        7. Write unit tests for each class and method.
        8. Use type hints for all method parameters and return values.
        9. Include proper error handling and input validation.
        10. Follow PEP 8 style guidelines.

        Test Plan:
        1. Unit tests for each class and method.
        2. Integration tests for the entire system.
        3. Edge case tests:
        - Test with minimum and maximum valid inputs.
        - Test with invalid inputs.
        4. Performance tests (if applicable).
        5. Exception handling tests.
        6. Dependency Injection tests.

        Implement the solution following this structure:
        1. Create an abstract base class or interface for the main functionality.
        2. Implement concrete classes that inherit from the base class or implement the interface.
        3. Use dependency injection for any dependencies.
        4. Implement a simple DI container if needed.
        5. Create a main function that demonstrates the usage of the classes.
        6. Write comprehensive unit tests for each class and method.

        Use pytest for all tests. Follow all the rules and guidelines provided in the system prompt.

        Now, create the test file:

        cat > tests/test_main.py << EOL
        '''This module contains tests for the main implementation.'''
        import pytest
        from {self.project_name}.main import FactorialCalculator, CalculatorFactory, DIContainer, Calculator

        @pytest.fixture
        def factorial_calculator():
            return FactorialCalculator()

        @pytest.fixture
        def di_container():
            container = DIContainer()
            container.register(Calculator, FactorialCalculator())
            return container

        def test_factorial_zero(factorial_calculator):
            assert factorial_calculator.calculate(0) == 1

        def test_factorial_one(factorial_calculator):
            assert factorial_calculator.calculate(1) == 1

        def test_factorial_positive_integer(factorial_calculator):
            assert factorial_calculator.calculate(5) == 120

        def test_factorial_large_number(factorial_calculator):
            assert factorial_calculator.calculate(20) == 2432902008176640000

        def test_factorial_negative_integer(factorial_calculator):
            with pytest.raises(ValueError):
                factorial_calculator.calculate(-1)

        def test_factorial_float(factorial_calculator):
            with pytest.raises(ValueError):
                factorial_calculator.calculate(5.5)

        def test_factorial_string(factorial_calculator):
            with pytest.raises(ValueError):
                factorial_calculator.calculate("5")

        def test_calculator_factory_valid():
            calculator = CalculatorFactory.create_calculator("factorial")
            assert isinstance(calculator, FactorialCalculator)

        def test_calculator_factory_invalid():
            with pytest.raises(ValueError):
                CalculatorFactory.create_calculator("invalid_type")

        def test_di_container_registration_and_resolution(di_container):
            calculator = di_container.resolve(Calculator)
            assert isinstance(calculator, FactorialCalculator)

        def test_di_container_unregistered_service():
            container = DIContainer()
            with pytest.raises(ValueError):
                container.resolve(str)

        def test_factorial_performance(factorial_calculator):
            import time
            start_time = time.time()
            factorial_calculator.calculate(1000)
            end_time = time.time()
            assert end_time - start_time < 1, "Factorial calculation took too long"
        EOL

        Now run the tests using pytest:

        poetry run pytest tests/test_main.py -v

        It should fail initially. Implement the main functionality in the main.py file.
        
        Follow this example structure for the main.py file:

        cat > {self.project_name}/main.py << EOL
        '''This module contains the main implementation for {self.project_name}.'''
        from abc import ABC, abstractmethod
        from typing import Protocol, Any

        class Calculator(Protocol):
            def calculate(self, n: int) -> int:
                ...

        class FactorialCalculator:
            def calculate(self, n: int) -> int:
                if not isinstance(n, int):
                    raise ValueError("Input must be a non-negative integer")
                if n < 0:
                    raise ValueError("Input must be a non-negative integer")
                if n == 0 or n == 1:
                    return 1
                return n * self.calculate(n - 1)

        class CalculatorFactory:
            @staticmethod
            def create_calculator(calculator_type: str) -> Calculator:
                if calculator_type == "factorial":
                    return FactorialCalculator()
                raise ValueError(
                    f"Unknown calculator type: {{calculator_type}}")

        class DIContainer:
            def __init__(self):
                self._services = {{}}

            def register(self, service_type: type, implementation: Any):
                self._services[service_type] = implementation

            def resolve(self, service_type: type) -> Any:
                if service_type not in self._services:
                    raise ValueError(
                        f"Service {{service_type}} not registered")
                return self._services[service_type]

        def main(container: DIContainer) -> None:
            calculator = container.resolve(Calculator)
            result = calculator.calculate(5)
            print(f"Factorial of 5 is: {{result}}")

        if __name__ == "__main__":
            container = DIContainer()
            container.register(
                Calculator, CalculatorFactory.create_calculator("factorial"))
            main(container)
        EOL

        Now run the tests using pytest:

        poetry run pytest tests/test_main.py -v

        And keep refining the implementation until all tests pass.

        """

        solution = self.get_response(prompt)
        print("Executing solution:")
        print(solution)
        self.validate_and_execute_commands(solution)

        # Validate that the implementation matches the original task
        if not self.validate_implementation():
            self.recover_implementation()

        # Update pyproject.toml if necessary
        pyproject_update = self.get_response(
            f"Provide necessary updates to pyproject.toml for the task: {self.task}, including adding any required dependencies if they're not already there. Also, add a [tool.pytest.ini_options] section with pythonpath = '.' if it doesn't exist.")
        self.validate_and_execute_commands(pyproject_update)

        # Run poetry update to ensure all dependencies are installed
        try:
            subprocess.run(["poetry", "update"], check=True, cwd=self.pwd)
            print("Poetry update completed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error updating dependencies: {e}")

    def validate_implementation(self):
        prompt = f"""
        Review the current implementation and confirm if it correctly addresses the original task: {self.task}
        If the implementation is correct, respond with 'VALID'.
        If the implementation does not match the task or is a generic example, respond with 'INVALID'.
        Provide a brief explanation for your decision.
        """
        response = self.get_response(prompt)
        if "VALID" in response.upper():
            print("Implementation validated successfully.")
            return True
        else:
            print("Implementation does not match the original task.")
            return False

    def recover_implementation(self):
        prompt = f"""
        The current implementation does not correctly address the original task: {self.task}
        Please provide a corrected implementation that focuses specifically on this task.
        Do not default to a generic or "Hello World" example.
        Follow all the rules and guidelines provided in the original implementation prompt.
        """
        corrected_solution = self.get_response(prompt)
        print("Executing corrected solution:")
        print(corrected_solution)
        self.validate_and_execute_commands(corrected_solution)

        # Validate the corrected implementation
        if not self.validate_implementation():
            print(
                "Failed to recover implementation. Manual intervention may be required.")

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

    def setup_init_files(self):
        print("Setting up __init__.py file in the project directory...")
        init_file = os.path.join(self.pwd, self.project_name, '__init__.py')
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write('"""This module is part of the {} project."""\n'.format(
                    self.project_name))
            print(f"Created {init_file}")
        else:
            print(f"{init_file} already exists")
        print("Finished setting up __init__.py file.")

    def clean_code_with_pylint(self, file_path):
        try:
            # Check if the file is empty
            if os.path.getsize(file_path) == 0:
                print(
                    f"File {file_path} is empty. Skipping autopep8 and pylint check.")
                return 10.0  # Assume perfect score for empty files

            # Run autopep8 to automatically fix style issues
            print(f"Running autopep8 on {file_path}")
            autopep8_cmd = ["poetry", "run", "autopep8",
                            "--in-place", "--aggressive", "--aggressive", file_path]
            subprocess.run(autopep8_cmd, check=True,
                           capture_output=True, text=True, cwd=self.pwd)
            print("autopep8 completed successfully.")

            # Determine if the file is a special file
            file_name = os.path.basename(file_path)
            is_test_file = 'test' in file_name.lower()
            is_init_file = file_name == '__init__.py'

            # Adjust pylint command for different file types
            pylint_cmd = ["poetry", "run", "pylint"]
            if is_test_file:
                pylint_cmd.extend(
                    ["--disable=missing-function-docstring,missing-module-docstring"])
            elif is_init_file:
                pylint_cmd.extend(["--disable=missing-module-docstring"])
            pylint_cmd.append(file_path)

            result = subprocess.run(
                pylint_cmd,
                capture_output=True,
                text=True,
                cwd=self.pwd
            )
            output = result.stdout + result.stderr
            score_match = re.search(
                r'Your code has been rated at (\d+\.\d+)/10', output)
            score = float(score_match.group(1)) if score_match else 0.0

            print(output)
            print(f"Pylint score for {file_path}: {score}/10")

            if score < 6.0:
                print(f"Score is below 6.0. Attempting to improve the code...")
                self.improve_code(file_path, score, output,
                                  is_test_file, is_init_file)

            elif 'missing-module-docstring' in output and not is_test_file and not is_init_file:
                self.add_module_docstring(file_path)
                # Re-run pylint after adding the docstring
                return self.clean_code_with_pylint(file_path)

            else:
                print(f"Code quality is good. Score: {score}/10")

            return score
        except subprocess.CalledProcessError as e:
            print(f"Error running autopep8 or pylint: {e}")
            return 0.0

    def add_module_docstring(self, file_path):
        with open(file_path, 'r') as file:
            content = file.read()

        if not content.startswith('"""'):
            module_name = os.path.basename(file_path).replace('.py', '')
            docstring = f'"""\nThis module contains the implementation for {
                module_name}.\n"""\n\n'
            with open(file_path, 'w') as file:
                file.write(docstring + content)
            print(f"Added module docstring to {file_path}")

    def improve_code(self, file_path, current_score, pylint_output, is_test_file, is_init_file, attempt=1):
        if current_score >= 6.0:
            print(f"Code quality is already good. Score: {current_score}/10")
            return

        if attempt > self.MAX_IMPROVEMENT_ATTEMPTS:
            print(f"Maximum improvement attempts reached for {
                  file_path}. Moving on.")
            return

        # Run autopep8 again before manual improvements
        print(f"Running autopep8 on {file_path}")
        autopep8_cmd = ["poetry", "run", "autopep8",
                        "--in-place", "--aggressive", "--aggressive", file_path]
        subprocess.run(autopep8_cmd, check=True,
                       capture_output=True, text=True, cwd=self.pwd)
        print("autopep8 completed successfully.")

        file_type = "test file" if is_test_file else "init file" if is_init_file else "regular Python file"
        prompt = f"""
        The current pylint score for {file_path} (a {file_type}) is {current_score:.2f}/10. Please analyze the pylint output and suggest improvements to reach a score of at least 6/10.

        {'This is a test file, so some rules like missing docstrings may not apply.' if is_test_file else ''}
        {'This is an __init__.py file, so it may not need a module docstring.' if is_init_file else ''}

        Pylint output:
        {pylint_output}

        Provide specific code changes to improve the score. Use the appropriate commands (cat, sed) to modify the file.
        Focus on addressing the issues reported by pylint, such as unused imports, code style issues, etc.
        {'For test files, focus on improving code quality without adding unnecessary docstrings.' if is_test_file else ''}
        {'For __init__.py files, focus on improving code quality while considering its special purpose.' if is_init_file else ''}
        """
        improvements = self.get_response(prompt)
        self.validate_and_execute_commands(improvements)

        # Run pylint again to check if the score improved
        new_score = self.clean_code_with_pylint(file_path)
        if new_score < 6.0:
            print(f"Score is still below 6.0. Attempting another improvement (attempt {
                  attempt + 1})...")
            self.improve_code(file_path, new_score, pylint_output,
                              is_test_file, is_init_file, attempt + 1)

    def improve_test_coverage(self, attempt=1):
        if attempt > self.MAX_IMPROVEMENT_ATTEMPTS:
            print("Maximum test coverage improvement attempts reached. Moving on.")
            return

        coverage_result = self.get_current_coverage()
        if coverage_result >= 80:
            print(f"Test coverage is already at {
                  coverage_result}%. No improvements needed.")
            return

        prompt = f"""
        The current test coverage for the project is {coverage_result}%, which is below the target of 80%.
        Please analyze the coverage report and suggest improvements to increase the coverage to at least 80%.

        Focus on:
        1. Adding new test cases for untested functions or methods.
        2. Testing edge cases and boundary conditions.
        3. Ensuring all code paths in the main implementation are tested.
        4. Use pytest fixtures where appropriate to set up test data.
        5. Use parametrized tests to cover multiple scenarios efficiently.

        Provide specific code changes or additional tests to improve the coverage.
        Use the following format for creating or modifying test files:
        cat > tests/test_filename.py << EOL
        # Test file content
        EOL

        or

        sed -i 's/old_content/new_content/g' tests/test_filename.py

        REMEMBER: Do not modify any files outside the 'tests' directory.
        """
        improvements = self.get_response(prompt)
        self.validate_and_execute_commands(improvements)

        new_coverage = self.get_current_coverage()
        if new_coverage < 80:
            print(f"Coverage is still below 80% (current: {
                  new_coverage}%). Attempting another improvement (attempt {attempt + 1})...")
            self.improve_test_coverage(attempt + 1)
        else:
            print(f"Coverage goal achieved. Current coverage: {new_coverage}%")

    def get_current_coverage(self):
        try:
            result = subprocess.run(
                ["poetry", "run", "pytest", "--cov=" + self.project_name,
                    "--cov-report=term-missing", "--cov-fail-under=0"],
                capture_output=True,
                text=True,
                cwd=self.pwd
            )
            coverage_match = re.search(
                r'TOTAL\s+\d+\s+\d+\s+(\d+)%', result.stdout)
            if coverage_match:
                return int(coverage_match.group(1))
            else:
                print("Couldn't parse coverage information. Assuming 0%")
                return 0
        except subprocess.CalledProcessError as e:
            print(f"Error running coverage: {e}")
            return 0

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
            if command_parts[0] in allowed_commands:
                if command_parts[0] == 'poetry' and 'run' in command_parts and 'streamlit' in command_parts:
                    print(
                        "Warning: Running Streamlit apps is not allowed. Skipping this command.")
                    return False
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
                corrected_command = self.auto_correct_command(command)

                if corrected_command.strip().startswith('cat >'):
                    if 'tests/__init__.py' in corrected_command:
                        print("Skipping creation of __init__.py in tests directory")
                        continue
                    self.execute_heredoc_command(corrected_command)
                elif corrected_command.startswith(('ls', 'cd', 'mkdir', 'poetry', 'sed', 'cat', 'echo', 'python3', 'source', 'pytest', 'python')):
                    result = subprocess.run(
                        corrected_command, shell=True, check=True, capture_output=True, text=True, cwd=self.pwd)
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
            if file_path.startswith('tests/'):
                if file_path.endswith('__init__.py'):
                    print("Skipping creation of __init__.py in tests directory")
                    return
                full_file_path = os.path.join(self.pwd, file_path)
            elif file_path.startswith(f'{self.project_name}/'):
                full_file_path = os.path.join(self.pwd, file_path)
            else:
                full_file_path = os.path.join(
                    self.pwd, self.project_name, file_path)

            # Ensure the directory exists
            os.makedirs(os.path.dirname(full_file_path), exist_ok=True)

            print(f"Writing file to: {full_file_path}")

            # Write the content to the file using a context manager
            with open(full_file_path, 'w') as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())

            # Add a small delay to ensure the file is fully written
            time.sleep(0.1)

            if self.file_exists_and_has_content(full_file_path):
                print(f"File successfully created/updated: {full_file_path}")
                self.verify_file_contents(full_file_path)

                # Clean the code if it's a Python file and not a test file
                if full_file_path.endswith('.py') and 'test_' not in os.path.basename(full_file_path) and 'tests/' not in full_file_path:
                    self.clean_code_with_pylint(full_file_path)
                elif 'test_' in os.path.basename(full_file_path) or 'tests/' in full_file_path:
                    print(f"Skipping pylint for test file: {full_file_path}")
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
        print("Running tests and checking code quality...")
        try:
            # Delete tests/__init__.py if it exists
            tests_init_file = os.path.join(self.pwd, 'tests', '__init__.py')
            if os.path.exists(tests_init_file):
                os.remove(tests_init_file)
                print(f"Deleted {tests_init_file}")

            # Run pylint only on non-test Python files in the project
            for root, dirs, files in os.walk(self.pwd):
                if 'tests' not in root:  # Skip the tests directory
                    for file in files:
                        if file.endswith('.py'):
                            file_path = os.path.join(root, file)
                            self.clean_code_with_pylint(file_path)

            # Create a .coveragerc file to exclude empty files and __init__.py
            coveragerc_content = """
    [run]
    source = {self.project_name}
    omit =
        */__init__.py
        tests/*
        **/test_*.py

    [report]
    exclude_lines =
        pragma: no cover
        def __repr__
        if self.debug:
        if __name__ == .__main__.:
        raise NotImplementedError
        pass
        except ImportError:
        def main
    """
            with open(os.path.join(self.pwd, '.coveragerc'), 'w') as f:
                f.write(coveragerc_content)

            # Run pytest with coverage
            result = subprocess.run(
                ["poetry", "run", "pytest", "--cov=fizzbuzz_456", "--cov-config=.coveragerc", 
                "--cov-report=term-missing", "--cov-fail-under=80"],
                capture_output=True,
                text=True,
                cwd=self.pwd
            )
            print("Pytest output:")
            print(result.stdout)
            print(result.stderr)

            # Check if coverage report was generated
            if "No data to report." in result.stdout or "No data to report." in result.stderr:
                print("No coverage data was collected. Ensure that the tests are running correctly.")
                return False

            if result.returncode == 0:
                print("All tests passed successfully and coverage is at least 80%.")
                return True
            else:
                print("Tests failed or coverage is below 80%. Please review the output above.")
                return False

        except subprocess.CalledProcessError as e:
            print(f"Error running tests: {e}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return False



@click.command()
@click.argument('task', required=False)
def cli(task: str = None):
    """
    Run Nemo Agent tasks to create Python projects using Poetry and Streamlit.
    If no task is provided, it will prompt the user for input.
    """
    if task is None:
        task = click.prompt("Please enter the task for Nemo Agent")

    nemo_agent = NemoAgent(task=task)
    nemo_agent.run_task()


if __name__ == "__main__":
    cli()
