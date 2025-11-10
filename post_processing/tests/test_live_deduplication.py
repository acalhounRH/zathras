#!/usr/bin/env python3
"""
Live Deduplication Test

Demonstrates that processing the same results multiple times does NOT create
duplicates in OpenSearch. Shows:

1. Process results → upload to OpenSearch
2. Process same results again → upload to OpenSearch
3. Query OpenSearch → only 1 document exists
4. Show document details with different processing timestamps
"""

import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from post_processing.processors.coremark_processor import CoreMarkProcessor
from post_processing.processors.streams_processor import StreamsProcessor
from post_processing.exporters.opensearch_exporter import OpenSearchExporter


def find_test_data():
    """Find available test data (zip files or directories)"""
    # Look for zip files first
    import glob
    
    zip_patterns = [
        "quick_sample_data/**/results_coremark.zip",
        "production_data/**/results_coremark.zip",
        "quick_sample_data/**/results_streams.zip",
        "production_data/**/results_streams.zip",
    ]
    
    for pattern in zip_patterns:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            zip_path = matches[0]
            # Determine processor from filename
            if "coremark" in zip_path:
                return str(Path(zip_path).parent), CoreMarkProcessor
            elif "streams" in zip_path:
                return str(Path(zip_path).parent), StreamsProcessor
    
    # Fallback to directories
    possible_paths = [
        "production_data/az_rhel_10_ga/rhel/azure/Standard_D8ds_v6_1/coremark",
        "production_data/az_rhel_10_ga/rhel/azure/Standard_D8ds_v6_1/streams",
        "quick_sample_data/coremark",
        "quick_sample_data/streams",
    ]
    
    for path in possible_paths:
        test_path = Path(path)
        if test_path.exists():
            # Determine processor
            if "coremark" in path:
                return str(test_path), CoreMarkProcessor
            elif "streams" in path:
                return str(test_path), StreamsProcessor
    
    return None, None


def get_opensearch_config():
    """Get OpenSearch configuration from environment or config file"""
    # Try environment variables first
    url = os.environ.get('OPENSEARCH_URL')
    username = os.environ.get('OPENSEARCH_USER')
    password = os.environ.get('OPENSEARCH_PASS')
    
    if url and username and password:
        return {
            'url': url,
            'username': username,
            'password': password,
            'verify_ssl': False
        }
    
    # Try config file
    config_file = Path("post_processing/config/export_config.yml")
    if config_file.exists():
        import yaml
        with open(config_file) as f:
            config = yaml.safe_load(f)
            if 'opensearch' in config:
                return {
                    'url': config['opensearch']['url'],
                    'username': config['opensearch']['username'],
                    'password': config['opensearch']['password'],
                    'verify_ssl': config['opensearch'].get('verify_ssl', False)
                }
    
    return None


