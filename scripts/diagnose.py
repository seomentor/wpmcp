#!/usr/bin/env python3
"""
Diagnostic script for WordPress MCP Server
Helps identify common configuration issues
"""

import os
import sys
import yaml
from pathlib import Path

print("=== WordPress MCP Server Diagnostics ===\n")

# Check Python version
print("1. Python Version:")
print(f"   {sys.version}")
if sys.version_info < (3, 8):
    print("   ❌ Python 3.8+ required!")
else:
    print("   ✅ Python version OK")

# Check if running from correct directory
print("\n2. Working Directory:")
print(f"   {os.getcwd()}")
if os.path.exists("src/server.py"):
    print("   ✅ Running from correct directory")
else:
    print("   ❌ Not running from project root directory!")

# Check dependencies
print("\n3. Dependencies:")
try:
    import mcp
    print("   ✅ MCP package installed")
except ImportError:
    print("   ❌ MCP package not installed! Run: pip install -r requirements.txt")

try:
    import openai
    print("   ✅ OpenAI package installed")
except ImportError:
    print("   ❌ OpenAI package not installed! Run: pip install openai")

try:
    from dotenv import load_dotenv
    print("   ✅ python-dotenv installed")
except ImportError:
    print("   ❌ python-dotenv not installed! Run: pip install python-dotenv")

# Check configuration
print("\n4. Configuration:")
config_path = Path("config/wordpress_sites.yaml")
if config_path.exists():
    print("   ✅ wordpress_sites.yaml found")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            sites = config.get('sites', [])
            print(f"   📋 {len(sites)} site(s) configured")
    except Exception as e:
        print(f"   ❌ Error reading config: {e}")
else:
    print("   ❌ wordpress_sites.yaml not found!")

# Check environment variables
print("\n5. Environment Variables:")

# Check .env file
env_file = Path(".env")
if env_file.exists():
    print("   ✅ .env file found")
    from dotenv import load_dotenv
    load_dotenv()
else:
    print("   ⚠️  .env file not found (optional if using Claude config)")

# Check OPENAI_API_KEY
print("\n6. OpenAI API Key:")
env_key = os.environ.get('OPENAI_API_KEY')
dotenv_key = None

if env_file.exists():
    # Load .env and check
    from dotenv import dotenv_values
    env_values = dotenv_values(".env")
    dotenv_key = env_values.get('OPENAI_API_KEY')

if env_key and dotenv_key and env_key != dotenv_key:
    print("   ⚠️  WARNING: Different API keys found!")
    print(f"   System env: {env_key[:15]}...")
    print(f"   .env file:  {dotenv_key[:15]}...")
    print("   💡 The system environment variable will override .env!")
    print("   💡 Consider removing system env variable or using Claude config")
elif env_key:
    print(f"   ✅ API key found in environment: {env_key[:15]}...")
elif dotenv_key:
    print(f"   ✅ API key found in .env: {dotenv_key[:15]}...")
else:
    print("   ❌ No OpenAI API key found!")
    print("   💡 Add to .env file or Claude Desktop config")

# Test OpenAI connection
if env_key or dotenv_key:
    print("\n7. Testing OpenAI Connection:")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=env_key or dotenv_key)
        models = client.models.list()
        print("   ✅ Successfully connected to OpenAI!")
    except Exception as e:
        print(f"   ❌ Failed to connect to OpenAI: {e}")
        print("   💡 Check if your API key is valid and has credits")

# Provide recommendations
print("\n=== Recommendations ===")
if env_key and dotenv_key and env_key != dotenv_key:
    print("• You have conflicting API keys. Either:")
    print("  1. Remove OPENAI_API_KEY from system environment variables")
    print("  2. Add the API key directly to Claude Desktop config")
    print("  3. Ensure both keys are the same and valid")

print("\n✨ Diagnosis complete!") 
