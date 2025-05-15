# Always run these, even if a file with the same name exists
.PHONY: install run verify test coverage lint type-check format clean

# Path to our venv activation
VENV_ACT = . venv/bin/activate;

install:
	python3 -m venv venv
	$(VENV_ACT) pip install --upgrade pip
	$(VENV_ACT) pip install -r requirements.txt -r requirements-dev.txt

run:
	$(VENV_ACT) python main.py

verify: lint type-check

test: verify
	$(VENV_ACT) pytest test/

coverage: verify
	$(VENV_ACT) pytest --cov=src test/ \
		--cov-report=term --cov-report=html

# Show INFO‑level logs during testing
test-log:
	$(VENV_ACT) pytest --log-cli-level=INFO test/

lint:
	$(VENV_ACT) flake8 src/ test/

type-check:
	$(VENV_ACT) mypy src/ test/ \
		--install-types --non-interactive

format:
	$(VENV_ACT) autoflake --in-place --remove-all-unused-imports --recursive src/ test/
	$(VENV_ACT) autopep8 --in-place --aggressive --recursive src/ test/
	$(VENV_ACT) isort src/ test/
	$(VENV_ACT) black src/ test/

clean:
	rm -rf venv .pytest_cache htmlcov
	find . -type f -name "*.py[cod]" -delete
