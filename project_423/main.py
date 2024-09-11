import streamlit as st


class TodoApp:
    def __init__(self):
        self.tasks = []

    def add_task(self, task):
        self.tasks.append(task)

    def remove_task(self, index):
        if 0 <= index < len(self.tasks):
            del self.tasks[index]

    def display_tasks(self):
        for i, task in enumerate(self.tasks):
            st.write(f"{i + 1}. {task}")


def main():
    app = TodoApp()

    st.title("Todo App")

    new_task = st.text_input("Enter a new task:")
    if st.button("Add Task"):
        app.add_task(new_task)

    app.display_tasks()

    if st.button("Remove Task"):
        selected_task_index = st.number_input(
            "Select task index to remove", min_value=0)
        app.remove_task(selected_task_index)


if __name__ == "__main__":
    main()
