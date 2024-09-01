import ast
from contextlib import contextmanager
from datetime import time
import fcntl
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
        data = {"model": self.model, "prompt": prompt, "stream": True}
        response = requests.post(url, json=data, stream=True)
        if response.status_code == 200:
            full_response = ""
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode("utf-8")
                    try:
                        json_line = json.loads(decoded_line)
                        chunk = json_line.get("response", "")
                        full_response += chunk
                        print(chunk, end="", flush=True)
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
                stream=True,
            )
            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    chunk_text = chunk.choices[0].delta.content
                    full_response += chunk_text
                    print(chunk_text, end="", flush=True)
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
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        self.client = Anthropic(api_key=self.api_key)

    def generate(self, prompt):
        try:
            response = self.client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
                max_tokens=1000,
            )
            full_response = ""
            for completion in response:
                if completion.type == "content_block_delta":
                    chunk_text = completion.delta.text
                    full_response += chunk_text
                    print(chunk_text, end="", flush=True)
            print()  # Print a newline at the end
            return full_response
        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}")


class NemoAgent:
    MAX_IMPROVEMENT_ATTEMPTS = 5
    MAX_WRITE_ATTEMPTS = 3
    WRITE_RETRY_DELAY = 1  # second

    def __init__(
        self, task: str, model: str = "mistral-nemo", provider: str = "ollama"
    ):
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
            subprocess.run(["git", "commit", "-m", message], check=True, cwd=self.pwd)
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

        pylint_score, complexipy_score, pylint_output, complexipy_output = self.code_check(f"{self.project_name}/main.py")

        code_check_attempts = 1
        while code_check_attempts < self.MAX_IMPROVEMENT_ATTEMPTS:
            if pylint_score < 7 and complexipy_score > 15:
                self.improve_code(f"{self.project_name}/main.py", pylint_score, complexipy_score, pylint_output, complexipy_output)
                pylint_score, complexipy_score, pylint_output, complexipy_output = self.code_check(f"{self.project_name}/main.py")
            else:
                break
            code_check_attempts += 1
        
        test_check_attempts = 1
        while test_check_attempts < self.MAX_IMPROVEMENT_ATTEMPTS:
            tests_passed, coverage, test_output = self.run_tests()
            if not tests_passed or coverage < 80:
                self.improve_test_file(test_output)
                tests_passed, coverage, test_output = self.run_tests()
            else:
                break
            test_check_attempts += 1

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
                    self.logger.info(f"Successfully wrote to file: {file_path}")
                    return True
            except IOError as e:
                self.logger.error(f"IOError writing to {file_path}: {e}")
                if attempt < self.MAX_WRITE_ATTEMPTS - 1:
                    self.logger.info(f"Retrying in {self.WRITE_RETRY_DELAY} seconds...")
                    time.sleep(self.WRITE_RETRY_DELAY)
                else:
                    self.logger.error(
                        f"Failed to write to {file_path} after {self.MAX_WRITE_ATTEMPTS} attempts"
                    )
            except Exception as e:
                self.logger.error(f"Unexpected error writing to {file_path}: {e}")
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
                        self.logger.debug(f"Content of {full_path}:\n{f.read()}")
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
                1, IMPORTANT: Never use pass statements in your code or tests. Always provide a meaningful implementation.
                2. CRITICAL: Use the following code block format for specifying file content:                
                    For code files, use:
                    <<<{self.project_name}/main.py>>>
                    # File content here
                    <<<end>>>

                    For test files, use:
                    <<<tests/test_main.py>>>
                    # Test file content here
                    <<<end>>>

                    For HTML templates (Flask), use:
                    <<<{self.project_name}/templates/template_name.html>>>
                    <!-- HTML content here -->
                    <<<end>>>
                3. The test command is `poetry run pytest --cov={self.project_name} --cov-config=.coveragerc`
                4. IMPORTANT: Do not add any code comments to the files.
                5. IMPORTANT: Always follow PEP8 style guide, follow best practices for Python, use snake_case naming, and provide meaningful docstrings.
                6. IMPORTANT: Do not redefine built-in functions or use reserved keywords as variable names.
                7. CRITICAL: Create any non-existent directories or files as needed that are not Python files.
                8. CRITICAL: Your response should ONLY contain the code blocks and `poetry add package_name` command at the end after all the code blocks. Do not include any explanations or additional text.
                9. IMPORTANT: Do not modify the existing poetry dependencies. Only add new ones if necessary.
                10. CRITICAL: Only create 1 file for the python code: {self.project_name}/main.py
                11. CRITICAL: Only create 1 file for the python tests: tests/test_main.py
                12. CRITICAL: Create a main method to run the app in main.py and if a web app run the app on port 8080.
                13. IMPORTANT: Use the proper import statements for the test file to import the main file and its functions using the {self.project_name} namespace.
                14. IMPORTANT: Use pytest.fixture for any setup code that is reused across multiple tests including web servers like Flask and FastAPI.
                15. IMPORTANT: Use the hypothesis library for property-based testing if applicable.
                16. IMPORTANT: Use pytest parametrize for testing multiple inputs and outputs if applicable.
            Working directory: {self.pwd}
            """

        for attempt in range(max_attempts):
            self.logger.info(f"Attempt {attempt + 1} to implement solution")
            solution = self.get_response(prompt)
            self.logger.info(f"Received solution:\n{solution}")

            # Parse and execute any poetry add commands
            poetry_commands = [
                line.strip()
                for line in solution.split("\n")
                if line.strip().startswith("poetry add")
            ]
            for command in poetry_commands:
                try:
                    subprocess.run(command, shell=True, check=True)
                    self.logger.info(f"Executed command: {command}")
                except subprocess.CalledProcessError as e:
                    self.logger.error(
                        f"Failed to execute command: {command}. Error: {str(e)}"
                    )

            success = self.process_file_changes(solution)

            if success:
                self.logger.info(
                    "All files created successfully and passed pylint check"
                )
                self.commit_changes("Implement initial solution")
                return True

            self.logger.warning(
                f"Attempt {attempt + 1} failed to create the correct files or pass pylint. Retrying..."
            )

        self.logger.error("Failed to implement solution after maximum attempts")
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

    def get_response(self, prompt):
        try:
            return self.llm.generate(prompt)
        except Exception as e:
            self.logger.error(f"Error getting response from {self.provider}: {str(e)}")
            return ""

    def code_check(self, file_path):
        try:
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

            # Adjust pylint command for different file types
            pylint_cmd = ["poetry", "run", "pylint"]
            pylint_cmd.extend(
                [
                    "--disable=missing-function-docstring,missing-module-docstring",
                    "--max-line-length=120",
                ]
            )
            pylint_cmd.append(file_path)

            result = subprocess.run(
                pylint_cmd, capture_output=True, text=True, cwd=self.pwd
            )
            pylint_output = result.stdout + result.stderr
            score_match = re.search(
                r"Your code has been rated at (\d+\.\d+)/10", pylint_output
            )

            print(pylint_output)
            pylint_score = float(score_match.group(1)) if score_match else 0.0

            complexipy_cmd = ["poetry", "run", "complexipy", file_path]
            result = subprocess.run(
                complexipy_cmd, capture_output=True, text=True, cwd=self.pwd
            )
            complexipy_output = result.stdout + result.stderr
            escaped_path = re.escape(file_path)
            pattern = rf"🧠 Total Cognitive Complexity in\s*{escaped_path}:\s*(\d+)"
            score_match = re.search(pattern, complexipy_output, re.DOTALL)
            print(score_match)
            print(complexipy_output)
            complexipy_score = int(score_match.group(1)) if score_match else None

            print(f"Pylint score for {file_path}: {pylint_score}/10")
            print(f"Complexipy score for {file_path}: {complexipy_score}")

            # You can define your own threshold for complexipy score
            if pylint_score < 7.0 or (
                complexipy_score is not None and complexipy_score > 15
            ):
                print("Score is below threshold. Attempting to improve the code...")
                self.improve_code(
                    file_path,
                    pylint_score,
                    complexipy_score,
                    pylint_output,
                    complexipy_output,
                    1,
                )
            else:
                print(
                    f"Code quality is good. Pylint score: {pylint_score}/10, Complexipy score: {complexipy_score}"
                )

            return pylint_score, complexipy_score, pylint_output, complexipy_output
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
        1. CRITICAL: Only suggest changes to the test file (tests/test_main.py)
        2. Do not change the code file in {self.project_name}/main.py
        3. Focus on fixing failing tests or obvious errors
        4. Keep changes minimal and specific
        5. Do not rewrite entire test functions unless absolutely necessary
        6. IMPORTANT: put all your code in the code directory: {self.project_name}
        7. IMPORTANT: put all your tests in the tests directory: tests
        8. CRITICAL: Use the following code block format for specifying file content:
            For test files, use:
            <<<tests/test_main.py>>>
            # Test file content here
            <<<end>>>
        9. CRITICAL: Do not explain the task only implement the required functionality in the code blocks.
        10. IMPORTANT: Use the proper import statements for the test file to import the main file and its functions using the {self.project_name} namespace.
        11. IMPORTANT: Use pytest.fixture for any setup code that is reused across multiple tests including web servers like Flask and FastAPI.
        12. IMPORTANT: Use the hypothesis library for property-based testing if applicable.
        13. IMPORTANT: Use pytest parametrize for testing multiple inputs and outputs if applicable.
        Working directory: {self.pwd}
        """
        proposed_improvements = self.get_response(prompt)

        if self.validate_implementation(proposed_improvements):
            print("Executing validated test improvements:")
            success = self.process_file_changes(proposed_improvements)
            if success:
                print(
                    "Test improvements have been applied. Please review the changes manually."
                )
            else:
                print("Failed to apply some or all test improvements.")
        else:
            print(
                "Proposed test improvements do not align with the original task. No changes were made."
            )

    def validate_implementation(self, proposed_improvements):
        prompt = f"""
        Review the proposed improvements: {proposed_improvements} and confirm if it correctly addresses the original task: {self.task}
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

    def improve_code(
        self,
        file_path,
        current_pylint_score,
        current_complexipy_score,
        pylint_output,
        complexipy_output,
    ):
        prompt = f"""
        The current pylint score for {file_path} is {current_pylint_score:.2f}/10.
        The current complexipy score is {current_complexipy_score}.
        Please analyze the pylint output and suggest improvements to the code implementation only.
        Focus on reducing cognitive complexity while maintaining or improving the pylint score.
        Do not modify the test file.

        Pylint output:
        {pylint_output}

        Complexipy output:
        {complexipy_output}

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

        if self.validate_implementation(proposed_improvements):
            print("Executing validated improvements:")
            success = self.process_file_changes(proposed_improvements)

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
            coverage_match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", test_output)
            coverage_percentage = int(coverage_match.group(1)) if coverage_match else 0

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
@click.option(
    "--provider",
    default="ollama",
    type=click.Choice(["ollama", "openai", "claude"]),
    help="The LLM provider to use",
)
@click.option(
    "--zip", type=click.Path(), help="Path to save the zip file of the agent run"
)
def cli(
    task: str = None,
    model: str = "mistral-nemo",
    provider: str = "ollama",
    zip: str = None,
):
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
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
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
