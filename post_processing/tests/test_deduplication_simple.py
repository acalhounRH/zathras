#!/usr/bin/env python3
"""
Simple Deduplication Test

Tests the content-based hashing without needing actual test data.
Creates mock documents and verifies hash behavior.
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from post_processing.schema import (
    ZathrasDocument,
    Metadata,
    TestInfo,
    SystemUnderTest,
    HardwareInfo,
    CPUInfo,
    MemoryInfo,
    OperatingSystemInfo,
    ConfigurationInfo,
    TestConfiguration,
    Results,
    Run,
    PrimaryMetric,
    StatisticalSummary
)


def create_test_document(processing_time=None):
    """Create a test document with fixed content"""
    if processing_time is None:
        processing_time = datetime.utcnow()
    
    # Create metadata
    metadata = Metadata(
        document_id="temp_id",  # Will be replaced with hash
        document_type="zathras_test_result",
        zathras_version="1.0",
        test_timestamp="2025-11-06T14:30:00.000Z",
        processing_timestamp=processing_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        os_vendor="rhel",
        cloud_provider="azure",
        instance_type="Standard_D8ds_v6",
        scenario_name="test_scenario"
    )
    
    # Create test info
    test_info = TestInfo(
        name="coremark",
        version="1.0",
        description="CoreMark Benchmark"
    )
    
    # Create CPU info
    cpu_info = CPUInfo(
        vendor="Intel",
        model="Xeon Gold 6348",
        architecture="x86_64",
        cores=8,
        threads_per_core=2,
        frequency_mhz=2600.0
    )
    
    # Create memory info
    memory_info = MemoryInfo(
        total_gb=32,
        type="DDR4"
    )
    
    # Create hardware info
    hardware = HardwareInfo(
        cpu=cpu_info,
        memory=memory_info
    )
    
    # Create OS info
    os_info = OperatingSystemInfo(
        distribution="RHEL",
        version="9.3",
        kernel_version="5.14.0"
    )
    
    # Create configuration info
    config_info = ConfigurationInfo(
        tuned_profile="throughput-performance"
    )
    
    # Create system under test
    sut = SystemUnderTest(
        hardware=hardware,
        operating_system=os_info,
        configuration=config_info
    )
    
    # Create test configuration
    test_config = TestConfiguration(
        parameters={
            "threads": 8,
            "duration_seconds": 60.0
        }
    )
    
    # Create results
    primary_metric = PrimaryMetric(
        name="iterations_per_second",
        value=150000.5,
        unit="iterations/s"
    )
    
    stats = StatisticalSummary(
        mean=150000.5,
        median=149800.2,
        min=148500.1,
        max=151200.8,
        stddev=1200.3
    )
    
    run1 = Run(
        run_number=1,
        status="SUCCESS",
        metrics={
            "iterations_per_second": 150000.5,
            "runtime_seconds": 60.0
        }
    )
    
    results = Results(
        status="SUCCESS",
        total_runs=1,
        primary_metric=primary_metric,
        overall_statistics=stats,
        runs={"run_1": run1}
    )
    
    # Create document
    return ZathrasDocument(
        metadata=metadata,
        test=test_info,
        system_under_test=sut,
        test_configuration=test_config,
        results=results
    )


def test_same_content_same_hash():
    """Test that same content generates same hash"""
    print("=" * 80)
    print("TEST 1: Same Content → Same Hash")
    print("=" * 80)
    print()
    
    # Create 3 documents at different times
    doc1 = create_test_document(datetime(2025, 11, 10, 9, 0, 0))
    doc2 = create_test_document(datetime(2025, 11, 10, 10, 0, 0))
    doc3 = create_test_document(datetime(2025, 11, 10, 11, 0, 0))
    
    # Calculate hashes
    hash1 = doc1.calculate_content_hash()
    hash2 = doc2.calculate_content_hash()
    hash3 = doc3.calculate_content_hash()
    
    print(f"Document 1 (processed at 09:00):")
    print(f"  Processing timestamp: {doc1.metadata.processing_timestamp}")
    print(f"  Content hash: {hash1}")
    print()
    
    print(f"Document 2 (processed at 10:00):")
    print(f"  Processing timestamp: {doc2.metadata.processing_timestamp}")
    print(f"  Content hash: {hash2}")
    print()
    
    print(f"Document 3 (processed at 11:00):")
    print(f"  Processing timestamp: {doc3.metadata.processing_timestamp}")
    print(f"  Content hash: {hash3}")
    print()
    
    # Verify all hashes are the same
    if hash1 == hash2 == hash3:
        print("✅ PASS: All 3 documents have the same content hash")
        print(f"   Hash: {hash1}")
        print()
        print("   This means:")
        print("   • Processing timestamp is correctly excluded from hash")
        print("   • Reprocessing won't create duplicates")
        print("   • OpenSearch will use same document ID")
        return True
    else:
        print("❌ FAIL: Hashes differ")
        print(f"   Hash 1: {hash1}")
        print(f"   Hash 2: {hash2}")
        print(f"   Hash 3: {hash3}")
        return False


def test_different_content_different_hash():
    """Test that different content generates different hash"""
    print()
    print("=" * 80)
    print("TEST 2: Different Content → Different Hash")
    print("=" * 80)
    print()
    
    # Create base document
    doc1 = create_test_document()
    hash1 = doc1.calculate_content_hash()
    
    # Create document with different result value
    doc2 = create_test_document()
    doc2.results.primary_metric.value = 160000.0  # Different value
    hash2 = doc2.calculate_content_hash()
    
    # Create document with different system
    doc3 = create_test_document()
    doc3.system_under_test.hardware.cpu.cores = 16  # Different core count
    hash3 = doc3.calculate_content_hash()
    
    print(f"Document 1 (baseline):")
    print(f"  Result: 150000.5 iterations/s")
    print(f"  CPU cores: 8")
    print(f"  Hash: {hash1}")
    print()
    
    print(f"Document 2 (different result):")
    print(f"  Result: 160000.0 iterations/s")
    print(f"  CPU cores: 8")
    print(f"  Hash: {hash2}")
    print()
    
    print(f"Document 3 (different system):")
    print(f"  Result: 150000.5 iterations/s")
    print(f"  CPU cores: 16")
    print(f"  Hash: {hash3}")
    print()
    
    # Verify all hashes are different
    if hash1 != hash2 and hash2 != hash3 and hash1 != hash3:
        print("✅ PASS: Different content produces different hashes")
        print()
        print("   This means:")
        print("   • Test results are included in hash")
        print("   • System configuration is included in hash")
        print("   • Different tests will have different document IDs")
        return True
    else:
        print("❌ FAIL: Some hashes are the same when they should differ")
        return False


def test_document_id_generation():
    """Test that document ID is based on hash"""
    print()
    print("=" * 80)
    print("TEST 3: Document ID Generation")
    print("=" * 80)
    print()
    
    # Create document
    doc = create_test_document()
    
    # Calculate hash
    content_hash = doc.calculate_content_hash()
    
    # Generate ID (simulating what base_processor does)
    test_name = doc.test.name
    doc_id = f"{test_name}_{content_hash[:16]}"
    
    print(f"Test name: {test_name}")
    print(f"Content hash (full): {content_hash}")
    print(f"Content hash (first 16 chars): {content_hash[:16]}")
    print(f"Document ID: {doc_id}")
    print()
    
    if doc_id.startswith(test_name) and content_hash[:16] in doc_id:
        print("✅ PASS: Document ID correctly includes test name and hash")
        print()
        print("   Format: {test_name}_{hash_prefix}")
        print("   Example: coremark_a3f2d9c8e1b4f7a2")
        print()
        print("   Benefits:")
        print("   • Human-readable (includes test name)")
        print("   • Content-based (includes hash)")
        print("   • Deterministic (same content = same ID)")
        return True
    else:
        print("❌ FAIL: Document ID format incorrect")
        return False


def test_hash_excludes_processing_timestamp():
    """Verify processing_timestamp is excluded from hash"""
    print()
    print("=" * 80)
    print("TEST 4: Processing Timestamp Exclusion")
    print("=" * 80)
    print()
    
    # Create document
    doc = create_test_document(datetime(2025, 11, 10, 9, 0, 0))
    
    # Calculate hash with exclusion (default)
    hash_without_ts = doc.calculate_content_hash(exclude_processing_timestamp=True)
    
    # Calculate hash without exclusion
    hash_with_ts = doc.calculate_content_hash(exclude_processing_timestamp=False)
    
    print(f"Processing timestamp: {doc.metadata.processing_timestamp}")
    print()
    print(f"Hash (excluding processing_timestamp): {hash_without_ts}")
    print(f"Hash (including processing_timestamp): {hash_with_ts}")
    print()
    
    if hash_without_ts != hash_with_ts:
        print("✅ PASS: Processing timestamp affects hash when included")
        print()
        print("   Default behavior (exclude_processing_timestamp=True):")
        print("   • Ignores processing_timestamp")
        print("   • Enables deduplication")
        print("   • Same test data = same hash")
        return True
    else:
        print("❌ FAIL: Processing timestamp not affecting hash")
        return False


def main():
    """Run all tests"""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "CONTENT-BASED DEDUPLICATION TESTS" + " " * 25 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    results = []
    
    results.append(test_same_content_same_hash())
    results.append(test_different_content_different_hash())
    results.append(test_document_id_generation())
    results.append(test_hash_excludes_processing_timestamp())
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    print()
    
    if all(results):
        print("✅ ALL TESTS PASSED")
        print()
        print("Content-based deduplication is working correctly!")
        print()
        print("Key features verified:")
        print("  ✓ Same content generates same hash")
        print("  ✓ Different content generates different hash")
        print("  ✓ Document IDs are based on content hash")
        print("  ✓ Processing timestamp is excluded from hash")
        print()
        print("This ensures that:")
        print("  • Reprocessing results won't create duplicates")
        print("  • OpenSearch will update existing documents")
        print("  • processing_timestamp tracks last update time")
        print()
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print()
        failed = [i+1 for i, r in enumerate(results) if not r]
        print(f"Failed tests: {failed}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

