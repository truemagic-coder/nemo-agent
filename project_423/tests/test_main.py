import pytest
from main import TodoApp

@pytest.fixture
def todo_app():
    return TodoApp()

def test_add_task(todo_app):
    todo_app.add_task("Test task")
    assert "Test task" in todo_app.tasks

def test_remove_task(todo_app):
    todo_app.add_task("Test task")
    todo_app.remove_task(0)
    assert not todo_app.tasks

if __name__ == "__main__":
    pytest.main()