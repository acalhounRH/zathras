#!/usr/bin/env python3
"""
Test CoreMark Processor

Validates Phase 1 + Phase 2 implementation by processing real sample data
and generating JSON output.

Usage:
    python test_coremark_processor.py
"""

import json
import sys
from pathlib import Path

# Add post_processing to path
sys.path.insert(0, str(Path(__file__).parent))

from post_processing.processors.coremark_processor import CoreMarkProcessor


def test_coremark_processor():
    """Test CoreMark processor with sample data"""
    
    print("=" * 60)
    print("Testing CoreMark Processor")
    print("=" * 60)
    
    # Path to sample data
    sample_dir = Path(__file__).parent / "quick_sample_data" / "rhel" / "local" / "localhost_0"
    
    if not sample_dir.exists():
        print(f"❌ Sample directory not found: {sample_dir}")
        return False
    
    print(f"\n📂 Sample directory: {sample_dir}")
    
    # Check for required files
    required_files = [
        "results_coremark.zip",
        "sysconfig_info.tar",
        "ansible_vars.yml"
    ]
    
    for file in required_files:
        file_path = sample_dir / file
        if file_path.exists():
            print(f"✅ Found: {file}")
        else:
            print(f"❌ Missing: {file}")
            return False
    
    print("\n" + "=" * 60)
    print("Processing CoreMark Results...")
    print("=" * 60)
    
    try:
        # Create processor
        processor = CoreMarkProcessor(str(sample_dir))
        
        # Process results
        document = processor.process()
        
        # Convert to dict
        doc_dict = document.to_dict()
        
        print("\n✅ Processing complete!")
        
        # Validate structure
        print("\n" + "=" * 60)
        print("Validating Document Structure")
        print("=" * 60)
        
        errors = []
        
        # Check top-level sections
        required_sections = ['metadata', 'test', 'system_under_test', 'test_configuration', 'results']
        for section in required_sections:
            if section in doc_dict:
                print(f"✅ Section '{section}' present")
            else:
                errors.append(f"Missing section: {section}")
                print(f"❌ Section '{section}' missing")
        
        # Check results structure
        if 'results' in doc_dict:
            results = doc_dict['results']
            
            # Check runs object (not array!)
            if 'runs' in results:
                runs = results['runs']
                if isinstance(runs, dict):
                    print(f"✅ runs is an object (not array)")
                    
                    # Check for run_1, run_2
                    if 'run_1' in runs:
                        print(f"✅ run_1 present")
                    else:
                        errors.append("run_1 not found")
                    
                    if 'run_2' in runs:
                        print(f"✅ run_2 present")
                    else:
                        print(f"⚠️  run_2 not found (may only have 1 run)")
                    
                    # Check timeseries structure in run_1
                    if 'run_1' in runs and 'timeseries' in runs['run_1']:
                        timeseries = runs['run_1']['timeseries']
                        if isinstance(timeseries, dict):
                            print(f"✅ timeseries is an object (timestamp keys)")
                            
                            # Check timestamp keys
                            for ts_key in list(timeseries.keys())[:3]:
                                if 'Z' in ts_key and 'T' in ts_key:
                                    print(f"✅ Valid timestamp key: {ts_key}")
                                else:
                                    errors.append(f"Invalid timestamp key: {ts_key}")
                            
                            # Check for sequence numbers
                            first_point = list(timeseries.values())[0]
                            if 'sequence' in first_point:
                                print(f"✅ sequence field present")
                            else:
                                errors.append("sequence field missing")
                        else:
                            errors.append("timeseries is not an object")
                else:
                    errors.append("runs is not an object")
        
        # Check SUT metadata structure
        if 'system_under_test' in doc_dict:
            sut = doc_dict['system_under_test']
            
            if 'hardware' in sut:
                hw = sut['hardware']
                if 'cpu' in hw:
                    print(f"✅ CPU info present")
                if 'memory' in hw:
                    print(f"✅ Memory info present")
                if 'numa' in hw and isinstance(hw['numa'], dict):
                    print(f"✅ NUMA info present (object-based)")
                    if 'node_0' in hw['numa']:
                        print(f"✅ NUMA node_0 present")
        
        # Validate document
        print("\n" + "=" * 60)
        print("Running Built-in Validation")
        print("=" * 60)
        
        is_valid, validation_errors = document.validate()
        
        if is_valid:
            print("✅ Document validation passed")
        else:
            print(f"❌ Document validation failed:")
            for error in validation_errors:
                print(f"   - {error}")
                errors.append(error)
        
        # Write output
        print("\n" + "=" * 60)
        print("Writing Output")
        print("=" * 60)
        
        output_file = Path(__file__).parent / "output_coremark.json"
        
        with open(output_file, 'w') as f:
            json.dump(doc_dict, f, indent=2)
        
        print(f"✅ JSON written to: {output_file}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)
        
        print(f"\nDocument ID: {doc_dict['metadata']['document_id']}")
        print(f"Test: {doc_dict['test']['name']}")
        print(f"Status: {doc_dict['results']['status']}")
        print(f"Total Runs: {doc_dict['results'].get('total_runs', 0)}")
        
        if 'primary_metric' in doc_dict['results']:
            pm = doc_dict['results']['primary_metric']
            print(f"Primary Metric: {pm['name']} = {pm['value']:.2f} {pm['unit']}")
        
        if 'runs' in doc_dict['results']:
            runs = doc_dict['results']['runs']
            print(f"\nRuns:")
            for run_key in sorted(runs.keys()):
                run = runs[run_key]
                print(f"  - {run_key}: {run.get('status', 'UNKNOWN')}")
                if 'timeseries' in run:
                    ts_count = len(run['timeseries'])
                    print(f"    Time series points: {ts_count}")
        
        # Final verdict
        print("\n" + "=" * 60)
        
        if errors:
            print("❌ VALIDATION FAILED")
            print("\nErrors:")
            for error in errors:
                print(f"  - {error}")
            return False
        else:
            print("✅ ALL TESTS PASSED!")
            print("\nPhase 1 + Phase 2 implementation validated successfully!")
            return True
        
    except Exception as e:
        print(f"\n❌ Error during processing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_coremark_processor()
    sys.exit(0 if success else 1)

