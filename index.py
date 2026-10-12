"""Vercel Flask entry point. Vercel discovers this top-level WSGI app."""
from app import create_app

app = create_app()