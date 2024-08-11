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

1. Provide complete, fully functional code when creating or editing files.
2. Always install packages using `pip` into the venv created for the project at the start.
3. CRITICAL: Never execute the code you created other than tests.
4. Always create a venv for the Python project.
5. Use absolute paths when referring to files and directories when required.
6. Always use type hints in your Python code.
7. Use pytest for testing, focusing on positive test cases only.
8. Implement the solution first, then write simple tests to verify functionality.
9. CRITICAL: Only provide Python code and never any English commentary, explanations, or comments.
10. CRITICAL: Always use proper Python syntax and indentation in your code. Never add extra characters or spaces.
11. CRITICAL: Never use jsonify or request.json in Flask applications. 

Current working directory: {{cwd}}
Operating System: {{os_name}}
Default Shell: {{default_shell}}
Home Directory: {{home_dir}}
"""

class NemoAgent:
    allowed_commands = ['cat', 'ls', 'cd', 'mkdir', 'pip', 'python3', 'pytest', 'python']

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
        return Assistant(
            llm=Ollama(model="mistral-nemo"),
            system_prompt=system_prompt,
            tools=[FileTools()],
            show_tool_calls=True,
            markdown=True,
        )

    def run_task(self):
        project_name = self.task.split()[0].lower()
        self.create_project_folder(project_name)
        self.create_virtual_environment()
        self.install_pip()
        self.install_required_packages()
        self.generate_and_write_file()
        self.install_packages_from_file()
        self.run_tests()

    def create_project_folder(self, project_name):
        project_path = os.path.join(self.cwd, project_name)
        os.makedirs(project_path, exist_ok=True)
        os.chdir(project_path)
        self.cwd = project_path
        print(f"Created and moved to project folder: {project_path}")

    def create_virtual_environment(self):
        subprocess.run(["python3", "-m", "venv", "venv"], check=True)
        self.venv_path = os.path.join(self.cwd, "venv")
        print("Virtual environment created.")

    def install_pip(self):
        subprocess.run([f"{self.venv_path}/bin/python3", "-m", "ensurepip", "--upgrade"], check=True)
        print("Pip installed/upgraded in the virtual environment.")

    def install_required_packages(self):
        subprocess.run([f"{self.venv_path}/bin/pip", "install", "pytest"], check=True)
        print("Required packages installed.")

    def generate_and_write_file(self):
        prompt = f"""
            You are Nemo Agent, an expert Python developer. 
            You follow these rules strictly to generate a single Python file:
            1. Always use type hints in your Python code.
            2. Never test games or GUI applications.
            3. Always use pytest for testing within the same file, if not a game or GUI application.
            4. Provide complete and fully functional code with all the necessary imports.
            3. CRITICAL: Never use any commentary, explanations, or comments just provide Python code.
            4. CRITICAL: Always use proper Python syntax and indentation in your code. Never add extra characters or spaces.
            5. CRITICAL: Use other JSON methods instead of jsonify in Flask applications. 
            Task: {self.task}
        """
        response = self.get_response(prompt)
        self.write_file("main.py", response)

    def install_packages_from_file(self):
        with open(os.path.join(self.cwd, "main.py"), 'r') as f:
            content = f.read()
        
        tree = ast.parse(content)
        imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0:  # absolute import
                    imports.add(node.module.split('.')[0])
        
        for package in imports:
            if package not in ['os', 'sys', 'pytest']:  # Skip standard library modules
                self.install_package(package)

    def install_package(self, package):
        try:
            subprocess.run([f"{self.venv_path}/bin/pip", "install", package], check=True)
            print(f"Package {package} installed.")
        except subprocess.CalledProcessError:
            print(f"Failed to install package {package}.")

    def run_tests(self):
        result = subprocess.run([f"{self.venv_path}/bin/pytest", "main.py"], capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print("Some tests failed. Please review the implementation and tests manually.")
        else:
            print("All tests passed successfully.")

    def get_response(self, prompt):
        response = self.assistant.run(prompt)
        return self.post_process_response(''.join(response))

    def post_process_response(self, response):
        response = re.sub(r'```python|```', '', response)
        response = re.sub(r'^#.*$', '', response, flags=re.MULTILINE)
        response = re.sub(r'^\s*$', '', response, flags=re.MULTILINE)
        return response.strip()

    def write_file(self, filename, content):
        with open(os.path.join(self.cwd, filename), 'w') as f:
            f.write(content)
        print(f"File {filename} created.")

@click.command()
@click.argument('task', required=False)
def cli(task: str = None):
    if task is None:
        task = click.prompt("Please enter the task for Nemo Agent")
    nemo_agent = NemoAgent(task=task)
    nemo_agent.run_task()

if __name__ == "__main__":
    cli()
