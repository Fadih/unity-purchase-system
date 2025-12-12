.PHONY: help build test test-local test-docker clean run docker-build docker-run docker-push docker-release lint format install-deps deploy-backend undeploy status logs update-kustomize-image port-forward kafka-check

# Variables
IMAGE_NAME ?= fadihussien/unity
IMAGE_TAG ?= backend-v1.0.4
FULL_IMAGE_NAME = $(IMAGE_NAME):$(IMAGE_TAG)
PORT ?= 8000
NAMESPACE ?= app

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(GREEN)Available targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

install-deps: ## Install Python dependencies
	@echo "$(GREEN)Installing dependencies...$(NC)"
	@if [ ! -d "venv" ]; then \
		python3 -m venv venv; \
	fi
	@. venv/bin/activate && \
		pip install --upgrade pip setuptools wheel && \
		pip install -r requirements.txt
	@echo "$(GREEN)✅ Dependencies installed$(NC)"

build: ## Build Docker image
	@echo "$(GREEN)Building Docker image: $(FULL_IMAGE_NAME)$(NC)"
	@docker build -t $(FULL_IMAGE_NAME) .
	@echo "$(GREEN)✅ Docker image built successfully$(NC)"

test: test-local ## Run all tests (local by default)

test-local: ## Run tests locally
	@echo "$(GREEN)Running local tests...$(NC)"
	@if [ ! -d "venv" ]; then \
		echo "$(YELLOW)Creating virtual environment...$(NC)"; \
		python3 -m venv venv; \
	fi
	@. venv/bin/activate && \
		pip install --quiet --upgrade pip setuptools wheel && \
		pip install --quiet -r requirements.txt && \
		python -m pytest tests/ -v --tb=short || (echo "$(RED)❌ Tests failed$(NC)" && exit 1)
	@echo "$(GREEN)✅ Local tests completed$(NC)"

test-docker: build ## Run tests in Docker container
	@echo "$(GREEN)Running tests in Docker container...$(NC)"
	@docker run --rm $(FULL_IMAGE_NAME) \
		python -m pytest tests/ -v --tb=short || (echo "$(RED)❌ Tests failed$(NC)" && exit 1)
	@echo "$(GREEN)✅ Docker tests completed$(NC)"

test-health: ## Test health endpoint
	@echo "$(GREEN)Testing health endpoint...$(NC)"
	@curl -f http://localhost:$(PORT)/health || \
		(echo "$(RED)❌ Health check failed. Is the server running?$(NC)" && exit 1)
	@echo "$(GREEN)✅ Health check passed$(NC)"

run: ## Run the application locally
	@echo "$(GREEN)Starting application on port $(PORT)...$(NC)"
	@if [ ! -d "venv" ]; then \
		echo "$(YELLOW)Creating virtual environment...$(NC)"; \
		python3 -m venv venv; \
	fi
	@. venv/bin/activate && \
		pip install --quiet --upgrade pip setuptools wheel && \
		pip install --quiet -r requirements.txt && \
		python -m uvicorn app.main:app --host 0.0.0.0 --port $(PORT) --reload

docker-build: build ## Alias for build

docker-run: build ## Run Docker container
	@echo "$(GREEN)Running Docker container on port $(PORT)...$(NC)"
	@docker run --rm -p $(PORT):8000 \
		-e MONGODB_URI=mongodb://localhost:27017/purchases \
		-e KAFKA_BOOTSTRAP_SERVERS=localhost:9092 \
		-e KAFKA_TOPIC=purchase-events \
		-e KAFKA_GROUP_ID=customer-management-api \
		$(FULL_IMAGE_NAME)

docker-push: ## Push Docker image to Docker Hub (assumes image already built)
	@echo "$(GREEN)Pushing $(FULL_IMAGE_NAME) to Docker Hub...$(NC)"
	@echo "$(YELLOW)Make sure you're logged in: docker login$(NC)"
	@docker push $(FULL_IMAGE_NAME)
	@echo "$(GREEN)✅ Image pushed successfully to $(FULL_IMAGE_NAME)$(NC)"

docker-release: build docker-push ## Build and push Docker image to Docker Hub
	@echo "$(GREEN)✅ Release completed: $(FULL_IMAGE_NAME)$(NC)"

lint: ## Run linter (if available)
	@echo "$(GREEN)Running linter...$(NC)"
	@if command -v pylint > /dev/null; then \
		pylint app/ || true; \
	else \
		echo "$(YELLOW)⚠️  pylint not installed, skipping...$(NC)"; \
	fi

