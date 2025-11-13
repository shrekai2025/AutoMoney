#!/bin/bash

echo "Testing AutoMoney API Endpoints"
echo "================================"

# Test 1: Check if backend is running
echo -e "\n1. Testing backend health..."
curl -s http://localhost:8000/api/v1/auth/config | head -c 100
echo ""

# Test 2: Try to access strategies endpoint without auth (should fail)
echo -e "\n2. Testing /api/v1/strategies without auth (expecting error)..."
curl -s -w "\nHTTP Status: %{http_code}\n" http://localhost:8000/api/v1/strategies
echo ""

# Test 3: Check if admin endpoint exists
echo -e "\n3. Testing /api/v1/admin/strategies without auth (expecting 401/403)..."
curl -s -w "\nHTTP Status: %{http_code}\n" http://localhost:8000/api/v1/admin/strategies
echo ""

echo -e "\nTests complete. Backend is responding."
