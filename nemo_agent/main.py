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
10. Only use pytest for testing.
11. Always use module imports when referring to files in tests.
12. Use the following format for creating files:
    For code files with inline tests: cat > {project_name}/filename.py << EOL
13. IMPORTANT: Write to disk after EVERY step, no matter how small.
14. Always break up tests into multiple test functions for better organization.
15. Always mock external services, database calls, and APIs.
16. Always include module docstrings at the beginning of Python files, unless they are test files or __init__.py files.
17. You use your tools like `cd`, `ls`, and `cat` to verify and understand the contents of files and directories.
18. Always use `cat` with heredoc syntax to create and modify files. Example:
   cat > filename.py << EOL
   # File content here
   EOL
19. Use the following format for creating files:
            For code files: cat > {project_name}/filename.py << EOL
            For test files: cat > tests/test_filename.py << EOL
20. Never use `poetry shell` only use `poetry run` for running commands.
21. The test command is `poetry run pytest --cov={project_name} --cov-config=.coveragerc`
22. IMPORTANT: Write to disk after EVERY step using `cat` or `sed`, no matter how small.
23. You write code to the code directory on disk: {project_name}
24. You write tests to the tests directory on disk: tests
25. IMPORTANT: Never use pass statements in your code. Always provide a meaningful implementation.
26. Use `sed` for making specific modifications to existing files:
    sed -i 's/old_text/new_text/g' filename.py
27. Use the following format for creating files:
            For code files: cat > {project_name}/main.py << EOL
            For test files: cat > tests/test_main.py << EOL
