import streamlit as st
import re
from urllib.parse import urlparse
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.firecrawl import FirecrawlTools
from agno_compat import AgentRunResult
from agno.utils.log import logger
from security_config import security_manager

class SecurityError(Exception):
    pass

class SocialMediaAgent:
    MAX_OUTPUT_CHARS = 12000

    def __init__(self):
        self.agent_name = "Social Media Content Specialist"
        self.agent_id = "social_media_specialist"
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
        st.markdown("## 📱 Social Media Content Generator")
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 1rem; border-radius: 10px; color: white; margin: 1rem 0;">
            <h3>🚀 Transform Content into Engaging Social Media Posts</h3>
            <p>Convert articles, blogs, or any content into platform-specific social media posts with hashtags and engagement strategies!</p>
        </div>
        """, unsafe_allow_html=True)
        
        input_method = st.radio(
            "Choose Input Method:",
            ["🌐 Article/Blog URL", "📝 Content Input", "📄 Existing Content"],
            help="Select how you want to provide your content"
        )
        
        if input_method == "🌐 Article/Blog URL":
            content_input = st.text_input(
                "🌐 Enter URL:",
                placeholder="https://example.com/article-or-blog",
                help="Enter the URL of the article or blog post"
            )
        elif input_method == "📝 Content Input":
            content_input = st.text_area(
                "📝 Enter Your Content:",
                placeholder="Paste or type the content you want to convert to social media posts...",
                height=200,
                help="Enter the content you want to transform"
            )
        else:
            content_input = st.text_area(
                "📄 Paste Existing Content:",
                placeholder="Paste your existing content, articles, or marketing materials...",
                height=200,
                help="Paste existing content to convert to social media posts"
            )
        
        col1, col2 = st.columns(2)
        with col1:
            platform = st.selectbox(
                "📱 Platform:",
                ["Twitter/X", "LinkedIn", "Instagram", "Facebook", "TikTok", "All Platforms"],
                help="Select your target social media platform"
            )
        with col2:
            content_type = st.selectbox(
                "🎯 Content Type:",
                ["Informational", "Promotional", "Educational", "Entertainment", "Storytelling"],
                help="Choose the type of content you want to create"
            )
        
        post_count = st.selectbox(
            "📊 Number of Posts:",
            ["1 post", "3 posts", "5 posts", "10 posts"],
            help="Select how many social media posts you want to generate"
        )
        
        generate_button = st.button(
            "📱 Generate Social Media Posts", 
            help="Click to create your social media content"
        )
        
        if generate_button:
            if not content_input.strip():
                st.error("⚠️ Input Required: Please provide content to generate social media posts.")
            else:
                self.generate_social_media_posts(content_input, input_method, platform, content_type, post_count)
    
    def generate_social_media_posts(self, content_input, input_method, platform, content_type, post_count):
        with st.spinner("📱 Creating your social media posts... This may take a few moments"):
            try:
                openai_key = self.openai_key
                firecrawl_key = self.firecrawl_key

                if not openai_key:
                    st.error("❌ OpenAI API key is missing. Add it in the sidebar.")
                    return
                if input_method == "🌐 Article/Blog URL" and not firecrawl_key:
                    st.error("❌ Firecrawl API key is missing. Add it in the sidebar.")
                    return

                user_id = security_manager.get_user_id()
                if input_method == "🌐 Article/Blog URL":
                    input_data = {"url": content_input, "platform": platform, "content_type": content_type, "post_count": post_count}
                else:
                    input_data = {"content": content_input, "platform": platform, "content_type": content_type, "post_count": post_count}
                is_secure, message = security_manager.check_request_security(user_id, input_data)
                if not is_secure:
                    st.error(f"Security Error: {message}")
                    return

                if input_method == "🌐 Article/Blog URL":
                    if not self.is_safe_url(content_input):
                        st.error("❌ Invalid or unsafe URL. Please provide a valid public URL.")
                        return

                sanitized_content = self.sanitize_input(content_input, max_length=5000)
                sanitized_platform = self.sanitize_input(platform, max_length=100)
                sanitized_type = self.sanitize_input(content_type, max_length=100)
                sanitized_count = self.sanitize_input(post_count, max_length=100)
                
                social_media_agent = Agent(
                    name=self.agent_name,
                    agent_id=self.agent_id,
                    model=OpenAIChat(id="gpt-4o", api_key=openai_key),
                    tools=[FirecrawlTools(api_key=firecrawl_key)] if input_method == "🌐 Article/Blog URL" else [],
                    description="An AI specialist in creating engaging social media content with platform-specific formatting and hashtags.",
                    instructions=[
                        f"Create {sanitized_count.lower()} {sanitized_type.lower()} social media posts for {sanitized_platform}",
                        "Include:",
                        "1. Platform-specific formatting and character limits",
                        "2. Engaging headlines and hooks",
                        "3. Relevant hashtags and mentions",
                        "4. Call-to-action statements",
                        "5. Visual content suggestions",
                        "6. Engagement strategies",
                        "7. Posting schedule recommendations",
                        "Make each post unique, engaging, and optimized for the platform"
                    ],
                    markdown=True,
                )

                if input_method == "🌐 Article/Blog URL":
                    prompt = f"Create social media posts from this content: {sanitized_content}"
                else:
                    prompt = f"Create social media posts for: {sanitized_content}"

                generated_posts: AgentRunResult = social_media_agent.run(prompt)

                if generated_posts.content:
                    st.success("🎉 Social media posts generated successfully!")

                    st.markdown("### 📱 Your Social Media Posts")
                    generated_text = str(generated_posts.content).strip()
                    generated_text = generated_text[:self.MAX_OUTPUT_CHARS]
                    st.markdown(generated_text)
                    
                    st.markdown("### 💾 Download Options")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            label="📄 Download as TXT",
                            data=generated_text,
                            file_name=f"social_media_posts_{sanitized_platform.lower()}.txt",
                            mime="text/plain"
                        )
                    with col2:
                        st.download_button(
                            label="📝 Download as Markdown",
                            data=generated_text,
                            file_name=f"social_media_posts_{sanitized_platform.lower()}.md",
                            mime="text/markdown"
                        )
                else:
                    st.error("❌ Generation Failed: No social media posts were created. Please try again.")

            except SecurityError as security_error:
                st.error(f"❌ Security violation: {str(security_error)}")
                logger.error(f"Social media agent security error: {security_error}")
            except Exception as error_details:
                st.error(f"❌ Error Encountered: {str(error_details)}")
                logger.error(f"Social media agent error: {error_details}")
            finally:
                if st.session_state.get("AUTO_CLEAR_KEYS", True):
                    st.session_state["CLEAR_API_KEYS_NEXT_RUN"] = True
                    st.rerun()
