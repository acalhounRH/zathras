# Zathras Results Data Analysis

## Executive Summary

After analyzing actual Zathras test results, I've identified **3 main data categories** that need JSON conversion:

1. **Test Results Data** (Time Series + Statistical Summaries)
2. **System Under Test (SUT) Metadata** (Hardware, OS, Configuration)
3. **Test Execution Metadata** (Runtime info, versions, settings)

---

## Directory Structure

```
quick_sample_data/
└── {os_vendor}/           # e.g., rhel
    └── {system_type}/     # e.g., local, aws, azure
        └── {system_name}_{iteration}/  # e.g., localhost_0
            ├── results_{test}.zip        # Primary test results
            ├── hw_config.yml             # Hardware mapping
            ├── ansible_vars.yml          # Test configuration
            ├── ansible_run_vars.yml      # Runtime variables
            ├── test_info                 # All test definitions (JSON)
            ├── test_times                # Test execution times
            ├── test_system_usage         # Resource usage summary
            ├── sysconfig_info.tar        # Detailed SUT info
            ├── boot_info/                # Boot metrics
            ├── {test}.cmd                # Test invocation commands
            └── test_tools/               # Test wrapper code
```

---

## Data Categories

### 1. TEST RESULTS DATA

#### Location
- `results_{test}.zip` files contain `results_{test}_.tar`
- Tar unpacks to `{test}_{timestamp}/` directory

#### Structure (CoreMark Example)
```
coremark_2025.11.06-05.09.45/
├── test_results_report          # PASS/FAIL status
├── version                       # Test wrapper version
├── tuned_setting                 # System tuning applied
├── results_coremark.csv          # TIME SERIES DATA ⭐
├── run1_summary                  # STATISTICAL SUMMARY ⭐
├── run2_summary                  # STATISTICAL SUMMARY ⭐
├── run1_iter=1_threads=4.log     # Individual run logs
├── run1_iter=2_threads=4.log
├── run2_iter=1_threads=4.log
└── ...
```

#### Data Types

**A. Time Series Data** (`results_coremark.csv`)
```csv
iteration:threads:IterationsPerSec
1:4:193245.201809
1:4:195999.821818
2:4:190905.935439
2:4:191537.523942
...
```
- Multiple measurements over iterations
- Can be graphed over time
- Shows variance and trends
- **Needs:** Array of measurements with timestamps/iteration numbers

**B. Statistical Summary** (`run1_summary`)
```
CoreMark Size    : 666
Total time (secs): 22.449000
Iterations/Sec   : 195999.821818  ⭐ PRIMARY METRIC
Iterations       : 4400000
Compiler version : GCC15.2.1 20251022
Compiler flags   : -O2 -DMULTITHREAD=4 ...
Parallel PThreads : 4
```
- Aggregated statistics (mean, min, max, stddev)
- Configuration used for the run
- Primary performance metrics
- **Needs:** Structured key-value pairs

**C. Individual Run Logs** (`run1_iter=1_threads=4.log`)
- Raw test output
- Detailed per-iteration data
- Validation checksums
- **Needs:** Optional, can be linked or summarized

---

### 2. SYSTEM UNDER TEST (SUT) METADATA

#### A. Hardware Configuration

**`sysconfig_info.tar`** contains:
- **`lscpu.json`** ✅ Already JSON!
  ```json
  {
    "lscpu": [
      {"field": "Architecture:", "data": "aarch64"},
      {"field": "CPU(s):", "data": "4"},
      {"field": "Vendor ID:", "data": "Apple"},
      {"field": "NUMA node(s):", "data": "1"}
    ]
  }
  ```

- **`lshw.json`** ✅ Already JSON!
  - Full hardware inventory
  - Detailed component info

- **`lsmem.json`** ✅ Already JSON!
  - Memory layout and configuration

- **`proc_cpuinfo.out`** - CPU details (text)
- **`proc_meminfo.out`** - Memory details (text)
- **`dmidecode.out`** - BIOS/system info (text)
- **`lspci.out`** - PCI devices (text)
- **`numactl.out`** - NUMA topology (text)

**Conversion Need:** Parse text files into structured JSON

