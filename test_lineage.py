#!/usr/bin/env python3
"""
Test script for the lineage extraction endpoint
"""
import requests
import json

BASE_URL = "http://localhost:8080"
AUTH_HEADER = {"X-Authorization": "test-token"}

def test_lineage_endpoint():
    print("="*60)
    print("Testing Lineage Extraction Endpoint")
    print("="*60)
    
    # Step 1: Create a test artifact with known lineage
    print("\n1. Creating test artifact (fine-tuned model)...")
    # Using a model known to have base model dependencies
    create_data = {
        "url": "https://huggingface.co/distilbert/distilbert-base-uncased"
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
    
    # Step 2: Get lineage for the artifact
    print(f"\n2. Extracting lineage for artifact {artifact_id}...")
    response = requests.get(
        f"{BASE_URL}/artifact/model/{artifact_id}/lineage",
        headers=AUTH_HEADER
    )
    
    if response.status_code == 200:
        lineage = response.json()
        print(f"✓ Lineage extracted successfully!")
        print(f"\n{'='*60}")
        print("LINEAGE GRAPH:")
        print('='*60)
        
        nodes = lineage.get('nodes', [])
        edges = lineage.get('edges', [])
        
        print(f"\nNodes ({len(nodes)}):")
        for i, node in enumerate(nodes, 1):
            print(f"\n  {i}. {node.get('name')}")
            print(f"     ID: {node.get('artifact_id', 'N/A')}")
            print(f"     Source: {node.get('source')}")
            metadata = node.get('metadata')
            if metadata:
                print(f"     Metadata: {json.dumps(metadata, indent=10)}")
        
        print(f"\nEdges ({len(edges)}):")
        for i, edge in enumerate(edges, 1):
            from_id = edge.get('from_node_artifact_id')
            to_id = edge.get('to_node_artifact_id')
            relationship = edge.get('relationship')
            
            # Find node names
            from_name = next((n['name'] for n in nodes if n.get('artifact_id') == from_id), from_id)
            to_name = next((n['name'] for n in nodes if n.get('artifact_id') == to_id), to_id)
            
            print(f"\n  {i}. {from_name}")
            print(f"     --[{relationship}]-->")
            print(f"     {to_name}")
        
        if len(edges) == 0:
            print("  (No dependencies found)")
        
    else:
        print(f"✗ Failed to get lineage: {response.status_code}")
        print(response.text)
        return
    
    # Step 3: Test with a base model (BERT)
    print(f"\n{'='*60}")
    print("3. Testing with base model (BERT)...")
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
        print(f"✓ Base model artifact created: {artifact['metadata']['name']}")
        
        response = requests.get(
            f"{BASE_URL}/artifact/model/{artifact_id}/lineage",
            headers=AUTH_HEADER
        )
        
        if response.status_code == 200:
            lineage = response.json()
            nodes = lineage.get('nodes', [])
            edges = lineage.get('edges', [])
            print(f"  Lineage: {len(nodes)} nodes, {len(edges)} edges")
            
            if len(nodes) > 0:
                print(f"  Root node: {nodes[0].get('name')}")
        else:
            print(f"  ✗ Failed to get lineage: {response.status_code}")
    
    print("\n" + "="*60)
    print("TEST COMPLETE! ✓")
    print("="*60)


if __name__ == "__main__":
    try:
        test_lineage_endpoint()
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to API server.")
        print("  Make sure the server is running: python -m api.main")
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
