# Project Quickstart

A Python script to detect potential duplicate user accounts by:
1. Querying an Oracle DB for IPs  
2. Enriching with geo‑location from a web API (key in `.env`)  
3. Writing the joined data for downstream review

---

## Prerequisites

- Python 3.8+  
- Oracle client libraries (for `oracledb`)  
- A `.env` file (see `.env.example`)

---

## First‑Time Setup

```bash
git clone <repo>
cd <repo>
make install
```

This will:

Create a virtual environment (venv/)

Install runtime & dev dependencies

| Task            | Command         | What it does                        |
| --------------- | --------------- | ----------------------------------- |
| Run app         | `make run`      | Launches `main.py`                  |
| Lint & typing   | `make verify`   | Runs flake8 + mypy                  |
| Run tests       | `make test`     | Unit tests                          |
| Coverage report | `make coverage` | Test coverage (term + HTML archive) |
| Auto‑format     | `make format`   | Autoflake, autopep8, isort, black   |


# Tips 

Don't forget to keep requirements.txt, requirements-dev.txt files up to date when you update project runtime and development dependencies respectively. Otherwise, next time wthen the code is checked out make install will miss needed dependencies.

**Silent mode:**
```bash
make -s test
```
**Single test:**
```bash
pytest test/test_database.py::test_connect_success -v
```
**Clean up:** If you clean the project then you have to make install again to create virtual environment again, otherwise make tasks will give errors for unknown commands because dependencies will not be found.
```bash
make clean
```
**Security:** Never commit real credentials—.env is in .gitignore.

