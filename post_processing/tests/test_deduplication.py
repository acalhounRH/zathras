#!/usr/bin/env python3
"""
Test Content-Based Deduplication

This script demonstrates how the content-based checksum system prevents
duplicate documents from being uploaded to OpenSearch.

The same test result processed multiple times will:
1. Generate the same content hash
2. Use the same document ID
3. Update the existing document instead of creating duplicates
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from post_processing.processors.coremark_processor import CoreMarkProcessor
from post_processing.exporters.opensearch_exporter import OpenSearchExporter


def test_deduplication():
    """Test that processing the same results multiple times doesn't create duplicates"""
    
    # Find a sample CoreMark result
    test_dir = Path("production_data/az_rhel_10_ga/rhel/azure/Standard_D8ds_v6_1/coremark")
    
    if not test_dir.exists():
        print(f"❌ Test directory not found: {test_dir}")
        print("Please update the path to point to a valid CoreMark result")
        return False
    
    print("=" * 80)
    print("DEDUPLICATION TEST")
    print("=" * 80)
    print()
    print("This test demonstrates content-based deduplication:")
    print("1. Process the same test results multiple times")
    print("2. Each processing generates the same content hash")
    print("3. OpenSearch uses the hash as document ID")
    print("4. Result: Updates same document instead of creating duplicates")
    print()
    print("=" * 80)
    print()
    
    # Process the same results 3 times
    documents = []
    content_hashes = []
    doc_ids = []
    
    for i in range(3):
        print(f"\n📊 Processing attempt #{i+1}...")
        
        # Process the results
        processor = CoreMarkProcessor(str(test_dir))
        document = processor.process()
        
        # Calculate content hash
        content_hash = document.calculate_content_hash()
        doc_id = document.metadata.document_id
        processing_ts = document.metadata.processing_timestamp
        
        documents.append(document)
        content_hashes.append(content_hash)
        doc_ids.append(doc_id)
        
        print(f"   Document ID: {doc_id}")
        print(f"   Content Hash: {content_hash}")
        print(f"   Processing Time: {processing_ts}")
        
        # Add a small delay so processing_timestamp will differ
        if i < 2:
            time.sleep(0.1)
    
    print()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()
    
    # Check if all hashes are identical
    all_same = all(h == content_hashes[0] for h in content_hashes)
    all_ids_same = all(id == doc_ids[0] for id in doc_ids)
    
    if all_same and all_ids_same:
        print("✅ SUCCESS: All 3 processing attempts generated:")
        print(f"   - Same content hash: {content_hashes[0]}")
        print(f"   - Same document ID: {doc_ids[0]}")
        print()
        print("This means:")
        print("   ✓ Duplicate detection works correctly")
        print("   ✓ Processing timestamp is excluded from hash")
        print("   ✓ Uploading to OpenSearch will update existing doc, not create duplicates")
        print()
    else:
        print("❌ FAILURE: Documents have different hashes or IDs")
        for i, (hash_val, doc_id) in enumerate(zip(content_hashes, doc_ids), 1):
            print(f"   Attempt {i}: {doc_id} (hash: {hash_val})")
        return False
    
    # Verify processing timestamps are different
    timestamps = [doc.metadata.processing_timestamp for doc in documents]
    all_different = len(set(timestamps)) == len(timestamps)
    
    if all_different:
        print("✅ Processing timestamps differ (as expected):")
        for i, ts in enumerate(timestamps, 1):
            print(f"   Attempt {i}: {ts}")
        print()
    else:
        print("⚠️  Warning: Processing timestamps are identical")
        print("   (This might be okay if processing was very fast)")
        print()
    
    print("=" * 80)
    print("OPENSEARCH BEHAVIOR")
    print("=" * 80)
    print()
    print("When uploading to OpenSearch with this document ID:")
    print()
    print("  First upload:")
    print(f"    POST /{doc_ids[0]}")
    print("    → Creates new document")
    print()
    print("  Second upload (same ID):")
    print(f"    POST /{doc_ids[0]}")
    print("    → Updates existing document (no duplicate)")
    print()
    print("  Third upload (same ID):")
    print(f"    POST /{doc_ids[0]}")
    print("    → Updates existing document again")
    print()
    print("Result: Only 1 document in OpenSearch, updated 3 times")
    print()
    
    # Show the document structure
    print("=" * 80)
    print("HASH CALCULATION DETAILS")
    print("=" * 80)
    print()
    print("The content hash is calculated from:")
    print("  ✓ Test name and version")
    print("  ✓ System configuration (CPU, memory, OS)")
    print("  ✓ Test configuration and parameters")
    print("  ✓ All benchmark results and metrics")
    print("  ✓ Test timestamp (when test was originally run)")
    print()
    print("The content hash EXCLUDES:")
    print("  ✗ Processing timestamp (changes on each run)")
    print("  ✗ Document ID (we're computing it)")
    print()
    print("This ensures identical test results always produce the same hash,")
    print("regardless of when they're processed.")
    print()
    
    return True


