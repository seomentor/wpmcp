# WordPress MCP Server 🚀

[![MCP](https://img.shields.io/badge/MCP-1.0-blue.svg)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Model Context Protocol (MCP) server that enables AI assistants to manage WordPress sites and create content with AI-generated featured images.

![WordPress + AI = Magic](https://img.shields.io/badge/WordPress-AI%20Powered-21759B?style=for-the-badge&logo=wordpress&logoColor=white)

## ✨ Features

- **🌐 Multi-Site Management** - Control multiple WordPress sites from a single interface
- **🤖 AI-Powered Content** - Create articles with automatic featured image generation using DALL-E 3
- **📝 Smart Publishing** - Full control over categories, tags, and post status
- **🔐 Secure Authentication** - Uses WordPress Application Passwords for API access
- **🌍 International Support** - Full Unicode support for Hebrew, Arabic, and other languages
- **⚡ Bulk Operations** - Create multiple articles across different sites efficiently

## 🎯 Use Cases

- **Content Agencies** - Manage multiple client WordPress sites from one place
- **Blog Networks** - Publish content across multiple blogs simultaneously
- **AI-Assisted Writing** - Let AI help create content with relevant images
- **Multilingual Publishing** - Create content in any language with proper support

## 📋 Prerequisites

- Python 3.8 or higher
- Claude Desktop (or any MCP-compatible client)
- WordPress sites with REST API enabled
- OpenAI API key (for image generation)

## 🚀 Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/seomentor/wpmcp.git
cd wpmcp
pip install -r requirements.txt
```

### 2. Configure WordPress Sites

Edit `config/wordpress_sites.yaml`:

```yaml
sites:
  - id: "site1"
    name: "My WordPress Blog"
    url: "https://myblog.com"
    username: "your-username"
    password: "your-app-password"
```

### 3. Set Up OpenAI (Optional, for images)

Create a `.env` file:
```
OPENAI_API_KEY=your-api-key-here
```

**⚠️ Important Note:** If you have an `OPENAI_API_KEY` already set in your Windows/Mac environment variables, it might override the one in `.env`. To avoid conflicts:
- Remove any existing `OPENAI_API_KEY` from your system environment variables, OR
- Add the API key directly to Claude Desktop config (see option 2 below)

### 4. Configure Claude Desktop

Add to Claude's config file:

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

**Option 2: Include OpenAI API Key in Claude Config (Recommended if having issues)**

```json
{
  "mcpServers": {
    "wordpress": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "C:/path/to/wordpress-mcp-server",
      "env": {
        "OPENAI_API_KEY": "your-openai-api-key-here"
      }
    }
  }
}
```

### 5. Start Using!

In Claude Desktop:
```
"Create an article about AI trends with an image on site1"
```

## 📚 Documentation

### Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| List sites | Show all configured sites | "Show me all WordPress sites" |
| Create article | Create a new post | "Create an article about Python on site1" |
| Create with image | Create post with AI image | "Create article with image about space on blog1" |
| Test connection | Verify site access | "Test connection to site1" |
| Get categories | List site categories | "Show categories on site1" |
| Get tags | List site tags | "Show tags on site1" |

### WordPress Setup

1. **Enable REST API** (enabled by default in WordPress 5.0+)
2. **Create Application Password**:
   - Go to Users → Profile → Application Passwords
   - Generate new password
   - Use in configuration

3. **Required Permissions**:
   - `edit_posts` - Create and edit posts
   - `upload_files` - Upload media
   - `manage_categories` - Create categories
   - `manage_post_tags` - Create tags

## 🎨 Image Generation

The server uses OpenAI's DALL-E 3 for automatic image generation:

- **Automatic prompts** - Generated from article title and content
- **Smart filenames** - SEO-friendly names based on content
- **Direct upload** - Images uploaded directly to WordPress media library
- **Featured image** - Automatically set as post featured image

### Costs
- Standard quality: ~$0.04 per image
- HD quality: ~$0.08 per image

## 🔧 Advanced Configuration

### Environment Variables

```bash
OPENAI_API_KEY=sk-...          # OpenAI API key for image generation
```

### Configuration Options

```yaml
settings:
  default_post_status: "draft"   # draft, publish, private
  default_post_format: "standard"
  max_retries: 3
  timeout: 30
```

## 🐛 Troubleshooting

### Diagnostic Tool

Run the diagnostic script to check your setup:

```bash
python scripts/diagnose.py
```

This will check:
- Python version
- Required dependencies
- Configuration files
- Environment variables
- OpenAI API key conflicts
- Connection to OpenAI

### Common Issues

**"Server disconnected"**
- Check Python installation
- Verify path in Claude config
- Check for error messages in terminal

**"Image generation failed"**
- Verify OpenAI API key is valid
- Check API credits
- Ensure proper .env file format
- Check if you have conflicting `OPENAI_API_KEY` in system environment variables
- Try adding the API key directly to Claude Desktop config (see Option 2 above)

**"Authentication failed"**
- Regenerate WordPress application password
- Check username is correct
- Verify site URL includes protocol (https://)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io) by Anthropic
- WordPress REST API team
- OpenAI for DALL-E 3

## 📞 Support

- 📧 Email: shay@seomentor.co.il
- 🐛 Issues: [GitHub Issues](https://github.com/seomentor/wpmcp/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/seomentor/wpmcp/discussions)

---

Made with ❤️ by Shay Amos for WordPress developers, SEO`s and AI enthusiasts 

Visit my website for more cool apps :) https://www.seomentor.co.il 
