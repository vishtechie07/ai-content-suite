import streamlit as st
import html
import re
from urllib.parse import urlparse
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.firecrawl import FirecrawlTools
from agno.agent import RunResponse
from agno.utils.log import logger

class SecurityError(Exception):
    """Custom exception for security violations"""
    pass

class BrandVoiceAgent:
    def __init__(self):
        self.agent_name = "Brand Voice Analysis Specialist"
        self.agent_id = "brand_voice_specialist"
        
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
        
    def render_interface(self):
        st.markdown("## 🎨 Brand Voice Analyzer")
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 1rem; border-radius: 10px; color: white; margin: 1rem 0;">
            <h3>🎭 Analyze and Define Your Brand's Unique Voice</h3>
            <p>Discover your brand's personality, create voice guidelines, and get content recommendations that align with your brand identity!</p>
        </div>
        """, unsafe_allow_html=True)
        
        input_method = st.radio(
            "Choose Input Method:",
            ["🌐 Company Website", "📝 Company Description", "📄 Existing Content"],
            help="Select how you want to provide your brand information"
        )
        
        if input_method == "🌐 Company Website":
            content_input = st.text_input(
                "🌐 Enter Company Website:",
                placeholder="https://yourcompany.com",
                help="Enter your company's main website URL"
            )
        elif input_method == "📝 Company Description":
            content_input = st.text_area(
                "📝 Describe Your Company:",
                placeholder="Describe your company, mission, values, target audience, and industry...",
                height=200,
                help="Provide a detailed description of your company and brand"
            )
        else:
            content_input = st.text_area(
                "📄 Paste Existing Content:",
                placeholder="Paste your existing marketing content, website copy, or brand materials...",
                height=200,
                help="Paste existing content to analyze your current brand voice"
            )
        
        col1, col2 = st.columns(2)
        with col1:
            industry_focus = st.selectbox(
                "🏭 Industry Focus:",
                ["Technology", "Healthcare", "Finance", "Education", "Retail", "Manufacturing", "Services", "Other"],
                help="Select your primary industry"
            )
        with col2:
            target_audience = st.selectbox(
                "👥 Target Audience:",
                ["B2B Professionals", "B2C Consumers", "Students", "Healthcare Providers", "Financial Advisors", "Other"],
                help="Select your primary target audience"
            )
        
        analysis_depth = st.selectbox(
            "🔍 Analysis Depth:",
            ["Basic Analysis", "Comprehensive Analysis", "Detailed Report with Recommendations"],
            help="Choose how detailed you want your brand voice analysis to be"
        )
        
        analyze_button = st.button(
            "🎨 Analyze Brand Voice", 
            help="Click to analyze your brand voice and generate guidelines"
        )
        
        if analyze_button:
            if not content_input.strip():
                st.error("⚠️ Input Required: Please provide company information to analyze your brand voice.")
            else:
                self.analyze_brand_voice(content_input, input_method, industry_focus, target_audience, analysis_depth)
    
    def analyze_brand_voice(self, content_input, input_method, industry_focus, target_audience, analysis_depth):
        with st.spinner("🎨 Analyzing your brand voice... This may take a few moments"):
            try:
                # Secure URL validation for website input
                if input_method == "🌐 Company Website":
                    if not self.is_safe_url(content_input):
                        st.error("❌ Invalid or unsafe URL. Please provide a valid public URL.")
                        return
                
                # Sanitize all inputs
                sanitized_content = self.sanitize_input(content_input, max_length=5000)
                sanitized_industry = self.sanitize_input(industry_focus, max_length=100)
                sanitized_audience = self.sanitize_input(target_audience, max_length=100)
                sanitized_depth = self.sanitize_input(analysis_depth, max_length=100)
                
                brand_agent = Agent(
                    name=self.agent_name,
                    agent_id=self.agent_id,
                    model=OpenAIChat(id="gpt-4o"),
                    tools=[FirecrawlTools()] if input_method == "🌐 Company Website" else [],
                    description="An AI specialist in analyzing brand voice, personality, and creating comprehensive brand guidelines.",
                    instructions=[
                        f"Analyze the brand voice for a {sanitized_industry} company targeting {sanitized_audience}",
                        f"Provide a {sanitized_depth.lower()} analysis including:",
                        "1. Brand personality traits and characteristics",
                        "2. Tone of voice recommendations",
                        "3. Content style guidelines",
                        "4. Messaging framework",
                        "5. Brand voice examples and do's/don'ts",
                        "6. Implementation recommendations",
                        "Base your analysis on the provided company information and industry best practices"
                    ],
                    markdown=True,
                )

                if input_method == "🌐 Company Website":
                    prompt = f"Analyze the brand voice of this company website: {sanitized_content}"
                else:
                    prompt = f"Analyze the brand voice based on this company description: {sanitized_content}"

                generated_analysis: RunResponse = brand_agent.run(prompt)

                if generated_analysis.content:
                    st.success("🎉 Brand voice analysis completed successfully!")

                    st.markdown("### 🎭 Your Brand Voice Analysis")
                    st.markdown(generated_analysis.content)
                    
                    st.markdown("### 💾 Download Options")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            label="📄 Download as TXT",
                            data=generated_analysis.content,
                            file_name=f"brand_voice_analysis_{sanitized_industry.lower()}.txt",
                            mime="text/plain"
                        )
                    with col2:
                        st.download_button(
                            label="📝 Download as Markdown",
                            data=generated_analysis.content,
                            file_name=f"brand_voice_analysis_{sanitized_industry.lower()}.md",
                            mime="text/markdown"
                        )
                else:
                    st.error("❌ Analysis Failed: No brand voice analysis was generated. Please try again.")

            except SecurityError as security_error:
                st.error(f"❌ Security violation: {str(security_error)}")
                logger.error(f"Brand voice agent security error: {security_error}")
            except Exception as error_details:
                st.error(f"❌ Error Encountered: {str(error_details)}")
                logger.error(f"Brand voice agent error: {error_details}")
