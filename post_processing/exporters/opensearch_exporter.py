#!/usr/bin/env python3
"""
OpenSearch Exporter

Handles exporting processed benchmark results to OpenSearch/Elasticsearch.
Supports bulk operations, retry logic, and connection management.
"""

import json
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from urllib.parse import urljoin
import urllib.request
import urllib.error


class OpenSearchExporter:
    """Export benchmark results to OpenSearch."""
    
    def __init__(
        self,
        url: str,
        index: str,
        auth_token: Optional[str] = None,
        verify_ssl: bool = True,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: int = 5
    ):
        """
        Initialize OpenSearch exporter.
        
        Args:
            url: OpenSearch endpoint URL (e.g., https://opensearch.example.com)
            index: Index name to write documents to
            auth_token: Optional authentication token
            verify_ssl: Whether to verify SSL certificates
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.url = url.rstrip('/')
        self.index = index
        self.auth_token = auth_token
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logging.getLogger(__name__)
        
    def _build_headers(self) -> Dict[str, str]:
        """Build HTTP headers for requests."""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
            
        return headers
    
    def _make_request(
        self,
        endpoint: str,
        method: str = 'POST',
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to OpenSearch with retry logic.
        
        Args:
            endpoint: API endpoint path
            method: HTTP method
            data: Request payload
            
        Returns:
            Response data as dictionary
            
        Raises:
            Exception: If request fails after retries
        """
        url = urljoin(self.url, endpoint)
        headers = self._build_headers()
        
        for attempt in range(self.max_retries):
            try:
                # Prepare request
                request_data = json.dumps(data).encode('utf-8') if data else None
                req = urllib.request.Request(
                    url,
                    data=request_data,
                    headers=headers,
                    method=method
                )
                
                # Make request
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    response_data = json.loads(response.read().decode('utf-8'))
                    self.logger.debug(f"Request to {endpoint} succeeded")
                    return response_data
                    
            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8')
                self.logger.error(
                    f"HTTP {e.code} error on attempt {attempt + 1}/{self.max_retries}: {error_body}"
                )
                
                # Don't retry on client errors (4xx)
                if 400 <= e.code < 500:
                    raise Exception(f"Client error {e.code}: {error_body}")
                    
                # Retry on server errors (5xx)
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise Exception(f"Request failed after {self.max_retries} attempts: {error_body}")
                    
            except urllib.error.URLError as e:
                self.logger.error(f"Connection error on attempt {attempt + 1}/{self.max_retries}: {e.reason}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise Exception(f"Connection failed after {self.max_retries} attempts: {e.reason}")
                    
            except Exception as e:
                self.logger.error(f"Unexpected error on attempt {attempt + 1}/{self.max_retries}: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise
    
    def test_connection(self) -> bool:
        """
        Test connection to OpenSearch.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self._make_request('/', method='GET')
            self.logger.info(f"Connected to OpenSearch cluster: {response.get('cluster_name', 'unknown')}")
            return True
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def ensure_index_exists(self) -> bool:
        """
        Ensure the target index exists, create if it doesn't.
        
        Returns:
            True if index exists or was created successfully
        """
        try:
            # Check if index exists
            self._make_request(f'/{self.index}', method='HEAD')
            self.logger.info(f"Index '{self.index}' already exists")
            return True
        except:
            # Index doesn't exist, create it
            try:
                index_settings = {
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 1,
                        "index": {
                            "mapping": {
                                "total_fields": {
                                    "limit": 2000
                                }
                            }
                        }
                    },
                    "mappings": {
                        "properties": {
                            "test_run": {
                                "properties": {
                                    "timestamp": {"type": "date"},
                                    "zathras_version": {"type": "keyword"}
                                }
                            },
                            "infrastructure": {
                                "properties": {
                                    "type": {"type": "keyword"},
                                    "instance_type": {"type": "keyword"},
                                    "region": {"type": "keyword"}
                                }
                            },
                            "test": {
                                "properties": {
                                    "name": {"type": "keyword"},
                                    "version": {"type": "keyword"},
                                    "status": {"type": "keyword"},
                                    "duration_seconds": {"type": "float"}
                                }
                            }
                        }
                    }
                }
                
                self._make_request(f'/{self.index}', method='PUT', data=index_settings)
                self.logger.info(f"Created index '{self.index}'")
                return True
            except Exception as e:
                self.logger.error(f"Failed to create index: {str(e)}")
                return False
    
    def export_document(self, document: Dict[str, Any], doc_id: Optional[str] = None) -> str:
        """
        Export a single document to OpenSearch.
        
        Args:
            document: Document to export
            doc_id: Optional document ID (auto-generated if not provided)
            
        Returns:
            Document ID of the indexed document
            
        Raises:
            Exception: If export fails
        """
        # Add export metadata
        document['_export_metadata'] = {
            'exported_at': datetime.utcnow().isoformat() + 'Z',
            'exporter': 'zathras-opensearch-exporter',
            'exporter_version': '0.1.0'
        }
        
        # Determine endpoint
        if doc_id:
            endpoint = f'/{self.index}/_doc/{doc_id}'
        else:
            endpoint = f'/{self.index}/_doc'
        
        # Index document
        try:
            response = self._make_request(endpoint, method='POST', data=document)
            doc_id = response.get('_id')
            self.logger.info(f"Exported document with ID: {doc_id}")
            return doc_id
        except Exception as e:
            self.logger.error(f"Failed to export document: {str(e)}")
            raise
    
    def export_bulk(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Export multiple documents using bulk API.
        
        Args:
            documents: List of documents to export
            
        Returns:
            Bulk operation results
            
        Raises:
            Exception: If bulk export fails
        """
        if not documents:
            self.logger.warning("No documents to export")
            return {"items": [], "errors": False}
        
        # Build bulk request body
        bulk_body = []
        for doc in documents:
            # Add export metadata
            doc['_export_metadata'] = {
                'exported_at': datetime.utcnow().isoformat() + 'Z',
                'exporter': 'zathras-opensearch-exporter',
                'exporter_version': '0.1.0'
            }
            
            # Index action
            bulk_body.append(json.dumps({"index": {"_index": self.index}}))
            bulk_body.append(json.dumps(doc))
        
        bulk_data = '\n'.join(bulk_body) + '\n'
        
        # Make bulk request
        try:
            url = urljoin(self.url, '/_bulk')
            headers = self._build_headers()
            headers['Content-Type'] = 'application/x-ndjson'
            
            req = urllib.request.Request(
                url,
                data=bulk_data.encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                result = json.loads(response.read().decode('utf-8'))
                
            # Check for errors
            if result.get('errors'):
                error_count = sum(1 for item in result.get('items', []) 
                                if 'error' in item.get('index', {}))
                self.logger.warning(f"Bulk export completed with {error_count} errors")
            else:
                self.logger.info(f"Successfully exported {len(documents)} documents")
                
            return result
            
        except Exception as e:
            self.logger.error(f"Bulk export failed: {str(e)}")
            raise
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document from OpenSearch.
        
        Args:
            doc_id: Document ID to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            self._make_request(f'/{self.index}/_doc/{doc_id}', method='DELETE')
            self.logger.info(f"Deleted document: {doc_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete document {doc_id}: {str(e)}")
            return False
    
    def search(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a search query.
        
        Args:
            query: OpenSearch query DSL
            
        Returns:
            Search results
        """
        try:
            return self._make_request(f'/{self.index}/_search', method='POST', data=query)
        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
            raise

