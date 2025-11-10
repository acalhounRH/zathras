#!/bin/bash
#
# Apply OpenSearch index templates and recreate indices with increased field limits
#
# Usage: ./apply_opensearch_templates.sh <opensearch_url> <username> <password>
#
# Example:
#   ./apply_opensearch_templates.sh https://opensearch.app.intlab.redhat.com automotive 'D6O8#zke0iSc'
#

set -e

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <opensearch_url> <username> <password>"
    echo ""
    echo "Example:"
    echo "  $0 https://opensearch.app.intlab.redhat.com automotive 'password'"
    exit 1
fi

OPENSEARCH_URL="$1"
USERNAME="$2"
PASSWORD="$3"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================"
echo "Applying OpenSearch Templates"
echo "========================================"
echo ""

# Apply results template
echo "1. Applying zathras-results template..."
curl -k -X PUT "${OPENSEARCH_URL}/_index_template/zathras-results-template" \
  -u "${USERNAME}:${PASSWORD}" \
  -H 'Content-Type: application/json' \
  -d @"${SCRIPT_DIR}/opensearch_index_template.json"
echo ""
echo ""

# Apply timeseries template
echo "2. Applying zathras-timeseries template..."
curl -k -X PUT "${OPENSEARCH_URL}/_index_template/zathras-timeseries-template" \
  -u "${USERNAME}:${PASSWORD}" \
  -H 'Content-Type: application/json' \
  -d @"${SCRIPT_DIR}/opensearch_timeseries_template.json"
echo ""
echo ""

echo "========================================"
echo "Deleting Existing Indices"
echo "========================================"
echo ""

# Delete existing indices to apply new templates
echo "3. Deleting zathras-results index (if exists)..."
curl -k -X DELETE "${OPENSEARCH_URL}/zathras-results" \
  -u "${USERNAME}:${PASSWORD}" 2>/dev/null || echo "Index does not exist (OK)"
echo ""
echo ""

echo "4. Deleting zathras-timeseries index (if exists)..."
curl -k -X DELETE "${OPENSEARCH_URL}/zathras-timeseries" \
  -u "${USERNAME}:${PASSWORD}" 2>/dev/null || echo "Index does not exist (OK)"
echo ""
echo ""

echo "========================================"
echo "Verification"
echo "========================================"
echo ""

# Verify templates are applied
echo "5. Verifying templates..."
echo ""
echo "Results template:"
curl -k -s -X GET "${OPENSEARCH_URL}/_index_template/zathras-results-template" \
  -u "${USERNAME}:${PASSWORD}" | python3 -m json.tool | grep -A 5 "total_fields"
echo ""
echo "Timeseries template:"
curl -k -s -X GET "${OPENSEARCH_URL}/_index_template/zathras-timeseries-template" \
  -u "${USERNAME}:${PASSWORD}" | python3 -m json.tool | grep -A 5 "total_fields"
echo ""

echo "========================================"
echo "Done!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Re-run the post-processing script to re-index all data"
echo "2. The new indices will be created with the 5000 field limit"
echo ""

