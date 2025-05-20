.PHONY: install run verify test coverage lint type-check format clean

VENV_ACT = . .venv/bin/activate;

install:
	python3 -m venv .venv
	$(VENV_ACT) pip install --upgrade pip
	$(VENV_ACT) pip install -r requirements.txt -r requirements-dev.txt

# "@" prefix suppresses command echoing so that only the output is shown or redirected to a file
run:
	@$(VENV_ACT) python main.py $(ARGS)

verify: lint type-check

test: verify
	$(VENV_ACT) pytest test/

coverage: verify
	$(VENV_ACT) pytest --cov=src test/ \
        --cov-report=term --cov-report=html

test-log:
	$(VENV_ACT) pytest --log-cli-level=INFO test/

lint:
	$(VENV_ACT) ruff check src/ test/

type-check:
	$(VENV_ACT) mypy src/ test/ \
        --install-types --non-interactive

format:
	$(VENV_ACT) ruff format src/ test/
	$(VENV_ACT) isort src/ test/

clean:
	rm -rf .venv venv .pytest_cache htmlcov app.log
	find . -type f -name "*.py[cod]" -delete