.PHONY: install dev-backend dev-frontend dev-streamlit lint format docker-up docker-down clean cli-install

install:
	uv sync --all-packages && uv tool install --force "cocoindex-code[full]"
dev-backend:
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm install && npm run dev

dev-streamlit:
	uv run streamlit run streamlit_app.py --server.port 8501


cli-install:
	uv tool install --force ./cli

generate-samples:
	cd backend && uv run python ../scripts/generate_samples_output.py

lint:
	uv run ruff check .

format:
	uv run ruff check --fix .
	uv run black .

docker-up:
	docker compose up --build

docker-down:
	docker compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/.tmp_projects
