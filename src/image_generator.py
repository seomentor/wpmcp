"""
Image Generator for WordPress Articles
Uses OpenAI DALL-E 3 to generate images for articles
"""

import os
import tempfile
import logging
import re
import hashlib
from typing import Dict, Optional
import requests
from openai import OpenAI

logger = logging.getLogger(__name__)

class ImageGenerator:
    """Image generator using OpenAI DALL-E 3"""
    
    def __init__(self):
        """Initialize the image generator"""
        self.client = None
        self.temp_dir = tempfile.gettempdir()
        
        # Initialize OpenAI client if API key is available
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            try:
                self.client = OpenAI(api_key=api_key)
                logger.info("Image generator initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
        else:
            logger.warning("OPENAI_API_KEY not found - image generation disabled")
    
    def is_available(self) -> bool:
        """Check if image generation is available"""
        return self.client is not None
    
    def clean_filename_string(self, text: str, max_length: int = 50) -> str:
        """Clean and shorten a string for use in filenames or titles"""
        if not text:
            return "image"
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Keep only alphanumeric characters, spaces, hyphens, and underscores
        text = re.sub(r'[^\w\s\-]', '', text)
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Replace spaces with underscores for filenames
        text = text.replace(' ', '_')
        
        # Convert to lowercase
        text = text.lower().strip()
        
        # Truncate to max length
        if len(text) > max_length:
            text = text[:max_length].rstrip('_')
        
        # Ensure it's not empty
        if not text:
            text = "image"
        
        return text
    
    def generate_short_filename(self, title: str) -> str:
        """Generate a short, clean filename based on the title"""
        # Clean the title for filename use
        clean_title = self.clean_filename_string(title, max_length=15)
        
        # Create a short hash for uniqueness
        title_hash = hashlib.md5(title.encode()).hexdigest()[:6]
        
        # Combine into a short filename
        filename = f"{clean_title}_{title_hash}.png"
        
        # Ensure total length is reasonable (max 30 characters)
        if len(filename) > 30:
            filename = f"img_{title_hash}.png"
        
        logger.info(f"Generated filename: {filename} (from title: {title[:50]}...)")
        return filename
    
    def create_prompt(self, title: str, content: str) -> str:
        """Create a prompt for image generation based on article content"""
        # Extract key themes from title and content
        combined_text = f"{title}. {content}"
        
        # Clean HTML tags from content
        clean_content = re.sub(r'<[^>]+>', '', combined_text)
        
        # Create a focused prompt
        prompt = f"""Create a professional, high-quality image for an article titled "{title}".
        
        The image should be:
        - Clean and modern
        - Relevant to the topic
        - Suitable for a blog article
        - Professional looking
        - Without any text overlays
        
        Style: Modern, clean, professional illustration or photography
        """
        
        return prompt
    
    def generate_and_download_image(self, title: str, content: str) -> Optional[Dict[str, str]]:
        """Generate and download an image for the article"""
        if not self.is_available():
            logger.warning("Image generator not available")
            return None
        
        try:
            # Create prompt
            prompt = self.create_prompt(title, content)
            logger.info(f"Generating image with prompt: {prompt[:100]}...")
            
            # Generate image using DALL-E 3
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            
            # Get image URL
            image_url = response.data[0].url
            logger.info(f"Image generated successfully: {image_url}")
            
            # Download image
            image_response = requests.get(image_url, timeout=60)
            image_response.raise_for_status()
            
            # Generate short, clean filename
            filename = self.generate_short_filename(title)
            temp_path = os.path.join(self.temp_dir, filename)
            
            with open(temp_path, 'wb') as f:
                f.write(image_response.content)
            
            logger.info(f"Image downloaded and saved to: {temp_path}")
            
            # Also create a shortened title for upload
            short_title = self.clean_filename_string(title, max_length=30).replace('_', ' ').title()
            
            return {
                "url": image_url,
                "local_path": temp_path,
                "filename": filename,
                "title": title,
                "short_title": short_title  # Add shortened title for upload
            }
            
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return None
    
    def cleanup_temp_file(self, file_path: str) -> bool:
        """Clean up temporary image file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Temporary file cleaned up: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error cleaning up temporary file {file_path}: {e}")
            return False 