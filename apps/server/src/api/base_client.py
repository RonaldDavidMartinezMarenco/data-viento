"""
Base API Client

Provides common HTTP functionality for all external API clients:
- Retry logic with exponential backoff
- Error handling and logging
- Request/response formatting
- Timeout management
"""

import httpx
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class BaseAPIClient:
    """
    Base class for all external API clients
    
    Features:
    - HTTP request handling (GET, POST, PUT, DELETE)
    - Automatic retry with exponential backoff
    - Detailed error logging
    - Request timeouts
    - Connection pooling
    """
    
    BASE_URL: str = ""
    TIMEOUT: int = 30  # seconds
    MAX_RETRIES: int = 5
    RETRY_DELAY: float = 1.0  # seconds
    
    def __init__(self, timeout: int = None):
        """
        Initialize the API client
        
        Args:
            timeout: Request timeout in seconds (uses class default if None)
        """
        self.timeout = timeout or self.TIMEOUT
        self.client = httpx.AsyncClient(timeout=self.timeout)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retries: int = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Make an HTTP request with automatic retry logic
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path (appended to BASE_URL)
            params: Query parameters (for GET requests)
            json_data: JSON body (for POST/PUT requests)
            headers: Custom headers
            retries: Number of retry attempts (uses class default if None)
        
        Returns:
            Response JSON as dictionary, or None if failed
        
        Explanation:
        - Automatically retries on network errors
        - Uses exponential backoff (1s, 2s, 4s)
        - Logs all errors for debugging
        - Raises exception on final failure
        """
        
        if retries is None:
            retries = self.MAX_RETRIES
        
        url = f"{self.BASE_URL}/{endpoint}" if endpoint else self.BASE_URL
        retry_delay = self.RETRY_DELAY
        
        for attempt in range(retries):
            try:
                self.logger.debug(f"Request attempt {attempt + 1}/{retries}: {method} {url}")
                
                response = await self.client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    headers=headers,
                )
                
                response.raise_for_status()
                
                self.logger.info(f"✓ API request successful: {method} {url} [{response.status_code}]")
                return response.json()
            
            except httpx.HTTPStatusError as e:
                """HTTP error (4xx, 5xx)"""
                self.logger.error(
                    f"HTTP {e.response.status_code} on attempt {attempt + 1}/{retries}: {e.response.text[:200]}"
                )
                
                if attempt == retries - 1:
                    raise
                
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            
            except httpx.RequestError as e:
                """Network error (timeout, connection refused, etc.)"""
                self.logger.error(f"Network error on attempt {attempt + 1}/{retries}: {e}")
                
                if attempt == retries - 1:
                    raise
                
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
        
        return None
    
    async def close(self):
        """Close the HTTP client connection"""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()