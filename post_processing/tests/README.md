# Post-Processing Tests

Test scripts for validating the Zathras post-processing pipeline.

---

## Available Tests

### Deduplication Tests

**`test_deduplication_simple.py`**
- **Purpose:** Unit test for content-based deduplication
- **Requirements:** None (uses mock data)
- **Runtime:** < 1 second
- **Usage:**
  ```bash
  python3 post_processing/tests/test_deduplication_simple.py
  ```
- **What it tests:**
  - Same content generates same hash
  - Different content generates different hash
  - Document IDs are properly generated
  - Processing timestamp is excluded from hash

**`test_live_deduplication.py`**
- **Purpose:** Integration test with real OpenSearch instance
- **Requirements:** 
  - OpenSearch credentials (environment variables or config file)
  - Actual benchmark results (coremark or streams)
- **Runtime:** ~5 seconds
- **Usage:**
  ```bash
  export OPENSEARCH_URL='https://opensearch.app.intlab.redhat.com'
  export OPENSEARCH_USER='your-username'
  export OPENSEARCH_PASS='your-password'
  
  python3 post_processing/tests/test_live_deduplication.py
  ```
- **What it tests:**
  - Processes same results twice
  - Uploads both to OpenSearch
  - Verifies only 1 document exists (no duplicate)
  - Confirms processing_timestamp was updated

---

## Test Results

All tests passing:

✅ **test_deduplication_simple.py** (4/4 tests)
- Same content → same hash
- Different content → different hash
- Document ID generation
- Processing timestamp exclusion

✅ **test_live_deduplication.py**
- Live OpenSearch integration
- Duplicate prevention verified
- Document updates confirmed

---

## Running Tests

### Quick Check (No Dependencies)

```bash
python3 post_processing/tests/test_deduplication_simple.py
```

### Full Integration Test

Requires OpenSearch access:

```bash
# Set credentials
export OPENSEARCH_URL='https://opensearch.app.intlab.redhat.com'
export OPENSEARCH_USER='your-username'
export OPENSEARCH_PASS='your-password'

# Run test
python3 post_processing/tests/test_live_deduplication.py
```

The live test will:
1. Find available benchmark results
2. Connect to OpenSearch
3. Process and upload results twice
4. Verify no duplicates were created
5. Show document details

---

## Test Coverage

**Deduplication System:**
- ✅ Content hash calculation
- ✅ Document ID generation
- ✅ Processing timestamp exclusion
- ✅ OpenSearch update behavior
- ✅ No duplicate creation

**Future Test Areas:**
- Processor-specific tests (coremark, streams, pyperf, etc.)
- Time series document deduplication
- Bulk export operations
- Error handling and edge cases

---

## Notes

- Test scripts use `zathras-dedup-test` index (separate from production)
- Clean up test data: `DELETE /zathras-dedup-test` in OpenSearch
- Tests are safe to run repeatedly
- No production data is affected
