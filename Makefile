check:
	ruff check . --fix
	ruff format --check .
	mypy src
	pytest -q --cov=algorithms --cov-report=term-missing --cov-report=xml
