import io
import os
import sys
from unittest.mock import patch, AsyncMock

import pytest
from PIL import Image

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from whats_for_dinner.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Test client for the FastAPI application.""" 
    return TestClient(app)


@pytest.fixture
def mock_recipe_service():
    """Mock RecipeService for testing."""
    with patch("whats_for_dinner.api.recipes.RecipeService") as mock:
        service_instance = AsyncMock()
        mock.return_value = service_instance
        service_instance.recommend_recipe.return_value = "# Mock Recipe\\n\\nThis is a test recipe."
        yield service_instance


@pytest.fixture  
def mock_image_extractor():
    """Mock ExtractFoodItemsFromImage component for testing."""
    with patch("whats_for_dinner.api.recipes.ExtractFoodItemsFromImage") as mock:
        extractor_instance = AsyncMock()
        mock.return_value = extractor_instance
        extractor_instance.run.return_value = {"answer": "• chicken breast\\n• rice\\n• vegetables"}
        yield extractor_instance


@pytest.fixture
def test_image():
    """Create a test image file for upload testing."""
    img = Image.new('RGB', (100, 100), color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    return buffer


class TestRecipeAPI:
    """Tests for the recipe recommendation API endpoints."""

    @pytest.mark.anyio
    async def test_health_endpoint(self, client):
        """Test the health check endpoint works."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    @pytest.mark.anyio
    async def test_recommend_recipe_success(self, client, mock_recipe_service):
        """Test successful recipe recommendation with text ingredients."""
        request_data = {"ingredients": "chicken, rice, vegetables"}
        
        response = client.post("/recommend_recipe", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "recipe" in data
        assert isinstance(data["recipe"], str)
        
        # Verify the service was called correctly
        mock_recipe_service.recommend_recipe.assert_called_once_with(
            ingredients="chicken, rice, vegetables"
        )

    @pytest.mark.anyio
    async def test_recommend_recipe_empty_ingredients(self, client, mock_recipe_service):
        """Test recipe recommendation with empty ingredients."""
        request_data = {"ingredients": ""}
        
        response = client.post("/recommend_recipe", json=request_data)
        
        assert response.status_code == 200
        mock_recipe_service.recommend_recipe.assert_called_once_with(ingredients="")


    @pytest.mark.anyio
    async def test_recommend_recipe_with_image_success(
        self, 
        client, 
        mock_recipe_service, 
        mock_image_extractor,
        test_image
    ):
        """Test successful recipe recommendation with image and text."""
        files = {"image": ("test.jpg", test_image, "image/jpeg")}
        data = {"ingredients": "chicken, rice"}
        
        response = client.post("/recommend_recipe_with_image", files=files, data=data)
        
        assert response.status_code == 200
        response_data = response.json()
        assert "recipe" in response_data
        assert isinstance(response_data["recipe"], str)
        
        # Verify both services were called
        mock_image_extractor.run.assert_called_once()
        mock_recipe_service.recommend_recipe.assert_called_once()

    @pytest.mark.anyio
    async def test_recommend_recipe_text_only(self, client, mock_recipe_service):
        """Test recipe recommendation with text only (no image)."""
        data = {"ingredients": "chicken, rice, vegetables"}
        
        response = client.post("/recommend_recipe_with_image", data=data)
        
        assert response.status_code == 200
        response_data = response.json()
        assert "recipe" in response_data
        
        # Verify service called with no extracted ingredients
        mock_recipe_service.recommend_recipe.assert_called_once_with(
            ingredients="chicken, rice, vegetables",
            extracted_ingredients=None
        )

    @pytest.mark.anyio
    async def test_recommend_recipe_missing_ingredients_field(self, client):
        """Test recipe recommendation without ingredients field."""
        request_data = {}
        
        response = client.post("/recommend_recipe", json=request_data)
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_recommend_recipe_invalid_json(self, client):
        """Test recipe recommendation with invalid JSON."""
        response = client.post(
            "/recommend_recipe", 
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_recommend_recipe_service_exception(self, client):
        """Test recipe recommendation when service raises exception."""
        with patch("whats_for_dinner.api.recipes.RecipeService") as mock_service:
            service_instance = AsyncMock()
            mock_service.return_value = service_instance
            service_instance.recommend_recipe.side_effect = Exception("Service error")
            
            request_data = {"ingredients": "chicken, rice"}
            # The actual exception should be raised rather than caught
            with pytest.raises(Exception):
                response = client.post("/recommend_recipe", json=request_data)

    @pytest.mark.anyio
    async def test_recommend_recipe_image_only(
        self, 
        client, 
        mock_recipe_service, 
        mock_image_extractor,
        test_image
    ):
        """Test recipe recommendation with image only (empty text)."""
        files = {"image": ("test.jpg", test_image, "image/jpeg")}
        data = {"ingredients": ""}
        
        response = client.post("/recommend_recipe_with_image", files=files, data=data)
        
        assert response.status_code == 200
        
        mock_image_extractor.run.assert_called_once()
        mock_recipe_service.recommend_recipe.assert_called_once_with(
            ingredients="",
            extracted_ingredients="• chicken breast\\n• rice\\n• vegetables"
        )

    @pytest.mark.anyio
    async def test_recommend_recipe_invalid_image_type(self, client):
        """Test recipe recommendation with invalid image file type."""
        files = {"image": ("test.txt", io.BytesIO(b"not an image"), "text/plain")}
        data = {"ingredients": "chicken, rice"}
        
        # Should raise an exception due to invalid image type
        with pytest.raises(Exception):
            response = client.post("/recommend_recipe_with_image", files=files, data=data)

    @pytest.mark.anyio
    async def test_recommend_recipe_missing_ingredients_field_with_image(self, client, test_image):
        """Test recipe recommendation without ingredients field with image."""
        files = {"image": ("test.jpg", test_image, "image/jpeg")}
        
        response = client.post("/recommend_recipe_with_image", files=files)
        
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_recommend_recipe_image_extraction_error(
        self, 
        client, 
        mock_recipe_service,
        test_image
    ):
        """Test recipe recommendation when image extraction fails."""
        with patch("whats_for_dinner.api.recipes.ExtractFoodItemsFromImage") as mock:
            extractor_instance = AsyncMock()
            mock.return_value = extractor_instance
            extractor_instance.run.side_effect = Exception("Image processing error")
            
            files = {"image": ("test.jpg", test_image, "image/jpeg")}
            data = {"ingredients": "chicken, rice"}
            
            # Should raise an exception when image processing fails
            with pytest.raises(Exception):
                response = client.post("/recommend_recipe_with_image", files=files, data=data)

    @pytest.mark.anyio
    async def test_recommend_recipe_large_image(
        self, 
        client, 
        mock_recipe_service, 
        mock_image_extractor
    ):
        """Test recipe recommendation with larger image file."""
        # Create a larger test image
        img = Image.new('RGB', (1000, 1000), color='red')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        
        files = {"image": ("large_test.jpg", buffer, "image/jpeg")}
        data = {"ingredients": "tomatoes, basil"}
        
        response = client.post("/recommend_recipe_with_image", files=files, data=data)
        
        assert response.status_code == 200
        mock_image_extractor.run.assert_called_once()

    @pytest.mark.anyio
    async def test_recommend_recipe_special_characters_ingredients(
        self, 
        client, 
        mock_recipe_service
    ):
        """Test recipe recommendation with special characters in ingredients."""
        data = {"ingredients": "jalapenos, pinon nuts, cafe au lait"}
        
        response = client.post("/recommend_recipe_with_image", data=data)
        
        assert response.status_code == 200
        mock_recipe_service.recommend_recipe.assert_called_once_with(
            ingredients="jalapenos, pinon nuts, cafe au lait",
            extracted_ingredients=None
        )

    @pytest.mark.anyio
    async def test_recommend_recipe_png_image(
        self, 
        client, 
        mock_recipe_service, 
        mock_image_extractor
    ):
        """Test recipe recommendation with PNG image format."""
        img = Image.new('RGBA', (100, 100), color='blue')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        files = {"image": ("test.png", buffer, "image/png")}
        data = {"ingredients": "blueberries, flour"}
        
        response = client.post("/recommend_recipe_with_image", files=files, data=data)
        
        assert response.status_code == 200
        mock_image_extractor.run.assert_called_once()

    @pytest.mark.anyio
    async def test_openapi_schema_available(self, client):
        """Test that OpenAPI schema is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_data = response.json()
        assert "paths" in openapi_data
        assert "/recommend_recipe" in openapi_data["paths"]
        assert "/recommend_recipe_with_image" in openapi_data["paths"]
        
        # Verify both endpoints are POST methods
        assert "post" in openapi_data["paths"]["/recommend_recipe"]
        assert "post" in openapi_data["paths"]["/recommend_recipe_with_image"]