format: ## Format code (if available)
	@echo "$(GREEN)Formatting code...$(NC)"
	@if command -v black > /dev/null; then \
		black app/ || true; \
	else \
		echo "$(YELLOW)⚠️  black not installed, skipping...$(NC)"; \
	fi

clean: ## Clean build artifacts and virtual environment
	@echo "$(GREEN)Cleaning...$(NC)"
	@rm -rf venv/
	@rm -rf __pycache__/
	@rm -rf app/__pycache__/
	@rm -rf .pytest_cache/
	@rm -rf .coverage
	@rm -rf htmlcov/
	@docker rmi $(FULL_IMAGE_NAME) 2>/dev/null || true
	@echo "$(GREEN)✅ Clean completed$(NC)"

deploy-backend: update-kustomize-image ## Deploy backend API to Kubernetes using Kustomize (requires kubectl and KEDA)
	@echo "$(GREEN)Deploying backend API to Kubernetes namespace: $(NAMESPACE) using Kustomize...$(NC)"
	@echo "$(YELLOW)Note: Assumes KEDA is installed via k8s/infrastructure/install.sh$(NC)"
	@kubectl apply -k ../k8s/app/backend/
	@echo "$(GREEN)✅ Backend deployment completed $(NC)"

update-kustomize-image: ## Update image tag in kustomization.yaml to match Makefile IMAGE_TAG
	@echo "$(YELLOW)Updating kustomization.yaml with image: $(FULL_IMAGE_NAME)$(NC)"
	@sed -i.bak "s|newName:.*|newName: $(IMAGE_NAME)|g; s|newTag:.*|newTag: $(IMAGE_TAG)|g" ../k8s/app/backend/kustomization.yaml && rm -f ../k8s/app/backend/kustomization.yaml.bak
	@echo "$(GREEN)✅ Kustomize image updated$(NC)"

undeploy: ## Remove backend deployment from Kubernetes using Kustomize
	@echo "$(GREEN)Removing backend deployment from Kubernetes namespace: $(NAMESPACE)$(NC)"
	@kubectl delete -k ../k8s/app/backend/ 2>/dev/null || \
		(kubectl delete -f ../k8s/app/backend/scaledobject.yaml 2>/dev/null || true; \
		 kubectl delete -f ../k8s/app/backend/service.yaml 2>/dev/null || true; \
		 kubectl delete -f ../k8s/app/backend/deployment.yaml 2>/dev/null || true; \
		 kubectl delete -f ../k8s/app/backend/secret.yaml 2>/dev/null || true; \
		 kubectl delete -f ../k8s/app/backend/configmap.yaml 2>/dev/null || true; \
		 kubectl delete -f ../k8s/app/backend/namespace.yaml 2>/dev/null || true)
	@echo "$(GREEN)✅ Backend undeployment completed$(NC)"

status: ## Check deployment status
	@echo "$(GREEN)Checking deployment status...$(NC)"
	@kubectl get deployment backend-app -n $(NAMESPACE) || echo "$(RED)Deployment not found$(NC)"
	@kubectl get pods -l app=backend-app -n $(NAMESPACE) || echo "$(RED)Pods not found$(NC)"
	@kubectl get svc backend-app -n $(NAMESPACE) || echo "$(RED)Service not found$(NC)"

logs: ## Show application logs
	@echo "$(GREEN)Showing logs...$(NC)"
	@kubectl logs -l app=backend-app -n $(NAMESPACE) --tail=100 -f || \
		echo "$(RED)No logs found. Is the deployment running?$(NC)"

port-forward: ## Port-forward to backend API service (Ctrl+C to stop)
	@echo "$(GREEN)Starting port-forward to backend-app service...$(NC)"
	@echo "$(YELLOW)Access the API at: http://localhost:$(PORT)$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop$(NC)"
	@kubectl port-forward svc/backend-app $(PORT):8000 -n $(NAMESPACE)

kafka-check: ## Check if events are in Kafka topic (purchase-events)
	@echo "$(GREEN)Checking Kafka topic 'purchase-events' for messages...$(NC)"
	@echo "$(YELLOW)Reading last 10 messages (if any)...$(NC)"
	@kubectl -n kafka run kafka-check-$$(date +%s) --rm -i --restart=Never \
		--image=apache/kafka:4.0.0 -- \
		/opt/kafka/bin/kafka-console-consumer.sh \
			--topic purchase-events \
			--bootstrap-server kafka:9092 \
			--from-beginning \
			--max-messages 10 \
			--timeout-ms 3000 2>/dev/null || \
		echo "$(YELLOW)No messages found or topic is empty$(NC)"
