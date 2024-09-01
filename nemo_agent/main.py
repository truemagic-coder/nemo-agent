import ast
from contextlib import contextmanager
from datetime import time
import fcntl
import io
import json
import logging
import os
import platform
import random
import re
import shutil
import subprocess
import sys
import zipfile
import click
import requests
import openai
from anthropic import Anthropic


class OllamaAPI:
    def __init__(self, model):
        self.model = model
        self.base_url = "http://localhost:11434/api"

    def generate(self, prompt):
        url = f"{self.base_url}/generate"
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": True
        }
        response = requests.post(url, json=data, stream=True)
        if response.status_code == 200:
            full_response = ""
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    try:
                        json_line = json.loads(decoded_line)
                        chunk = json_line.get('response', '')
                        full_response += chunk
                        print(chunk, end='', flush=True)
                    except json.JSONDecodeError:
                        print(f"Error decoding JSON: {decoded_line}")
            print()  # Print a newline at the end
            return full_response
        else:
            raise Exception(f"Ollama API error: {response.text}")


class OpenAIAPI:
    def __init__(self, model):
        if model == "mistral-nemo":
            model = "gpt-4o-2024-08-06"
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        openai.api_key = self.api_key

    def generate(self, prompt):
        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    chunk_text = chunk.choices[0].delta.content
                    full_response += chunk_text
                    print(chunk_text, end='', flush=True)
            print()  # Print a newline at the end
            return full_response
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")


class ClaudeAPI:
    def __init__(self, model):
        if model == "mistral-nemo":
            model = "claude-3-5-sonnet-20240620"
        self.model = model
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is not set")
        self.client = Anthropic(api_key=self.api_key)

    def generate(self, prompt):
        try:
            response = self.client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
                max_tokens=1000
            )
            full_response = ""
            for completion in response:
                if completion.type == "content_block_delta":
                    chunk_text = completion.delta.text
                    full_response += chunk_text
                    print(chunk_text, end='', flush=True)
            print()  # Print a newline at the end
            return full_response
        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}")


