# Content-Based Deduplication

## Overview

The Zathras post-processing pipeline uses **content-based checksums** to prevent duplicate documents in OpenSearch. This ensures that processing the same test results multiple times will update the existing document rather than creating duplicates.

## How It Works

### 1. Content Hash Calculation

When a document is processed, a SHA256 hash is calculated based on:

**Included in hash:**
- Test name and version
- System configuration (CPU, memory, OS, cloud provider, instance type)
- Test configuration and parameters
- All benchmark results and metrics
- Test timestamp (when the test was originally executed)
- All runs and time series data

**Excluded from hash:**
- `processing_timestamp` - This changes every time you run post-processing
- `document_id` - This is what we're computing

### 2. Document ID Generation

The document ID is generated using the content hash:

```python
# Calculate hash of test content (excluding processing_timestamp)
content_hash = document.calculate_content_hash()

# Generate document ID
document_id = f"{test_name}_{content_hash[:16]}"
# Example: "coremark_a3f2d9c8e1b4f7a2"
```

### 3. OpenSearch Behavior

When uploading to OpenSearch using a specific document ID:

```python
# First upload
POST /zathras-results/_doc/coremark_a3f2d9c8e1b4f7a2
→ Creates new document

# Second upload (same ID, different processing_timestamp)
POST /zathras-results/_doc/coremark_a3f2d9c8e1b4f7a2
→ Updates existing document (no duplicate)

# Third upload (same ID)
POST /zathras-results/_doc/coremark_a3f2d9c8e1b4f7a2
→ Updates existing document again
```

**Result:** Only 1 document exists in OpenSearch, regardless of how many times it's processed.

## Benefits

### Prevents Duplicates

Reprocessing the same test results will not create duplicates:

```bash
# Day 1: Process and upload
python3 -m post_processing.run_postprocessing --input results/ --opensearch

# Day 2: Process same results again (maybe with updated processor)
python3 -m post_processing.run_postprocessing --input results/ --opensearch

# Result: Same document updated, no duplicate created
```

### Enables Safe Reprocessing

You can safely reprocess results:
- After fixing processor bugs
- When adding new extractors
- To update metadata or add new fields
- Without worrying about creating duplicates

### Tracks Last Processing Time

The `processing_timestamp` field shows when the document was last processed:

```json
{
  "metadata": {
    "document_id": "coremark_a3f2d9c8e1b4f7a2",
    "test_timestamp": "2025-11-06T14:30:00.000Z",       // When test ran
    "processing_timestamp": "2025-11-10T09:15:30.123Z"   // When last processed
  }
}
```

## Time Series Documents

Time series documents also use deterministic IDs based on the parent document's hash:

```python
# Parent document
document_id = "coremark_a3f2d9c8e1b4f7a2"

# Time series documents
timeseries_id = f"{document_id}_{run_key}_{sequence_key}"
# Examples:
#   "coremark_a3f2d9c8e1b4f7a2_run_1_sequence_0"
#   "coremark_a3f2d9c8e1b4f7a2_run_1_sequence_1"
#   "coremark_a3f2d9c8e1b4f7a2_run_2_sequence_0"
```

This ensures time series data is also deduplicated correctly.

## When Duplicates WILL Occur

Duplicates will only occur when the **actual test data changes**:

### Different Test Runs
```bash
# Test run on Monday
./burden --test coremark
# Processing creates: coremark_abc123...

# Test run on Tuesday (different results)
./burden --test coremark  
# Processing creates: coremark_def456...  (different hash)
```

### Different Systems
```bash
# Same test on different instance types
Standard_D8ds_v6_1/coremark  → coremark_abc123...
Standard_D16ds_v6_1/coremark → coremark_xyz789...  (different system)
```

### Different Configurations
```bash
# Same test with different parameters
coremark --threads=4  → coremark_abc123...
coremark --threads=8  → coremark_def456...  (different config)
```

## Testing Deduplication

Run the deduplication test script:

```bash
cd /Users/acalhoun/Documents/Sandbox/zathras
python3 post_processing/tests/test_deduplication.py
```

This will:
1. Process the same test results 3 times
2. Show that all 3 generate the same content hash
3. Show that all 3 generate the same document ID
4. Demonstrate that `processing_timestamp` differs but is excluded from hash

### Test with OpenSearch

To test actual deduplication in OpenSearch:

