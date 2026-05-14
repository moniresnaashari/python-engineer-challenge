from haystack import component
from PIL import Image

import base64
import io
import tempfile
from pathlib import Path

from fastapi import UploadFile
from openai import AsyncOpenAI

from whats_for_dinner.core.config import settings

@component()
class ExtractFoodItemsFromImage:
    """Extracts food ingredients visible in a given image"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    @component.output_types(answer=str)
    async def run(
        self,
        image_path: str | None = None,
        image_file: UploadFile | None = None,
    ) -> dict[str, str]:
        """Extract ingredients from image path or uploaded file."""
        
        if image_file is not None:
            # Handle uploaded file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                content = await image_file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                image_base64 = self.image_to_base64(temp_file_path)
                result = await self._extract_ingredients(image_base64)
                return {"answer": result}
            finally:
                Path(temp_file_path).unlink(missing_ok=True)
                
        elif image_path is not None:
            # Handle file path
            image_base64 = self.image_to_base64(image_path)
            result = await self._extract_ingredients(image_base64)
            return {"answer": result}
        else:
            raise ValueError("Either image_path or image_file must be provided")

    async def _extract_ingredients(self, image_base64: str) -> str:
        """Extract ingredients using OpenAI Vision API."""
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "List the visible food ingredients as a bullet list. Be specific about the types of ingredients you can identify."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}",
                            "detail": "high",
                        },
                    }
                ],
            },
        ]

        response = await self.client.chat.completions.create(
            model="gpt-4o", 
            messages=messages, 
            stream=False
        )
        content = response.choices[0].message.content
        
        if content is None:
            raise ValueError("OpenAI returned empty response for image analysis")
            
        return content

    def image_to_base64(self, image_path: str) -> str:
        """
        Load an image from the given path and convert it to a base64 string.
        Supports various formats including WEBP, PNG, and JPEG.
        """
        try:
            # Open the image using PIL
            with Image.open(image_path) as img:
                # Convert to RGB if it's not already (e.g., for PNG with transparency)
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # Create a byte stream
                byte_arr = io.BytesIO()
                # Save as JPEG to the byte stream
                img.save(byte_arr, format='JPEG')
                # Get the byte string
                byte_arr = byte_arr.getvalue()

                # Encode to base64
                return base64.b64encode(byte_arr).decode('utf-8')
        except Exception as e:
            print(f"Error processing image: {e}")
            return None