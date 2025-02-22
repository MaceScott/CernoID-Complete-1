#!/bin/bash

# Set variables
NAMESPACE="face-recognition"
REGISTRY="your-registry.com"
VERSION=$(git describe --tags --always)

# Create namespace if it doesn't exist
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Build and push Docker images
docker build -t $REGISTRY/face-recognition-system:$VERSION -f deployment/Dockerfile .
docker push $REGISTRY/face-recognition-system:$VERSION

docker build -t $REGISTRY/face-recognition-dashboard:$VERSION -f deployment/Dockerfile.dashboard .
docker push $REGISTRY/face-recognition-dashboard:$VERSION

# Update Kubernetes manifests with new version
sed -i "s|face-recognition-system:latest|face-recognition-system:$VERSION|" \
    deployment/kubernetes/*.yaml

# Apply Kubernetes manifests
kubectl apply -f deployment/kubernetes/

# Wait for deployment to complete
kubectl rollout status deployment/face-recognition-api -n $NAMESPACE

echo "Kubernetes deployment completed successfully!" 