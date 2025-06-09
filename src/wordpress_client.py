"""
WordPress Client for MCP Server
Handles WordPress API operations including posts, media, categories, and tags
"""

import requests
import base64
import yaml
import os
import json
import mimetypes
import logging
from typing import List, Dict, Optional, Any

from .models import WordPressSite, WordPressPost, ArticleResponse
from .image_generator import ImageGenerator

logger = logging.getLogger(__name__)

class WordPressClient:
    """WordPress API client with image generation support"""
    
    def __init__(self, config_path: str = "config/wordpress_sites.yaml"):
        """Initialize WordPress client"""
        self.sites = {}
        self.settings = {}
        self.load_config(config_path)
        
        # Initialize image generator
        try:
            self.image_generator = ImageGenerator()
            if self.image_generator.is_available():
                logger.info("Image generator enabled successfully")
            else:
                logger.warning("Image generator not available - missing OpenAI API key")
                self.image_generator = None
        except Exception as e:
            logger.error(f"Failed to initialize image generator: {e}")
            self.image_generator = None
    
    def load_config(self, config_path: str):
        """Load WordPress sites configuration"""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                
                # Load settings
                self.settings = config.get('settings', {})
                
                # Load sites
                sites_config = config.get('sites', [])
                for site_config in sites_config:
                    site = WordPressSite(
                        id=site_config['id'],
                        name=site_config['name'],
                        url=site_config['url'],
                        api_url=f"{site_config['url'].rstrip('/')}/wp-json/wp/v2",
                        username=site_config['username'],
                        password=site_config['password']
                    )
                    self.sites[site.id] = site
                
                logger.info(f"Loaded {len(self.sites)} WordPress sites")
                
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise
    
    def get_sites_list(self) -> List[Dict[str, str]]:
        """Get list of available sites"""
        return [{"id": site.id, "name": site.name, "url": site.url} 
                for site in self.sites.values()]
    
    def get_site(self, site_id: str) -> Optional[WordPressSite]:
        """Get site configuration by ID"""
        return self.sites.get(site_id)
    
    def create_auth_header(self, site: WordPressSite) -> Dict[str, str]:
        """Create authentication header for WordPress API"""
        credentials = f"{site.username}:{site.password}"
        token = base64.b64encode(credentials.encode()).decode()
        return {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json"
        }
    
    def create_post(self, site_id: str, post: WordPressPost) -> ArticleResponse:
        """Create a WordPress post"""
        site = self.get_site(site_id)
        if not site:
            return ArticleResponse(
                success=False,
                message=f"Site with ID {site_id} not found",
                site_name="Unknown"
            )
        
        try:
            # Prepare post data
            post_data = {
                "title": post.title,
                "content": post.content,
                "status": post.status or self.settings.get('default_post_status', 'draft'),
                "excerpt": post.excerpt or "",
                "format": self.settings.get('default_post_format', 'standard')
            }
            
            # Add categories if provided
            if post.categories:
                categories = self._get_or_create_categories(site, post.categories)
                if categories:
                    post_data["categories"] = categories
            
            # Add tags if provided
            if post.tags:
                tags = self._get_or_create_tags(site, post.tags)
                if tags:
                    post_data["tags"] = tags
            
            # Create post
            headers = self.create_auth_header(site)
            response = requests.post(
                f"{site.api_url}/posts",
                json=post_data,
                headers=headers,
                timeout=self.settings.get('timeout', 30)
            )
            
            if response.status_code == 201:
                post_info = response.json()
                return ArticleResponse(
                    success=True,
                    post_id=post_info.get('id'),
                    url=post_info.get('link'),
                    message=f"Article created successfully on {site.name}",
                    site_name=site.name
                )
            else:
                logger.error(f"Error creating post: {response.status_code} - {response.text}")
                return ArticleResponse(
                    success=False,
                    message=f"Error creating article: {response.text}",
                    site_name=site.name
                )
                
        except Exception as e:
            logger.error(f"Error creating post on site {site.name}: {e}")
            return ArticleResponse(
                success=False,
                message=f"Error creating article: {str(e)}",
                site_name=site.name
            )
    
    def _get_or_create_categories(self, site: WordPressSite, category_names: List[str]) -> List[int]:
        """Get or create categories and return their IDs"""
        category_ids = []
        headers = self.create_auth_header(site)
        
        for category_name in category_names:
            try:
                # Search for existing category
                search_response = requests.get(
                    f"{site.api_url}/categories",
                    params={"search": category_name, "per_page": 10},
                    headers=headers,
                    timeout=self.settings.get('timeout', 30)
                )
                
                if search_response.status_code == 200:
                    categories = search_response.json()
                    
                    # Check for exact match
                    exact_match = None
                    for cat in categories:
                        if cat.get('name', '').lower() == category_name.lower():
                            exact_match = cat
                            break
                    
                    if exact_match:
                        category_ids.append(exact_match['id'])
                        logger.info(f"Found existing category: {category_name} (ID: {exact_match['id']})")
                    else:
                        # Create new category
                        create_response = requests.post(
                            f"{site.api_url}/categories",
                            json={"name": category_name},
                            headers=headers,
                            timeout=self.settings.get('timeout', 30)
                        )
                        
                        if create_response.status_code == 201:
                            new_category = create_response.json()
                            category_ids.append(new_category['id'])
                            logger.info(f"Created new category: {category_name} (ID: {new_category['id']})")
                        else:
                            logger.warning(f"Failed to create category {category_name}: {create_response.text}")
                
            except Exception as e:
                logger.error(f"Error processing category {category_name}: {e}")
        
        return category_ids
    
    def _get_or_create_tags(self, site: WordPressSite, tag_names: List[str]) -> List[int]:
        """Get or create tags and return their IDs"""
        tag_ids = []
        headers = self.create_auth_header(site)
        
        for tag_name in tag_names:
            try:
                # Search for existing tag
                search_response = requests.get(
                    f"{site.api_url}/tags",
                    params={"search": tag_name, "per_page": 10},
                    headers=headers,
                    timeout=self.settings.get('timeout', 30)
                )
                
                if search_response.status_code == 200:
                    tags = search_response.json()
                    
                    # Check for exact match
                    exact_match = None
                    for tag in tags:
                        if tag.get('name', '').lower() == tag_name.lower():
                            exact_match = tag
                            break
                    
                    if exact_match:
                        tag_ids.append(exact_match['id'])
                        logger.info(f"Found existing tag: {tag_name} (ID: {exact_match['id']})")
                    else:
                        # Create new tag
                        create_response = requests.post(
                            f"{site.api_url}/tags",
                            json={"name": tag_name},
                            headers=headers,
                            timeout=self.settings.get('timeout', 30)
                        )
                        
                        if create_response.status_code == 201:
                            new_tag = create_response.json()
                            tag_ids.append(new_tag['id'])
                            logger.info(f"Created new tag: {tag_name} (ID: {new_tag['id']})")
                        else:
                            logger.warning(f"Failed to create tag {tag_name}: {create_response.text}")
                
            except Exception as e:
                logger.error(f"Error processing tag {tag_name}: {e}")
        
        return tag_ids
    
    def test_site_connection(self, site_id: str) -> Dict[str, any]:
        """Test connection to WordPress site"""
        site = self.get_site(site_id)
        if not site:
            return {
                "success": False,
                "message": f"Site with ID {site_id} not found",
                "site_name": "Unknown"
            }
        
        try:
            headers = self.create_auth_header(site)
            response = requests.get(
                f"{site.api_url}/users/me",
                headers=headers,
                timeout=self.settings.get('timeout', 30)
            )
            
            if response.status_code == 200:
                user_info = response.json()
                return {
                    "success": True,
                    "message": f"Successfully connected to {site.name}",
                    "site_name": site.name,
                    "user": user_info.get('name', 'Unknown'),
                    "user_id": user_info.get('id'),
                    "capabilities": user_info.get('capabilities', {})
                }
            else:
                return {
                    "success": False,
                    "message": f"Connection failed: {response.status_code} - {response.text}",
                    "site_name": site.name
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection error: {str(e)}",
                "site_name": site.name
            }
    
    def get_categories(self, site_id: str) -> List[Dict[str, any]]:
        """Get categories from WordPress site"""
        site = self.get_site(site_id)
        if not site:
            raise ValueError(f"Site with ID {site_id} not found")
        
        try:
            headers = self.create_auth_header(site)
            response = requests.get(
                f"{site.api_url}/categories",
                params={"per_page": 100, "orderby": "name", "order": "asc"},
                headers=headers,
                timeout=self.settings.get('timeout', 30)
            )
            
            if response.status_code == 200:
                categories = response.json()
                return [
                    {
                        "id": cat.get('id'),
                        "name": cat.get('name'),
                        "slug": cat.get('slug'),
                        "description": cat.get('description', ''),
                        "count": cat.get('count', 0)
                    }
                    for cat in categories
                ]
            else:
                logger.error(f"Error getting categories from site {site.name}: {response.text}")
                raise Exception(f"API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error getting categories from site {site.name}: {e}")
            raise
    
    def get_tags(self, site_id: str) -> List[Dict[str, any]]:
        """Get tags from WordPress site"""
        site = self.get_site(site_id)
        if not site:
            raise ValueError(f"Site with ID {site_id} not found")
        
        try:
            headers = self.create_auth_header(site)
            response = requests.get(
                f"{site.api_url}/tags",
                params={"per_page": 100, "orderby": "name", "order": "asc"},
                headers=headers,
                timeout=self.settings.get('timeout', 30)
            )
            
            if response.status_code == 200:
                tags = response.json()
                return [
                    {
                        "id": tag.get('id'),
                        "name": tag.get('name'),
                        "slug": tag.get('slug'),
                        "description": tag.get('description', ''),
                        "count": tag.get('count', 0)
                    }
                    for tag in tags
                ]
            else:
                logger.error(f"Error getting tags from site {site.name}: {response.text}")
                raise Exception(f"API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error getting tags from site {site.name}: {e}")
            raise
    
    def upload_image(self, site_id: str, image_path: str, title: str = None, alt_text: str = None) -> Optional[Dict[str, Any]]:
        """Upload image to WordPress media library"""
        site = self.get_site(site_id)
        if not site:
            logger.error(f"Site {site_id} not found")
            return None
        
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return None
        
        try:
            # Determine media type
            mime_type, _ = mimetypes.guess_type(image_path)
            if not mime_type or not mime_type.startswith('image/'):
                logger.error(f"File not recognized as image: {image_path}")
                return None
            
            # Read file
            with open(image_path, 'rb') as f:
                file_data = f.read()
            
            # Prepare upload data
            filename = os.path.basename(image_path)
            
            # Clean and shorten the title if it's too long
            if title:
                # Remove HTML tags and clean the title
                import re
                clean_title = re.sub(r'<[^>]+>', '', title)
                clean_title = re.sub(r'[^\w\s\-]', '', clean_title)
                clean_title = re.sub(r'\s+', ' ', clean_title).strip()
                
                # Shorten if too long (max 50 characters for compatibility)
                if len(clean_title) > 50:
                    clean_title = clean_title[:47] + "..."
                
                # Use cleaned title or fallback to filename
                upload_title = clean_title if clean_title else os.path.splitext(filename)[0]
            else:
                upload_title = os.path.splitext(filename)[0]
            
            # Create short alt text
            short_alt_text = alt_text if alt_text else upload_title
            if len(short_alt_text) > 50:
                short_alt_text = short_alt_text[:47] + "..."
            
            logger.info(f"📝 Upload title: '{upload_title}' (original: '{title}')")
            logger.info(f"📄 Filename: '{filename}'")
            
            # Create upload request
            files = {
                'file': (filename, file_data, mime_type)
            }
            
            headers = self.create_auth_header(site)
            # Remove Content-Type so requests sets it automatically for multipart
            headers.pop('Content-Type', None)
            
            data = {
                'title': upload_title,
                'alt_text': short_alt_text,
                'caption': upload_title
            }
            
            # Upload image
            response = requests.post(
                f"{site.api_url}/media",
                files=files,
                data=data,
                headers=headers,
                timeout=self.settings.get('timeout', 60)
            )
            
            if response.status_code == 201:
                media_info = response.json()
                media_id = media_info.get("id")
                logger.info(f"✅ Image uploaded successfully to site {site.name}")
                logger.info(f"🆔 Image ID: {media_id}")
                logger.info(f"🔗 URL: {media_info.get('source_url')}")
                logger.info(f"📋 Full media data: {json.dumps(media_info, indent=2)}")
                
                return {
                    "id": media_id,
                    "url": media_info.get("source_url"),
                    "title": media_info.get("title", {}).get("rendered"),
                    "alt_text": media_info.get("alt_text"),
                    "caption": media_info.get("caption", {}).get("rendered"),
                    "filename": filename,
                    "mime_type": mime_type
                }
            else:
                logger.error(f"Error uploading image: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error uploading image to site {site.name}: {e}")
            return None
    
    def create_post_with_image(self, site_id: str, post: WordPressPost, generate_image: bool = True) -> ArticleResponse:
        """Create article with automatically generated image"""
        featured_image_id = None
        temp_image_path = None
        
        try:
            # Generate image if requested and image generator is available
            if generate_image and self.image_generator:
                logger.info("🎨 Starting image generation process for article...")
                logger.info(f"📝 Article title: {post.title}")
                
                image_result = self.image_generator.generate_and_download_image(
                    post.title, 
                    post.content
                )
                
                if image_result:
                    temp_image_path = image_result["local_path"]
                    logger.info(f"✅ Image created and saved temporarily at: {temp_image_path}")
                    
                    # Upload image to WordPress using shortened title
                    logger.info(f"📤 Uploading image to site {site_id}...")
                    
                    # Use the short_title from image generator if available, otherwise create one
                    upload_title = image_result.get("short_title", f"Article Image")
                    
                    upload_result = self.upload_image(
                        site_id, 
                        temp_image_path, 
                        title=upload_title,
                        alt_text=upload_title
                    )
                    
                    if upload_result:
                        featured_image_id = upload_result["id"]
                        logger.info(f"✅ Image uploaded successfully to WordPress!")
                        logger.info(f"🆔 Image ID: {featured_image_id}")
                        logger.info(f"🔗 Image URL: {upload_result['url']}")
                        
                        # Verify image exists in media library
                        if self._verify_media_exists(site_id, featured_image_id):
                            logger.info(f"✅ Image verified in media library")
                        else:
                            logger.warning(f"⚠️  Image not found in media library, canceling featured image setting")
                            featured_image_id = None
                    else:
                        logger.error("❌ Image upload to WordPress failed")
                else:
                    logger.error("❌ Image generation failed")
            elif generate_image and not self.image_generator:
                logger.warning("⚠️  Image generation requested but image generator not available (missing OpenAI API key?)")
            else:
                logger.info("ℹ️  No image generation requested for this article")
            
            # Create article with featured image
            result = self._create_post_internal(site_id, post, featured_image_id)
            
            # Verify and fix featured image if needed
            if featured_image_id and result.success and result.post_id:
                logger.info("🔍 Checking if featured image was set correctly...")
                
                # Check if image was actually set
                site = self.get_site(site_id)
                if site:
                    try:
                        headers = self.create_auth_header(site)
                        check_response = requests.get(
                            f"{site.api_url}/posts/{result.post_id}",
                            headers=headers,
                            timeout=self.settings.get('timeout', 30)
                        )
                        
                        if check_response.status_code == 200:
                            post_data = check_response.json()
                            current_featured = post_data.get('featured_media', 0)
                            
                            if current_featured == featured_image_id:
                                logger.info(f"✅ Featured image set correctly: {current_featured}")
                            else:
                                logger.warning(f"⚠️  Featured image not set, trying again...")
                                
                                # Try to set featured image again
                                update_data = {"featured_media": featured_image_id}
                                update_response = requests.post(
                                    f"{site.api_url}/posts/{result.post_id}",
                                    json=update_data,
                                    headers=headers,
                                    timeout=self.settings.get('timeout', 30)
                                )
                                
                                if update_response.status_code == 200:
                                    updated_post = update_response.json()
                                    new_featured = updated_post.get('featured_media', 0)
                                    if new_featured == featured_image_id:
                                        logger.info(f"✅ Featured image set on second attempt!")
                                    else:
                                        logger.error(f"❌ Featured image still not set: {new_featured}")
                                else:
                                    logger.error(f"❌ Error updating featured image: {update_response.text}")
                    except Exception as e:
                        logger.error(f"Error checking featured image: {e}")
            
            # Add image info to result
            if featured_image_id and result.success:
                result.message += f" with featured image (ID: {featured_image_id})"
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating article with image: {e}")
            return ArticleResponse(
                success=False,
                message=f"Error creating article with image: {str(e)}",
                site_name=self.sites.get(site_id, {}).get("name", "Unknown")
            )
        finally:
            # Clean up temporary file
            if temp_image_path and self.image_generator:
                self.image_generator.cleanup_temp_file(temp_image_path)
    
    def _verify_media_exists(self, site_id: str, media_id: int) -> bool:
        """Check if image exists in media library"""
        site = self.get_site(site_id)
        if not site:
            return False
        
        try:
            headers = self.create_auth_header(site)
            response = requests.get(
                f"{site.api_url}/media/{media_id}",
                headers=headers,
                timeout=self.settings.get('timeout', 30)
            )
            
            if response.status_code == 200:
                media_info = response.json()
                logger.info(f"📋 Image info: {media_info.get('title', {}).get('rendered', 'No title')}")
                return True
            else:
                logger.warning(f"⚠️  Image {media_id} not found: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying image: {e}")
            return False
    
    def _create_post_internal(self, site_id: str, post: WordPressPost, featured_image_id: Optional[int] = None) -> ArticleResponse:
        """Internal function to create post"""
        site = self.get_site(site_id)
        if not site:
            return ArticleResponse(
                success=False,
                message=f"Site with ID {site_id} not found",
                site_name="Unknown"
            )
        
        try:
            # Prepare post data
            post_data = {
                "title": post.title,
                "content": post.content,
                "status": post.status or self.settings.get('default_post_status', 'draft'),
                "excerpt": post.excerpt or "",
                "format": self.settings.get('default_post_format', 'standard')
            }
            
            # Add featured image if provided
            if featured_image_id:
                # Ensure ID is integer
                try:
                    featured_image_id = int(featured_image_id)
                    post_data["featured_media"] = featured_image_id
                    logger.info(f"🖼️  Setting featured image for article - ID: {featured_image_id}")
                except (ValueError, TypeError):
                    logger.error(f"❌ Invalid image ID: {featured_image_id}")
            else:
                logger.info("📄 Creating article without featured image")
            
            # Add categories if provided
            if post.categories:
                categories = self._get_or_create_categories(site, post.categories)
                if categories:
                    post_data["categories"] = categories
            
            # Add tags if provided
            if post.tags:
                tags = self._get_or_create_tags(site, post.tags)
                if tags:
                    post_data["tags"] = tags
            
            # Create post
            logger.info(f"📝 Sending request to create article on site {site.name}...")
            logger.info(f"📊 Article data includes: {list(post_data.keys())}")
            if featured_image_id:
                logger.info(f"🖼️  Including featured image with ID: {featured_image_id}")
            
            headers = self.create_auth_header(site)
            response = requests.post(
                f"{site.api_url}/posts",
                json=post_data,
                headers=headers,
                timeout=self.settings.get('timeout', 30)
            )
            
            logger.info(f"📡 Server response: {response.status_code}")
            if response.status_code != 201:
                logger.error(f"❌ Response error: {response.text}")
            
            if response.status_code == 201:
                post_info = response.json()
                logger.info(f"✅ Article created successfully - ID: {post_info.get('id')}")
                
                # Check if featured image was set
                if 'featured_media' in post_info and post_info['featured_media']:
                    logger.info(f"🖼️  Featured image set in WordPress - ID: {post_info['featured_media']}")
                elif featured_image_id:
                    logger.warning(f"⚠️  Featured image not set despite sending ID: {featured_image_id}")
                else:
                    logger.info("📄 Article created without featured image (as requested)")
                
                return ArticleResponse(
                    success=True,
                    post_id=post_info.get('id'),
                    url=post_info.get('link'),
                    message=f"Article created successfully on {site.name}",
                    site_name=site.name
                )
            else:
                logger.error(f"❌ Error creating article: {response.status_code} - {response.text}")
                return ArticleResponse(
                    success=False,
                    message=f"Error creating article: {response.text}",
                    site_name=site.name
                )
                
        except Exception as e:
            logger.error(f"Error creating article on site {site.name}: {e}")
            return ArticleResponse(
                success=False,
                message=f"Error creating article: {str(e)}",
                site_name=site.name
            ) 