#### B. Operating System Configuration

- **`etc_release.out`** - OS name and version
  ```
  Fedora release 42 (Adams)
  NAME="Fedora Linux"
  VERSION="42 (Container Image)"
  VERSION_ID=42
  KERNEL_VERSION=6.15.10-200.fc42.aarch64
  ```

- **`uname.out`** - Kernel info
- **`sysctl.out`** - Kernel parameters
- **`tuned.out`** - Performance tuning profile

**Conversion Need:** Parse key=value pairs and structured text

#### C. Simple Hardware Mapping

**`hw_config.yml`**
```yaml
storage: none
server_ips: none
client_ips: none
```
- High-level configuration
- Network and storage mapping
- Already YAML (easy to convert)

---

### 3. TEST EXECUTION METADATA

#### A. Test Configuration

**`ansible_vars.yml`** (Primary test config)
```yaml
config_info:
  system_type: local
  host_config: localhost
  run_label: quick_sample_data_rhel
  os_vendor: rhel
  test_to_run: [streams,coremark,pig]
  test_iterations: 1
  user_running: root
  selinux_state: disabled
  cloud_terminate_instance: 1
  java_version: none
  rhel_tuned_setting: none
  # 60+ configuration fields
```
- Already YAML (easy to convert)
- Contains critical test parameters

**`ansible_run_vars.yml`** (Runtime variables)
```yaml
ct_server: none
storage: none
ssh_i_option: "-i /root/.ssh/id_rsa"
test_hostname: localhost
kit_upload_directory: /
```

#### B. Test Definitions

**`test_info`** - JSON file containing all test definitions
```json
{
  "test2": {
    "test_name": "streams",
    "test_description": "...",
    "location": "https://github.com/redhat-performance/streams-wrapper/...",
    "repo_file": "v2.0.tar.gz",
    "test_specific": "--iterations 5",
    "archive_results": "yes"
  }
}
```
✅ Already JSON!

#### C. Test Execution Metrics

**`test_times`**
```
test: streams execution time 2
test: coremark execution time 204
test: pig execution time 519
```

**`test_system_usage`**
```
User  Run label              Instance   Date       Price  Test      Time  Cost
root  quick_sample_data_rhel localhost  2025.11.06 0      coremark  204   0
```

**`{test}.cmd`** - Exact command invoked
```bash
#!/bin/bash
//root/workloads/coremark-wrapper-2.0/coremark/coremark_run \
  --run_user root \
  --home_parent / \
  --iterations 5 \
  --tuned_setting tuned_none_sys_file_ \
  --host_config "localhost" \
  --sysname "localhost" \
  --sys_type local
```

#### D. Boot Information

**`boot_info/initial_boot_info.tar`** contains:
- `boot_info` - Boot timing data
- `bootup.svg` - Boot visualization
- `systemd.svg` - Service startup visualization
- `journal_ctl` - System logs

---

## Proposed JSON Schema Structure

### Top-Level Document Structure

**Architecture Decision:** Fully denormalized - one complete document per test execution with all SUT metadata embedded.

