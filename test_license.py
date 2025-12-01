#!/usr/bin/env python3
"""
Test script for the license compatibility check endpoint
"""
import requests
import json

BASE_URL = "http://localhost:8080"
AUTH_HEADER = {"X-Authorization": "test-token"}

def test_license_check_endpoint():
    print("="*60)
    print("Testing License Compatibility Check Endpoint")
    print("="*60)
    
    # Step 1: Create test artifacts
    print("\n1. Creating test artifact (BERT model)...")
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
        print(f"✓ Artifact created successfully!")
        print(f"  Name: {artifact['metadata']['name']}")
        print(f"  ID: {artifact_id}")
    else:
        print(f"✗ Failed to create artifact: {response.status_code}")
        print(response.text)
        return
    
    # Step 2: Check compatibility with MIT licensed repo
    print(f"\n2. Checking compatibility with MIT licensed repo...")
    license_check_data = {
        "github_url": "https://github.com/huggingface/transformers"
    }
    
    response = requests.post(
        f"{BASE_URL}/artifact/model/{artifact_id}/license-check",
        headers=AUTH_HEADER,
        json=license_check_data
    )
    
    if response.status_code == 200:
        is_compatible = response.json()
        print(f"✓ License check completed!")
        print(f"  Artifact: google-bert/bert-base-uncased")
        print(f"  GitHub: huggingface/transformers")
        print(f"  Compatible: {is_compatible}")
        if is_compatible:
            print("  ✓ Licenses are COMPATIBLE for fine-tuning and inference")
        else:
            print("  ✗ Licenses are NOT COMPATIBLE")
    else:
        print(f"✗ Failed to check license: {response.status_code}")
        print(response.text)
        return
    
    # Step 3: Check with Apache 2.0 repo
    print(f"\n3. Checking compatibility with Apache 2.0 licensed repo...")
    license_check_data = {
        "github_url": "https://github.com/google-research/bert"
    }
    
    response = requests.post(
        f"{BASE_URL}/artifact/model/{artifact_id}/license-check",
        headers=AUTH_HEADER,
        json=license_check_data
    )
    
    if response.status_code == 200:
        is_compatible = response.json()
        print(f"✓ License check completed!")
        print(f"  Artifact: google-bert/bert-base-uncased")
        print(f"  GitHub: google-research/bert")
        print(f"  Compatible: {is_compatible}")
        if is_compatible:
            print("  ✓ Licenses are COMPATIBLE")
        else:
            print("  ✗ Licenses are NOT COMPATIBLE")
    else:
        print(f"✗ Failed to check license: {response.status_code}")
        print(response.text)
    
    # Step 4: Check with GPL repo (should be less compatible)
    print(f"\n4. Checking compatibility with GPL licensed repo...")
    license_check_data = {
        "github_url": "https://github.com/pandas-dev/pandas"
    }
    
    response = requests.post(
        f"{BASE_URL}/artifact/model/{artifact_id}/license-check",
        headers=AUTH_HEADER,
        json=license_check_data
    )
    
    if response.status_code == 200:
        is_compatible = response.json()
        print(f"✓ License check completed!")
        print(f"  Artifact: google-bert/bert-base-uncased")
        print(f"  GitHub: pandas-dev/pandas")
        print(f"  Compatible: {is_compatible}")
        if is_compatible:
            print("  ✓ Licenses are COMPATIBLE")
        else:
            print("  ✗ Licenses are NOT COMPATIBLE")
    else:
        print(f"✗ Failed to check license: {response.status_code}")
        print(response.text)
    
    # Step 5: Test error handling - invalid GitHub URL
    print(f"\n5. Testing error handling (invalid GitHub URL)...")
    license_check_data = {
        "github_url": "https://github.com/nonexistent/fakerepo12345"
    }
    
    response = requests.post(
        f"{BASE_URL}/artifact/model/{artifact_id}/license-check",
        headers=AUTH_HEADER,
        json=license_check_data
    )
    
    if response.status_code == 404:
        print(f"✓ Correctly handled non-existent repo (404)")
    else:
        print(f"  Response: {response.status_code}")
        print(f"  {response.text}")
    
    print("\n" + "="*60)
    print("TEST COMPLETE! ✓")
    print("="*60)


if __name__ == "__main__":
    try:
        test_license_check_endpoint()
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to API server.")
        print("  Make sure the server is running: python -m api.main")
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
