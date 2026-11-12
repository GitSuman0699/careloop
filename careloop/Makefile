.PHONY: dev test seed simulate lint build deps-report

dev:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
	cd frontend && npx vite dev

test:
	cd backend && python -m pytest tests/ -v

seed:
	cd backend && python -m app.seed.generator

simulate:
	cd backend && python -m sim.run

lint:
	cd backend && ruff check app/ sim/

build:
	cd frontend && npx vite build
	cp -r frontend/dist backend/static

deps-report:
	cd backend && pip list
	cd frontend && npm list --depth=0
