.PHONY: install seed eval test run

install:
	python -m pip install -e ".[dev]"

seed:
	python -m karatmatch.seed

eval:
	python -m karatmatch.evals

test:
	pytest -q

run:
	uvicorn karatmatch.api:app --reload --port 8000