class NemoAgent:
    MAX_IMPROVEMENT_ATTEMPTS = 10
    MAX_WRITE_ATTEMPTS = 3
    WRITE_RETRY_DELAY = 1  # second

    def __init__(self, task: str, model: str = "mistral-nemo", provider: str = "ollama"):
        self.pwd = os.getcwd()
        self.task = task
        self.model = model
        self.provider = provider
        self.setup_logging()
        self.project_name = self.generate_project_name()
        self.llm = self.setup_llm()
        self.previous_suggestions = set()

    def setup_llm(self):
        if self.provider == "ollama":
            return OllamaAPI(self.model)
        elif self.provider == "openai":
            return OpenAIAPI(self.model)
        elif self.provider == "claude":
            return ClaudeAPI(self.model)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

    def generate_project_name(self):
        random_number = random.randint(100, 999)
        project_name = f"project_{random_number}"

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

    def run_task(self):
        print(f"Current working directory: {os.getcwd()}")
        self.ensure_poetry_installed()
        self.create_project_with_poetry()
        self.implement_solution()

        max_improvement_attempts = 3
        for attempt in range(max_improvement_attempts):
            tests_passed, coverage, test_output = self.run_tests()
            if coverage >= 80:
                print(f"Task completed successfully after {attempt + 1} attempts.")
                print(f"Coverage is {coverage}%.")
                if not tests_passed:
                    print(
                        "Note: Some tests are still failing, but coverage is above 80%."
                    )
                return  # Exit the method immediately
            elif attempt < max_improvement_attempts - 1:
                print(f"Attempt {attempt + 1} failed. Trying to improve implementation...")
                self.improve_implementation(test_output)
                print("Attempting to improve test file...")
                self.improve_test_file(test_output)
            else:
                print(
                    "Maximum improvement attempts reached. Please review the output manually."
                )

        print(
            "Task completed. Please review the output and make any necessary manual adjustments."
        )

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

            # Initialize Git repository in the project directory
            self.initialize_git_repo()

            print(f"Current working directory: {os.getcwd()}")
            print("Contents of the directory:")
            print(os.listdir(self.pwd))

            # Determine the operating system
            is_mac = platform.system() == "Darwin"

            # First sed command
            sed_inplace = "-i ''" if is_mac else "-i"
            sed_command_1 = f"""
            sed {sed_inplace} '
            /^\\[tool.poetry\\]/a\\
            packages = [{{include = "{self.project_name}"}}]
            ' pyproject.toml
            """

            subprocess.run(
                sed_command_1,
                shell=True,
                check=True,
                cwd=self.pwd,
            )
            print("Added packages variable to pyproject.toml")

            # Second sed command
            sed_command_2 = f"""
            sed {sed_inplace} '
            $a\\
            [tool.pytest.ini-options]\\
            python_paths = [".","tests"]
            ' pyproject.toml
            """

            subprocess.run(
                sed_command_2,
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
                        "complexipy@*",
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

    @contextmanager
    def file_lock(self, file_path):
        lock_path = f"{file_path}.lock"
        with open(lock_path, "w") as lock_file:
            try:
                fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                yield
            finally:
                fcntl.flock(lock_file, fcntl.LOCK_UN)
                os.remove(lock_path)

    def robust_write_file(self, file_path: str, content: str) -> bool:
        self.logger.info(f"Attempting to write to file: {file_path}")
        for attempt in range(self.MAX_WRITE_ATTEMPTS):
            try:
                with self.file_lock(file_path):
                    # Write the new content
                    with open(file_path, "w") as f:
                        f.write(content)
                    self.logger.info(
                        f"Successfully wrote to file: {file_path}")
                    return True
            except IOError as e:
                self.logger.error(f"IOError writing to {file_path}: {e}")
                if attempt < self.MAX_WRITE_ATTEMPTS - 1:
                    self.logger.info(
                        f"Retrying in {self.WRITE_RETRY_DELAY} seconds...")
                    time.sleep(self.WRITE_RETRY_DELAY)
                else:
                    self.logger.error(f"Failed to write to {file_path} after {self.MAX_WRITE_ATTEMPTS} attempts")
            except Exception as e:
                self.logger.error(
                    f"Unexpected error writing to {file_path}: {e}")
                break
        return False

    def process_file_changes(self, proposed_changes):
        file_contents = self.extract_file_contents_direct(proposed_changes)
        success = True

        for file_path, content in file_contents.items():
            full_path = os.path.join(self.pwd, file_path)
            try:
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                content = self.clean_markdown_artifacts(content)

                with open(full_path, "w") as f:
                    self.robust_write_file(full_path, content)

                if os.path.exists(full_path) and os.path.getsize(full_path) > 0:
                    self.logger.info(f"File written successfully: {full_path}")
                    with open(full_path, "r") as f:
                        self.logger.debug(
                            f"Content of {full_path}:\n{f.read()}")

                    # Run pylint only on files in the project folder
                    if full_path.startswith(os.path.join(self.pwd, self.project_name)):
                        pylint_score, complexipy_score = self.clean_code_with_pylint(full_path)
                        if pylint_score < 7.0 and complexipy_score is not None and complexipy_score > 15:
                            self.logger.warning(f"Pylint score for {full_path} is below 7.0: {pylint_score}")
                            success = False
                else:
                    self.logger.error(
                        f"Failed to write file or file is empty: {full_path}"
                    )
                    success = False
            except Exception as e:
                self.logger.error(f"Error writing file {full_path}: {str(e)}")
                success = False

        return success

    def implement_solution(self, max_attempts=3):
        prompt = f"""
            Create a comprehensive implementation for the task: {self.task}.
            You must follow these rules strictly:
                1. Use the correct import statements: from {self.project_name}.module_name import method_name.
                2. Follow PEP8 style guide.
                3. IMPORTANT: Never use pass statements in your code or tests. Always provide a meaningful implementation.
                4. Use parametrized tests to cover multiple scenarios efficiently.
                5. CRITICAL: Use the following code block format for specifying file content:                
                    For code files, use:
                    <<<{self.project_name}/main.py>>>
                    # File content here
                    <<<end>>>

                    For test files, use:
                    <<<tests/test_main.py>>>
                    # Test file content here
                    <<<end>>>

                    For HTML templates (Flask), use:
                    <<<templates/template_name.html>>>
                    <!-- HTML content here -->
                    <<<end>>>

                    For static files (CSS, JS), use:
                    <<<static/filename.ext>>>
                    // Static file content here
                    <<<end>>>
                6. The test command is `poetry run pytest --cov={self.project_name} --cov-config=.coveragerc`
                7. IMPORTANT: Do not add any code comments to the files.
                8. IMPORTANT: Always follow PEP8 style guide, follow best practices for Python, use snake_case naming, and provide meaningful docstrings.
                9. IMPORTANT: Do not redefine built-in functions or use reserved keywords as variable names.
                10. CRITICAL: Create any non-existent directories or files as needed that are not Python files.
                11. CRITICAL: Your response should ONLY contain the code blocks and `poetry add package_name` command at the end after all the code blocks. Do not include any explanations or additional text.
                12. IMPORTANT: For Flask apps, create necessary HTML templates in the 'templates' directory.
                13. IMPORTANT: For Flask apps, create necessary static files (CSS, JS) in the 'static' directory.
                14. IMPORTANT: Do not modify the existing poetry dependencies. Only add new ones if necessary.
                15. IMPORTANT: Use the flask-testing library for testing Flask apps.
                16. IMPORTANT: Only create 1 file for the main implementation: {self.project_name}/main.py
                17. IMPORTANT: Only create 1 file for the tests: tests/test_main.py
            Working directory: {self.pwd}
            """

        for attempt in range(max_attempts):
            self.logger.info(f"Attempt {attempt + 1} to implement solution")
            solution = self.get_response(prompt)
            self.logger.info(f"Received solution:\n{solution}")

            # Parse and execute any poetry add commands
            poetry_commands = [line.strip() for line in solution.split('\n') if line.strip().startswith('poetry add')]
            for command in poetry_commands:
                try:
                    subprocess.run(command, shell=True, check=True)
                    self.logger.info(f"Executed command: {command}")
                except subprocess.CalledProcessError as e:
                    self.logger.error(f"Failed to execute command: {command}. Error: {str(e)}")

            success = self.process_file_changes(solution)

            if success:
                self.logger.info(
                    "All files created successfully and passed pylint check"
                )
                self.commit_changes("Implement initial solution")
                return True

            self.logger.warning(f"Attempt {attempt + 1} failed to create the correct files or pass pylint. Retrying...")

        self.logger.error(
            "Failed to implement solution after maximum attempts")
        return False

    def extract_content_between_markers(self, text, start_marker, end_marker):
        start_index = text.find(start_marker)
        if start_index == -1:
            return None
        start_index += len(start_marker)
        end_index = text.find(end_marker, start_index)
        if end_index == -1:
            return None
        return text[start_index:end_index].strip()

    def extract_file_contents_direct(self, solution):
        file_contents = {}
        pattern = r"<<<(.+?)>>>\n(.*?)<<<end>>>"
        matches = re.findall(pattern, solution, re.DOTALL)

        for filename, content in matches:
            file_contents[filename.strip()] = content.strip()

        return file_contents

    def validate_against_task(self, proposed_changes):
        prompt = f"""
        Review the following proposed changes and confirm if they correctly address the original task: {self.task}

        Proposed changes:
        {proposed_changes}

        If the proposed changes are correct and fully address the task, respond with 'VALID'.
        If the proposed changes do not match the task or are incomplete, respond with 'INVALID'.
        Do not provide any additional information or explanations.
        """
        response = self.get_response(prompt)
        if "VALID" in response.upper():
            print("Proposed changes validated successfully against the original task.")
            return True
        else:
            print("Proposed changes do not fully address the original task.")
            return False

    def improve_implementation(self, test_output=""):
        initial_pylint_score = self.get_pylint_score()
        initial_complexipy_score = self.get_complexipy_score()
        initial_test_results, initial_coverage, _ = self.run_tests()

        git_diff = self.get_git_diff()
        git_log = self.get_git_log()

        print("Checking and cleaning existing files...")
        for root, dirs, files in os.walk(self.pwd):
            for file in files:
                if file.endswith(".py") and not file.startswith("test_"):
                    file_path = os.path.join(root, file)
                    with open(file_path, "r") as f:
                        content = f.read()
                    cleaned_content = self.validate_file_content(
                        file_path, content)
                    if cleaned_content != content:
                        with open(file_path, "w") as f:
                            f.write(cleaned_content)
                        print(f"Cleaned up file: {file_path}")
        print("File check and clean completed.")

        prompt = f"""
        The current implementation needs improvement for the task: {self.task}
        Current pylint score: {initial_pylint_score:.2f}/10
        Current complexipy score: {initial_complexipy_score}
        Current test status: {'Passing' if initial_test_results else 'Failing'}
        Current test coverage: {initial_coverage}%

        Test output:
        {test_output}

        Git diff:
        {git_diff}

        Git log:
        {git_log}

        Please provide improvements to the existing code to:
        1. Improve or maintain the pylint score (target: at least 7.0/10)
        2. Ensure all tests are passing
        3. Improve or maintain the test coverage (target: at least 80%)
        4. CRITICAL: Handle list indices properly to avoid IndexError exceptions
        5. Implement input validation and error handling for list operations
        6. Handle empty lists and edge cases correctly
        7. Use defensive programming techniques to prevent IndexError

        Follow these rules strictly:
        1. CRITICAL: Only modify the code implementation in {self.project_name}.
        2. IMPORTANT: Never use pass statements in your code. Always provide a meaningful implementation.
        3. Consider the Git history when suggesting changes to avoid reverting recent improvements.
        4. IMPORTANT: Do not create new files. Only modify the existing ones.
        5. IMPORTANT: Never remove existing poetry dependencies. Only add new ones if necessary.
        6. The test command is `poetry run pytest --cov={self.project_name} --cov-config=.coveragerc`
        7. IMPORTANT: Do not add any code comments to the files.
        8. IMPORTANT: Always follow PEP8 style guide, follow best practices for Python, use snake_case naming, and provide meaningful docstrings.
        9. IMPORTANT: Do not redefine built-in functions or use reserved keywords as variable names.
        10. CRITICAL: Use the following code block format for specifying file content:
            <<<{self.project_name}/main.py>>>
            # File content here
            <<<end>>>

            For test files, use:
            <<<tests/test_main.py>>>
            # Test file content here
            <<<end>>>
        11. CRITICAL: Put all Python code in 1 file only: {self.project_name}/main.py
        12. CRITICAL: Put all tests in 1 file only: tests/test_main.py.
        13. CRITICAL: Do not change the library dependencies from the original implementation.
        14. CRITICAL: Make the minimum number of changes necessary to improve the code.
        15. IMPORTANT: Use the flask-testing library for testing Flask apps.
        Working directory: {self.pwd}
        """
        improvements = self.get_response(prompt)
        print("Proposed improvements:")
        print(improvements)

        if self.validate_against_task(improvements):
            self.logger.info("Writing suggested improvements to files:")
            success = self.process_file_changes(improvements)
            if success:
                self.logger.info(
                    "Improvements have been written to the implementation files. Please review the changes manually."
                )
            else:
                self.logger.error("Failed to apply some or all improvements.")
        else:
            self.logger.info(
                "Proposed improvements do not align with the original task. No changes were made."
            )

    def validate_implementation(self):
        prompt = f"""
        Review the current implementation and confirm if it correctly addresses the original task: {self.task}
        If the implementation is correct or mostly correct, respond with 'VALID'.
        If the implementation is completely unrelated or fundamentally flawed, respond with 'INVALID'.
        Do not provide any additional information or explanations.
        """
        response = self.get_response(prompt)

        if "VALID" in response.upper():
            print("Implementation validated successfully.")
            return True
        else:
            print("Implementation does not match the original task.")
            return False

    def get_complexipy_score(self):
        try:
            result = subprocess.run(
                ["poetry", "run", "complexipy", self.project_name],
                capture_output=True,
                text=True,
                cwd=self.pwd
            )
            escaped_path = re.escape(self.project_name)
            pattern = fr'🧠 Total Cognitive Complexity in\s*{escaped_path}:\s*(\d+)'
            match = re.search(pattern, result.stdout, re.DOTALL)
            return int(match.group(1)) if match else None
        except subprocess.CalledProcessError as e:
            print(f"Error running complexipy: {e}")
            return None

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

    def get_response(self, prompt):
        try:
            return self.llm.generate(prompt)
        except Exception as e:
            self.logger.error(f"Error getting response from {self.provider}: {str(e)}")
            return ""

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
                    [
                        "--disable=missing-function-docstring,missing-module-docstring,redefined-outer-name",
                        "--max-line-length=120",
                    ]
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

            print(output)
            pylint_score = float(score_match.group(1)) if score_match else 0.0

            complexipy_cmd = ["poetry", "run", "complexipy", file_path]
            result = subprocess.run(
                complexipy_cmd, capture_output=True, text=True, cwd=self.pwd
            )
            output = result.stdout + result.stderr
            escaped_path = re.escape(file_path)
            pattern = fr'🧠 Total Cognitive Complexity in\s*{escaped_path}:\s*(\d+)'
            score_match = re.search(pattern, output, re.DOTALL)
            print(score_match)
            print(output)
            complexipy_score = int(score_match.group(1)) if score_match else None

            print(f"Pylint score for {file_path}: {pylint_score}/10")
            print(f"Complexipy score for {file_path}: {complexipy_score}")

            # You can define your own threshold for complexipy score
            if pylint_score < 7.0 or (complexipy_score is not None and complexipy_score > 15):
                print("Score is below threshold. Attempting to improve the code...")
                self.improve_code(
                    file_path, pylint_score, complexipy_score, output, is_test_file, is_init_file)

            elif (
                "missing-module-docstring" in output
                and not is_test_file
                and not is_init_file
            ):
                self.add_module_docstring(file_path)
                # Re-run pylint after adding the docstring
                return self.clean_code_with_pylint(file_path)

            else:
                print(f"Code quality is good. Pylint score: {pylint_score}/10, Complexipy score: {complexipy_score}")

            return pylint_score, complexipy_score
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

    def improve_test_file(self, test_output):
        prompt = f"""
        The current test file needs minor improvements. Please analyze the test output and suggest small, specific changes to fix any issues in the test file.
        Do not modify the main implementation file, only suggest minimal improvements to the tests.

        Test output:
        {test_output}

        Original task: {self.task}

        Provide specific, minimal code changes to improve the test file, addressing only the failing tests or obvious issues.
        Follow these rules strictly:
        1. Only suggest changes to the test file (tests/test_main.py)
        2. Do not change the code files in the {self.pwd}/{self.project_name}
        3. Focus on fixing failing tests or obvious errors
        4. Keep changes minimal and specific
        5. Do not rewrite entire test functions unless absolutely necessary
        6. Ensure all changes are meaningful and relate to the original task
        7. IMPORTANT: put all your code in the code directory: {self.project_name}
        8. IMPORTANT: put all your tests in the tests directory: tests
        9. CRITICAL: Use the following format for specifying changes:
                <<<tests/test_main.py>>>
                # Line number: Original line
                # Suggested change: New line
                <<<end>>>
        10. CRITICAL: Do not explain the task only implement the required functionality in the code blocks.
        11. IMPORTANT: Use the flask-testing library for testing Flask apps.
        Working directory: {self.pwd}
        """
        proposed_improvements = self.get_response(prompt)

        if self.validate_against_task(proposed_improvements):
            print("Executing validated test improvements:")
            success = self.apply_test_file_changes(proposed_improvements)
            if success:
                print(
                    "Test improvements have been applied. Please review the changes manually.")
            else:
                print("Failed to apply some or all test improvements.")
        else:
            print(
                "Proposed test improvements do not align with the original task. No changes were made.")

    def apply_test_file_changes(self, proposed_improvements):
        file_path = os.path.join(self.pwd, 'tests', 'test_main.py')
        changes = self.extract_test_file_changes(proposed_improvements)

        try:
            with open(file_path, 'r') as file:
                lines = file.readlines()

            for line_num, new_content in changes:
                if 0 <= line_num < len(lines):
                    lines[line_num] = new_content + '\n'
                else:
                    print(f"Warning: Line number {line_num + 1} is out of range. Skipping this change.")

            with open(file_path, 'w') as file:
                file.writelines(lines)

            return True
        except Exception as e:
            print(f"Error applying test file changes: {str(e)}")
            return False

    def extract_test_file_changes(self, proposed_improvements):
        changes = []
        lines = proposed_improvements.split("\n")
        for line_index, current_line in enumerate(lines):
            if current_line.startswith("# Line number:"):
                parts = current_line.split(":")
                if len(parts) >= 2:
                    try:
                        # Convert to 0-based index
                        line_num = int(parts[1].strip()) - 1
                        suggested_change_line = next(
                            (line for line in lines[line_index + 1:]
                             if line.startswith("# Suggested change:")),
                            None
                        )
                        if suggested_change_line:
                            new_line_content = suggested_change_line.split(":", 1)[
                                1].strip()
                            changes.append((line_num, new_line_content))
                    except ValueError:
                        continue
        return changes

    def extract_test_file_changes(self, proposed_improvements):
        changes = []
        lines = proposed_improvements.split("\n")
        for line_index, current_line in enumerate(lines):
            if current_line.startswith("# Line number:"):
                parts = current_line.split(":")
                if len(parts) >= 2:
                    try:
                        # Convert to 0-based index
                        line_num = int(parts[1].strip()) - 1
                        suggested_change_line = next(
                            (
                                line
                                for line in lines[line_index + 1:]
                                if line.startswith("# Suggested change:")
                            ),
                            None,
                        )
                        if suggested_change_line:
                            new_line_content = suggested_change_line.split(":", 1)[
                                1
                            ].strip()
                            changes.append((line_num, new_line_content))
                    except ValueError:
                        continue
        return changes

    def improve_code(
        self,
        file_path,
        current_pylint_score,
        current_complexipy_score,
        pylint_output,
        is_test_file,
        is_init_file,
        attempt=1,
    ):
        if current_pylint_score >= 7.0 and (current_complexipy_score is None or current_complexipy_score <= 15):
            print(f"Code quality is already good. Pylint score: {current_pylint_score}/10, Complexipy score: {current_complexipy_score}")
            return current_pylint_score, current_complexipy_score

        if attempt > self.MAX_IMPROVEMENT_ATTEMPTS:
            print(f"Maximum improvement attempts reached for {file_path}. Moving on.")
            return current_pylint_score, current_complexipy_score

        file_type = (
            "test file"
            if is_test_file
            else "init file"
            if is_init_file
            else "regular Python file"
        )

        prompt = f"""
        The current pylint score for {file_path} (a {file_type}) is {current_pylint_score:.2f}/10.
        The current complexipy score is {current_complexipy_score}.
        Please analyze the pylint output and suggest improvements to the code implementation only.
        Focus on reducing cognitive complexity while maintaining or improving the pylint score.
        Do not modify the test file.

        Pylint output:
        {pylint_output}

        Original task: {self.task}

        Provide specific code changes to improve the score and address any issues.
        Follow these rules strictly:
        1. Only modify the code implementation files
        2. Do not change the tests file
        3. Focus on improving code quality, readability, and adherence to PEP8
        4. Address any warnings or errors reported by pylint
        5. Ensure the implementation correctly handles edge cases and potential errors
        6. IMPORTANT: put all your code in the code directory: {self.project_name}
        7. IMPORTANT: put all your tests in the tests directory: tests
        8. CRITICAL: Use the following code block format for specifying file content:
                <<<{self.project_name}/main.py>>>
                # File content here
                <<<end>>>
        9. CRITICAL: Do not explain the task only implement the required functionality in the code blocks.
        Working directory: {self.pwd}
        """
        proposed_improvements = self.get_response(prompt)

        # Check if the proposed improvements are new
        if proposed_improvements in self.previous_suggestions:
            print("No new improvements suggested. Moving on.")
            return current_pylint_score, current_complexipy_score

        self.previous_suggestions.add(proposed_improvements)

        if self.validate_against_task(proposed_improvements):
            print("Executing validated improvements:")
            success = self.process_file_changes(proposed_improvements)

            if success:
                new_pylint_score, new_complexipy_score = self.clean_code_with_pylint(file_path)

                if new_pylint_score < 7.0 or (new_complexipy_score is not None and new_complexipy_score > 15):
                    print(
                        f"Score is still below 7.0 or complexity is above 15. Attempting another improvement (attempt {attempt + 1})..."
                    )
                    return self.improve_code(
                        file_path,
                        new_pylint_score,
                        new_complexipy_score,
                        pylint_output,
                        is_test_file,
                        is_init_file,
                        attempt + 1,
                    )
                else:
                    print(f"Code quality improved. New score: {new_pylint_score}/10")
                    print(f"Complexipy score: {new_complexipy_score}")
                    self.commit_changes(
                        f"Improve code quality for {file_path} to {new_pylint_score}/10"
                    )
                    return new_pylint_score, new_complexipy_score
            else:
                print("Failed to apply some or all improvements.")
                if attempt < self.MAX_IMPROVEMENT_ATTEMPTS:
                    print(
                        f"Attempting another improvement (attempt {attempt + 1})...")
                    return self.improve_code(
                        file_path,
                        current_pylint_score,
                        current_complexipy_score,
                        pylint_output,
                        is_test_file,
                        is_init_file,
                        attempt + 1,
                    )
                else:
                    return current_pylint_score, current_complexipy_score
        else:
            print(
                "Proposed improvements do not align with the original task. Skipping this improvement attempt."
            )
            if attempt < self.MAX_IMPROVEMENT_ATTEMPTS:
                print(
                    f"Attempting another improvement (attempt {attempt + 1})...")
                return self.improve_code(
                    file_path,
                    current_pylint_score,
                    current_complexipy_score,
                    pylint_output,
                    is_test_file,
                    is_init_file,
                    attempt + 1,
                )
            else:
                return current_pylint_score, current_complexipy_score

    def validate_file_content(self, file_path, content):
        if file_path.endswith(".py"):
            # Check for markdown artifacts
            if "```python" in content or "```" in content:
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
        content = re.sub(r"```python\n", "", content)
        content = re.sub(r"```\n", "", content)
        content = re.sub(r"```", "", content)

        # Remove any leading or trailing whitespace
        content = content.strip()

        # Remove any remaining markdown headers
        content = re.sub(r"^#+\s+.*$", "", content, flags=re.MULTILINE)

        # Remove any inline code markers
        content = re.sub(r"`([^`]+)`", r"\1", content)

        return content

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
            test_output = result.stdout + result.stderr
            print("Pytest output:")
            print(test_output)

            # Check if coverage report was generated
            if "No data to report." in test_output:
                print(
                    "No coverage data was collected. Ensure that the tests are running correctly."
                )
                return False, 0, test_output

            # Extract coverage percentage
            coverage_match = re.search(
                r"TOTAL\s+\d+\s+\d+\s+(\d+)%", test_output)
            coverage_percentage = int(
                coverage_match.group(1)) if coverage_match else 0

            # Check if all tests passed
            tests_passed = (
                "failed" not in test_output.lower() and result.returncode == 0
            )

            if tests_passed and coverage_percentage >= 80:
                print(
                    f"All tests passed successfully and coverage is "
                    f"{coverage_percentage}%."
                )
            else:
                if not tests_passed:
                    print("Some tests failed. Please review the test output above.")
                if coverage_percentage < 80:
                    print(
                        f"Coverage is below 80%. "
                        f"Current coverage: {coverage_percentage}%"
                    )

            return tests_passed, coverage_percentage, test_output

        except subprocess.CalledProcessError as e:
            print(f"Error running tests: {e}")
            return False, 0, str(e)
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return False, 0, str(e)


@click.command()
@click.argument("task", required=False)
@click.option("--model", default="mistral-nemo", help="The model to use for the LLM")
@click.option("--provider", default="ollama", type=click.Choice(["ollama", "openai", "claude"]), help="The LLM provider to use")
@click.option("--zip", type=click.Path(), help="Path to save the zip file of the agent run")
def cli(task: str = None, model: str = "mistral-nemo", provider: str = "ollama", zip: str = None):
    """
    Run Nemo Agent tasks to create Python projects using Poetry and Pytest.
    If no task is provided, it will prompt the user for input.
    """
    # Store the original working directory
    original_dir = os.getcwd()

    # Check for API keys if using OpenAI or Anthropic
    if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    elif provider == "claude" and not os.getenv("ANTHROPIC_API_KEY"):
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

    nemo_agent = NemoAgent(task=task, model=model, provider=provider)
    nemo_agent.run_task()
    
    project_dir = nemo_agent.pwd

    if zip:
        # Ensure the zip file is created in the original directory
        zip_path = os.path.join(original_dir, zip)
        
        # Create a zip file
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(project_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, project_dir)
                    zipf.write(file_path, arcname)
        print(f"Project files have been zipped to: {zip_path}")

        # Delete the project directory
        shutil.rmtree(project_dir)
        print(f"Project directory {project_dir} has been deleted.")
    else:
        print(f"Task completed. Project files are in: {nemo_agent.pwd}")


if __name__ == "__main__":
    cli()