```json
{
  "metadata": {
    "document_id": "coremark_localhost_20251106_050945_abc123",
    "document_type": "zathras_test_result",
    "zathras_version": "1.0",
    "collection_timestamp": "2025-11-06T05:09:45Z"
  },
  "test": {
    "name": "coremark",
    "version": "v1.01",
    "wrapper_version": "v2.0",
    "description": "CoreMark benchmark",
    "url": "https://github.com/redhat-performance/coremark-wrapper"
  },
  "system_under_test": {
    // FULLY EMBEDDED - Complete hardware, OS, and config at time of test
    "hardware": {
      "cpu": { ... },
      "memory": { ... },
      "numa": { ... },
      "storage": [ ... ],
      "network": [ ... ]
    },
    "operating_system": { ... },
    "configuration": { ... }
  },
  "test_configuration": {
    // FULLY EMBEDDED - All test parameters and settings
    "parameters": { ... },
    "environment": { ... },
    "tuning": { ... }
  },
  "results": {
    "status": "PASS|FAIL",
    "execution_time_seconds": 204,
    "primary_metric": {
      "name": "iterations_per_second",
      "value": 191234.5,
      "unit": "iterations/sec"
    },
    "statistical_summary": {
      // Aggregated statistics ACROSS all runs
      "mean": 191234.5,
      "median": 190905.9,
      "min": 188073.0,
      "max": 195999.8,
      "stddev": 2543.2,
      "count": 10
    },
    "runs": [
      // Each run is one complete benchmark execution
      {
        "run_number": 1,
        "start_time": "2025-11-06T05:09:45Z",
        "duration_seconds": 22.449,
        "configuration": { /* run-specific config */ },
        "summary_metrics": { /* aggregated metrics for this run */ },
        "time_series": [
          // Iterations WITHIN this run
          {
            "sequence": 0,
            "iteration": 1,
            "timestamp": "2025-11-06T05:09:45Z",
            "value": 193245.201809,
            "unit": "iterations/sec"
          }
        ],
        "validation": { /* checksums, status */ }
      }
    ]
  },
  "runtime_info": {
    "start_time": "2025-11-06T05:09:45Z",
    "end_time": "2025-11-06T05:12:49Z",
    "duration_seconds": 204,
    "command": "coremark_run --iterations 5 --threads 4",
    "working_directory": "/root/workloads/coremark-wrapper-2.0",
    "user": "root"
  }
}
```

---

## Detailed Schema Sections

### System Under Test (SUT) Schema

```json
{
  "system_under_test": {
    "hardware": {
      "cpu": {
        "architecture": "aarch64",
        "vendor": "Apple",
        "model": "Apple M-series",
        "cores": 4,
        "threads_per_core": 1,
        "sockets": 1,
        "numa_nodes": 1,
        "flags": ["fp", "asimd", "evtstrm", "..."],
        "cache_l1d": "...",
        "cache_l1i": "...",
        "cache_l2": "...",
        "cache_l3": "...",
        "frequency_mhz": 0,
        "bogomips": 48.00
      },
      "memory": {
        "total_kb": 16328328,
        "available_kb": 15526204,
        "swap_kb": 0
      },
      "numa": {
        "nodes": [
          {
            "node_id": 0,
            "cpus": "0-3",
            "memory_mb": 15953
          }
        ]
      },
      "storage": [],
      "network": []
    },
    "operating_system": {
      "distribution": "fedora",
      "version": "42",
      "codename": "Adams",
      "kernel": {
        "version": "6.15.10-200.fc42.aarch64",
        "build_date": "Fri Aug 15 16:32:40 UTC 2025"
      },
      "hostname": "00639c5d898e",
      "selinux_status": "disabled"
    },
    "configuration": {
      "tuned_profile": "none",
      "sysctl_parameters": { ... },
      "kernel_parameters": "...",
      "cgroups": { ... }
    }
  }
}
```

### Test Results Schema (CoreMark Example)

**Note:** Using **fully denormalized** documents - all SUT metadata and test config embedded in each result document. No joins required.

