import ast
from contextlib import contextmanager
from datetime import time
import fcntl
import glob
import json
import logging
import os
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
import tiktoken


class OllamaAPI:
    def __init__(self, model):
        self.model = model
        self.base_url = "http://localhost:11434/api"
        self.token_count = 0
        self.max_tokens = 128000  # Max tokens for Mistral-Nemo

    def count_tokens(self, text):
        return len(tiktoken.encoding_for_model("gpt-4o").encode(text))

    def generate(self, prompt):
        url = f"{self.base_url}/generate"
        full_response = ""
        remaining_tokens = self.max_tokens - self.count_tokens(prompt)
        data = {"model": self.model, "prompt": prompt, "stream": True}
        response = requests.post(url, json=data, stream=True)
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode("utf-8")
                    try:
                        json_line = json.loads(decoded_line)
                        chunk = json_line.get("response", "")
                        full_response += chunk
                        print(chunk, end="", flush=True)
                        remaining_tokens -= self.count_tokens(chunk)
                        if remaining_tokens <= 0 or "^^^end^^^" in full_response:
                            break
                    except json.JSONDecodeError:
                        print(f"Error decoding JSON: {decoded_line}")
        else:
            raise Exception(f"Ollama API error: {response.text}")

        print()  # Print a newline at the end

        # Extract content between markers if needed
        start_marker = "^^^start^^^"
        end_marker = "^^^end^^^"
        start_index = full_response.find(start_marker)
        end_index = full_response.find(end_marker)
        if start_index != -1 and end_index != -1:
            full_response = full_response[start_index + len(start_marker) : end_index].strip()

        self.token_count = self.count_tokens(full_response)
        print(f"Token count: {self.token_count}")

        return full_response

class OpenAIAPI:
    def __init__(self, model):
        if model == "mistral-nemo":
            model = "gpt-4o"
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        openai.api_key = self.api_key
        self.token_count = 0
        self.max_tokens = 128000
        self.max_output_tokens = 16384
        self.special_models = ["o1-preview", "o1-mini"]  # Add special models here

    def count_tokens(self, text):
        return len(tiktoken.encoding_for_model("gpt-4o").encode(text))

    def generate(self, prompt):
        try:
            full_response = ""
            prompt_tokens = self.count_tokens(prompt)
            
            if prompt_tokens >= self.max_tokens:
                print(f"Warning: Prompt exceeds maximum token limit ({prompt_tokens}/{self.max_tokens})")
                return "Error: Prompt too long"

            # Use the predefined max output tokens, or adjust if prompt is very long
            max_completion_tokens = min(self.max_output_tokens, self.max_tokens - prompt_tokens)

            if self.model in self.special_models:
                # Non-streaming approach
                response = openai.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_completion_tokens=max_completion_tokens,
                    stream=True,
                )
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        chunk_text = chunk.choices[0].delta.content
                        full_response += chunk_text
                        print(chunk_text, end="", flush=True)
                        if "^^^end^^^" in full_response:
                            break

                print()  # Print a newline at the end
            else:
                # Streaming approach
                response = openai.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_completion_tokens,
                    stream=True,
                )

                for chunk in response:
                    if chunk.choices[0].delta.content:
                        chunk_text = chunk.choices[0].delta.content
                        full_response += chunk_text
                        print(chunk_text, end="", flush=True)
                        if "^^^end^^^" in full_response:
                            break

                print()  # Print a newline at the end

            # Extract content between markers
            start_marker = "^^^start^^^"
            end_marker = "^^^end^^^"
            start_index = full_response.find(start_marker)
            end_index = full_response.find(end_marker)
            if start_index != -1 and end_index != -1:
                full_response = full_response[start_index + len(start_marker) : end_index].strip()

            self.token_count = self.count_tokens(full_response)
            print(f"Token count: {self.token_count}")

            return full_response
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")


class ClaudeAPI:
    def __init__(self, model):
        if model == "mistral-nemo":
            model = "claude-3-5-sonnet-20241022"
        self.model = model
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        self.client = Anthropic(api_key=self.api_key)
        self.token_count = 0
        self.max_tokens = 200000
        self.max_output_tokens = 8192

    def count_tokens(self, text):
        return len(tiktoken.encoding_for_model("gpt-4o").encode(text))

    def generate(self, prompt):
        try:
            full_response = ""
            prompt_tokens = self.count_tokens(prompt)
            
            if prompt_tokens >= self.max_tokens:
                print(f"Warning: Prompt exceeds maximum token limit ({prompt_tokens}/{self.max_tokens})")
                return "Error: Prompt too long"

            # Use the predefined max output tokens, or adjust if prompt is very long
            max_completion_tokens = min(self.max_output_tokens, self.max_tokens - prompt_tokens)

            response = self.client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_completion_tokens,
                stream=True,
            )

            for completion in response:
                if completion.type == "content_block_delta":
                    chunk_text = completion.delta.text
                    full_response += chunk_text
                    print(chunk_text, end="", flush=True)
                    if "^^^end^^^" in full_response:
                        break

            print()  # Print a newline at the end

            # Extract content between markers
            start_marker = "^^^start^^^"
            end_marker = "^^^end^^^"
            start_index = full_response.find(start_marker)
            end_index = full_response.find(end_marker)
            if start_index != -1 and end_index != -1:
                full_response = full_response[start_index + len(start_marker) : end_index].strip()

            self.token_count = self.count_tokens(full_response)
            print(f"Token count: {self.token_count}")

            return full_response
        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}")


