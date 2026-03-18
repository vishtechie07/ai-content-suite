import streamlit as st
import re
from urllib.parse import urlparse
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.firecrawl import FirecrawlTools
from agno_compat import AgentRunResult
from agno.utils.log import logger
from security_config import security_manager

try:
    from firecrawl import Firecrawl
    FIRECRAWL_SDK_AVAILABLE = True
except ImportError:
    FIRECRAWL_SDK_AVAILABLE = False

class SecurityError(Exception):
    pass

class VideoScriptAgent:
    MAX_OUTPUT_CHARS = 20000

    def __init__(self):
        self.agent_name = "Video Script Creation Specialist"
        self.agent_id = "video_script_specialist"
        self.openai_key = None
        self.firecrawl_key = None
        
    def is_safe_url(self, url):
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ['http', 'https']:
                return False
            if parsed.netloc in ['localhost', '127.0.0.1', '::1']:
                return False
            if parsed.netloc.startswith('192.168.') or parsed.netloc.startswith('10.'):
                return False
            if parsed.netloc.startswith('172.'):
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
        if not text or not isinstance(text, str):
            return ""
        sanitized = re.sub(r'[<>"\']', '', text)
        return sanitized[:max_length]
        
    def render_interface(self, openai_key, elevenlabs_key, firecrawl_key):
        self.openai_key = openai_key
        self.firecrawl_key = firecrawl_key
        st.markdown("## 🎬 Video Script Generator")
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 1rem; border-radius: 10px; color: white; margin: 1rem 0;">
            <h3>🎥 Transform Content into Engaging Video Scripts</h3>
            <p>Convert blog posts, articles, or any content into professional video scripts with timing, scenes, and transitions!</p>
        </div>
        """, unsafe_allow_html=True)
        
        input_method = st.radio(
            "Choose Input Method:",
            ["🌐 Blog URL", "📝 Direct Text Input"],
            help="Select how you want to provide your content"
        )
        
        if input_method == "🌐 Blog URL":
            content_input = st.text_input(
                "🌐 Enter Blog URL:",
                placeholder="https://example.com/blog-post",
                help="Paste the complete URL of the blog post"
            )
        else:
            content_input = st.text_area(
                "📝 Enter Your Content:",
                placeholder="Paste your content here...",
                height=200,
                help="Enter the content you want to convert to a video script"
            )
        
        col1, col2 = st.columns(2)
        with col1:
            video_style = st.selectbox(
                "🎨 Video Style:",
                ["Educational", "Entertainment", "Business", "Tutorial", "Storytelling"],
                help="Choose the style of video you want to create"
            )
        with col2:
            video_duration = st.selectbox(
                "⏱️ Target Duration:",
                ["2-3 minutes", "5-7 minutes", "10-15 minutes", "20+ minutes"],
                help="Select your target video length"
            )
        
        generate_button = st.button(
            "🎬 Generate Video Script", 
            help="Click to create your video script"
        )
        
        if generate_button:
            if not content_input.strip():
                st.error("⚠️ Input Required: Please provide content to generate a video script.")
            else:
                self.generate_video_script(content_input, input_method, video_style, video_duration)
    
    def generate_video_script(self, content_input, input_method, video_style, video_duration):
        with st.spinner("🎬 Creating your video script... This may take a few moments"):
            try:
                openai_key = self.openai_key
                firecrawl_key = self.firecrawl_key

                if not openai_key:
                    st.error("❌ OpenAI API key is missing. Add it in the sidebar.")
                    return
                if input_method == "🌐 Blog URL" and not firecrawl_key:
                    st.error("❌ Firecrawl API key is missing. Add it in the sidebar.")
                    return

                user_id = security_manager.get_user_id()
                if input_method == "🌐 Blog URL":
                    input_data = {"url": content_input, "video_style": video_style, "video_duration": video_duration}
                else:
                    input_data = {"content": content_input, "video_style": video_style, "video_duration": video_duration}
                is_secure, message = security_manager.check_request_security(user_id, input_data)
                if not is_secure:
                    st.error(f"Security Error: {message}")
                    return

                if input_method == "🌐 Blog URL":
                    st.info("🔍 Extracting blog content...")

                    if not self.is_safe_url(content_input):
                        st.error("❌ Invalid or unsafe URL. Please provide a valid public URL.")
                        return
                    
                    try:
                        if FIRECRAWL_SDK_AVAILABLE:
                            firecrawl_tools = Firecrawl(api_key=firecrawl_key)
                            st.success("✅ Firecrawl connection successful")
                        else:
                            firecrawl_tools = FirecrawlTools(api_key=firecrawl_key)
                            st.success("✅ Firecrawl connection successful")
                    except Exception as e:
                        st.error(f"❌ Firecrawl connection failed: {str(e)}")
                        return
                    
                    try:
                        if FIRECRAWL_SDK_AVAILABLE and hasattr(firecrawl_tools, 'extract'):
                            extracted_content = firecrawl_tools.extract(
                                [content_input], 
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
                            extracted_content = firecrawl_tools.scrape_website(content_input)
                            if extracted_content and len(str(extracted_content)) > 100:
                                blog_content = str(extracted_content)
                            else:
                                st.error("❌ Content extraction failed")
                                return
                    except Exception as extract_error:
                        st.error(f"❌ Content extraction failed: {str(extract_error)}")
                        return
                    
                    content_for_agent = self.sanitize_input(blog_content, max_length=3000)
                    st.success("✅ Blog content extracted successfully!")
                else:
                    content_for_agent = self.sanitize_input(content_input, max_length=5000)
                
                script_agent = Agent(
                    name=self.agent_name,
                    agent_id=self.agent_id,
                    model=OpenAIChat(id="gpt-4o", api_key=openai_key),
                    tools=[],
                    description="An AI specialist in creating engaging video scripts with proper structure and timing.",
                    instructions=[
                        f"Create a {video_style.lower()} video script for {video_duration} duration",
                        "Include:",
                        "1. Hook/Introduction (10-15% of total time)",
                        "2. Main content with clear sections (70-80% of total time)",
                        "3. Call-to-action and conclusion (10-15% of total time)",
                        "4. Scene descriptions and visual cues",
                        "5. Timing estimates for each section",
                        "6. Transitions between scenes",
                        "Make it engaging, conversational, and easy to follow"
                    ],
                    markdown=True,
                )

                if input_method == "🌐 Blog URL":
                    prompt = f"Create a {video_style.lower()} video script from this blog content:\n\n{content_for_agent}"
                else:
                    prompt = f"Create a {video_style.lower()} video script from this content:\n\n{content_for_agent}"
                
                generated_script: AgentRunResult = script_agent.run(prompt)

                if generated_script.content:
                    st.success("🎉 Success! Your video script has been generated!")

                    st.markdown("### 📝 Your Video Script")
                    generated_text = str(generated_script.content).strip()
                    generated_text = generated_text[:self.MAX_OUTPUT_CHARS]
                    st.markdown(generated_text)
                    
                    st.markdown("### 💾 Download Options")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            label="📄 Download as TXT",
                            data=generated_text,
                            file_name=f"video_script_{video_style.lower()}.txt",
                            mime="text/plain"
                        )
                    with col2:
                        st.download_button(
                            label="📝 Download as Markdown",
                            data=generated_text,
                            file_name=f"video_script_{video_style.lower()}.md",
                            mime="text/markdown"
                        )
                else:
                    st.error("❌ Generation Failed: No script content was produced. Please try again.")

            except SecurityError as security_error:
                st.error(f"❌ Security violation: {str(security_error)}")
                logger.error(f"Video script agent security error: {security_error}")
            except Exception as error_details:
                st.error(f"❌ Error Encountered: {str(error_details)}")
                logger.error(f"Video script agent error: {error_details}")
            finally:
                if st.session_state.get("AUTO_CLEAR_KEYS", True):
                    st.session_state["CLEAR_API_KEYS_NEXT_RUN"] = True
                    st.rerun()
