# Zathras Post-Processing

Export Zathras benchmark results to OpenSearch or Horreum for centralized analysis, dashboards, and performance tracking.

---

## 🚀 How to Run

### **After a Zathras Benchmark**

You have a result directory with your benchmark data:
```
/path/to/results/localhost_0/
├── results_coremark.zip      # Your benchmark results
├── sysconfig_info.tar        # System information
├── ansible_vars.yml          # Test configuration
└── test_info                 # Test metadata
```

**Export to OpenSearch in 3 lines:**

```python
from post_processing.processors.coremark_processor import CoreMarkProcessor
from post_processing.exporters.opensearch_exporter import OpenSearchExporter

# 1. Process results
processor = CoreMarkProcessor("/path/to/results/localhost_0")
document = processor.process()

# 2. Configure exporter
exporter = OpenSearchExporter(
    url="https://opensearch.app.intlab.redhat.com/",
    index="zathras-results",
    username="example-user",
    password="your-password"
)

# 3. Export
doc_id = exporter.export_zathras_document(document)
print(f"✅ Exported! View at: {exporter.url}/{exporter.index}/_doc/{doc_id}")
```

**Using the test script:**
```bash
# Quick test with sample data
cd /path/to/zathras
python3 post_processing/tests/export_to_opensearch.py --yes

# Verify it's in OpenSearch
python3 post_processing/tests/verify_opensearch.py
```

---

## 🔄 CI/CD Integration with Burden

### **Automatic Export After Every Benchmark Run**

Add post-processing to your existing Zathras workflows:

#### **Option 1: Shell Script Wrapper**

```bash
#!/bin/bash
# run_and_export.sh - Wrap your existing burden commands

# Your existing Zathras run
./bin/burden \
    --scenario benchmarks/coremark.yml \
    --host-config my-systems \
    --run-label "nightly-$(date +%Y%m%d)"

# Get the result directory
RESULT_DIR=$(ls -td */rhel/*/localhost_* | head -1)

# Export results automatically
python3 << EOF
from post_processing.processors.coremark_processor import CoreMarkProcessor
from post_processing.exporters.opensearch_exporter import OpenSearchExporter
import os

processor = CoreMarkProcessor("$RESULT_DIR")
document = processor.process()

exporter = OpenSearchExporter(
    url=os.getenv("OPENSEARCH_URL", "https://opensearch.app.intlab.redhat.com/"),
    index="zathras-results",
    username=os.getenv("OPENSEARCH_USER", "example-user"),
    password=os.getenv("OPENSEARCH_PASSWORD")
)

doc_id = exporter.export_zathras_document(document)
print(f"✅ Exported to OpenSearch: {doc_id}")
EOF
```

**Usage:**
```bash
# Set credentials once
export OPENSEARCH_PASSWORD="your-password"

# Run your tests as normal
./run_and_export.sh
```

#### **Option 2: Post-Process Existing Results**

Already have results? Process them all at once:

```bash
#!/bin/bash
# bulk_export.sh - Export all existing results

RESULTS_BASE="my_results_20251106/rhel/local"

for result_dir in $RESULTS_BASE/localhost_*; do
    echo "Processing: $result_dir"
    
    python3 << EOF
from post_processing.processors.coremark_processor import CoreMarkProcessor
from post_processing.exporters.opensearch_exporter import OpenSearchExporter

try:
    processor = CoreMarkProcessor("$result_dir")
    document = processor.process()
    
    exporter = OpenSearchExporter(
        url="https://opensearch.app.intlab.redhat.com/",
        index="zathras-results",
        username="example-user",
        password="$OPENSEARCH_PASSWORD"
    )
    
    doc_id = exporter.export_zathras_document(document)
    print(f"✅ $result_dir: {doc_id}")
except Exception as e:
    print(f"❌ $result_dir: {e}")
EOF
done
```

#### **Option 3: Jenkins/GitLab CI Pipeline**

```yaml
# .gitlab-ci.yml
stages:
  - test
  - export

run_benchmarks:
  stage: test
  script:
    - ./bin/burden --scenario benchmarks/coremark.yml --result-dir results/
  artifacts:
    paths:
      - results/
    expire_in: 30 days

export_results:
  stage: export
  dependencies:
    - run_benchmarks
  script:
    - |
      for result_dir in results/*/rhel/*/localhost_*; do
        python3 << EOF
      from post_processing.processors.coremark_processor import CoreMarkProcessor
      from post_processing.exporters.opensearch_exporter import OpenSearchExporter
      import os
      
      processor = CoreMarkProcessor("$result_dir")
      document = processor.process()
      
      exporter = OpenSearchExporter(
          url=os.getenv("OPENSEARCH_URL"),
          index="zathras-ci-${CI_PROJECT_NAME}",
          username=os.getenv("OPENSEARCH_USER"),
          password=os.getenv("OPENSEARCH_PASSWORD")
      )
      
      exporter.export_zathras_document(document)
      EOF
      done
  only:
    - main
    - schedules
```