```bash
export OPENSEARCH_URL='https://opensearch.example.com'
export OPENSEARCH_USER='your-username'
export OPENSEARCH_PASS='your-password'

python3 post_processing/tests/test_deduplication.py
```

This will upload the same document 3 times and verify only 1 document exists in OpenSearch.

## Implementation Details

### Schema (`schema.py`)

```python
class ZathrasDocument:
    def calculate_content_hash(self, exclude_processing_timestamp: bool = True) -> str:
        """
        Calculate SHA256 hash of document content.
        
        Returns:
            Hex string of SHA256 hash (64 characters)
        """
        # Create deep copy
        doc_dict = copy.deepcopy(self.to_dict())
        
        # Remove fields that change on re-processing
        if exclude_processing_timestamp:
            doc_dict['metadata'].pop('processing_timestamp', None)
            doc_dict['metadata'].pop('document_id', None)
        
        # Sort keys for deterministic ordering
        sorted_json = json.dumps(doc_dict, sort_keys=True, separators=(',', ':'))
        
        # Calculate SHA256
        hash_obj = hashlib.sha256(sorted_json.encode('utf-8'))
        return hash_obj.hexdigest()
```

### Processor (`base_processor.py`)

```python
def process(self) -> ZathrasDocument:
    # Build document sections
    metadata = self.build_metadata()
    test_info = self.build_test_info()
    # ... build other sections ...
    
    # Create document
    document = ZathrasDocument(
        metadata=metadata,
        test=test_info,
        # ...
    )
    
    # Calculate content-based hash
    content_hash = document.calculate_content_hash()
    
    # Update document_id with hash
    document.metadata.document_id = f"{test_name}_{content_hash[:16]}"
    
    return document
```

### Exporter (`opensearch_exporter.py`)

```python
def export_zathras_document(self, document: ZathrasDocument) -> str:
    doc_dict = document.to_dict()
    
    # Use document_id from metadata as OpenSearch document ID
    doc_id = doc_dict['metadata']['document_id']
    
    # POST with explicit ID updates existing doc if ID already exists
    return self.export_document(doc_dict, doc_id=doc_id)
```

## Query Examples

### Find Documents by Content Hash

```bash
# Search by document ID (which contains the hash)
GET /zathras-results/_search
{
  "query": {
    "term": {
      "metadata.document_id.keyword": "coremark_a3f2d9c8e1b4f7a2"
    }
  }
}
```

### Find All Versions of a Test on a System

```bash
# Find all CoreMark results for a specific instance type
GET /zathras-results/_search
{
  "query": {
    "bool": {
      "must": [
        {"prefix": {"metadata.document_id.keyword": "coremark_"}},
        {"term": {"metadata.instance_type.keyword": "Standard_D8ds_v6_1"}}
      ]
    }
  }
}
```

### Check for Recent Reprocessing

```bash
# Find documents processed in last 24 hours
GET /zathras-results/_search
{
  "query": {
    "range": {
      "metadata.processing_timestamp": {
        "gte": "now-24h"
      }
    }
  }
}
```

## Troubleshooting

### Duplicates Still Appearing?

If you're seeing duplicates despite using content hashes:

1. **Check document IDs:**
   ```bash
   # Search for documents with similar IDs
   GET /zathras-results/_search
   {
     "query": {
       "prefix": {"metadata.document_id.keyword": "coremark_"}
     }
   }
   ```

2. **Compare content hashes:**
   - Documents with different hashes represent different test runs
   - This is expected behavior

3. **Check if test data actually differs:**
   - Different timestamps from original test run
   - Different system configurations
   - Different test parameters

### Hash Collisions?

SHA256 has extremely low collision probability:
- 2^256 possible hashes
- Practically impossible to have accidental collision
- If collision occurs, documents genuinely have identical content

## Future Enhancements

Potential improvements:

1. **Shorter hashes:** Use first 16 chars instead of 64 (already implemented)
2. **Custom ID format:** Include date/system info for readability
3. **Explicit version tracking:** Track how many times document was reprocessed
4. **Change detection:** Alert when reprocessing changes results

## Summary

✅ **Automatic:** No configuration needed, works by default
✅ **Safe:** Reprocess results without creating duplicates  
✅ **Transparent:** Document ID shows it's content-based
✅ **Trackable:** `processing_timestamp` shows last update time
✅ **Consistent:** Same approach for summary and time series documents

The content-based deduplication system ensures your OpenSearch indices stay clean and organized, even when reprocessing historical results or fixing processor issues.

