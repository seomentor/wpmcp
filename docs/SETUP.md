# Setup Guide

## Quick Start

1. **Clone the repository**
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Configure WordPress sites** in `config/wordpress_sites.yaml`
4. **Set up OpenAI API key** in `.env` file (optional, for images)
5. **Configure Claude Desktop** with the MCP server
6. **Start using** in Claude Desktop!

## Detailed Setup

### WordPress Configuration

1. **Create Application Password**:
   - Go to WordPress Admin → Users → Your Profile
   - Scroll to "Application Passwords"
   - Enter a name (e.g., "MCP Server")
   - Click "Add New Application Password"
   - Copy the generated password

2. **Edit config/wordpress_sites.yaml**:
   ```yaml
   sites:
     - id: "myblog"
       name: "My WordPress Blog"
       url: "https://myblog.com"
       username: "your-username"
       password: "xxxx xxxx xxxx xxxx xxxx xxxx"
   ```

### OpenAI Setup (For Image Generation)

1. **Get API Key**:
   - Sign up at https://platform.openai.com
   - Go to API Keys section
   - Create new secret key

2. **Create .env file**:
   ```
   OPENAI_API_KEY=sk-...your-key-here...
   ```

### Claude Desktop Configuration

Add to your Claude Desktop config:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "wordpress": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "C:/path/to/wordpress-mcp-server"
    }
  }
}
```

## Troubleshooting

### Common Issues

- **"Server disconnected"**: Check Python path and installation
- **"Authentication failed"**: Verify WordPress credentials
- **"Image generation failed"**: Check OpenAI API key and credits

### Testing Connection

In Claude Desktop, try:
```
"Test connection to [your-site-id]"
```

This will verify your configuration is correct. 