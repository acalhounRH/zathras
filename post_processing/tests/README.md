# Post-Processing Tests

This directory is for test scripts and validation. Test files are not included in the repository.

---

## Test Recommendations

When developing or validating the post-processing pipeline, consider creating:

### Unit Tests
- Mock data tests for individual processors
- Schema validation tests
- Hash calculation and deduplication tests

### Integration Tests
- OpenSearch export tests with real instance
- Horreum export tests
- End-to-end processing tests

---

## Example Test Structure

**Deduplication Test:**
```python
# test_deduplication.py
def test_same_content_same_hash():
    """Verify identical test data generates same hash"""
    doc1 = create_test_document()
    doc2 = create_test_document()
    assert doc1.calculate_content_hash() == doc2.calculate_content_hash()
```

**Processor Test:**
```python
# test_coremark.py
def test_coremark_processor():
    """Test CoreMark result parsing"""
    processor = CoreMarkProcessor("path/to/results")
    document = processor.process()
    assert document.test.name == "coremark"
    assert document.results.status == "SUCCESS"
```

**OpenSearch Integration Test:**
```python
# test_opensearch_export.py
def test_no_duplicates():
    """Verify same results don't create duplicates"""
    exporter = OpenSearchExporter(...)
    
    # Process and upload twice
    doc1 = processor.process()
    exporter.export_zathras_document(doc1)
    
    doc2 = processor.process()
    exporter.export_zathras_document(doc2)
    
    # Query - should find only 1 document
    results = exporter.search({"query": {"term": {"metadata.document_id": doc1.metadata.document_id}}})
    assert results['hits']['total']['value'] == 1
```

---

## Running Tests

Add test files to `.gitignore` to keep them local:

```bash
# In post_processing/tests/.gitignore
*.py
!__init__.py
```

Run tests:
```bash
python3 post_processing/tests/test_deduplication.py
python3 post_processing/tests/test_opensearch_export.py
```

---

## Test Data

Use sample benchmark results from:
- `quick_sample_data/` - Small test datasets
- `production_data/` - Full benchmark results (usually in .gitignore)

---

## Notes

- Tests are not committed to the repository
- Create tests as needed for your development workflow
- Use generic URLs (e.g., `opensearch.example.com`) in examples
- Store credentials in environment variables, not in code
