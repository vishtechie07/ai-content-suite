# AI Agent Suite

A collection of AI-powered tools that help you create content in different formats. Turn blogs into podcasts, generate video scripts, analyze brand voice, create study plans, and craft social media posts - all using AI.

## What's Inside

### 🎙️ Podcast Creator
Turn any blog post into a podcast episode. The AI reads the content, creates a summary, and generates natural-sounding audio using ElevenLabs.

### 🎬 Video Script Generator  
Convert articles or text into video scripts with timing, scene descriptions, and transitions. Choose from different styles like educational, business, or storytelling.

### 🎯 Brand Voice Agent
Get insights about your brand's personality and voice. Perfect for companies looking to understand how they come across to customers.

### 📚 Study Plan Agent
Create personalized learning paths from any content. Great for students, teachers, or anyone wanting to organize their learning.

### 📱 Social Media Agent
Transform content into platform-specific social media posts. Works with Twitter, LinkedIn, Instagram, and Facebook.

## Recent changes

- **Sidebar API keys** — Keys are entered in the app sidebar and passed only into the SDK calls that need them (not written to shared `os.environ`), so different visitors do not overwrite each other’s credentials on public hosting.
- **Auto-clear keys** — Optional checkbox in the sidebar clears key fields after each agent run (via a follow-up rerun).
- **`security_config.py`** — Per-visitor rate limiting, stricter input validation, and output caps where applied.
- **Podcast output** — Audio files go under `generated_audio_files/<visitor-id>/`.
- **Deploy on GitHub** — Use [Streamlit Community Cloud](https://share.streamlit.io/) with main file `ai_agent_suite.py` and `requirements.txt`. This repo is a Streamlit app.

## Getting Started

### What You Need
- Python 3.8 or newer
- API keys for:
  - OpenAI (for AI content generation)
  - ElevenLabs (for voice synthesis) 
  - Firecrawl (for web scraping)

### Quick Setup

1. **Get the code**
   ```bash
   git clone <repository-url>
   cd ai_agent_suite
   ```

2. **Install packages**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your keys**
   Create a `.env` file in the project folder:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
   FIRECRAWL_API_KEY=your_firecrawl_api_key_here
   ```

   You can also rely on the **sidebar only** for keys when running Streamlit (`.env` is optional for local use).

4. **Run it**
   ```bash
   streamlit run ai_agent_suite.py
   ```

## Getting Your API Keys

### OpenAI
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Find the API Keys section
4. Create a new key
5. Copy it to your `.env` file

### ElevenLabs
1. Visit [ElevenLabs](https://elevenlabs.io/)
2. Create an account
3. Go to your profile settings
4. Copy your API key
5. Add it to `.env`

### Firecrawl
1. Check out [Firecrawl](https://firecrawl.dev/)
2. Sign up for an account
3. Go to the API section
4. Generate your key
5. Put it in `.env`

## How to Use

### First Time
1. **Start the app** - You'll see the main interface with all the tools
2. **Pick a tool** - Choose what you want to create
3. **Add your keys** - Put your API keys in the sidebar
4. **Give it content** - Paste a URL or type some text
5. **Generate** - Click the button and wait for the magic
6. **Download** - Save your results in various formats

### Podcast Creator Example
1. Select "Podcast Creator" from the menu
2. Paste a blog URL (like `https://example.com/blog-post`)
3. Click "Create Podcast Episode"
4. Wait for content extraction and AI processing
5. Listen to your generated audio
6. Download the podcast file

### Video Script Example
1. Choose "Video Script Generator"
2. Pick input method (URL or direct text)
3. Select your video style and length
4. Provide your content source
5. Generate the script
6. Download as TXT or Markdown

## How It Works

### The Tech Stack
- **Frontend**: Streamlit for the web interface
- **AI Framework**: Agno for managing the AI agents
- **Language Model**: OpenAI's GPT-4 for content generation
- **Voice**: ElevenLabs for audio synthesis
- **Scraping**: Firecrawl for getting content from websites

### Behind the Scenes
1. **Input Validation** - Checks your URLs and content
2. **Content Extraction** - Gets the actual article text from websites
3. **AI Generation** - GPT-4 creates your content
4. **Formatting** - Structures everything nicely
5. **Output** - Gives you files you can use

### Customization
- **Voice Selection** - Pick from ElevenLabs voice library
- **Content Length** - Adjust how long your summaries are
- **Style Preferences** - Choose tone and format
- **Output Formats** - Multiple download options

## Troubleshooting

### Common Issues

**API Connection Problems**
- Double-check your API keys
- Make sure you have internet
- Verify the services are working

**OpenAI “exceeded quota” while billing looks fine**
- The key may belong to a different org/project than the account you’re viewing. Create a new API key from the org that has billing and paste it in the sidebar.

**Windows: setting env vars**
- In **Command Prompt**: `set OPENAI_API_KEY=sk-...`
- In **PowerShell**: `$env:OPENAI_API_KEY="sk-..."`

**Content Extraction Fails**
- Check if the URL is public and accessible
- Some sites block scraping
- Try a different article

**Audio Generation Issues**
- Verify you have ElevenLabs credits
- Check if the voice ID is valid
- Look at file permissions

**Slow Performance**
- Try shorter content
- Check API rate limits
- Monitor your system resources

### Debug Mode
If you need more details, set these in your `.env`:
```env
DEBUG=true
LOG_LEVEL=DEBUG
```

## Project Structure

```
ai_agent_suite/
├── agents/                    # The AI tools
│   ├── podcast_agent.py      # Podcast creator
│   ├── video_script_agent.py # Video script generator
│   ├── brand_voice_agent.py  # Brand analyzer
│   ├── study_plan_agent.py   # Study planner
│   ├── social_media_agent.py # Social media tool
│   └── __init__.py           # Package setup
├── generated_audio_files/     # Where podcasts go
├── ai_agent_suite.py         # Main app
├── security_config.py        # Rate limits & input validation
├── requirements.txt           # Dependencies
├── .env                      # Your API keys (create this)
└── README.md                 # This file
```

## Contributing

Want to help improve this project?

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if you can
5. Submit a pull request

### Code Standards
- Follow Python style guidelines (PEP 8)
- Add docstrings to functions
- Include error handling
- Keep it readable

## License

This project uses the MIT License. See the LICENSE file for details.

## Thanks

Built with help from:
- **OpenAI** for the language model
- **ElevenLabs** for voice synthesis
- **Firecrawl** for web scraping
- **Streamlit** for the web framework
- **Agno** for AI agent management

## Support

Having trouble? Here are some options:
- Check the troubleshooting section above
- Look at the API documentation for the services you're using
- Create an issue in the GitHub repository

---

**Made for content creators, marketers, and anyone who wants to use AI to make better content.**