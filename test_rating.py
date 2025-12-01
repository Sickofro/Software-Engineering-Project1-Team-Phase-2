#!/usr/bin/env python3
"""
Quick test script for the rating endpoint
"""
import requests
import json
import time

BASE_URL = "http://localhost:8080"
AUTH_HEADER = {"X-Authorization": "test-token"}

def test_rating_endpoint():
    print("="*60)
    print("Testing Phase 2 Rating Endpoint")
    print("="*60)
    
    # Step 1: Create a test artifact
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
        print(f"✓ Artifact created successfully!")
        print(f"  Name: {artifact['metadata']['name']}")
        print(f"  ID: {artifact_id}")
        print(f"  Type: {artifact['metadata']['type']}")
    else:
        print(f"✗ Failed to create artifact: {response.status_code}")
        print(response.text)
        return
    
    # Step 2: Rate the artifact
    print(f"\n2. Rating artifact {artifact_id}...")
    print("   (This may take 10-30 seconds as it calculates all metrics...)")
    
    start_time = time.time()
    response = requests.get(
        f"{BASE_URL}/artifact/model/{artifact_id}/rate",
        headers=AUTH_HEADER
    )
    elapsed = time.time() - start_time
    
    if response.status_code == 200:
        rating = response.json()
        print(f"✓ Rating calculated in {elapsed:.2f} seconds!")
        print("\n" + "="*60)
        print("RATING RESULTS:")
        print("="*60)
        print(f"Name:                    {rating['name']}")
        print(f"Category:                {rating['category']}")
        print(f"\nNet Score:               {rating['net_score']:.4f}")
        print(f"Ramp-up Time:            {rating['ramp_up_time']:.4f}")
        print(f"Bus Factor:              {rating['bus_factor']:.4f}")
        print(f"Performance Claims:      {rating['performance_claims']:.4f}")
        print(f"License:                 {rating['license']:.4f}")
        print(f"Dataset & Code Score:    {rating['dataset_and_code_score']:.4f}")
        print(f"Dataset Quality:         {rating['dataset_quality']:.4f}")
        print(f"Code Quality:            {rating['code_quality']:.4f}")
        print(f"Reproducibility:         {rating['reproducibility']:.4f}")
        print(f"Reviewedness:            {rating['reviewedness']:.4f}")
        print(f"Tree Score:              {rating['tree_score']:.4f}")
        print(f"\nSize Scores:")
        print(f"  Raspberry Pi:          {rating['size_score']['raspberry_pi']:.4f}")
        print(f"  Jetson Nano:           {rating['size_score']['jetson_nano']:.4f}")
        print(f"  Desktop PC:            {rating['size_score']['desktop_pc']:.4f}")
        print(f"  AWS Server:            {rating['size_score']['aws_server']:.4f}")
        print("="*60)
    else:
        print(f"✗ Failed to rate artifact: {response.status_code}")
        print(response.text)
        return
    
    # Step 3: Test cache (should be instant)
    print(f"\n3. Testing cached rating (should be instant)...")
    start_time = time.time()
    response = requests.get(
        f"{BASE_URL}/artifact/model/{artifact_id}/rate",
        headers=AUTH_HEADER
    )
    elapsed = time.time() - start_time
    
    if response.status_code == 200:
        print(f"✓ Cached rating returned in {elapsed:.3f} seconds!")
        print("  (Much faster because it's cached)")
    else:
        print(f"✗ Cache test failed: {response.status_code}")
    
    print("\n" + "="*60)
    print("TEST COMPLETE! ✓")
    print("="*60)

if __name__ == "__main__":
    try:
        test_rating_endpoint()
    except requests.exceptions.ConnectionError:
        print("✗ Error: Could not connect to API server.")
        print("  Make sure the server is running: python -m api.main")
    except Exception as e:
        print(f"✗ Error: {e}")
