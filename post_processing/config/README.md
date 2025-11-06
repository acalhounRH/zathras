# Post-Processing Configuration

This directory contains configuration files for the Zathras post-processing pipeline.

## Files

### `opensearch_index_template.json`
OpenSearch index template with object-based mappings for Zathras benchmark results.

**Features:**
- Dynamic templates for runs (`run_1`, `run_2`, etc.)
- Timestamp-keyed time series data
- Boolean object for CPU flags
- Object mappings for NUMA nodes, storage devices, network interfaces
- Optimized for aggregations and queries

**Usage:**
The template is automatically applied by `OpenSearchExporter` when creating a new index.

### `export_config.example.yml`
Example configuration for OpenSearch and Horreum exporters.

**Setup:**
```bash
# Copy example to actual config
cp export_config.example.yml export_config.yml

# Set environment variables
export OPENSEARCH_TOKEN="your-token-here"

# Or edit export_config.yml directly
```

**Important:** `export_config.yml` is in `.gitignore` to prevent committing credentials.

## OpenSearch Connection

### Red Hat Internal OpenSearch
```yaml
opensearch:
  url: "https://opensearch.app.intlab.redhat.com/"
  index: "zathras-results"
  auth_token: "${OPENSEARCH_TOKEN}"
```

### Getting a Token
For Red Hat internal OpenSearch, obtain a token from:
- Internal SSO/Keycloak
- OpenSearch admin dashboard
- Or contact your OpenSearch administrator

### Testing Connection
```python
from post_processing.exporters.opensearch_exporter import OpenSearchExporter

exporter = OpenSearchExporter(
    url="https://opensearch.app.intlab.redhat.com/",
    index="zathras-results",
    auth_token="your-token"
)

# Test connection
if exporter.test_connection():
    print("✅ Connected to OpenSearch!")
else:
    print("❌ Connection failed")
```

## Index Template

The index template defines mappings for:

- **Metadata**: Document ID, type, version, timestamps
- **Test**: Name, version, description
- **System Under Test**: CPU, memory, NUMA, storage, network
- **Test Configuration**: Parameters, environment, tuning
- **Results**: Status, metrics, runs (object-based)
- **Runtime Info**: Start/stop times, command, user

### Dynamic Templates

1. **run_objects**: Maps `results.runs.run_*` to run objects
2. **timeseries_objects**: Maps `results.runs.*.timeseries.*` to time series points
3. **numa_nodes**: Maps `system_under_test.hardware.numa.node_*`
4. **storage_devices**: Maps `system_under_test.hardware.storage.device_*`
5. **network_interfaces**: Maps `system_under_test.hardware.network.interface_*`
6. **cpu_flags**: Maps CPU flags to boolean (e.g., `cpu.flags.avx2: true`)

## Querying Results

### Example Queries

**Find all CoreMark results:**
```json
GET /zathras-results/_search
{
  "query": {
    "term": { "test.name": "coremark" }
  }
}
```

**Find systems with AVX2 support:**
```json
GET /zathras-results/_search
{
  "query": {
    "term": { "system_under_test.hardware.cpu.flags.avx2": true }
  }
}
```

**Aggregate by CPU architecture:**
```json
GET /zathras-results/_search
{
  "size": 0,
  "aggs": {
    "by_architecture": {
      "terms": { "field": "system_under_test.hardware.cpu.architecture" }
    }
  }
}
```

**Get performance trends over time:**
```json
GET /zathras-results/_search
{
  "query": { "term": { "test.name": "coremark" }},
  "sort": [{ "metadata.collection_timestamp": "desc" }],
  "size": 100
}
```

## Security

⚠️ **Important:**
- Never commit `export_config.yml` with real credentials
- Use environment variables for sensitive data
- Rotate tokens regularly
- Use SSL/TLS in production (`verify_ssl: true`)

## Troubleshooting

### Connection Errors
```
Error: Connection failed after 3 attempts
```
**Solution:** Check URL, verify network access, confirm token is valid

### SSL Certificate Errors
```
Error: SSL certificate verify failed
```
**Solution:** 
- For production: Get proper SSL certificate
- For testing only: Set `verify_ssl: false` (not recommended)

### Authentication Errors
```
Error: 401 Unauthorized
```
**Solution:** Check token is valid and has proper permissions

### Index Creation Errors
```
Error: 400 index_already_exists_exception
```
**Solution:** This is normal if index exists. Exporter handles this automatically.

