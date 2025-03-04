#!/bin/bash

# Create necessary directories
mkdir -p src/lib/hooks
mkdir -p src/lib/utils

# Move hooks to the correct location
mv src/frontend/src/hooks/* src/lib/hooks/ 2>/dev/null || true

# Move utils to the correct location
mv src/frontend/src/utils/* src/lib/utils/ 2>/dev/null || true

# Ensure utils.ts is in the correct location
mv src/lib/utils/utils.ts src/lib/utils/index.ts 2>/dev/null || true

# Clean up empty directories
rm -rf src/frontend/src/hooks 2>/dev/null || true
rm -rf src/frontend/src/utils 2>/dev/null || true

echo "Frontend files organized successfully" 