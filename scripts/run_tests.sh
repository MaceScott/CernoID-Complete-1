#!/bin/bash

# Exit on any error
set -e

# Function to run backend tests
run_backend_tests() {
    echo "Running backend tests..."
    cd backend
    poetry run pytest --cov=src --cov-report=term-missing --cov-report=xml
    poetry run black . --check
    poetry run isort . --check
    poetry run flake8 .
    poetry run mypy src
    cd ..
}

# Function to run frontend tests
run_frontend_tests() {
    echo "Running frontend tests..."
    cd frontend
    npm run test
    npm run lint
    cd ..
}

# Function to run integration tests
run_integration_tests() {
    echo "Running integration tests..."
    
    # Start required services
    docker-compose up -d db redis vault
    
    # Wait for services to be ready
    echo "Waiting for services to be ready..."
    sleep 10
    
    # Run backend integration tests
    cd backend
    poetry run pytest tests/integration --cov=src --cov-report=term-missing
    cd ..
    
    # Run frontend integration tests
    cd frontend
    npm run test:integration
    cd ..
    
    # Stop services
    docker-compose down
}

# Function to run security tests
run_security_tests() {
    echo "Running security tests..."
    
    # Run Bandit security checks
    cd backend
    poetry run bandit -r src/
    cd ..
    
    # Run npm audit
    cd frontend
    npm audit
    cd ..
    
    # Run Trivy vulnerability scanner
    docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
        -v $PWD:/root/project aquasec/trivy \
        filesystem --security-checks vuln,config \
        --severity HIGH,CRITICAL /root/project
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --backend)
            RUN_BACKEND=true
            shift
            ;;
        --frontend)
            RUN_FRONTEND=true
            shift
            ;;
        --integration)
            RUN_INTEGRATION=true
            shift
            ;;
        --security)
            RUN_SECURITY=true
            shift
            ;;
        --all)
            RUN_BACKEND=true
            RUN_FRONTEND=true
            RUN_INTEGRATION=true
            RUN_SECURITY=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# If no arguments provided, run all tests
if [[ -z $RUN_BACKEND && -z $RUN_FRONTEND && -z $RUN_INTEGRATION && -z $RUN_SECURITY ]]; then
    RUN_BACKEND=true
    RUN_FRONTEND=true
    RUN_INTEGRATION=true
    RUN_SECURITY=true
fi

# Run selected tests
if [[ $RUN_BACKEND == true ]]; then
    run_backend_tests
fi

if [[ $RUN_FRONTEND == true ]]; then
    run_frontend_tests
fi

if [[ $RUN_INTEGRATION == true ]]; then
    run_integration_tests
fi

if [[ $RUN_SECURITY == true ]]; then
    run_security_tests
fi

echo "All tests completed successfully!" 