# Troubleshooting Guide

## OpenAI API Key Issues

### Problem: "Image generation not available: OpenAI API key not configured or invalid"

This is one of the most common issues. Here are the possible causes and solutions:

#### 1. Conflicting Environment Variables

**Symptom:** You have a `.env` file with your API key, but the server doesn't recognize it.

**Cause:** A different `OPENAI_API_KEY` is set in your system environment variables, which overrides the one in `.env`.

**Solution:**

Option A: Remove the system environment variable
- **Windows:** 
  ```powershell
  [System.Environment]::SetEnvironmentVariable("OPENAI_API_KEY", $null, "User")
  ```
  Then restart your computer or terminal.

- **Mac/Linux:**
  Remove the line `export OPENAI_API_KEY=...` from your `~/.bashrc`, `~/.zshrc`, or `~/.bash_profile`

Option B: Add the API key directly to Claude Desktop config:
```json
{
  "mcpServers": {
    "wordpress": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "C:/path/to/wordpress-mcp-server",
      "env": {
        "OPENAI_API_KEY": "your-correct-api-key-here"
      }
    }
  }
}
```

#### 2. Invalid API Key

**Symptom:** The API key is loaded but OpenAI returns an error.

**Solution:**
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Make sure your account has credits
4. Update your `.env` file or Claude config

#### 3. Line Break in API Key

**Symptom:** The API key appears split across multiple lines when you check it.

**Solution:** Make sure the entire API key is on one line in your `.env` file:
```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Running the Diagnostic Tool

Before troubleshooting, run:
```bash
python scripts/diagnose.py
```

This will help identify:
- Missing dependencies
- Configuration issues
- API key conflicts
- Connection problems

## Common Error Messages

### "Server disconnected"
1. Check if Python is in your PATH
2. Verify the path in Claude Desktop config is correct
3. Look for error messages in the terminal

### "Authentication failed"
1. Regenerate your WordPress application password
2. Ensure you're using the username (not email)
3. Check that the site URL includes `https://`

### "Failed to upload image"
1. Check WordPress upload permissions
2. Verify the user has `upload_files` capability
3. Check if ModSecurity is blocking uploads (contact hosting provider)

## Need More Help?

1. Run the diagnostic script
2. Check the logs in your terminal
3. Open an issue on GitHub with the diagnostic output 
