import tempfile
from pathlib import Path

from fastapi import UploadFile
from openai import AsyncOpenAI

from whats_for_dinner.core.config import settings

client = AsyncOpenAI(api_key=settings.openai_api_key)


class ImageService:
    """Handles image processing to extract ingredients."""

    async def extract_ingredients_from_image(
        self,
        image_file: UploadFile,
    ) -> str:
        """Extract ingredients from an uploaded image using OpenAI Vision."""
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            content = await image_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # Convert image to base64
            image_base64 = self._image_to_base64(temp_file_path)
            
            # Extract ingredients using OpenAI Vision
            extracted_ingredients = await self._extract_with_openai_vision(image_base64)
            
            return extracted_ingredients
            
        finally:
            # Clean up temporary file
            Path(temp_file_path).unlink(missing_ok=True)

    def _image_to_base64(self, image_path: str) -> str:
        """Convert image file to base64 string."""
        from PIL import Image
        import base64
        import io

        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                byte_arr = io.BytesIO()
                img.save(byte_arr, format='JPEG')
                byte_arr = byte_arr.getvalue()

                return base64.b64encode(byte_arr).decode('utf-8')
        except Exception as e:
            raise ValueError(f"Error processing image: {e}")

    async def _extract_with_openai_vision(self, image_base64: str) -> str:
        """Use OpenAI Vision to extract ingredients from image."""
        
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "List the visible food ingredients as a bullet list. Be specific about the types of ingredients you can identify.",
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

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            stream=False
        )
        
        content = response.choices[0].message.content
        
        if content is None:
            raise ValueError("OpenAI returned empty response for image analysis")
            
        return content