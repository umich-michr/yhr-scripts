# User Activity Analysis

This project analyzes user activity data from a database and outputs results as CSV. It includes tools for linting, formatting, type checking, and testing, all managed via a Makefile.

---

## Getting Started

### 1. Set Up the Python Virtual Environment

A [virtual environment](https://docs.python.org/3/tutorial/venv.html) is a self-contained directory that contains a Python installation for a particular version of Python, plus a number of additional packages.  
This helps keep your project’s dependencies isolated from your system Python.

To create and install dependencies, run:

```sh
make install
```

This will:
- Create a `.venv` directory for your virtual environment.
- Install all required packages into `.venv`.

---

### 2. **Activating the Virtual Environment**

**Important:**  
After running `make install`, you need to activate the virtual environment in your terminal **before running Python commands manually**.

Activate with:

```sh
source .venv/bin/activate
```

You should see your prompt change to show `(.venv)` at the beginning.  
While activated, any `python` or `pip` command will use the environment’s Python and packages.

**Why do I have to do this?**  
- The activation command only affects your current terminal session.
- Makefiles and scripts can’t change your parent shell’s environment, so you must run `source .venv/bin/activate` yourself.
- This is a standard Python workflow to keep dependencies isolated.

To deactivate, just run:

```sh
deactivate
```

---

## Usage

### Run the Analysis

- For all studies:
  ```sh
  make run
  ```
- For a specific study (e.g., study ID 4739):
  ```sh
  make run ARGS=4739
  ```

#### Without the Makefile

First, activate your virtual environment:

```sh
source .venv/bin/activate
```

Then run:

- For all studies:
  ```sh
  python main.py
  ```
- For a specific study (e.g., study ID 4739):
  ```sh
  python main.py 4739
  ```

---

## Development Tasks

All common tasks are available via the Makefile:

| Task         | Command                       | Description                                 |
|--------------|------------------------------|---------------------------------------------|
| Install      | `make install`               | Set up venv and install dependencies        |
| Lint         | `make lint`                  | Lint code with Ruff                         |
| Format       | `make format`                | Format code with Ruff and isort             |
| Type Check   | `make type-check`            | Static type checking with mypy              |
| Test         | `make test`                  | Run all tests                               |
| Coverage     | `make coverage`              | Run tests with coverage report              |
| Clean        | `make clean`                 | Remove venv and all build/test artifacts    |

---

## Notes for Python Newbies

- **Always activate your virtual environment** before running Python scripts or using pip, unless you are using the Makefile (which handles activation for you).
- If you open a new terminal, you’ll need to activate the venv again.
- The Makefile automates most tasks, but cannot activate the venv for your interactive shell—this is a limitation of how shells and Makefiles work.

---

## Troubleshooting

- If you see errors about missing modules, make sure you have activated your virtual environment.
- If you have issues with the Makefile, check that all recipe lines are indented with tabs, not spaces.

---

## License

MIT License
