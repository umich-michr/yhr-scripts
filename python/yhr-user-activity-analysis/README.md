# Create a Virtual Environment  

Use Python's built-in venv module to create an isolated environment inside your project directory.
```bash
python3 -m venv venv
```

# Activate the Virtual Environment

Activate the environment to work within it. This ensures commands like pip and python use the isolated setup.

```bash
source venv/bin/activate
```
Your terminal prompt will change (e.g., (venv)), indicating you’re in the virtual environment.

# Install Dependencies

```bash
pip install pandas requests oracledb
```

# Install Dependencies

```bash
pip install -r requirements.txt
# to install test dependencies
pip install -r requirements-dev.txt
```

# Freeze Dependencies

```bash
pip freeze > requirements.txt
```
This file ensures consistency across setups by listing all installed packages and their versions.

# Run Your Program  

Run your Python script within the active environment. It will use the isolated dependencies.

```bash
python my_script.py
```

# Deactivate the Environment

When finished, exit the virtual environment:  

```bash
deactivate
```

# Managing the Project

## Adding New Dependencies  

Activate the environment, install the new package, and update requirements.txt:  
```bash
source venv/bin/activate
pip install new_package
pip freeze > requirements.txt
deactivate
```

## Removing the Project  

To delete the project and its dependencies, simply remove the project directory. Since the virtual environment is inside project directory, all dependencies are deleted with it, leaving no traces in the global environment.

# Run the Script 

```bash
python main.py
```

# Run Tests

For the packages to be found implied by dunder init files (__init.py__), either the PYTHONPATH env variable should be set to the project root or the pytest.ini file should set pythonpath to . in the project root using init file format. 

```bash
# without coverage
PYTHONPATH=. pytest tests/
# with coverage
PYTHONPATH=. pytest --cov=src tests/ --cov-report=term --cov-report=html
```

## Run a single test

```bash
pytest tests/test_database.py::test_connect_success -v
```
