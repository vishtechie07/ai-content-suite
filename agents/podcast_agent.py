import os
import streamlit as st
import html
import re
from uuid import uuid4
from pathlib import Path
from urllib.parse import urlparse
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.eleven_labs import ElevenLabsTools
from agno.tools.firecrawl import FirecrawlTools
from agno.agent import RunResponse
from agno.utils.audio import write_audio_to_file
from agno.utils.log import logger

try:
    from firecrawl import Firecrawl
    FIRECRAWL_SDK_AVAILABLE = True
except ImportError:
    FIRECRAWL_SDK_AVAILABLE = False

class SecurityError(Exception):
    """Custom exception for security violations"""
    pass

class PodcastAgent:
    def __init__(self):
        self.agent_name = "Podcast Creation Specialist"
        self.agent_id = "podcast_creation_specialist"
        
    def is_safe_url(self, url):
        """Validate URL for security - prevent SSRF attacks"""
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ['http', 'https']:
                return False
            if parsed.netloc in ['localhost', '127.0.0.1', '::1']:
                return False
            if parsed.netloc.startswith('192.168.') or parsed.netloc.startswith('10.'):
                return False
            if parsed.netloc.startswith('172.'):
                # Check for 172.16.0.0/12 range
                try:
                    parts = parsed.netloc.split('.')
                    if len(parts) == 4 and 16 <= int(parts[1]) <= 31:
                        return False
                except (ValueError, IndexError):
                    pass
            return True
        except Exception:
            return False
    
    def sanitize_input(self, text, max_length=5000):
        """Sanitize user input to prevent injection attacks"""
        if not text or not isinstance(text, str):
            return ""
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', text)
        # Limit length
        return sanitized[:max_length]
    
    def secure_file_path(self, directory, filename):
        """Ensure file operations are within safe boundaries"""
        try:
            base_dir = Path(directory).resolve()
            current_dir = Path.cwd().resolve()
            
            # Ensure the directory is within current working directory
            if not base_dir.is_relative_to(current_dir):
                raise SecurityError("Invalid directory path")
            
            # Ensure filename doesn't contain path traversal
            safe_filename = Path(filename).name
            if '..' in safe_filename or '/' in safe_filename or '\\' in safe_filename:
                raise SecurityError("Invalid filename")
            
            return base_dir / safe_filename
        except Exception as e:
            logger.error(f"File path security error: {e}")
            raise SecurityError("File path validation failed")
    
    def render_interface(self):
        st.markdown("## 🎙️ Podcast Creator")
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 1rem; border-radius: 10px; color: white; margin: 1rem 0;">
            <h3>🚀 Transform Any Blog into an Engaging Podcast</h3>
            <p>Simply paste a blog URL and watch as our AI creates a professional podcast episode for you!</p>
        </div>
        """, unsafe_allow_html=True)
        
        blog_url_input = st.text_input(
            "🌐 Enter the Blog URL to Convert:",
            placeholder="https://example.com/blog-post",
            help="Paste the complete URL of the blog post you want to convert"
        )
        
        convert_button = st.button(
            "🎙️ Create Podcast Episode", 
            help="Click to start the conversion process"
        )
        
        if convert_button:
            if not blog_url_input.strip():
                st.error("⚠️ Input Required: Please enter a blog URL to proceed with the conversion.")
            else:
                self.generate_podcast(blog_url_input)
    
    def generate_podcast(self, blog_url):
        with st.spinner("🔄 Processing your request... This may take a few moments"):
            try:
                # Secure URL validation
                if not self.is_safe_url(blog_url):
                    st.error("❌ Invalid or unsafe URL. Please provide a valid public URL.")
                    return
                
                st.info("🔍 Testing API connections...")
                
                try:
                    test_model = OpenAIChat(id="gpt-4o")
                    st.success("✅ OpenAI connection successful")
                except Exception as e:
                    st.error(f"❌ OpenAI connection failed: {str(e)}")
                    return
                
                try:
                    if FIRECRAWL_SDK_AVAILABLE:
                        firecrawl_tools = Firecrawl(api_key=os.environ.get("FIRECRAWL_API_KEY"))
                        st.success("✅ Firecrawl connection successful")
                    else:
                        firecrawl_tools = FirecrawlTools()
                        st.success("✅ Firecrawl connection successful")
                except Exception as e:
                    st.error(f"❌ Firecrawl connection failed: {str(e)}")
                    return
                
                try:
                    elevenlabs_tools = ElevenLabsTools(
                        voice_id="pNInz6obpgDQGcFmaJgB",
                        model_id="eleven_multilingual_v2",
                        target_directory="generated_audio_files",
                    )
                    st.success("✅ ElevenLabs connection successful")
                except Exception as e:
                    st.error(f"❌ ElevenLabs connection failed: {str(e)}")
                    return
                
                st.info("🚀 Creating AI agent...")
                
                try:
                    if FIRECRAWL_SDK_AVAILABLE and hasattr(firecrawl_tools, 'extract'):
                        extracted_content = firecrawl_tools.extract(
                            [blog_url], 
                            prompt="Extract the main content, title, and key points from this blog post. Focus on the actual article content, not navigation or ads."
                        )
                        
                        if extracted_content and hasattr(extracted_content, 'data') and extracted_content.data:
                            if isinstance(extracted_content.data, list) and len(extracted_content.data) > 0:
                                first_item = extracted_content.data[0]
                                if hasattr(first_item, 'get'):
                                    blog_content = first_item.get('content', '')
                                else:
                                    blog_content = str(first_item)
                            elif isinstance(extracted_content.data, dict):
                                blog_content = extracted_content.data.get('mainContent', '')
                                if not blog_content:
                                    blog_content = extracted_content.data.get('content', '')
                                    if not blog_content:
                                        blog_content = str(extracted_content.data)
                            else:
                                blog_content = str(extracted_content.data)
                            
                            if not blog_content or len(blog_content.strip()) < 100:
                                st.error("❌ Content extraction failed - insufficient content")
                                return
                        else:
                            st.error("❌ Content extraction failed - no data returned")
                            return
                    else:
                        extracted_content = firecrawl_tools.scrape_website(blog_url)
                        if extracted_content and len(str(extracted_content)) > 100:
                            blog_content = str(extracted_content)
                        else:
                            st.error("❌ Content extraction failed")
                            return
                except Exception as extract_error:
                    st.error(f"❌ Content extraction failed: {str(extract_error)}")
                    return
                
                # Sanitize extracted content
                sanitized_content = self.sanitize_input(blog_content, max_length=3000)
                
                podcast_creation_agent = Agent(
                    name=self.agent_name,
                    agent_id=self.agent_id,
                    model=test_model,
                    tools=[elevenlabs_tools],
                    description="An intelligent AI agent specialized in creating engaging podcast content from blog articles.",
                    instructions=[
                        "You have been provided with blog content that has already been extracted.",
                        "Your task is to:",
                        "1. Create a compelling summary (MAX 2000 characters) of the provided blog content",
                        "2. Make the summary engaging, conversational, and capture key insights",
                        "3. Convert the summary to audio using ElevenLabsTools",
                        "4. Ensure the summary is based on the actual content provided, not generic text",
                        "The summary should be suitable for a podcast episode and maintain listener engagement."
                    ],
                    markdown=True,
                )

                st.info("📝 Generating podcast content...")
                
                # Use sanitized content in prompt
                prompt = f"Create a compelling podcast summary and audio from this blog content:\n\n{sanitized_content}"
                generated_podcast: RunResponse = podcast_creation_agent.run(prompt)
                
                # Secure file operations
                try:
                    output_directory = self.secure_file_path("generated_audio_files", "")
                    output_directory.mkdir(exist_ok=True)
                except SecurityError as e:
                    st.error(f"❌ Security error: {str(e)}")
                    return
                
                if hasattr(generated_podcast, 'content') and generated_podcast.content:
                    content_text = str(generated_podcast.content).strip()
                    
                    if len(content_text.strip()) > 100:
                        st.success("✅ Content generated successfully!")
                        st.markdown("### 📝 Generated Content:")
                        st.markdown(content_text)
                    else:
                        st.error("❌ Generated content is too short")
                        return
                else:
                    st.error("❌ No content was generated")
                    return

                if hasattr(generated_podcast, 'audio') and generated_podcast.audio and len(generated_podcast.audio) > 0:
                    st.success("✅ Audio generated successfully!")
                    
                    try:
                        # Secure filename generation
                        safe_filename = f"podcast_episode_{uuid4()}.wav"
                        output_filename = self.secure_file_path("generated_audio_files", safe_filename)
                        
                        write_audio_to_file(
                            audio=generated_podcast.audio[0].base64_audio,
                            filename=str(output_filename)
                        )
                        
                        st.success(f"💾 Audio saved to: {safe_filename}")
                        
                        st.markdown("### 🎧 Listen to Your Podcast")
                        
                        # Secure file reading
                        try:
                            with open(output_filename, "rb") as audio_file:
                                audio_file_content = audio_file.read()
                            st.audio(audio_file_content, format="audio/wav")

                            st.markdown("### 💾 Download Options")
                            st.download_button(
                                label="📥 Download Podcast Episode",
                                data=audio_file_content,
                                file_name=safe_filename,
                                mime="audio/wav",
                                help="Save your podcast episode to your device"
                            )
                        except Exception as file_error:
                            st.error(f"❌ File reading error: {str(file_error)}")
                        
                    except Exception as audio_error:
                        st.error(f"❌ Audio file error: {str(audio_error)}")
                        
                else:
                    st.warning("⚠️ No audio content was produced")
                    st.info("This might be due to:")
                    st.info("• ElevenLabs voice ID not found")
                    st.info("• Insufficient ElevenLabs credits")
                    st.info("• Audio generation failed")

            except SecurityError as security_error:
                st.error(f"❌ Security violation: {str(security_error)}")
                logger.error(f"Podcast agent security error: {security_error}")
            except Exception as error_details:
                st.error(f"❌ Error Encountered: {str(error_details)}")
                logger.error(f"Podcast agent error: {error_details}")