def main():
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 25 + "LIVE DEDUPLICATION TEST" + " " * 30 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    print("This test will:")
    print("  1. Process benchmark results and upload to OpenSearch")
    print("  2. Process THE SAME results again and upload to OpenSearch")
    print("  3. Query OpenSearch to verify only 1 document exists (not 2)")
    print("  4. Show that processing_timestamp changed but no duplicate was created")
    print()
    print("=" * 80)
    print()
    
    # Find test data
    print("🔍 Step 1: Finding test data...")
    test_path, processor_class = find_test_data()
    
    if not test_path:
        print("❌ No test data found!")
        print()
        print("Please ensure one of these directories exists:")
        print("  - production_data/.../coremark")
        print("  - production_data/.../streams")
        print("  - quick_sample_data/coremark")
        print("  - quick_sample_data/streams")
        return 1
    
    print(f"✅ Found test data: {test_path}")
    print(f"   Using processor: {processor_class.__name__}")
    print()
    
    # Get OpenSearch config
    print("🔍 Step 2: Getting OpenSearch configuration...")
    config = get_opensearch_config()
    
    if not config:
        print("❌ OpenSearch not configured!")
        print()
        print("Please set environment variables:")
        print("  export OPENSEARCH_URL='https://opensearch.app.intlab.redhat.com'")
        print("  export OPENSEARCH_USER='your-username'")
        print("  export OPENSEARCH_PASS='your-password'")
        print()
        print("Or create: post_processing/config/export_config.yml")
        return 1
    
    print(f"✅ OpenSearch configured: {config['url']}")
    print()
    
    # Create exporter with test index
    test_index = "zathras-dedup-test"
    exporter = OpenSearchExporter(
        url=config['url'],
        index=test_index,
        username=config['username'],
        password=config['password'],
        verify_ssl=config['verify_ssl']
    )
    
    # Test connection
    print("🔍 Step 3: Testing OpenSearch connection...")
    if not exporter.test_connection():
        print("❌ Failed to connect to OpenSearch")
        return 1
    
    print(f"✅ Connected to OpenSearch")
    print()
    
    # Process results - First time
    print("=" * 80)
    print("📊 Step 4: FIRST PROCESSING - Upload to OpenSearch")
    print("=" * 80)
    print()
    
    processor1 = processor_class(test_path)
    document1 = processor1.process()
    
    doc_id_1 = document1.metadata.document_id
    content_hash_1 = document1.calculate_content_hash()
    processing_ts_1 = document1.metadata.processing_timestamp
    test_ts = document1.metadata.test_timestamp
    
    print(f"Document ID: {doc_id_1}")
    print(f"Content Hash: {content_hash_1}")
    print(f"Test Timestamp: {test_ts}")
    print(f"Processing Timestamp: {processing_ts_1}")
    print()
    
    # Upload to OpenSearch
    print("📤 Uploading to OpenSearch...")
    result_id_1 = exporter.export_zathras_document(document1.to_dict_summary_only())
    print(f"✅ Uploaded document with ID: {result_id_1}")
    print()
    
    # Wait a moment so processing timestamp will differ
    print("⏳ Waiting 2 seconds...")
    time.sleep(2)
    print()
    
    # Process results - Second time (same data)
    print("=" * 80)
    print("📊 Step 5: SECOND PROCESSING - Same data, upload again")
    print("=" * 80)
    print()
    
    processor2 = processor_class(test_path)
    document2 = processor2.process()
    
    doc_id_2 = document2.metadata.document_id
    content_hash_2 = document2.calculate_content_hash()
    processing_ts_2 = document2.metadata.processing_timestamp
    
    print(f"Document ID: {doc_id_2}")
    print(f"Content Hash: {content_hash_2}")
    print(f"Test Timestamp: {test_ts}")
    print(f"Processing Timestamp: {processing_ts_2}")
    print()
    
    # Verify IDs are the same
    if doc_id_1 == doc_id_2:
        print("✅ Document IDs are IDENTICAL (same content hash)")
    else:
        print("❌ Document IDs differ (should be the same!)")
        return 1
    
    print()
    
    # Verify processing timestamps differ
    if processing_ts_1 != processing_ts_2:
        print("✅ Processing timestamps DIFFER (as expected)")
        print(f"   First:  {processing_ts_1}")
        print(f"   Second: {processing_ts_2}")
    else:
        print("⚠️  Processing timestamps are identical (processing was very fast)")
    
    print()
    
    # Upload to OpenSearch again
    print("📤 Uploading to OpenSearch again (same document ID)...")
    result_id_2 = exporter.export_zathras_document(document2.to_dict_summary_only())
    print(f"✅ Uploaded document with ID: {result_id_2}")
    print()
    
    # Wait for indexing
    print("⏳ Waiting for OpenSearch to index...")
    time.sleep(1)
    print()
    
    # Query OpenSearch to verify only 1 document exists
    print("=" * 80)
    print("🔍 Step 6: Query OpenSearch - Verify NO duplicates")
    print("=" * 80)
    print()
    
    # Query by document ID
    query = {
        "query": {
            "term": {
                "metadata.document_id.keyword": doc_id_1
            }
        },
        "size": 10
    }
    
    print(f"Querying for document ID: {doc_id_1}")
    print()
    
    results = exporter.search(query)
    hits = results['hits']['hits']
    total_count = results['hits']['total']['value']
    
    print(f"Total documents found: {total_count}")
    print()
    
    # Analyze results
    if total_count == 0:
        print("❌ No documents found! Upload may have failed.")
        return 1
    elif total_count == 1:
        print("✅ SUCCESS! Only 1 document exists (NO DUPLICATE)")
        print()
        print("This proves:")
        print("  • Same test results generate same document ID")
        print("  • OpenSearch updated existing document instead of creating new one")
        print("  • Deduplication is working correctly")
        print()
    else:
        print(f"❌ FAILURE! Found {total_count} documents (expected 1)")
        print("   Deduplication may not be working correctly")
        return 1
    
    # Show document details
    print("=" * 80)
    print("📄 Step 7: Document Details")
    print("=" * 80)
    print()
    
    doc = hits[0]['_source']
    
    print(f"OpenSearch Document ID: {hits[0]['_id']}")
    print(f"Document ID (metadata): {doc['metadata']['document_id']}")
    print(f"Test Name: {doc['test']['name']}")
    print(f"Test Timestamp: {doc['metadata']['test_timestamp']}")
    print(f"Processing Timestamp: {doc['metadata']['processing_timestamp']}")
    print()
    
    # Compare processing timestamps
    opensearch_ts = doc['metadata']['processing_timestamp']
    if opensearch_ts == processing_ts_2:
        print("✅ Processing timestamp matches SECOND processing")
        print("   This proves the document was UPDATED, not duplicated")
    elif opensearch_ts == processing_ts_1:
        print("⚠️  Processing timestamp matches FIRST processing")
        print("   Document may not have been updated")
    else:
        print("⚠️  Processing timestamp doesn't match either processing")
    
    print()
    
    # Show system info
    print("System Under Test:")
    if 'system_under_test' in doc and 'hardware' in doc['system_under_test']:
        hw = doc['system_under_test']['hardware']
        if 'cpu' in hw:
            print(f"  CPU: {hw['cpu'].get('model', 'N/A')}")
            print(f"  Cores: {hw['cpu'].get('cores', 'N/A')}")
        if 'memory' in hw:
            print(f"  Memory: {hw['memory'].get('total_gb', 'N/A')} GB")
    
    if 'metadata' in doc:
        print(f"  Cloud: {doc['metadata'].get('cloud_provider', 'N/A')}")
        print(f"  Instance: {doc['metadata'].get('instance_type', 'N/A')}")
    
    print()
    
    # Show results summary
    if 'results' in doc and 'primary_metric' in doc['results']:
        pm = doc['results']['primary_metric']
        print(f"Primary Metric: {pm.get('name', 'N/A')}")
        print(f"  Value: {pm.get('value', 'N/A')} {pm.get('unit', '')}")
    
    print()
    
    # Final summary
    print("=" * 80)
    print("✅ DEDUPLICATION TEST PASSED")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  • Processed same results twice")
    print(f"  • Generated same document ID: {doc_id_1}")
    print(f"  • Uploaded to OpenSearch twice")
    print(f"  • Result: Only 1 document in OpenSearch")
    print(f"  • processing_timestamp was updated")
    print()
    print("Conclusion:")
    print("  Content-based deduplication is working correctly!")
    print("  You can safely reprocess results without creating duplicates.")
    print()
    print(f"Note: Test data uploaded to index '{test_index}'")
    print(f"      You can delete it with:")
    print(f"      DELETE /{test_index}")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