```json
{
  "results": {
    "status": "PASS",
    "execution_time_seconds": 204,
    "primary_metric": {
      "name": "iterations_per_second",
      "value": 191234.567,
      "unit": "iterations/sec"
    },
    "statistical_summary": {
      // Aggregated statistics ACROSS all runs
      "metric": "iterations_per_second",
      "mean": 191234.567,
      "median": 190905.935,
      "min": 188073.035,
      "max": 195999.822,
      "stddev": 2543.21,
      "variance": 6467915.4,
      "count": 10,
      "percentile_95": 195000.0,
      "percentile_99": 195999.0
    },
    "runs": [
      {
        "run_number": 1,
        "start_time": "2025-11-06T05:09:45Z",
        "end_time": "2025-11-06T05:10:07Z",
        "duration_seconds": 22.449,
        "configuration": {
          "threads": 4,
          "iterations": 4400000,
          "compiler": "GCC15.2.1 20251022 (Red Hat 15.2.1-3)",
          "compiler_flags": "-O2 -DMULTITHREAD=4 -DUSE_PTHREAD -pthread -DPERFORMANCE_RUN=1 -lrt"
        },
        "summary_metrics": {
          "coremark_size": 666,
          "total_ticks": 18798,
          "total_time_seconds": 22.449,
          "iterations_per_second": 195999.821818,
          "iterations": 4400000
        },
        "time_series": [
          // Time series data WITHIN this run
          {
            "sequence": 0,
            "iteration": 1,
            "timestamp": "2025-11-06T05:09:45Z",
            "value": 193245.201809,
            "unit": "iterations/sec"
          },
          {
            "sequence": 1,
            "iteration": 2,
            "timestamp": "2025-11-06T05:09:50Z",
            "value": 195999.821818,
            "unit": "iterations/sec"
          }
        ],
        "validation": {
          "status": "PASS",
          "seedcrc": "0xe9f5",
          "crclist": ["0xe714", "0xe714", "0xe714", "0xe714"],
          "crcmatrix": ["0x1fd7", "0x1fd7", "0x1fd7", "0x1fd7"],
          "crcstate": ["0x8e3a", "0x8e3a", "0x8e3a", "0x8e3a"],
          "crcfinal": ["0x33ff", "0x33ff", "0x33ff", "0x33ff"]
        }
      },
      {
        "run_number": 2,
        "start_time": "2025-11-06T05:10:10Z",
        "end_time": "2025-11-06T05:10:32Z",
        "duration_seconds": 22.1,
        "configuration": {
          "threads": 4,
          "compiler": "GCC15.2.1 20251022 (Red Hat 15.2.1-3)",
          "compiler_flags": "-O2 -DMULTITHREAD=4"
        },
        "summary_metrics": {
          "iterations_per_second": 190905.935439
        },
        "time_series": [
          // Time series data for RUN 2
          {
            "sequence": 0,
            "iteration": 1,
            "timestamp": "2025-11-06T05:10:10Z",
            "value": 190905.935439,
            "unit": "iterations/sec"
          },
          {
            "sequence": 1,
            "iteration": 2,
            "timestamp": "2025-11-06T05:10:15Z",
            "value": 191537.523942,
            "unit": "iterations/sec"
          }
        ]
      }
    ]
  }
}
```

---

## Data Processing Requirements

### By File Type

| File Type | Current Format | Processing Needed | Priority |
|-----------|---------------|-------------------|----------|
| `results_{test}.zip` | ZIP → TAR → mixed | Full extraction pipeline | **HIGH** |
| `*.csv` | CSV | Parse to JSON array | **HIGH** |
| `*_summary` | Text (key:value) | Regex parsing | **HIGH** |
| `*.log` | Text (unstructured) | Optional/reference | LOW |
| `test_results_report` | Text (PASS/FAIL) | Simple read | **HIGH** |
| `lscpu.json` | JSON | Use as-is | MEDIUM |
| `lshw.json` | JSON | Use as-is | MEDIUM |
| `lsmem.json` | JSON | Use as-is | MEDIUM |
| `*.out` (proc_*) | Text (key:value) | Parse to JSON | MEDIUM |
| `dmidecode.out` | Text (structured) | Parse sections | MEDIUM |
| `ansible_vars.yml` | YAML | YAML→JSON | **HIGH** |
| `test_info` | JSON | Use as-is | **HIGH** |
| `test_times` | Text (structured) | Parse lines | MEDIUM |
| `*.cmd` | Bash script | Extract args | MEDIUM |
| `sysconfig_info.tar` | TAR | Extract all | **HIGH** |

### Processing Pipeline