class NemoAgent:
    MAX_IMPROVEMENT_ATTEMPTS = 3
    MAX_WRITE_ATTEMPTS = 3
    WRITE_RETRY_DELAY = 1  # second

    def __init__(
        self, task: str, model: str = "mistral-nemo", provider: str = "ollama"
    ):
        self.task = task
        self.model = model
        self.provider = provider
        self.setup_logging()
        self.project_name = self.generate_project_name()
        self.pwd = os.getcwd() + "/" + self.project_name
        self.llm = self.setup_llm()
        self.previous_suggestions = set()
        self.token_counts = {}
        self.reference_material = ""
        self.code_content = ""
        self.data_content = ""
        self.previous_prompt = ""

    def count_tokens(self, text):
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        return len(encoding.encode(text))

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

    def ingest_docs(self, docs_path):
        docs_content = ""
        for ext in ("*.txt", "*.md"):
            for file_path in glob.glob(
                os.path.join(docs_path, "**", ext), recursive=True
            ):
                with open(file_path, "r") as f:
                    docs_content += f.read() + "\n\n"

        if docs_content:
            self.reference_material = docs_content
            print(f"Documentation from {docs_path} has been ingested.")
        else:
            print(f"No documentation files found in {docs_path}.")

    def ingest_code(self, docs_path):
        docs_content = ""
        for ext in ("*.php", "*.rs", "*.py", "*.js", "*.ts", "*.toml", "*.json", "*.rb", "*.yaml"):
            for file_path in glob.glob(
                os.path.join(docs_path, "**", ext), recursive=True
            ):
                with open(file_path, "r") as f:
                    docs_content += f.read() + "\n\n"

        if docs_content:
            self.code_content = docs_content
            print(f"Code files from {docs_path} has been ingested.")
        else:
            print(f"No code files found in {docs_path}.")

    def ingest_data(self, docs_path):
        docs_content = ""
        for ext in ("*.csv"):
            for file_path in glob.glob(
                os.path.join(docs_path, "**", ext), recursive=True
            ):
                if os.path.isfile(file_path):
                    with open(file_path, "r") as f:
                        docs_content += f.read() + "\n\n"

        if docs_content:
            self.data_content = docs_content
            print(f"Data files from {docs_path} has been ingested.")
        else:
            print(f"No data files found in {docs_path}.")

    def run_task(self):
        print(f"Current working directory: {os.getcwd()}")
        self.ensure_uv_installed()
        self.create_project_with_uv()
        self.implement_solution()

        pylint_score, complexipy_score, pylint_output, complexipy_output = (
            self.code_check("main.py")
        )

        code_check_attempts = 1
        while code_check_attempts < self.MAX_IMPROVEMENT_ATTEMPTS:
            if pylint_score < 7 and complexipy_score > 15:
                self.improve_code(
                    "main.py",
                    pylint_score,
                    complexipy_score,
                    pylint_output,
                    complexipy_output,
                )
                pylint_score, complexipy_score, pylint_output, complexipy_output = (
                    self.code_check("main.py")
                )
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

        total_tokens = sum(self.token_counts.values())
        print(f"\nTotal tokens used: {total_tokens}")

        print(
            "Task completed. Please review the output and make any necessary manual adjustments."
        )

    def ensure_uv_installed(self):
        try:
            subprocess.run(
                ["uv", "--version"], check=True, capture_output=True, text=True
            )
            print("uv is already installed.")
        except FileNotFoundError:
            print("uv is not installed. Installing uv...")
            try:
                subprocess.run("pip install uv", shell=True, check=True)
                print("uv installed successfully.")
            except subprocess.CalledProcessError as e:
                print(f"Error installing uv: {e}")
                sys.exit(1)

    def create_project_with_uv(self):
        print(f"Creating new uv project: {self.project_name}")
        try:
            result = subprocess.run(
                ["uv", "init", self.project_name, "--no-workspace"],
                capture_output=True,
                text=True,
                check=True,
            )
            print(result.stdout)

            try:
                subprocess.run(
                    [
                        "uv",
                        "add",
                        "pytest",
                        "pylint",
                        "autopep8",
                        "pytest-cov",
                        "complexipy",
                    ],
                    check=True,
                    cwd=self.pwd,
                )
                print("Added dev dependencies with latest versions.")
            except subprocess.CalledProcessError as e:
                print(f"Error adding development dependencies: {e}")

            try:
                # Create the __init__.py file in the tests directory
                tests_dir = os.path.join(self.pwd, "tests")
                os.makedirs(tests_dir)
                os.remove(f"{self.pwd}/hello.py")
                init_file_path = os.path.join(tests_dir, "__init__.py")
                with open(init_file_path, "w") as f:
                    f.write(
                        "# This file is required to make Python treat the directories as containing packages.\n"
                    )

            except Exception as e:
                print(f"Error creating tests/__init__.py: {str(e)}")

        except subprocess.CalledProcessError as e:
            print(f"Error creating uv project: {e.stderr}")
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
                1. IMPORTANT: Never use pass statements in your code or tests. Always provide a meaningful implementation.
                2. CRITICAL: Use the following code block format for specifying file content:                
                    For code or notebook files, use:
                    <<<main.py>>>
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

                    For pip dependencies, use:
                    ***uv_start***
                    package_name[optional_extra, optional_extra]; package_name; package_name
                    ***uv_end***
                3. IMPORTANT: Do not add any code comments to the files.
                4. IMPORTANT: Always follow PEP8 style guide, follow best practices for Python, use snake_case naming, and provide meaningful docstrings.
                5. CRITICAL: Your response should ONLY contain the code blocks and the pip dependencies required for both the test and code files. Do not include any additional information.
                6. CRITICAL: Create a main method to run the app in main.py and if a web app run the app on port 8080.

                7. CRITICAL: Enclose your entire response between ^^^start^^^ and ^^^end^^^ markers.
                8. IMPORTANT: Use the reference documentation provided to guide your implementation including the required dependencies.
                9. IMPORTANT: Use the code content as a reference to build a working solution based on the task provided by the user in Python.
                10. IMPORTANT: Use the CSV content to load data for your implementation of the task.
            Working directory: {self.pwd}
            Reference documentation: {self.reference_material}
            Code content: {self.code_content}
            CSV content: {self.data_content}
            """

        for attempt in range(max_attempts):
            self.logger.info(f"Attempt {attempt + 1} to implement solution")
            solution = self.get_response(prompt)

            # Extract content between markers
            start_marker = "^^^start^^^"
            end_marker = "^^^end^^^"
            start_index = solution.find(start_marker)
            end_index = solution.find(end_marker)
            if start_index != -1 and end_index != -1:
                solution = solution[start_index + len(start_marker) : end_index].strip()

            self.install_dependencies(solution)

            success = self.process_file_changes(solution)

            if success:
                self.logger.info(
                    "All files created successfully and passed pylint check"
                )
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
            full_prompt = (
                f"{self.previous_prompt}\n\n{prompt}"
                if self.previous_prompt
                else prompt
            )
            response = self.llm.generate(full_prompt)
            prompt_key = prompt[:50]  # Use first 50 characters as a key
            self.token_counts[prompt_key] = self.llm.token_count
            self.previous_prompt = full_prompt
            return response
        except Exception as e:
            self.logger.error(f"Error getting response from {self.provider}: {str(e)}")
            return ""

    def code_check(self, file_path):
        try:
            # Run autopep8 to automatically fix style issues
            print(f"Running autopep8 on {file_path}")
            autopep8_cmd = [
                "uv",
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
            pylint_cmd = ["uv", "run", "pylint"]
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

            complexipy_cmd = ["uv", "run", "complexipy", file_path]
            result = subprocess.run(
                complexipy_cmd, capture_output=True, text=True, cwd=self.pwd
            )
            complexipy_output = result.stdout + result.stderr
            escaped_path = re.escape(file_path)
            pattern = rf"🧠 Total Cognitive Complexity in\s*{escaped_path}:\s*(\d+)"
            score_match = re.search(pattern, complexipy_output, re.DOTALL)
            print(score_match)
            print(complexipy_output)
            complexipy_score = int(score_match.group(1)) if score_match else 0

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
                )
            else:
                print(
                    f"Code quality is good. Pylint score: {pylint_score}/10, Complexipy score: {complexipy_score}"
                )

            return pylint_score, complexipy_score, pylint_output, complexipy_output
        except subprocess.CalledProcessError as e:
            print(f"Error running autopep8 or pylint: {e}")
            return 0.0, 0, "", ""

    def improve_test_file(self, test_output):
        prompt = f"""
        Test output:
        {test_output}

        Original task: {self.task}

        Provide specific, minimal code changes to improve the test file, addressing only the failing tests or obvious issues.
        Follow these rules strictly:
        1. CRITICAL: Only suggest changes to the test file.
        2. CRITICAL: Use the following code block format for specifying file content:
            For test files, use:
            <<<tests/test_main.py>>>
            # Test file content here
            <<<end>>>
            
            For pip dependencies, use:
            ***uv_start***
            package_name[optional_extra, optional_extra]; package_name; package_name
            ***uv_end***
        3. CRITICAL: Enclose your entire response between ^^^start^^^ and ^^^end^^^ markers.
        4. CRITICAL: Your response should ONLY contain the code blocks and the pip dependencies required for both the test and code files. Do not include any additional information.
        Working directory: {self.pwd}
        """
        proposed_improvements = self.get_response(prompt)

        if self.validate_implementation(proposed_improvements):
            print("Executing validated test improvements:")

            self.install_dependencies(proposed_improvements)

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

    def install_dependencies(self, content):
        """
        Parse the content for pip packages and install them using uv.

        Args:
        content (str): The string content containing the pip packages block.

        Returns:
        bool: True if packages were found and installation was attempted, False otherwise.
        """
        pip_start = content.find("***uv_start***")
        pip_end = content.find("***uv_end***")

        if pip_start != -1 and pip_end != -1:
            pip_packages = (
                content[pip_start + len("***uv_start***") : pip_end].strip().split(";")
            )
            pip_packages = [pkg.strip() for pkg in pip_packages if pkg.strip()]

            if pip_packages:
                try:
                    for pip_package in pip_packages:
                        command = ["uv", "add", pip_package] 
                        subprocess.run(command, check=True, cwd=self.pwd)
                        self.logger.info(
                            f"Executed command: uv pip install {pip_package}"
                        )
                    return True
                except subprocess.CalledProcessError as e:
                    self.logger.error(
                        f"Failed to execute command: uv add {' '.join(pip_packages)}. Error: {str(e)}"
                    )

        return False

    def validate_implementation(self, proposed_improvements):
        prompt = f"""
        Review the proposed improvements: {proposed_improvements} and confirm if it correctly addresses the original task: {self.task}
        If the implementation is correct or mostly correct, respond with 'VALID'.
        If the implementation is completely unrelated or fundamentally flawed, respond with 'INVALID'.
        Do not provide any additional information or explanations beyond 'VALID' or 'INVALID'.
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
        6. CRITICAL: Use the following code block format for specifying file content:
                <<<main.py>>>
                # File content here
                <<<end>>>
        7. CRITICAL: Do not explain the task only implement the required functionality in the code blocks.
        8. IMPORTANT: Enclose your entire response between ^^^start^^^ and ^^^end^^^ markers.
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
            self.process_file_changes(proposed_improvements)

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
                    "uv",
                    "run",
                    "pytest",
                    "--cov=" + self.pwd,
                    "--cov-config=.coveragerc",
                    "--cov-report=term-missing",
                    "-vv",
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
@click.option(
    "--file",
    type=click.Path(exists=True),
    help="Path to a markdown file containing the task",
)
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
@click.option(
    "--docs",
    type=click.Path(exists=True),
    help="Path to the docs folder containing reference material",
)
@click.option(
    "--code",
    type=click.Path(exists=True),
    help="Path to the import folder containing code files",
)
@click.option(
    "--data",
    type=click.Path(exists=True),
    help="Path to the import folder containing data files",
)
def cli(
    task: str = None,
    file: str = None,
    model: str = "mistral-nemo",
    provider: str = "ollama",
    zip: str = None,
    docs: str = None,
    code: str = None,
    data: str = None,
):
    """
    Run Nemo Agent tasks to create Python projects using uv and pytest.
    If no task is provided, it will prompt the user for input.
    """
    # Store the original working directory
    original_dir = os.getcwd()

    # Check for API keys if using OpenAI or Anthropic
    if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    elif provider == "claude" and not os.getenv("ANTHROPIC_API_KEY"):
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

    # Read task from file if provided
    if file:
        file_extension = os.path.splitext(file)[1].lower()
        if file_extension not in [".md", ".txt"]:
            raise ValueError(
                "The task file must be either a markdown (.md) or text (.txt) file."
            )
        with open(file, "r") as f:
            task = f.read().strip()
    elif not task:
        task = click.prompt("Please enter your task")

    nemo_agent = NemoAgent(task=task, model=model, provider=provider)

    # Ingest docs if provided
    if docs:
        nemo_agent.ingest_docs(docs)

    # Ingest code if provided
    if code:
        nemo_agent.ingest_code(code)

    # Ingest data if provided
    if data:
        nemo_agent.ingest_data(data)

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
