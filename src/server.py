#!/usr/bin/env python3
"""
WordPress MCP Server
MCP server for managing WordPress sites and creating articles
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure unbuffered output for better Windows compatibility
os.environ['PYTHONUNBUFFERED'] = '1'

import asyncio
import json
import logging
from typing import Any, Sequence

try:
    import mcp.types as types
    from mcp.server.models import InitializationOptions
    from mcp.server import NotificationOptions, Server
    from pydantic import AnyUrl
    import mcp.server.stdio
    print("DEBUG: MCP imports successful", file=sys.stderr)
    sys.stderr.flush()
except Exception as e:
    print(f"DEBUG: Failed to import MCP: {e}", file=sys.stderr)
    sys.stderr.flush()
    sys.exit(1)

try:
    from .wordpress_client import WordPressClient
    from .models import WordPressPost, ArticleRequest
except ImportError:
    from wordpress_client import WordPressClient
    from models import WordPressPost, ArticleRequest

# Set up logging to stderr only
logging.basicConfig(
    level=logging.INFO,
    format='%(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("wordpress-mcp-server")

# Create MCP server
server = Server("wordpress-mcp-server")

# WordPress client will be initialized later
wp_client = None

def get_wp_client():
    """Get or create WordPress client instance"""
    global wp_client
    if wp_client is None:
        try:
            # Get the correct path to config file relative to this script
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, '..', 'config', 'wordpress_sites.yaml')
            config_path = os.path.normpath(config_path)
            
            logger.info(f"Loading config from: {config_path}")
            wp_client = WordPressClient(config_path)
            logger.info("WordPress client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize WordPress client: {e}")
            raise
    return wp_client

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List of available tools"""
    return [
        types.Tool(
            name="list_wordpress_sites",
            description="Display list of all available WordPress sites",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="create_wordpress_article", 
            description="Create a new article on a specific WordPress site. Use get_site_categories and get_site_tags to see existing categories and tags before creating the article",
            inputSchema={
                "type": "object",
                "properties": {
                    "site_id": {
                        "type": "string",
                        "description": "Site identifier (use list_wordpress_sites to see the list)"
                    },
                    "title": {
                        "type": "string", 
                        "description": "Article title"
                    },
                    "content": {
                        "type": "string",
                        "description": "Article content (supports HTML)"
                    },
                    "excerpt": {
                        "type": "string",
                        "description": "Article excerpt (optional)"
                    },
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of existing categories on the site (use get_site_categories to see list)"
                    },
                    "tags": {
                        "type": "array", 
                        "items": {"type": "string"},
                        "description": "List of existing tags on the site (use get_site_tags to see list)"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["draft", "publish", "private"],
                        "description": "Article status (default: draft)"
                    },
                    "generate_image": {
                        "type": "boolean",
                        "description": "Whether to automatically generate an image for the article using AI (default: false)"
                    }
                },
                "required": ["site_id", "title", "content"]
            }
        ),
        types.Tool(
            name="test_site_connection",
            description="Test connection to a specific WordPress site",
            inputSchema={
                "type": "object", 
                "properties": {
                    "site_id": {
                        "type": "string",
                        "description": "Site identifier to test"
                    }
                },
                "required": ["site_id"]
            }
        ),
        types.Tool(
            name="get_site_categories",
            description="Display all existing categories on a specific WordPress site",
            inputSchema={
                "type": "object",
                "properties": {
                    "site_id": {
                        "type": "string",
                        "description": "Site identifier"
                    }
                },
                "required": ["site_id"]
            }
        ),
        types.Tool(
            name="get_site_tags",
            description="Display all existing tags on a specific WordPress site",
            inputSchema={
                "type": "object",
                "properties": {
                    "site_id": {
                        "type": "string",
                        "description": "Site identifier"
                    }
                },
                "required": ["site_id"]
            }
        ),
        types.Tool(
            name="create_bulk_articles",
            description="Create articles in bulk across multiple sites",
            inputSchema={
                "type": "object",
                "properties": {
                    "articles": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "site_id": {"type": "string"},
                                "title": {"type": "string"},
                                "content": {"type": "string"},
                                "excerpt": {"type": "string"},
                                "categories": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "tags": {
                                    "type": "array", 
                                    "items": {"type": "string"}
                                },
                                "status": {"type": "string"}
                            },
                            "required": ["site_id", "title", "content"]
                        },
                        "description": "List of articles to create"
                    }
                },
                "required": ["articles"]
            }
        ),
        types.Tool(
            name="create_wordpress_article_with_image",
            description="Create a new article on WordPress site with automatically generated image using ChatGPT 4o (DALL-E). The image is created based on the article title and content",
            inputSchema={
                "type": "object",
                "properties": {
                    "site_id": {
                        "type": "string",
                        "description": "Site identifier (use list_wordpress_sites to see the list)"
                    },
                    "title": {
                        "type": "string", 
                        "description": "Article title"
                    },
                    "content": {
                        "type": "string",
                        "description": "Article content (supports HTML)"
                    },
                    "excerpt": {
                        "type": "string",
                        "description": "Article excerpt (optional)"
                    },
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of existing categories on the site (use get_site_categories to see list)"
                    },
                    "tags": {
                        "type": "array", 
                        "items": {"type": "string"},
                        "description": "List of existing tags on the site (use get_site_tags to see list)"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["draft", "publish", "private"],
                        "description": "Article status (default: draft)"
                    }
                },
                "required": ["site_id", "title", "content"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool calls"""
    
    if arguments is None:
        arguments = {}
    
    try:
        if name == "list_wordpress_sites":
            sites = get_wp_client().get_sites_list()
            sites_text = "\n".join([f"• {site['id']}: {site['name']} ({site['url']})" for site in sites])
            return [types.TextContent(type="text", text=f"Available WordPress sites:\n{sites_text}")]
        
        elif name == "create_wordpress_article":
            site_id = arguments.get("site_id")
            title = arguments.get("title") 
            content = arguments.get("content")
            excerpt = arguments.get("excerpt", "")
            categories = arguments.get("categories", [])
            tags = arguments.get("tags", [])
            status = arguments.get("status", "draft")
            generate_image = arguments.get("generate_image", False)
            
            if not site_id or not title or not content:
                return [types.TextContent(type="text", text="Error: site_id, title, and content are required")]
            
            post = WordPressPost(
                title=title,
                content=content,
                excerpt=excerpt,
                categories=categories,
                tags=tags,
                status=status
            )
            
            if generate_image:
                # Check if image generator is available first
                if not get_wp_client().image_generator:
                    return [types.TextContent(type="text", text="❌ Image generation not available: OpenAI API key not configured or invalid")]
                
                # Use the image generation function
                result = get_wp_client().create_post_with_image(site_id, post, True)
            else:
                # Regular post creation
                result = get_wp_client().create_post(site_id, post)
            
            if result.success:
                response_text = f"✅ {result.message}\n"
                if result.post_id:
                    response_text += f"📄 Post ID: {result.post_id}\n"
                    
                    # Verify featured image was set if image generation was requested
                    if generate_image:
                        try:
                            import requests
                            site = get_wp_client().get_site(site_id)
                            if site:
                                headers = get_wp_client().create_auth_header(site)
                                check_response = requests.get(
                                    f"{site.api_url}/posts/{result.post_id}",
                                    headers=headers,
                                    timeout=30
                                )
                                
                                if check_response.status_code == 200:
                                    post_data = check_response.json()
                                    featured_media_id = post_data.get('featured_media', 0)
                                    
                                    if featured_media_id and featured_media_id != 0:
                                        response_text += f"🖼️ Featured Image: Successfully set (ID: {featured_media_id})\n"
                                    else:
                                        response_text += "⚠️ Featured Image: NOT SET - Image may have failed to upload\n"
                                        response_text += "   Check WordPress logs for upload errors (likely ModSecurity/firewall blocking)\n"
                                else:
                                    response_text += "⚠️ Could not verify featured image status\n"
                        except Exception as e:
                            response_text += f"⚠️ Error verifying featured image: {str(e)}\n"
                
                if result.url:
                    response_text += f"🔗 URL: {result.url}"
                return [types.TextContent(type="text", text=response_text)]
            else:
                # Provide detailed error analysis for image generation failures
                error_msg = result.message
                detailed_error = f"❌ Error: {error_msg}\n\n"
                
                if generate_image:
                    if "406" in error_msg:
                        detailed_error += "🔍 DIAGNOSIS: WordPress server security (ModSecurity) is blocking uploads\n"
                        detailed_error += "💡 SOLUTION: Contact your hosting provider to whitelist WordPress API uploads\n"
                    elif "401" in error_msg or "403" in error_msg:
                        detailed_error += "🔍 DIAGNOSIS: Authentication or permission issues\n"
                        detailed_error += "💡 SOLUTION: Check WordPress credentials and user permissions\n"
                    elif "OpenAI" in error_msg:
                        detailed_error += "🔍 DIAGNOSIS: AI image generation failed\n"
                        detailed_error += "💡 SOLUTION: Check OpenAI API key and account credits\n"
                    elif "upload" in error_msg.lower():
                        detailed_error += "🔍 DIAGNOSIS: Image upload to WordPress failed\n"
                        detailed_error += "💡 SOLUTION: Check WordPress upload permissions and server limits\n"
                    else:
                        detailed_error += "🔍 DIAGNOSIS: General WordPress API error\n"
                        detailed_error += "💡 SOLUTION: Check site configuration and try again\n"
                    
                    detailed_error += f"\n📋 Site: {result.site_name}"
                    return [types.TextContent(type="text", text=detailed_error)]
                else:
                    return [types.TextContent(type="text", text=f"❌ Error: {result.message}")]
        
        elif name == "test_site_connection":
            site_id = arguments.get("site_id")
            if not site_id:
                return [types.TextContent(type="text", text="Error: site_id is required")]
            
            result = get_wp_client().test_site_connection(site_id)
            
            if result["success"]:
                response_text = f"✅ {result['message']}\n"
                response_text += f"📍 Site: {result['site_name']}\n"
                if 'user' in result:
                    response_text += f"👤 Connected as: {result['user']}"
                return [types.TextContent(type="text", text=response_text)]
            else:
                return [types.TextContent(type="text", text=f"❌ {result['message']}")]
        
        elif name == "get_site_categories":
            site_id = arguments.get("site_id")
            if not site_id:
                return [types.TextContent(type="text", text="Error: site_id is required")]
            
            try:
                categories = get_wp_client().get_categories(site_id)
                if categories:
                    categories_text = "\n".join([
                        f"• {cat['name']} (ID: {cat['id']}, Posts: {cat['count']})"
                        for cat in categories
                    ])
                    return [types.TextContent(type="text", text=f"Categories on site {site_id}:\n{categories_text}")]
                else:
                    return [types.TextContent(type="text", text=f"No categories found on site {site_id}")]
            except Exception as e:
                return [types.TextContent(type="text", text=f"Error getting categories: {str(e)}")]
        
        elif name == "get_site_tags":
            site_id = arguments.get("site_id")
            if not site_id:
                return [types.TextContent(type="text", text="Error: site_id is required")]
            
            try:
                tags = get_wp_client().get_tags(site_id)
                if tags:
                    tags_text = "\n".join([
                        f"• {tag['name']} (ID: {tag['id']}, Posts: {tag['count']})"
                        for tag in tags
                    ])
                    return [types.TextContent(type="text", text=f"Tags on site {site_id}:\n{tags_text}")]
                else:
                    return [types.TextContent(type="text", text=f"No tags found on site {site_id}")]
            except Exception as e:
                return [types.TextContent(type="text", text=f"Error getting tags: {str(e)}")]
        
        elif name == "create_bulk_articles":
            articles_data = arguments.get("articles", [])
            if not articles_data:
                return [types.TextContent(type="text", text="Error: articles list is required")]
            
            results = []
            for article_data in articles_data:
                try:
                    post = WordPressPost(
                        title=article_data.get("title"),
                        content=article_data.get("content"),
                        excerpt=article_data.get("excerpt", ""),
                        categories=article_data.get("categories", []),
                        tags=article_data.get("tags", []),
                        status=article_data.get("status", "draft")
                    )
                    
                    result = get_wp_client().create_post(article_data.get("site_id"), post)
                    results.append(f"• {article_data.get('title')}: {'✅' if result.success else '❌'} {result.message}")
                    
                except Exception as e:
                    results.append(f"• {article_data.get('title', 'Unknown')}: ❌ Error: {str(e)}")
            
            results_text = "\n".join(results)
            return [types.TextContent(type="text", text=f"Bulk article creation results:\n{results_text}")]
        
        elif name == "create_wordpress_article_with_image":
            site_id = arguments.get("site_id")
            title = arguments.get("title") 
            content = arguments.get("content")
            excerpt = arguments.get("excerpt", "")
            categories = arguments.get("categories", [])
            tags = arguments.get("tags", [])
            status = arguments.get("status", "draft")
            
            if not site_id or not title or not content:
                return [types.TextContent(type="text", text="Error: site_id, title, and content are required")]
            
            post = WordPressPost(
                title=title,
                content=content,
                excerpt=excerpt,
                categories=categories,
                tags=tags,
                status=status
            )
            
            # Check if image generator is available first
            if not get_wp_client().image_generator:
                return [types.TextContent(type="text", text="❌ Image generation not available: OpenAI API key not configured or invalid")]
            
            # Create article with image
            result = get_wp_client().create_post_with_image(site_id, post, True)
            
            if result.success:
                response_text = f"✅ {result.message}\n"
                if result.post_id:
                    response_text += f"📄 Post ID: {result.post_id}\n"
                    
                    # Verify featured image was actually set
                    try:
                        import requests
                        site = get_wp_client().get_site(site_id)
                        if site:
                            headers = get_wp_client().create_auth_header(site)
                            check_response = requests.get(
                                f"{site.api_url}/posts/{result.post_id}",
                                headers=headers,
                                timeout=30
                            )
                            
                            if check_response.status_code == 200:
                                post_data = check_response.json()
                                featured_media_id = post_data.get('featured_media', 0)
                                
                                if featured_media_id and featured_media_id != 0:
                                    response_text += f"🖼️ Featured Image: Successfully set (ID: {featured_media_id})\n"
                                else:
                                    response_text += "⚠️ Featured Image: NOT SET - Image may have failed to upload\n"
                                    response_text += "   Check WordPress logs for upload errors (likely ModSecurity/firewall blocking)\n"
                            else:
                                response_text += "⚠️ Could not verify featured image status\n"
                    except Exception as e:
                        response_text += f"⚠️ Error verifying featured image: {str(e)}\n"
                
                if result.url:
                    response_text += f"🔗 URL: {result.url}"
                return [types.TextContent(type="text", text=response_text)]
            else:
                # Provide detailed error analysis
                error_msg = result.message
                detailed_error = f"❌ Error: {error_msg}\n\n"
                
                if "406" in error_msg:
                    detailed_error += "🔍 DIAGNOSIS: WordPress server security (ModSecurity) is blocking uploads\n"
                    detailed_error += "💡 SOLUTION: Contact your hosting provider to whitelist WordPress API uploads\n"
                elif "401" in error_msg or "403" in error_msg:
                    detailed_error += "🔍 DIAGNOSIS: Authentication or permission issues\n"
                    detailed_error += "💡 SOLUTION: Check WordPress credentials and user permissions\n"
                elif "OpenAI" in error_msg:
                    detailed_error += "🔍 DIAGNOSIS: AI image generation failed\n"
                    detailed_error += "💡 SOLUTION: Check OpenAI API key and account credits\n"
                elif "upload" in error_msg.lower():
                    detailed_error += "🔍 DIAGNOSIS: Image upload to WordPress failed\n"
                    detailed_error += "💡 SOLUTION: Check WordPress upload permissions and server limits\n"
                else:
                    detailed_error += "🔍 DIAGNOSIS: General WordPress API error\n"
                    detailed_error += "💡 SOLUTION: Check site configuration and try again\n"
                
                detailed_error += f"\n📋 Site: {result.site_name}"
                return [types.TextContent(type="text", text=detailed_error)]
        
        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        logger.error(f"Error in {name}: {e}")
        return [types.TextContent(type="text", text=f"Error creating article with image: {str(e)}")]

async def main():
    """Main function to run the MCP server"""
    try:
        print("DEBUG: Starting main function", file=sys.stderr)
        sys.stderr.flush()
        
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            print("DEBUG: stdio_server created", file=sys.stderr)
            sys.stderr.flush()
            
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="wordpress-mcp-server",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
            print("DEBUG: Server run completed", file=sys.stderr)
            sys.stderr.flush()
    except Exception as e:
        print(f"DEBUG: Error in main: {e}", file=sys.stderr)
        print(f"DEBUG: Error type: {type(e).__name__}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        raise

if __name__ == "__main__":
    asyncio.run(main()) 