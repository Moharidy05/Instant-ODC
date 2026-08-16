"""Supabase client initialization.

This module provides functions to instantiate and return Supabase clients
for both admin (backend operations) and public (read operations) use cases.
"""
from supabase import create_client
from src.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_ANON_KEY

def get_admin_client():
    """Get Supabase client with service role key for backend operations.
    
    This client has elevated privileges and can bypass Row Level Security (RLS).
    It should only be used in secure backend environments.
    
    Returns:
        Client: An initialized Supabase client with the service role key.
        
    Raises:
        ValueError: If SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY is not configured.
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise ValueError('SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env')
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def get_client():
    """Get Supabase client with anon key for read operations.
    
    This client adheres to Row Level Security (RLS) policies and is suitable
    for public or restricted client-side operations.
    
    Returns:
        Client: An initialized Supabase client with the anon key.
        
    Raises:
        ValueError: If SUPABASE_URL or SUPABASE_ANON_KEY is not configured.
    """
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise ValueError('SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env')
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