```
1. EXTRACT
   ├── Unzip results_{test}.zip
   ├── Untar results_{test}_.tar
   ├── Untar sysconfig_info.tar
   └── Untar boot_info/initial_boot_info.tar

2. PARSE TEST RESULTS
   ├── Read test_results_report (status)
   ├── Parse results_{test}.csv (time series)
   ├── Parse run*_summary files (statistics)
   ├── Extract version, tuned_setting
   └── Optionally parse individual logs

3. PARSE SUT METADATA
   ├── Load lscpu.json, lshw.json, lsmem.json (already JSON)
   ├── Parse proc_cpuinfo.out
   ├── Parse proc_meminfo.out
   ├── Parse etc_release.out
   ├── Parse uname.out
   ├── Parse numactl.out
   └── Parse dmidecode.out

4. PARSE TEST CONFIGURATION
   ├── Load ansible_vars.yml (YAML→JSON)
   ├── Load ansible_run_vars.yml (YAML→JSON)
   ├── Load test_info (already JSON)
   ├── Parse test_times
   ├── Parse {test}.cmd
   └── Parse test_system_usage

5. ENRICH & MERGE
   ├── Calculate statistical summaries
   ├── Add timestamps
   ├── Generate unique IDs
   ├── Cross-reference data
   └── Validate completeness

6. EXPORT
   ├── Generate final JSON document
   ├── Validate against schema
   └── Export to OpenSearch/Horreum
```

---

## Test-Specific Considerations

### CoreMark
- **Primary Metric:** Iterations/Second
- **Time Series:** Yes (CSV file)
- **Statistical Summary:** Multiple runs with detailed config
- **Special:** Validation checksums must be included

### STREAM (Expected - not generated in sample)
- **Primary Metric:** Memory bandwidth (MB/s)
- **Typical Output:** Copy, Scale, Add, Triad operations
- **Time Series:** Per-iteration measurements
- **Special:** Multiple memory operations tested

### Pig (Limited data in sample)
- **Note:** Sample only has version/tuned_setting
- **Expected:** Memory latency metrics
- **Need:** Real pig sample to define schema

### FIO (Not in sample, but important)
- **Primary Metric:** IOPS, Bandwidth, Latency
- **Time Series:** Per-second statistics
- **Special:** Multiple I/O patterns (read/write/random/sequential)
- **Format:** Often JSON output from FIO itself

---

## Challenges & Solutions

### Challenge 1: Test-Specific Formats
**Problem:** Each test wrapper produces different output formats
**Solution:** 
- Create base processor class with common extraction
- Test-specific processors extend base class
- Processors implement: `parse_time_series()`, `parse_summary()`, `extract_metrics()`

### Challenge 2: Time Series vs Summary Data
**Problem:** Some tests produce time series, others only summaries
**Solution:**
- Make time_series optional in schema
- Always include statistical_summary (even if calculated from single value)
- Flag in metadata indicates data type

### Challenge 3: Mixed Format in System Files
**Problem:** SUT data is in JSON, YAML, text, and structured text
**Solution:**
- Create utility parsers for common formats (proc files, dmidecode, etc.)
- Cache parsed results
- Reuse parsers across all tests

### Challenge 4: Incomplete Results
**Problem:** Some tests may fail partway through
**Solution:**
- Mark status as FAILED/INCOMPLETE
- Include whatever partial data exists
- Add error messages to metadata

### Challenge 5: Large Log Files
**Problem:** Individual iteration logs can be large
**Solution:**
- Don't include full logs in JSON
- Store only summary/metrics
- Optionally link to log file location

---

## Recommendations

### Phase 1: Core Implementation
1. ✅ Directory structure created
2. ✅ Exporters created (OpenSearch, Horreum)
3. **TODO:** Utility modules
   - `archive_handler.py` - Extract ZIP/TAR files
   - `metadata_extractor.py` - Parse SUT metadata
   - `parser_utils.py` - Common parsing functions (CSV, key-value, etc.)
4. **TODO:** Base processor class
   - Common extraction logic
   - Schema validation
   - Error handling
5. **TODO:** Test-specific processors
   - Start with CoreMark (complete data)
   - Then FIO (if sample available)
   - Then others

### Phase 2: Schema Refinement
1. Define OpenSearch index mappings
2. Define Horreum schemas
3. Add field metadata (units, descriptions)
4. Add validation rules

### Phase 3: Enhancement
1. Add statistical calculations (if not present)
2. Add data quality checks
3. Add data aggregation options
4. Add filtering/sampling for large datasets

---

## Next Steps

1. **Create utility modules** for common operations
2. **Implement CoreMark processor** (we have complete data)
3. **Test end-to-end** with sample data
4. **Iterate on schema** based on results
5. **Add more test processors** progressively

Would you like me to start implementing the processors now?

