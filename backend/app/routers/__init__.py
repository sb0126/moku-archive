"""Router package — re-export all router modules."""

from app.routers import admin, articles, comments, config, inquiries, posts

__all__ = ["admin", "articles", "comments", "config", "inquiries", "posts"]
