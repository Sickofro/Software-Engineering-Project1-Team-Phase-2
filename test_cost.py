#!/usr/bin/env python3
"""
Test script for the cost calculation endpoint
"""
import requests
import json

BASE_URL = "http://localhost:8080"
AUTH_HEADER = {"X-Authorization": "test-token"}

def test_cost_endpoint():
    print("="*60)
    print("Testing Cost Calculation Endpoint")
    print("="*60)
    
    # Step 1: Create a test artifact (or use existing one)
    print("\n1. Creating test artifact...")
    create_data = {
        "url": "https://huggingface.co/google-bert/bert-base-uncased"
    }
    
    response = requests.post(
        f"{BASE_URL}/artifact/model",
        headers=AUTH_HEADER,
        json=create_data
    )
    
    if response.status_code in [200, 201]:
        artifact = response.json()
        artifact_id = artifact['metadata']['id']
        print(f"✓ Artifact created/retrieved successfully!")
        print(f"  Name: {artifact['metadata']['name']}")
        print(f"  ID: {artifact_id}")
    else:
        print(f"✗ Failed to create artifact: {response.status_code}")
        print(response.text)
        return
    
    # Step 2: Get cost without dependencies
    print(f"\n2. Calculating cost (without dependencies)...")
    response = requests.get(
        f"{BASE_URL}/artifact/model/{artifact_id}/cost",
        headers=AUTH_HEADER,
        params={"dependency": False}
    )
    
    if response.status_code == 200:
        cost_data = response.json()
        print(f"✓ Cost calculated successfully!")
        print(f"\n  Result:")
        print(f"  {json.dumps(cost_data, indent=2)}")
        
        artifact_cost = cost_data.get(artifact_id, {})
        total_cost = artifact_cost.get('total_cost', 0)
        print(f"\n  Total download size: {total_cost} MB")
    else:
        print(f"✗ Failed to get cost: {response.status_code}")
        print(response.text)
        return
    
    # Step 3: Get cost with dependencies
    print(f"\n3. Calculating cost (with dependencies)...")
    response = requests.get(
        f"{BASE_URL}/artifact/model/{artifact_id}/cost",
        headers=AUTH_HEADER,
        params={"dependency": True}
    )
    
    if response.status_code == 200:
        cost_data = response.json()
        print(f"✓ Cost calculated successfully!")
        print(f"\n  Result:")
        print(f"  {json.dumps(cost_data, indent=2)}")
        
        artifact_cost = cost_data.get(artifact_id, {})
        standalone = artifact_cost.get('standalone_cost', 0)
        total = artifact_cost.get('total_cost', 0)
        print(f"\n  Standalone cost: {standalone} MB")
        print(f"  Total cost (with deps): {total} MB")
    else:
        print(f"✗ Failed to get cost: {response.status_code}")
        print(response.text)
        return
    
    # Step 4: Test with GitHub repository
    print(f"\n4. Testing with GitHub repository...")
    create_data = {
        "url": "https://github.com/huggingface/transformers"
    }
    
    response = requests.post(
        f"{BASE_URL}/artifact/code",
        headers=AUTH_HEADER,
        json=create_data
    )
    
    if response.status_code in [200, 201]:
        artifact = response.json()
        artifact_id = artifact['metadata']['id']
        print(f"✓ GitHub artifact created!")
        print(f"  Name: {artifact['metadata']['name']}")
        print(f"  ID: {artifact_id}")
        
        # Get cost
        response = requests.get(
            f"{BASE_URL}/artifact/code/{artifact_id}/cost",
            headers=AUTH_HEADER
        )
        
        if response.status_code == 200:
            cost_data = response.json()
            artifact_cost = cost_data.get(artifact_id, {})
            total_cost = artifact_cost.get('total_cost', 0)
            print(f"  Repository size: {total_cost} MB")
        else:
            print(f"  ✗ Failed to get cost: {response.status_code}")
    else:
        print(f"✗ Failed to create GitHub artifact: {response.status_code}")
    
    print("\n" + "="*60)
    print("TEST COMPLETE! ✓")
    print("="*60)


if __name__ == "__main__":
    try:
        test_cost_endpoint()
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to API server.")
        print("  Make sure the server is running: python -m api.main")
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