Current working directory: {pwd}
"""


class CustomSystemTools:
    def __init__(self):
        self.pwd = os.getcwd()

    def execute_command(self, command: str) -> str:
        try:
            result = subprocess.run(
                command,
                shell=True,
                check=True,
                capture_output=True,
                text=True,
                cwd=self.pwd,
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error executing command: {e.stderr}"


class NemoAgent:
    MAX_IMPROVEMENT_ATTEMPTS = 10

    def __init__(self, task: str, model: str = "mistral-nemo"):
        self.pwd = os.getcwd()
        self.task = task
        self.model = model
        self.project_name = self.generate_project_name()
        self.assistant = self.setup_assistant()

    def setup_assistant(self):
        system_prompt = SYSTEM_PROMPT.format(
            pwd=self.pwd,
            project_name=self.project_name,
            os_name=os.uname().sysname,
            default_shell=os.environ.get("SHELL", "/bin/sh"),
            home_dir=os.path.expanduser("~"),
        )
        custom_system_tools = CustomSystemTools()
        return Assistant(
            llm=Ollama(model=self.model),
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
            llm=Ollama(model=self.model),
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
        project_name = response.strip().strip('"').strip("'").lower().replace(" ", "_")

        # Ensure the project name has exactly two segments
        segments = project_name.split("_")
        if len(segments) != 2:
            # If not, generate a default name
            # fmt: off
            project_name = f"task_{segments[0]}" if segments else "default_project"
            # fmt: on

        # Add a random 3-digit number as the third segment
        random_number = random.randint(100, 999)
        project_name = f"{project_name}_{random_number}"

        return project_name

    def initialize_git_repo(self):
        try:
            subprocess.run(["git", "init"], check=True, cwd=self.pwd)
            print("Git repository initialized.")

            # Set Git user name and email
            subprocess.run(
                ["git", "config", "user.name", "Nemo Agent"], check=True, cwd=self.pwd
            )
            subprocess.run(
                ["git", "config", "user.email", "hello@nemo-agent.com"],
                check=True,
                cwd=self.pwd,
            )
            print("Git user name and email configured.")

            # Create .gitignore file
            gitignore_content = """
            __pycache__/
            *.py[cod]
            .pytest_cache/
            .coverage
            """
            with open(os.path.join(self.pwd, ".gitignore"), "w") as f:
                f.write(gitignore_content)

            # Initial commit
            subprocess.run(["git", "add", "."], check=True, cwd=self.pwd)
            subprocess.run(
                ["git", "commit", "-m", "Initial commit"], check=True, cwd=self.pwd
            )
            print("Initial commit created.")
        except subprocess.CalledProcessError as e:
            print(f"Error initializing Git repository: {e}")

    def commit_changes(self, message):
        try:
            subprocess.run(["git", "add", "."], check=True, cwd=self.pwd)
            subprocess.run(["git", "commit", "-m", message],
                           check=True, cwd=self.pwd)
            print(f"Changes committed: {message}")
        except subprocess.CalledProcessError as e:
            print(f"Error committing changes: {e}")

    def get_git_diff(self):
        try:
            result = subprocess.run(
                ["git", "diff", "HEAD"], capture_output=True, text=True, cwd=self.pwd
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error getting Git diff: {e}")
            return ""

    def get_git_log(self, num_commits=5):
        try:
            result = subprocess.run(
                ["git", "log", f"-{num_commits}", "--oneline"],
                capture_output=True,
                text=True,
                cwd=self.pwd,
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error getting Git log: {e}")
            return ""

    def update_system_prompt(self):
        updated_prompt = SYSTEM_PROMPT.format(
            pwd=self.pwd,
            project_name=self.project_name,
            os_name=os.uname().sysname,
            default_shell=os.environ.get("SHELL", "/bin/sh"),
            home_dir=os.path.expanduser("~"),
        )
        self.assistant.system_prompt = updated_prompt

    def run_task(self):
        print(f"Current working directory: {os.getcwd()}")
        self.ensure_poetry_installed()
        self.create_project_with_poetry()
        self.check_and_fix_pyproject_toml()
        self.implement_solution()
        tests_passed, coverage = self.run_tests()
        if not tests_passed or coverage < 80:
            self.improve_test_coverage(initial_coverage=coverage)

        print("Task completed. Please review the output and make any necessary manual adjustments.")

    def ensure_poetry_installed(self):
        try:
            subprocess.run(
                ["poetry", "--version"], check=True, capture_output=True, text=True
            )
            print("Poetry is already installed.")
        except FileNotFoundError:
            print("Poetry is not installed. Installing Poetry...")
            try:
                subprocess.run("pip install poetry", shell=True, check=True)
                print("Poetry installed successfully.")
            except subprocess.CalledProcessError as e:
                print(f"Error installing Poetry: {e}")
                sys.exit(1)

    def create_project_with_poetry(self):
        print(f"Creating new Poetry project: {self.project_name}")
        try:
            self.initialize_git_repo()

            result = subprocess.run(
                ["poetry", "new", self.project_name],
                capture_output=True,
                text=True,
                cwd=self.pwd,
                check=True,
            )
            print(result.stdout)

            self.pwd = os.path.join(self.pwd, self.project_name)
            os.chdir(self.pwd)

            print(f"Project directory created: {self.pwd}")

            # Update the system prompt with the new working directory
            self.update_system_prompt()

            print(f"Current working directory: {os.getcwd()}")
            print("Contents of the directory:")
            print(os.listdir(self.pwd))

            subprocess.run(
                (
                    f"sed -i '/^\\[tool.poetry\\]/a packages = [{{include = \""
                    f"{self.project_name}\"}}]' pyproject.toml"
                ),
                shell=True,
                check=True,
                cwd=self.pwd,
            )
            print("Added packages variable to pyproject.toml")

            # Add [tool.pytest.ini-options] section to pyproject.toml
            subprocess.run(
                'sed -i \'$a\\[tool.pytest.ini-options]\\npython_paths = [".", "tests"]\' pyproject.toml',
                shell=True,
                check=True,
                cwd=self.pwd,
            )
            print("Added [tool.pytest.ini-options] section to pyproject.toml")

            try:
                subprocess.run(
                    [
                        "poetry",
                        "add",
                        "--dev",
                        "pytest@*",
                        "pylint@*",
                        "autopep8@*",
                        "pytest-cov@*",
                        "pytest-flask@*",
                        "httpx@*",
                    ],
                    check=True,
                    cwd=self.pwd,
                )
                print(
                    "Added pytest, pylint, autopep8, pytest-cov, pytest-flask, and httpx as development dependencies with latest versions."
                )
            except subprocess.CalledProcessError as e:
                print(f"Error adding development dependencies: {e}")

        except subprocess.CalledProcessError as e:
            print(f"Error creating Poetry project: {e.stderr}")
        except Exception as e:
            print(f"Error: {str(e)}")

    def implement_solution(self, max_attempts=3):
        prompt = f"""
        Create a comprehensive implementation for the task: {self.task}.
        You must follow these rules strictly:
            1. CRITICAL: only create one code file called `main.py` in {self.project_name} and one test file called `test_main.py` in tests/. Do not create any additional files.
            2. Use the correct import statements: from {self.project_name}.module_name import method_name.
            3. Follow PEP8 style guide and use type hints when appropriate.
            4. Never use pass statements in your code. Always provide a meaningful implementation.
            5. Use parametrized tests to cover multiple scenarios efficiently.
            6. Use the following for specifying file content:
                ```python
                # Filename: {self.project_name}/main.py
                # File content here
                ```
                ```python
                # Filename: tests/test_main.py
                # Test file content here
                ```
                ```toml
                # Filename: pyproject.toml
                # Updated pyproject.toml content here
                ```
            7. IMPORTANT: Only use `sed` for making specific modifications to existing files:
                sed -i 's/old_text/new_text/g' filename.py
            8. Use the following to create the files:
                        For code file: cat > {self.project_name}/main.py << EOL
                        For test file: cat > tests/test_main.py << EOL
        Working directory: {self.pwd}
        """

        for attempt in range(max_attempts):
            solution = self.get_response(prompt)
            print(f"Attempt {attempt + 1}: Executing solution:")
            print(solution)

            # Extract file contents from the solution
            file_contents = self.extract_file_contents(solution)

            # Write files using standard Python file operations
            for file_path, content in file_contents.items():
                full_path = os.path.join(self.pwd, file_path)
                try:
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, "w") as f:
                        f.write(content)
                    print(f"File written successfully: {full_path}")
                except Exception as e:
                    print(f"Error writing file {full_path}: {str(e)}")

            # Verify that files were created
            code_files = [f for f in os.listdir(os.path.join(
                self.pwd, self.project_name)) if f.endswith(".py") and f != "__init__.py"]
            test_files = [f for f in os.listdir(os.path.join(
                self.pwd, "tests")) if f.startswith("test_") and f.endswith(".py")]

            if len(code_files) == 1 and len(test_files) == 1 and os.path.exists(os.path.join(self.pwd, "pyproject.toml")):
                print("Files successfully created.")
                self.commit_changes("Implement initial solution")
                break
            else:
                print(
                    f"Attempt {attempt + 1} failed to create the correct files. Retrying...")

        # Validate that the implementation matches the original task
        if not self.validate_implementation():
            self.improve_implementation()

        # Run poetry update to ensure all dependencies are installed
        try:
            subprocess.run(["poetry", "update"], check=True, cwd=self.pwd)
            print("Poetry update completed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error updating dependencies: {e}")

    def write_file(self, file_path, content):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            f.write(content)
        print(f"File written successfully: {file_path}")

    def extract_file_contents(self, solution):
        file_contents = {}
        current_file = None
        current_content = []
        in_code_block = False

        for line in solution.split("\n"):
            stripped_line = line.strip()

            if stripped_line.startswith("# Filename:"):
                if current_file:
                    file_contents[current_file] = "\n".join(current_content)
                    current_content = []
                current_file = stripped_line.split(":", 1)[1].strip()
                in_code_block = False
            elif stripped_line.startswith("```"):
                in_code_block = not in_code_block
            elif current_file and not stripped_line.startswith("#") and not in_code_block:
                current_content.append(line)

        if current_file:
            file_contents[current_file] = "\n".join(current_content)

        return file_contents

    def validate_against_task(self, proposed_changes):
        prompt = f"""
        Review the following proposed changes and confirm if they correctly address the original task: {self.task}

        Proposed changes:
        {proposed_changes}

        If the proposed changes are correct and fully address the task, respond with 'VALID'.
        If the proposed changes do not match the task or are incomplete, respond with 'INVALID'.
        Provide a brief explanation for your decision.
        """
        response = self.get_response(prompt)
        if "VALID" in response.upper():
            print("Proposed changes validated successfully against the original task.")
            return True
        else:
            print("Proposed changes do not fully address the original task.")
            return False

    def improve_implementation(self):
        initial_pylint_score = self.get_pylint_score()
        initial_test_results, initial_coverage = self.run_tests()

        git_diff = self.get_git_diff()
        git_log = self.get_git_log()

        # Add this new block to check and clean existing files
        print("Checking and cleaning existing files...")
        for root, dirs, files in os.walk(self.pwd):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r') as f:
                        content = f.read()
                    cleaned_content = self.validate_file_content(
                        file_path, content)
                    if cleaned_content != content:
                        with open(file_path, 'w') as f:
                            f.write(cleaned_content)
                        print(f"Cleaned up file: {file_path}")
        print("File check and clean completed.")

        # Existing code continues from here
        prompt = f"""
        The current implementation needs improvement for the task: {self.task}
        Current pylint score: {initial_pylint_score:.2f}/10
        Current test status: {'Passing' if initial_test_results else 'Failing'}
        Current test coverage: {initial_coverage}%

        Git diff:
        {git_diff}

        Git log:
        {git_log}

        Please provide improvements to the existing code and tests to:
        1. Improve or maintain the pylint score (target: at least 6.0/10)
        2. Ensure all tests are passing
        3. Improve or maintain the test coverage (target: at least 80%)

        Follow these rules strictly:
        1. CRITICAL: The correct import statements for local files looks like `from {self.project_name}.module_name import method_name`.
        2. CRITICAL: Never create new files, only modify the existing ones.
        3. Only use pytest for testing.
        4. IMPORTANT: Never use pass statements in your code. Always provide a meaningful implementation.
        5. Consider the Git history when suggesting changes to avoid reverting recent improvements or duplicating work.
        6. Use parametrized tests to cover multiple scenarios efficiently
        7. IMPORTANT: Do not create new files. Only modify the existing files.
        8. IMPORTANT: Only use `sed` for making specific modifications to existing files:
            sed -i 's/old_text/new_text/g' filename.py
        9. IMPORTANT: Never remove existing poetry dependencies. Only add new ones if necessary.
        """
        improvements = self.get_response(prompt)
        print("Proposed improvements:")
        print(improvements)

        if self.validate_against_task(improvements):
            print("Executing validated improvements:")
            self.validate_and_execute_commands(improvements)

            # Check if the improvements actually improved both code quality and test coverage
            new_pylint_score = self.get_pylint_score()
            new_test_results, new_coverage = self.run_tests()

            if (
                new_pylint_score >= initial_pylint_score
                and new_test_results
                and new_coverage >= initial_coverage
            ):
                print("Improvements successfully applied.")
                self.commit_changes("Improve implementation")
                if self.validate_implementation():
                    print("Improved implementation validated successfully.")
                    return
                else:
                    print("Implementation still does not fully meet the requirements.")
            else:
                print(
                    "Improvements did not enhance both code quality and test coverage."
                )
        else:
            print("Proposed improvements do not align with the original task.")

        print("Attempting to recover implementation...")
        self.recover_implementation()

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
        Do not create new files - only modify the existing ones.
        Do not default to a generic or "Hello World" example.
        Follow all the rules and guidelines provided in the original implementation prompt.
        Ensure that the implementation maintains or improves the current pylint score and test coverage.
        """
        corrected_solution = self.get_response(prompt)
        print("Executing corrected solution:")
        print(corrected_solution)

        if self.validate_against_task(corrected_solution):
            initial_pylint_score = self.get_pylint_score()
            initial_test_results, initial_coverage = self.run_tests()

            self.validate_and_execute_commands(corrected_solution)

            new_pylint_score = self.get_pylint_score()
            new_test_results, new_coverage = self.run_tests()

            if (
                new_pylint_score >= initial_pylint_score
                and new_test_results
                and new_coverage >= initial_coverage
            ):
                print("Recovered implementation applied successfully.")
                self.commit_changes("Recover implementation")
                if self.validate_implementation():
                    print("Recovered implementation validated successfully.")
                    return
                else:
                    print(
                        "Recovered implementation still does not fully meet the requirements."
                    )
            else:
                print(
                    "Recovered implementation did not maintain or improve code quality and test coverage."
                )
        else:
            print("Recovered implementation does not align with the original task.")

        print("Failed to recover implementation. Manual intervention may be required.")

    def get_pylint_score(self):
        try:
            result = subprocess.run(
                ["poetry", "run", "pylint", self.project_name],
                capture_output=True,
                text=True,
                cwd=self.pwd,
            )
            score_match = re.search(
                r"Your code has been rated at (\d+\.\d+)/10", result.stdout
            )
            return float(score_match.group(1)) if score_match else 0.0
        except subprocess.CalledProcessError as e:
            print(f"Error running pylint: {e}")
            return 0.0

    def get_response(self, prompt, assistant=None):
        if assistant is None:
            assistant = self.assistant
        full_response = ""
        current_line = ""
        for response in assistant.run(prompt):
            if isinstance(response, str):
                full_response += response
                current_line += response
            elif isinstance(response, dict) and "content" in response:
                content = response["content"]
                full_response += content
                current_line += content
            else:
                full_response += str(response)
                print(str(response))

            if "\n" in current_line:
                lines = current_line.split("\n")
                for line in lines[:-1]:
                    print(line)
                current_line = lines[-1]

        if current_line:
            print(current_line)

        return full_response.strip()

    def clean_code_with_pylint(self, file_path):
        try:
            # Check if the file is empty
            if os.path.getsize(file_path) == 0:
                print(
                    f"File {file_path} is empty. Skipping autopep8 and pylint check.")
                return 10.0  # Assume perfect score for empty files

            # Run autopep8 to automatically fix style issues
            print(f"Running autopep8 on {file_path}")
            autopep8_cmd = [
                "poetry",
                "run",
                "autopep8",
                "--in-place",
                "--aggressive",
                "--aggressive",
                file_path,
            ]
            subprocess.run(
                autopep8_cmd, check=True, capture_output=True, text=True, cwd=self.pwd
            )
            print("autopep8 completed successfully.")

            # Determine if the file is a special file
            file_name = os.path.basename(file_path)
            is_test_file = "test" in file_name.lower()
            is_init_file = file_name == "__init__.py"

            # Adjust pylint command for different file types
            pylint_cmd = ["poetry", "run", "pylint"]
            if is_test_file:
                pylint_cmd.extend(
                    ["--disable=missing-function-docstring,missing-module-docstring"]
                )
            elif is_init_file:
                pylint_cmd.extend(["--disable=missing-module-docstring"])
            pylint_cmd.append(file_path)

            result = subprocess.run(
                pylint_cmd, capture_output=True, text=True, cwd=self.pwd
            )
            output = result.stdout + result.stderr
            score_match = re.search(
                r"Your code has been rated at (\d+\.\d+)/10", output
            )
            score = float(score_match.group(1)) if score_match else 0.0

            print(output)
            print(f"Pylint score for {file_path}: {score}/10")

            if score < 6.0:
                print("Score is below 6.0. Attempting to improve the code...")
                self.improve_code(file_path, score, output,
                                  is_test_file, is_init_file)

            elif (
                "missing-module-docstring" in output
                and not is_test_file
                and not is_init_file
            ):
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
        with open(file_path, "r") as file:
            content = file.read()

        if not content.startswith('"""'):
            module_name = os.path.basename(file_path).replace(".py", "")
            docstring = (
                f'"""\nThis module contains the implementation for '
                f'{module_name}.\n"""\n\n'
            )
            with open(file_path, "w") as file:
                file.write(docstring + content)
            print(f"Added module docstring to {file_path}")

    def improve_code(
        self,
        file_path,
        current_score,
        pylint_output,
        is_test_file,
        is_init_file,
        attempt=1,
    ):
        if current_score >= 6.0:
            print(f"Code quality is already good. Score: {current_score}/10")
            return current_score

        if attempt > self.MAX_IMPROVEMENT_ATTEMPTS:
            # fmt: off
            print(f"Maximum improvement attempts reached for {file_path}. Moving on.")
            # fmt: on
            return current_score

        # Check and fix pyproject.toml
        self.check_and_fix_pyproject_toml()

        git_diff = self.get_git_diff()
        git_log = self.get_git_log()

        file_type = (
            "test file"
            if is_test_file
            else "init file"
            if is_init_file
            else "regular Python file"
        )
        prompt = f"""
        The current pylint score for {file_path} (a {file_type}) is {current_score:.2f}/10. Please analyze the pylint output and suggest improvements to reach a score of at least 6/10.

        {'This is an __init__.py file, so it may not need a module docstring.' if is_init_file else ''}

        Pylint output:
        {pylint_output}

         Git diff:
        {git_diff}

        Git log:
        {git_log}

        Original task: {self.task}

        Provide specific code changes to improve the score.
        Follow these rules strictly:
        1. CRITICAL: The correct import statements for local files looks like `from {self.project_name}.module_name import method_name`.
        2. IMPORTANT: Never use pass statements in your code. Always provide a meaningful implementation.
        3. Only use pytest for testing.
        4. CRITICAL: Never create new files. Only modify the existing ones.
        5. Consider the Git history when suggesting changes to avoid reverting recent improvements.
        6. Use parametrized tests to cover multiple scenarios efficiently
        7. IMPORTANT: Only use `sed` for making specific modifications to existing files:
            sed -i 's/old_text/new_text/g' filename.py
        8. IMPORTANT: Never modify the existing pyproject.toml dependencies.
        9. IMPORTANT: Do not add new imports in the code or tests files for 3rd party dependencies.
        """
        proposed_improvements = self.get_response(prompt)

        if self.validate_against_task(proposed_improvements):
            print("Executing validated improvements:")
            self.validate_and_execute_commands(proposed_improvements)

            new_score = self.clean_code_with_pylint(file_path)

            if new_score < 6.0:
                # fmt: off
                print(f"Score is still below 6.0. Attempting another improvement (attempt {attempt + 1})...")
                # fmt: on
                return self.improve_code(
                    file_path,
                    new_score,
                    pylint_output,
                    is_test_file,
                    is_init_file,
                    attempt + 1,
                )
            else:
                print(f"Code quality improved. New score: {new_score}/10")
                self.commit_changes(
                    f"Improve code quality for {file_path} to {new_score}/10"
                )
                return new_score
        else:
            print(
                "Proposed improvements do not align with the original task. Skipping this improvement attempt."
            )
            if attempt < self.MAX_IMPROVEMENT_ATTEMPTS:
                print(
                    f"Attempting another improvement (attempt {attempt + 1})...")
                return self.improve_code(
                    file_path,
                    current_score,
                    pylint_output,
                    is_test_file,
                    is_init_file,
                    attempt + 1,
                )
            else:
                return current_score

    def improve_test_coverage(self, attempt=1, initial_coverage=0):
        if attempt > self.MAX_IMPROVEMENT_ATTEMPTS:
            print("Maximum test coverage improvement attempts reached. Moving on.")
            return initial_coverage

        coverage_result = (
            initial_coverage if attempt == 1 else self.get_current_coverage()
        )
        if coverage_result >= 80:
            # fmt: off
            print(f"Test coverage is already at {coverage_result}%. No improvements needed.")
            # fmt: on
            return coverage_result

        git_diff = self.get_git_diff()
        git_log = self.get_git_log()

        prompt = f"""
        The current test coverage for the project is {coverage_result}%, which is below the target of 80%.
        Please analyze the coverage report and suggest improvements to increase the coverage to at least 80%.

        Git diff:
        {git_diff}

        Git log:
        {git_log}

        Original task: {self.task}

        Provide specific code changes to improve the test coverage.
        Follow these rules strictly:
        1. Analyze the code and tests files to provide better changes using the `cd`, `ls`, or `cat` commands.
        2. IMPORTANT: Never use pass statements in your code. Always provide a meaningful implementation.
        3. Only use pytest for testing.
        4. CRITICAL: Only modify the existing tests files. Do not create new files.
        5. Make the minimum changes necessary in test files to improve the coverage.
        6. Consider the Git history when suggesting changes to avoid reverting recent improvements or duplicating tests.
        7. Use parametrized tests to cover multiple scenarios efficiently
        8. IMPORTANT: Do not create new files. Only modify the existing ones.
        9. IMPORTANT: Only use `sed` for making specific modifications to existing files:
            sed -i 's/old_text/new_text/g' filename.py
        10. IMPORTANT: Never modify the existing pyproject.toml dependencies.
        11. IMPORTANT: Do not add new imports in the code or tests files for 3rd party dependencies.
        """
        proposed_improvements = self.get_response(prompt)

        if self.validate_against_task(proposed_improvements):
            print("Executing validated improvements:")
            self.validate_and_execute_commands(proposed_improvements)

            new_coverage = self.get_current_coverage()
            if new_coverage < 80:
                # fmt: off
                print(f"Coverage is still below 80% (current: {new_coverage}%). Attempting another improvement (attempt {attempt + 1})...")
                # fmt: on
                return self.improve_test_coverage(attempt + 1, new_coverage)
            else:
                print(f"Coverage goal achieved. Current coverage: {
                      new_coverage}%")
                self.commit_changes(
                    f"Improve test coverage to {new_coverage}%")
                return new_coverage
        else:
            print(
                "Proposed improvements do not align with the original task. Skipping this improvement attempt."
            )
            if attempt < self.MAX_IMPROVEMENT_ATTEMPTS:
                print(
                    f"Attempting another improvement (attempt {attempt + 1})...")
                return self.improve_test_coverage(attempt + 1, coverage_result)
            else:
                return coverage_result

    def check_and_fix_pyproject_toml(self):
        pyproject_path = os.path.join(self.pwd, "pyproject.toml")
        if not os.path.exists(pyproject_path):
            print("pyproject.toml not found. Creating a new one.")
            self.create_default_pyproject_toml()
        else:
            with open(pyproject_path, 'r') as f:
                content = f.read()

            # Check for common issues and fix them
            fixed_content = self.fix_pyproject_toml_issues(content)

            if fixed_content != content:
                with open(pyproject_path, 'w') as f:
                    f.write(fixed_content)
                print("Fixed issues in pyproject.toml")
            else:
                print("No issues found in pyproject.toml")

    def validate_file_content(self, file_path, content):
        if file_path.endswith('.py'):
            # Check for markdown artifacts
            if '```python' in content or '```' in content:
                print(f"Warning: Markdown artifacts found in {file_path}")
                content = self.clean_markdown_artifacts(content)

            # Validate Python syntax
            try:
                ast.parse(content)
            except SyntaxError as e:
                print(f"Syntax error in {file_path}: {e}")
                return None

        return content

    def clean_markdown_artifacts(self, content):
        # Remove markdown code block syntax
        content = re.sub(r'```python\n', '', content)
        content = re.sub(r'```\n', '', content)
        content = re.sub(r'```', '', content)

        # Remove any remaining markdown syntax (you can add more as needed)
        content = re.sub(r'#{1,6}\s', '', content)  # Remove headers
        content = re.sub(r'\*\*(.+?)\*\*', r'\1', content)  # Remove bold
        content = re.sub(r'\*(.+?)\*', r'\1', content)  # Remove italic

        return content

    def create_default_pyproject_toml(self):
        default_content = f"""
    [tool.poetry]
    name = "{self.project_name}"
    version = "0.1.0"
    description = ""
    authors = ["Your Name <you@example.com>"]

    [tool.poetry.dependencies]
    python = "^3.8"

    [tool.poetry.dev-dependencies]
    pytest = "^6.2"
    pytest-cov = "^2.12"

    [build-system]
    requires = ["poetry-core>=1.0.0"]
    build-backend = "poetry.core.masonry.api"

    [tool.pytest.ini_options]
    pythonpath = [
    "."
    ]
        """
        with open(os.path.join(self.pwd, "pyproject.toml"), 'w') as f:
            f.write(default_content)
        print("Created default pyproject.toml")

    def fix_pyproject_toml_issues(self, content):
        # Fix common issues here
        fixed_content = content

        # Ensure the project name is correct
        fixed_content = re.sub(
            r'name = ".*"', f'name = "{self.project_name}"', fixed_content)

        # Ensure pytest-cov is in dev-dependencies
        if 'pytest-cov' not in fixed_content:
            fixed_content = fixed_content.replace(
                "[tool.poetry.dev-dependencies]",
                "[tool.poetry.dev-dependencies]\npytest-cov = \"^2.12\""
            )

        # Ensure pythonpath is set correctly
        if '[tool.pytest.ini_options]' not in fixed_content:
            fixed_content += '\n[tool.pytest.ini_options]\npythonpath = ["."]\n'

        # Fix unclosed inline table issue
        fixed_content = re.sub(
            r'(\[.*?\].*?{[^}]*$)', r'\1}', fixed_content, flags=re.DOTALL)

        return fixed_content

    def get_current_coverage(self):
        try:
            result = subprocess.run(
                [
                    "poetry",
                    "run",
                    "pytest",
                    "--cov=" + self.project_name,
                    "--cov-config=.coveragerc",
                ],
                capture_output=True,
                text=True,
                cwd=self.pwd,
            )
            coverage_match = re.search(
                r"TOTAL\s+\d+\s+\d+\s+(\d+)%", result.stdout)
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
        lines = response.split("\n")
        in_bash_block = False
        current_command = ""
        in_heredoc = False
        heredoc_delimiter = ""

        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith("```bash"):
                in_bash_block = True
            elif stripped_line.startswith("```") and in_bash_block:
                in_bash_block = False
                if current_command:
                    commands.append(current_command.strip())
                    current_command = ""
            elif in_bash_block:
                if not in_heredoc and "<<" in stripped_line:
                    heredoc_delimiter = stripped_line.split("<<", 1)[1].strip()
                    in_heredoc = True
                    current_command += line + "\n"
                elif in_heredoc and stripped_line == heredoc_delimiter:
                    in_heredoc = False
                    current_command += line + "\n"
                elif in_heredoc:
                    current_command += line + "\n"
                else:
                    if current_command:
                        commands.append(current_command.strip())
                    current_command = stripped_line

        if current_command:
            commands.append(current_command.strip())

        return commands

    def auto_correct_command(self, command):
        corrections = {
            "pyhton": "python",
            "pirnt": "print",
            "impotr": "import",
            "defien": "define",
            "fucntion": "function",
            "retrun": "return",
            "flase": "false",
            "ture": "true",
            "elif": "elif",
            "esle": "else",
            "fixtrue": "fixture",
            "@pytest.fixtrue": "@pytest.fixture",
        }
        for typo, correction in corrections.items():
            command = command.replace(typo, correction)
        return command

    def validate_command(self, command):
        allowed_commands = [
            "cat",
            "ls",
            "cd",
            "mkdir",
            "sed",
            "poetry",
            "echo",
            "python3",
            "source",
            "pytest",
            "python",
            "git",
        ]
        command_parts = command.strip().split()
        if command_parts:
            if command_parts[0] in allowed_commands:
                if (
                    command_parts[0] == "poetry"
                    and "run" in command_parts
                    and "streamlit" in command_parts
                ):
                    print(
                        "Warning: Running Streamlit apps is not allowed. Skipping this command."
                    )
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

                if corrected_command.strip().startswith("cat >"):
                    self.execute_heredoc_command(corrected_command)
                elif corrected_command.startswith(
                    (
                        "ls",
                        "cd",
                        "mkdir",
                        "poetry",
                        "sed",
                        "cat",
                        "echo",
                        "python3",
                        "source",
                        "pytest",
                        "python",
                        "git",
                    )
                ):
                    result = subprocess.run(
                        corrected_command,
                        shell=True,
                        check=True,
                        capture_output=True,
                        text=True,
                        cwd=self.pwd,
                    )
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
            with open(file_path, "r") as f:
                content = f.read()
            print(f"Contents of {file_path}:")
            print(content)
            print(f"File size: {os.path.getsize(file_path)} bytes")
        except Exception as e:
            print(f"Error verifying file contents: {e}")

    def execute_heredoc_command(self, command):
        try:
            file_path, content = command.split("<<", 1)
            file_path = file_path.split(">", 1)[1].strip()
            content = content.strip()

            # Remove the EOL markers
            content_lines = content.split("\n")
            if len(content_lines) >= 2 and content_lines[0] == content_lines[-1]:
                content = "\n".join(content_lines[1:-1])

            # Ensure the file path is within the project directory
            if file_path.startswith("tests/"):
                full_file_path = os.path.join(self.pwd, file_path)
            elif file_path.startswith(f"{self.project_name}/"):
                full_file_path = os.path.join(self.pwd, file_path)
            else:
                full_file_path = os.path.join(
                    self.pwd, self.project_name, file_path)

            # Ensure the directory exists
            os.makedirs(os.path.dirname(full_file_path), exist_ok=True)

            # Validate and clean the content
            validated_content = self.validate_file_content(
                full_file_path, content)
            if validated_content is None:
                # fmt: off
                print(f"Failed to validate content for {full_file_path}. Skipping file creation.")
                # fmt: on
                return

            # Ensure the directory exists
            os.makedirs(os.path.dirname(full_file_path), exist_ok=True)

            print(f"Writing file to: {full_file_path}")

            # Write the content to the file using a context manager
            print(f"Attempting to write file: {full_file_path}")
            with open(full_file_path, "w") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            if os.path.exists(full_file_path):
                print(f"File created successfully: {full_file_path}")
                print("File contents:")
                with open(full_file_path, "r") as f:
                    print(f.read())
            else:
                print(f"Failed to create file: {full_file_path}")

            # Add a small delay to ensure the file is fully written
            time.sleep(0.1)

            if self.file_exists_and_has_content(full_file_path):
                print(f"File successfully created/updated: {full_file_path}")
                self.verify_file_contents(full_file_path)

                # Clean the code if it's a Python file and not a test file
                if (
                    full_file_path.endswith(".py")
                    and "test_" not in os.path.basename(full_file_path)
                    and "tests/" not in full_file_path
                ):
                    self.clean_code_with_pylint(full_file_path)
                elif (
                    "test_" in os.path.basename(full_file_path)
                    or "tests/" in full_file_path
                ):
                    print(f"Skipping pylint for test file: {full_file_path}")
            else:
                print(f"Failed to create/update file: {full_file_path}")

        except Exception as e:
            print(f"Error executing heredoc command: {e}")
            print(f"Command that caused the error: {command}")

    def extract_python_code(self, command):
        match = re.search(r"cat > .*\.py << EOL\n(.*?)\nEOL",
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
            # Run pylint only on non-test Python files in the project
            for root, dirs, files in os.walk(self.pwd):
                if "tests" not in root:  # Skip the tests directory
                    for file in files:
                        if file.endswith(".py"):
                            file_path = os.path.join(root, file)
                            self.clean_code_with_pylint(file_path)

            # Create a .coveragerc file to exclude empty files and __init__.py
            coveragerc_content = f"""
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
            with open(os.path.join(self.pwd, ".coveragerc"), "w") as f:
                f.write(coveragerc_content)

            # Run pytest with coverage
            result = subprocess.run(
                [
                    "poetry",
                    "run",
                    "pytest",
                    "--cov=" + self.project_name,
                    "--cov-config=.coveragerc",
                    "--cov-report=term-missing",
                ],
                capture_output=True,
                text=True,
                cwd=self.pwd,
            )
            print("Pytest output:")
            print(result.stdout)
            print(result.stderr)

            # Check if coverage report was generated
            if (
                "No data to report." in result.stdout
                or "No data to report." in result.stderr
            ):
                print(
                    "No coverage data was collected. Ensure that the tests are running correctly."
                )
                return False, 0

            # Extract coverage percentage
            coverage_match = re.search(
                r"TOTAL\s+\d+\s+\d+\s+(\d+)%", result.stdout)
            coverage_percentage = int(
                coverage_match.group(1)) if coverage_match else 0

            # Check if all tests passed
            tests_passed = (
                "failed" not in result.stdout.lower() and result.returncode == 0
            )

            if tests_passed and coverage_percentage >= 80:
                print(
                    f"All tests passed successfully and coverage is "
                    f"{coverage_percentage}%."
                )
                return True, coverage_percentage
            else:
                if not tests_passed:
                    print("Some tests failed. Please review the test output above.")
                if coverage_percentage < 80:
                    print(
                        f"Coverage is below 80%. "
                        f"Current coverage: {coverage_percentage}%"
                    )
                return False, coverage_percentage

        except subprocess.CalledProcessError as e:
            print(f"Error running tests: {e}")
            return False, 0
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return False, 0


@click.command()
@click.argument("task", required=False)
@click.option(
    "--model", default="mistral-nemo", help="The model to use for the Ollama LLM"
)
def cli(task: str = None, model: str = "mistral-nemo"):
    """
    Run Nemo Agent tasks to create Python projects using Poetry and Pytest.
    If no task is provided, it will prompt the user for input.
    """
    if task is None:
        task = click.prompt("Please enter the task for Nemo Agent")

    nemo_agent = NemoAgent(task=task, model=model)
    nemo_agent.run_task()


if __name__ == "__main__":
    cli()
