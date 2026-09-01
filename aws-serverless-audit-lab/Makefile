.PHONY: test lint audit validate localstack-up localstack-down

test:
	pytest --cov=audit --cov=src --cov-report=term-missing

lint:
	ruff check audit src tests

audit:
	python -m audit.audit_template template.yaml --format markdown

validate:
	cfn-lint template.yaml
	sam validate --lint --template-file template.yaml

localstack-up:
	@test -n "$$LOCALSTACK_AUTH_TOKEN" || (echo "LOCALSTACK_AUTH_TOKEN is required; IAM remains UNVERIFIED." && exit 2)
	docker compose up -d

localstack-down:
	docker compose down
