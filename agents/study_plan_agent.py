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

class StudyPlanAgent:
    MAX_OUTPUT_CHARS = 12000

    def __init__(self):
        self.agent_name = "Study Plan Creation Specialist"
        self.agent_id = "study_plan_specialist"
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
        st.markdown("## 📚 Study Plan Generator")
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 1rem; border-radius: 10px; color: white; margin: 1rem 0;">
            <h3>🎯 Create Personalized Study Plans from Any Content</h3>
            <p>Transform articles, courses, or any learning material into structured study plans with timelines, milestones, and progress tracking!</p>
        </div>
        """, unsafe_allow_html=True)
        
        input_method = st.radio(
            "Choose Input Method:",
            ["🌐 Article/Course URL", "📝 Learning Content", "📄 Existing Materials"],
            help="Select how you want to provide your learning content"
        )
        
        if input_method == "🌐 Article/Course URL":
            content_input = st.text_input(
                "🌐 Enter URL:",
                placeholder="https://example.com/article-or-course",
                help="Enter the URL of the article, course, or learning material"
            )
        elif input_method == "📝 Learning Content":
            content_input = st.text_area(
                "📝 Describe What You Want to Learn:",
                placeholder="Describe the subject, topics, skills, or concepts you want to study...",
                height=200,
                help="Provide a detailed description of what you want to learn"
            )
        else:
            content_input = st.text_area(
                "📄 Paste Learning Materials:",
                placeholder="Paste your existing learning materials, notes, or course content...",
                height=200,
                help="Paste existing learning content to create a study plan from"
            )
        
        col1, col2 = st.columns(2)
        with col1:
            study_level = st.selectbox(
                "📖 Study Level:",
                ["Beginner", "Intermediate", "Advanced", "Expert"],
                help="Select your current knowledge level"
            )
        with col2:
            time_available = st.selectbox(
                "⏰ Time Available:",
                ["1-2 hours/week", "3-5 hours/week", "10+ hours/week", "Full-time study"],
                help="Select how much time you can dedicate to studying"
            )
        
        study_duration = st.selectbox(
            "📅 Study Duration:",
            ["2-4 weeks", "1-2 months", "3-6 months", "6+ months"],
            help="Choose your target study timeline"
        )
        
        generate_button = st.button(
            "📚 Generate Study Plan", 
            help="Click to create your personalized study plan"
        )
        
        if generate_button:
            if not content_input.strip():
                st.error("⚠️ Input Required: Please provide learning content to generate a study plan.")
            else:
                self.generate_study_plan(content_input, input_method, study_level, time_available, study_duration)
    
    def generate_study_plan(self, content_input, input_method, study_level, time_available, study_duration):
        with st.spinner("📚 Creating your study plan... This may take a few moments"):
            try:
                openai_key = self.openai_key
                firecrawl_key = self.firecrawl_key

                if not openai_key:
                    st.error("❌ OpenAI API key is missing. Add it in the sidebar.")
                    return
                if input_method == "🌐 Article/Course URL" and not firecrawl_key:
                    st.error("❌ Firecrawl API key is missing. Add it in the sidebar.")
                    return

                user_id = security_manager.get_user_id()
                if input_method == "🌐 Article/Course URL":
                    input_data = {"url": content_input, "study_level": study_level, "time_available": time_available, "study_duration": study_duration}
                else:
                    input_data = {"content": content_input, "study_level": study_level, "time_available": time_available, "study_duration": study_duration}
                is_secure, message = security_manager.check_request_security(user_id, input_data)
                if not is_secure:
                    st.error(f"Security Error: {message}")
                    return

                if input_method == "🌐 Article/Course URL":
                    if not self.is_safe_url(content_input):
                        st.error("❌ Invalid or unsafe URL. Please provide a valid public URL.")
                        return

                sanitized_content = self.sanitize_input(content_input, max_length=5000)
                sanitized_level = self.sanitize_input(study_level, max_length=100)
                sanitized_time = self.sanitize_input(time_available, max_length=100)
                sanitized_duration = self.sanitize_input(study_duration, max_length=100)
                
                study_agent = Agent(
                    name=self.agent_name,
                    id=self.agent_id,
                    model=OpenAIChat(id="gpt-4o", api_key=openai_key),
                    tools=[FirecrawlTools(api_key=firecrawl_key)] if input_method == "🌐 Article/Course URL" else [],
                    description="An AI specialist in creating personalized study plans with structured learning objectives and timelines.",
                    instructions=[
                        f"Create a {sanitized_level.lower()} level study plan for {sanitized_duration} with {sanitized_time}",
                        "Include:",
                        "1. Learning objectives and goals",
                        "2. Weekly study schedule and milestones",
                        "3. Recommended resources and materials",
                        "4. Practice exercises and assessments",
                        "5. Progress tracking methods",
                        "6. Study tips and strategies",
                        "7. Timeline with specific deadlines",
                        "Make it practical, achievable, and tailored to the learner's needs"
                    ],
                    markdown=True,
                )

                if input_method == "🌐 Article/Course URL":
                    prompt = f"Create a study plan from this learning material: {sanitized_content}"
                else:
                    prompt = f"Create a study plan for: {sanitized_content}"

                generated_plan: AgentRunResult = study_agent.run(prompt, stream=False)

                if generated_plan.content:
                    st.success("🎉 Study plan generated successfully!")

                    st.markdown("### 📚 Your Study Plan")
                    generated_text = str(generated_plan.content).strip()
                    generated_text = generated_text[:self.MAX_OUTPUT_CHARS]
                    st.markdown(generated_text)
                    
                    st.markdown("### 💾 Download Options")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            label="📄 Download as TXT",
                            data=generated_text,
                            file_name=f"study_plan_{sanitized_level.lower()}.txt",
                            mime="text/plain"
                        )
                    with col2:
                        st.download_button(
                            label="📝 Download as Markdown",
                            data=generated_text,
                            file_name=f"study_plan_{sanitized_level.lower()}.md",
                            mime="text/markdown"
                        )
                else:
                    st.error("❌ Generation Failed: No study plan was created. Please try again.")

            except SecurityError as security_error:
                st.error(f"❌ Security violation: {str(security_error)}")
                logger.error(f"Study plan agent security error: {security_error}")
            except Exception as error_details:
                st.error(f"❌ Error Encountered: {str(error_details)}")
                logger.error(f"Study plan agent error: {error_details}")
            finally:
                if st.session_state.get("AUTO_CLEAR_KEYS", True):
                    st.session_state["CLEAR_API_KEYS_NEXT_RUN"] = True
                    st.rerun()