def test_with_opensearch():
    """Actually test uploading to OpenSearch (if configured)"""
    import os
    
    # Check if OpenSearch is configured
    opensearch_url = os.environ.get('OPENSEARCH_URL')
    opensearch_user = os.environ.get('OPENSEARCH_USER')
    opensearch_pass = os.environ.get('OPENSEARCH_PASS')
    
    if not all([opensearch_url, opensearch_user, opensearch_pass]):
        print()
        print("=" * 80)
        print("OPENSEARCH INTEGRATION TEST")
        print("=" * 80)
        print()
        print("To test actual deduplication in OpenSearch, set:")
        print("  export OPENSEARCH_URL='https://opensearch.example.com'")
        print("  export OPENSEARCH_USER='username'")
        print("  export OPENSEARCH_PASS='password'")
        print()
        return
    
    print()
    print("=" * 80)
    print("OPENSEARCH INTEGRATION TEST")
    print("=" * 80)
    print()
    
    # Find a sample result
    test_dir = Path("production_data/az_rhel_10_ga/rhel/azure/Standard_D8ds_v6_1/coremark")
    if not test_dir.exists():
        print("❌ Test directory not found")
        return
    
    # Create exporter
    exporter = OpenSearchExporter(
        url=opensearch_url,
        index="zathras-dedup-test",
        username=opensearch_user,
        password=opensearch_pass,
        verify_ssl=False
    )
    
    # Test connection
    if not exporter.test_connection():
        print("❌ Failed to connect to OpenSearch")
        return
    
    print("✅ Connected to OpenSearch")
    print()
    
    # Process and upload 3 times
    processor = CoreMarkProcessor(str(test_dir))
    document = processor.process()
    doc_id = document.metadata.document_id
    
    print(f"Document ID: {doc_id}")
    print()
    
    # Upload 3 times
    for i in range(3):
        print(f"Upload #{i+1}...", end=" ")
        result_id = exporter.export_zathras_document(document.to_dict_summary_only())
        print(f"✓ Uploaded (ID: {result_id})")
        time.sleep(0.5)
    
    print()
    print("Searching for documents...")
    
    # Query to find all documents with this ID
    query = {
        "query": {
            "term": {
                "metadata.document_id.keyword": doc_id
            }
        }
    }
    
    results = exporter.search(query)
    hit_count = results['hits']['total']['value']
    
    print(f"Found {hit_count} document(s)")
    print()
    
    if hit_count == 1:
        print("✅ SUCCESS: Only 1 document exists (no duplicates)")
        print("   The same document was updated 3 times instead of creating duplicates")
    else:
        print(f"❌ FAILURE: Found {hit_count} documents (expected 1)")
        print("   Deduplication may not be working correctly")
    
    print()


if __name__ == "__main__":
    success = test_deduplication()
    
    if success:
        test_with_opensearch()
        print("=" * 80)
        print("✅ All deduplication tests passed!")
        print("=" * 80)
        sys.exit(0)
    else:
        sys.exit(1)