#### **Option 4: Cron Job for Nightly Runs**

```bash
# /etc/cron.d/zathras-nightly
# Run nightly benchmarks and export results

0 2 * * * zathras /path/to/nightly_benchmark.sh >> /var/log/zathras-nightly.log 2>&1
```

```bash
#!/bin/bash
# nightly_benchmark.sh

export OPENSEARCH_PASSWORD="your-password"

# Run benchmark
./bin/burden \
    --scenario benchmarks/nightly.yml \
    --run-label "nightly-$(date +%Y%m%d)"

# Export results
RESULT_DIR=$(ls -td */rhel/*/localhost_* | head -1)

python3 -c "
from post_processing.processors.coremark_processor import CoreMarkProcessor
from post_processing.exporters.opensearch_exporter import OpenSearchExporter
import os

processor = CoreMarkProcessor('$RESULT_DIR')
document = processor.process()

exporter = OpenSearchExporter(
    url='https://opensearch.app.intlab.redhat.com/',
    index='zathras-nightly',
    username='example-user',
    password=os.getenv('OPENSEARCH_PASSWORD')
)

doc_id = exporter.export_zathras_document(document)
print(f'✅ Nightly export complete: {doc_id}')
"

# Optional: Send notification
curl -X POST "$SLACK_WEBHOOK" \
    -d '{"text": "Nightly benchmarks complete and exported to OpenSearch"}'
```

---

## 📊 View Your Results

### **OpenSearch Dashboards**

Access your exported data:
- **Discover:** https://opensearch.app.intlab.redhat.com/_dashboards/app/discover
- **Dev Tools:** https://opensearch.app.intlab.redhat.com/_dashboards/app/dev_tools

### **Quick Queries**

```json
# Get latest results
GET /zathras-results/_search
{
  "size": 10,
  "sort": [{ "metadata.collection_timestamp": "desc" }]
}

# Find CoreMark results
GET /zathras-results/_search
{
  "query": { "term": { "test.name": "coremark" }}
}

# Performance over time
GET /zathras-results/_search
{
  "query": { "term": { "test.name": "coremark" }},
  "sort": [{ "metadata.collection_timestamp": "asc" }],
  "_source": ["metadata.collection_timestamp", "results.primary_metric"]
}

# Compare by CPU architecture
GET /zathras-results/_search
{
  "size": 0,
  "aggs": {
    "by_arch": {
      "terms": { "field": "system_under_test.hardware.cpu.architecture" },
      "aggs": {
        "avg_performance": { "avg": { "field": "results.primary_metric.value" }}
      }
    }
  }
}
```

---

## 🔧 Installation & Setup

### **Prerequisites**
- Python 3.8+
- Zathras benchmark results
- OpenSearch or Horreum access (optional for local testing)

### **Install Dependencies**

```bash
cd /path/to/zathras
pip3 install -r post_processing/requirements.txt
```

**Dependencies:**
- `pyyaml` - Configuration and result parsing
- `python-dateutil` - Timestamp handling
- `requests` - HTTP for Horreum

### **Configuration**

#### **Environment Variables (Recommended)**

```bash
# Add to ~/.bashrc or CI environment
export OPENSEARCH_URL="https://opensearch.app.intlab.redhat.com/"
export OPENSEARCH_USER="example-user"
export OPENSEARCH_PASSWORD="your-password"
export OPENSEARCH_INDEX="zathras-results"
```

#### **Configuration File**

```bash
# Copy example
cp post_processing/config/export_config.example.yml post_processing/config/export_config.yml

# Edit with your settings
vim post_processing/config/export_config.yml
```

Example config:
```yaml
opensearch:
  enabled: true
  url: "https://opensearch.app.intlab.redhat.com/"
  index: "zathras-results"
  username: "example-user"
  password: "${OPENSEARCH_PASSWORD}"  # Use env var
  verify_ssl: true
```

---

## 📖 Detailed Usage

### **Supported Benchmarks**

| Benchmark | Status | Processor |
|-----------|--------|-----------|
| CoreMark | ✅ Ready | `coremark_processor.py` |
| STREAMS | 🚧 Coming | Phase 4 |
| FIO | 🚧 Coming | Phase 4 |
| Pig | 🚧 Coming | Phase 4 |

### **Process Results Programmatically**

