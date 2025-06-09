"""
WordPress MCP Server Models
Data models for WordPress operations and API responses
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass

@dataclass
class WordPressSite:
    """WordPress site configuration"""
    id: str
    name: str
    url: str
    api_url: str
    username: str
    password: str

@dataclass
class WordPressPost:
    """WordPress post data"""
    title: str
    content: str
    status: str = "draft"
    excerpt: str = ""
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None

@dataclass
class ArticleResponse:
    """Response from article creation"""
    success: bool
    message: str
    site_name: str
    post_id: Optional[int] = None
    url: Optional[str] = None

class ArticleRequest(BaseModel):
    """בקשה ליצירת מאמר"""
    site_id: str = Field(description="מזהה האתר")
    title: str = Field(description="כותרת המאמר")
    content: str = Field(description="תוכן המאמר")
    excerpt: Optional[str] = Field(default=None, description="תקציר")
    categories: Optional[List[str]] = Field(default=None, description="קטגוריות")
    tags: Optional[List[str]] = Field(default=None, description="תגיות")
    status: str = Field(default="draft", description="סטטוס פרסום")
    seo_title: Optional[str] = Field(default=None, description="כותרת SEO")
    meta_description: Optional[str] = Field(default=None, description="תיאור מטא")

class SiteListResponse(BaseModel):
    """רשימת אתרים"""
    sites: List[Dict[str, str]]
    total_count: int 