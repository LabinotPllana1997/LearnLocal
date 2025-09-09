"""
Basic API tests for LearnerExpert endpoints.
"""

import pytest
import httpx


class TestBasicAPI:
    """Basic API endpoint tests."""
    
    BASE_URL = "http://localhost:8000"
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup for each test method."""
        self.client = httpx.Client(base_url=self.BASE_URL, timeout=300.0)
        
    def teardown_method(self):
        """Cleanup after each test method."""
        if hasattr(self, 'client'):
            self.client.close()
    
    def test_server_health(self):
        """Test that the server is running and healthy."""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_offline_status(self):
        """Test the offline status endpoint."""
        response = self.client.get("/offline/status")
        assert response.status_code == 200
        data = response.json()
        assert "offline_llm_enabled" in data
        if "backend_info" in data:
            assert "backend" in data["backend_info"]
            assert "available" in data["backend_info"]
    
    @pytest.mark.slow
    def test_offline_ask_basic(self):
        """Test basic offline ask functionality (may take several minutes)."""
        payload = {
            "question": "Hi",
            "context": "",
            "user_type": "teacher",
            "include_audio": False
        }
        
        response = self.client.post("/offline/ask", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert "question" in data
        assert "answer" in data
        assert "user_type" in data
        assert "response_time_ms" in data
        assert "created_at" in data
        
        assert data["question"] == payload["question"]
        assert data["user_type"] == payload["user_type"]
        assert isinstance(data["answer"], str)
        assert len(data["answer"]) > 0
    
    def test_api_docs(self):
        """Test that API documentation is accessible."""
        client = httpx.Client(base_url=self.BASE_URL, timeout=30.0)
        try:
            response = client.get("/docs")
            assert response.status_code == 200
            assert "text/html" in response.headers.get("content-type", "")
        finally:
            client.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])