```python
from post_processing.processors.coremark_processor import CoreMarkProcessor

# Process results
processor = CoreMarkProcessor("/path/to/result/directory/")
document = processor.process()

# Inspect the document
print(f"Test: {document.test.name} v{document.test.version}")
print(f"Status: {document.results.status}")
print(f"Runs: {len(document.results.runs)}")

# Access run data
for run_key, run in document.results.runs.items():
    print(f"{run_key}: {run.status}")
    if run.timeseries:
        print(f"  Time series points: {len(run.timeseries)}")

# Convert to JSON
import json
doc_dict = document.to_dict()
json_str = json.dumps(doc_dict, indent=2, default=str)
print(f"Document size: {len(json_str)} bytes")

# Save to file
with open('result.json', 'w') as f:
    f.write(json_str)
```

### **What Gets Extracted**

The processor extracts comprehensive data from your results:

**From `results_coremark.zip`:**
- Per-run metrics (iterations/sec, total time, etc.)
- Time series data (performance over time)
- Compiler information
- Validation checksums

**From `sysconfig_info.tar`:**
- CPU: vendor, model, cores, threads, cache, flags
- Memory: capacity, speed, NUMA topology
- Storage: devices, capacity, type
- Network: interfaces, speed, addresses
- OS: distribution, version, kernel

**From `ansible_vars.yml`:**
- Test parameters and iterations
- System configuration (tuned profile, sysctl)
- Zathras scenario information

---

## 🚢 Export to Different Targets

### **OpenSearch**

```python
from post_processing.exporters.opensearch_exporter import OpenSearchExporter

exporter = OpenSearchExporter(
    url="https://opensearch.app.intlab.redhat.com/",
    index="zathras-results",
    username="example-user",
    password="your-password",
    verify_ssl=True,
    timeout=30,
    max_retries=3
)

# Test connection
if exporter.test_connection():
    print("✅ Connected!")

# Ensure index exists
exporter.ensure_index_exists()

# Export document
doc_id = exporter.export_zathras_document(document)
print(f"Document ID: {doc_id}")
```

### **Horreum**

```python
from post_processing.exporters.horreum_exporter import HorreumExporter

exporter = HorreumExporter(
    url="https://horreum.example.com",
    test_name="zathras-coremark",
    auth_token="your-token",
    owner="your-team",
    access="PUBLIC"
)

# Export run
run_id = exporter.export_zathras_document(document)
print(f"Run ID: {run_id}")
```

---

## 📐 Schema & Data Structure

### **Object-Based Design**

The schema uses an **object-based structure** optimized for OpenSearch:

**✅ Runs as Objects** (not arrays):
```json
"results": {
  "runs": {
    "run_1": { "metrics": {...}, "timeseries": {...} },
    "run_2": { "metrics": {...}, "timeseries": {...} }
  }
}
```

**✅ Timestamp-Keyed Time Series**:
```json
"timeseries": {
  "2025-11-06T12:00:00.000Z": {
    "sequence": 0,
    "metrics": { "iterations_per_second": 193245.2 }
  },
  "2025-11-06T12:00:05.000Z": {
    "sequence": 1,
    "metrics": { "iterations_per_second": 195999.8 }
  }
}
```

**✅ CPU Flags as Boolean Object**:
```json
"cpu": {
  "flags": {
    "avx2": true,
    "avx512": true,
    "sse4_2": true
  }
}
```

**✅ Dynamic Keys for Hardware**:
```json
"numa": {
  "node_0": { "cpus": "0-23", "memory_gb": 64 },
  "node_1": { "cpus": "24-47", "memory_gb": 64 }
}
```

### **Why This Design?**

- **No nested arrays** → Better OpenSearch performance
- **Object-based** → Fast queries and aggregations
- **Timestamp keys** → Preserves order without sorting
- **Boolean flags** → Efficient filtering
- **Dynamic keys** → Flexible for varying hardware configs

---

## 🧪 Testing

### **Test With Sample Data**

```bash
# Run all tests
python3 post_processing/tests/test_coremark_processor.py
python3 post_processing/tests/test_exporters.py
python3 post_processing/tests/test_export_logic.py

# Test real OpenSearch connection
python3 post_processing/tests/test_real_opensearch.py

# Export sample data
python3 post_processing/tests/export_to_opensearch.py --yes

# Verify in OpenSearch
python3 post_processing/tests/verify_opensearch.py
```

Expected output:
```
✅ Index 'zathras-results' exists
✅ Total documents: 1
✅ Runs are objects: ['run_1', 'run_2']
✅ Timeseries are timestamp-keyed objects
✅ CPU flags are boolean object
✅ Document validation passed
```

---

## 🐛 Troubleshooting

### **Connection Issues**

```python
# Test OpenSearch connection
from post_processing.exporters.opensearch_exporter import OpenSearchExporter

exporter = OpenSearchExporter(
    url="https://opensearch.app.intlab.redhat.com/",
    index="test",
    username="example-user",
    password="your-password"
)

if exporter.test_connection():
    print("✅ Connected!")
else:
    print("❌ Connection failed")
    print("Check: VPN, credentials, firewall")
```

