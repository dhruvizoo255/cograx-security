.PHONY: run ui test lint format contract
run:
	uvicorn backend.main:app --reload --port 8000
ui:
	streamlit run frontend/app.py
test:
	pytest -q --cov=backend --cov-report=term-missing
lint:
	black --check backend frontend tests blockchain && isort --check-only backend frontend tests blockchain && flake8 backend frontend tests blockchain
format:
	black backend frontend tests blockchain && isort backend frontend tests blockchain
contract:
	python -m blockchain.scripts.deploy