### **Permission Errors**

**Required roles in OpenSearch:**
- ✅ `own_index` - Create indices and write documents
- ✅ `readall_and_monitor` - Read data

**Not required:**
- ❌ Admin access (for index templates)

### **File Not Found Errors**

```bash
# Verify result directory structure
ls -la /path/to/results/

# Required files:
# - results_coremark.zip
# - sysconfig_info.tar
# - ansible_vars.yml
```

### **Import Errors**

```bash
# Ensure you're in the Zathras root directory
cd /path/to/zathras

# Test import
python3 -c "from post_processing.processors.coremark_processor import CoreMarkProcessor; print('✅ Import works')"
```

### **OpenSearch Aggregation Errors**

**Error:** "Text fields are not optimised for aggregations"

**Solution:** Dynamic mappings may map fields as `text`. Use `.keyword` suffix:

```json
{
  "aggs": {
    "by_status": {
      "terms": { "field": "results.status.keyword" }
    }
  }
}
```

Or have an admin apply the index template for optimized mappings.

---

## 🔍 Advanced Queries

### **Performance Regression Detection**

```json
GET /zathras-results/_search
{
  "query": {
    "bool": {
      "must": [
        { "term": { "test.name": "coremark" }},
        { "range": { "metadata.collection_timestamp": { "gte": "now-7d" }}}
      ]
    }
  },
  "sort": [{ "metadata.collection_timestamp": "asc" }],
  "_source": ["metadata.collection_timestamp", "results.primary_metric"]
}
```

### **Hardware Comparison**

```json
GET /zathras-results/_search
{
  "query": { "term": { "test.name": "coremark" }},
  "aggs": {
    "by_cpu_model": {
      "terms": { "field": "system_under_test.hardware.cpu.model.keyword", "size": 10 },
      "aggs": {
        "avg_performance": { "avg": { "field": "results.primary_metric.value" }},
        "max_performance": { "max": { "field": "results.primary_metric.value" }}
      }
    }
  }
}
```

### **Find Systems with Specific Features**

```json
# Systems with AVX-512 and more than 64 cores
GET /zathras-results/_search
{
  "query": {
    "bool": {
      "must": [
        { "term": { "system_under_test.hardware.cpu.flags.avx512": true }},
        { "range": { "system_under_test.hardware.cpu.cores": { "gt": 64 }}}
      ]
    }
  }
}
```

### **Time Series Analysis**

```json
# Get time series data for specific run
GET /zathras-results/_doc/coremark_host1_20251106_120000
{
  "_source": ["results.runs.run_1.timeseries"]
}
```

---

## 📚 Additional Resources

### **Documentation**
- [Schema Analysis](DATA_ANALYSIS.md) - Detailed schema documentation
- [Implementation Plan](IMPLEMENTATION_TODO.md) - Development roadmap
- [Index Template](config/opensearch_index_template.json) - OpenSearch mappings

### **Zathras Documentation**
- [Main README](../README.md)
- [Testing Quickstart](../docs/testing_quickstart.md)
- [Command Line Reference](../docs/command_line_reference.md)

### **External Resources**
- [OpenSearch Query DSL](https://opensearch.org/docs/latest/query-dsl/)
- [OpenSearch Aggregations](https://opensearch.org/docs/latest/aggregations/)
- [Horreum Documentation](https://horreum.hyperfoil.io/)

---

## 🤝 Contributing

### **Adding New Benchmark Processors**

1. Create a new processor in `processors/`
2. Inherit from `BaseProcessor`
3. Implement `get_test_name()` and `parse_runs()`
4. Add tests

Example:
```python
from .base_processor import BaseProcessor

class MyBenchmarkProcessor(BaseProcessor):
    def get_test_name(self) -> str:
        return "mybenchmark"
    
    def parse_runs(self, extracted_result) -> dict:
        runs = {}
        # Your parsing logic here
        # Return object-based structure: {"run_1": {...}, "run_2": {...}}
        return runs
```

---

## ✨ Summary

**Zathras Post-Processing:**
- ✅ Converts benchmark results to structured JSON
- ✅ Exports to OpenSearch or Horreum
- ✅ Integrates with existing burden workflows
- ✅ CI/CD ready
- ✅ Time-series data preserved
- ✅ Comprehensive system metadata

**Get started in 3 steps:**
1. Run your Zathras benchmark (no changes needed)
2. Process results with `CoreMarkProcessor`
3. Export with `OpenSearchExporter`

**Questions?** See the [main Zathras repository](../) or [troubleshooting section](#-troubleshooting).
