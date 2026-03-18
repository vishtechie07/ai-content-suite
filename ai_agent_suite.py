import streamlit as st
import re
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.eleven_labs import ElevenLabsTools
from agno.tools.firecrawl import FirecrawlTools
from agno.utils.log import logger

from agents.podcast_agent import PodcastAgent
from agents.video_script_agent import VideoScriptAgent
from agents.brand_voice_agent import BrandVoiceAgent
from agents.study_plan_agent import StudyPlanAgent
from agents.social_media_agent import SocialMediaAgent

class SecurityError(Exception):
    pass

def validate_api_key(api_key, service_name):
    if not api_key or not isinstance(api_key, str):
        return False
    if len(api_key) < 20:
        return False
    if service_name.lower() == "openai":
        if not api_key.startswith("sk-"):
            return False
    elif service_name.lower() == "elevenlabs":
        if len(api_key) < 32:
            return False
    elif service_name.lower() == "firecrawl":
        if len(api_key) < 20:
            return False
    
    if re.search(r'[<>"\']', api_key):
        return False
    
    return True

def secure_environment_setup(openai_key, elevenlabs_key, firecrawl_key):
    try:
        if openai_key:
            if validate_api_key(openai_key, "openai"):
                pass
            else:
                st.error("❌ Invalid OpenAI API key format")
                st.session_state["openai_key_input"] = ""
                st.session_state["elevenlabs_key_input"] = ""
                st.session_state["firecrawl_key_input"] = ""
                return False
        else:
            pass
        if elevenlabs_key:
            if validate_api_key(elevenlabs_key, "elevenlabs"):
                pass
            else:
                st.error("❌ Invalid ElevenLabs API key format")
                st.session_state["openai_key_input"] = ""
                st.session_state["elevenlabs_key_input"] = ""
                st.session_state["firecrawl_key_input"] = ""
                return False
        else:
            pass
            
        if firecrawl_key:
            if validate_api_key(firecrawl_key, "firecrawl"):
                pass
            else:
                st.error("❌ Invalid Firecrawl API key format")
                st.session_state["openai_key_input"] = ""
                st.session_state["elevenlabs_key_input"] = ""
                st.session_state["firecrawl_key_input"] = ""
                return False
        else:
            pass
            
        return True
    except Exception as e:
        logger.error(f"Environment setup error: {e}")
        return False

st.set_page_config(
    page_title="AI Agent Suite - Multi-Purpose AI Tools",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/ai_agent_suite',
        'Report a bug': 'https://github.com/your-repo/ai_agent_suite/issues',
        'About': '# Agent Suite\n\nMulti-tool content creation helpers.'
    }
)

st.markdown("""
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:;">
<meta http-equiv="X-Content-Type-Options" content="nosniff">
<meta http-equiv="X-Frame-Options" content="DENY">
<meta http-equiv="X-XSS-Protection" content="1; mode=block">
<meta http-equiv="Referrer-Policy" content="strict-origin-when-cross-origin">
""", unsafe_allow_html=True)

st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%);
    }
    
    .main-header {
        font-size: 4rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 50%, #60a5fa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: 0 4px 8px rgba(30, 58, 138, 0.2);
        letter-spacing: -0.02em;
    }
    
    .suite-description {
        text-align: center;
        font-size: 1.3rem;
        color: #1e40af;
        margin-bottom: 2.5rem;
        padding: 1.5rem;
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 50%, #93c5fd 100%);
        border-radius: 20px;
        border: 2px solid #3b82f6;
        box-shadow: 0 8px 32px rgba(59, 130, 246, 0.15);
        font-weight: 500;
    }
    
    .agent-card {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 50%, #60a5fa 100%);
        padding: 2rem;
        border-radius: 20px;
        color: white;
        margin: 1.5rem 0;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        border: 2px solid #dbeafe;
        box-shadow: 0 8px 25px rgba(30, 64, 175, 0.2);
        position: relative;
        overflow: hidden;
    }
    
    .agent-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s;
    }
    
    .agent-card:hover::before {
        left: 100%;
    }
    
    .agent-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 20px 40px rgba(30, 64, 175, 0.3);
    }
    
    .agent-card h3 {
        font-size: 1.8rem;
        margin-bottom: 1rem;
        font-weight: 700;
    }
    
    .agent-card p {
        font-size: 1.1rem;
        line-height: 1.6;
        opacity: 0.95;
    }
    
    .status-box {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border: 2px solid #f59e0b;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(245, 158, 11, 0.15);
    }
    
    .status-box h4 {
        color: #92400e;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    
    .status-box p {
        color: #78350f;
        margin-bottom: 0.5rem;
    }
    
    .btn-primary {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 10px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
    }
    
    .btn-primary:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
    }
    
    .sidebar {
        background: linear-gradient(180deg, #1e40af 0%, #3b82f6 100%);
        padding: 2rem 1rem;
        border-radius: 0 20px 20px 0;
    }
    
    .sidebar h3 {
        color: white;
        text-align: center;
        margin-bottom: 1.5rem;
        font-weight: 600;
    }
    
    .input-field {
        background: rgba(255, 255, 255, 0.1);
        border: 2px solid rgba(255, 255, 255, 0.2);
        border-radius: 10px;
        padding: 0.75rem;
        color: white;
        margin-bottom: 1rem;
    }
    
    .input-field::placeholder {
        color: rgba(255, 255, 255, 0.7);
    }
    
    .select-box {
        background: rgba(255, 255, 255, 0.1);
        border: 2px solid rgba(255, 255, 255, 0.2);
        border-radius: 10px;
        padding: 0.75rem;
        color: white;
        margin-bottom: 1rem;
    }
    
    .scrollbar {
        scrollbar-width: thin;
        scrollbar-color: #3b82f6 #dbeafe;
    }
    
    .scrollbar::-webkit-scrollbar {
        width: 8px;
    }
    
    .scrollbar::-webkit-scrollbar-track {
        background: #dbeafe;
        border-radius: 4px;
    }
    
    .scrollbar::-webkit-scrollbar-thumb {
        background: #3b82f6;
        border-radius: 4px;
    }
    
    .metrics {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        border: 2px solid #3b82f6;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        text-align: center;
    }
    
    .metrics h4 {
        color: #1e40af;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    
    .metrics p {
        color: #1e3a8a;
        font-size: 1.2rem;
        font-weight: 500;
    }
    
    .footer {
        text-align: center;
        padding: 2rem;
        color: #6b7280;
        font-size: 0.9rem;
        border-top: 2px solid #e5e7eb;
        margin-top: 3rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    if st.session_state.get("CLEAR_API_KEYS_NEXT_RUN"):
        st.session_state["openai_key_input"] = ""
        st.session_state["elevenlabs_key_input"] = ""
        st.session_state["firecrawl_key_input"] = ""
        st.session_state["CLEAR_API_KEYS_NEXT_RUN"] = False

    if 'selected_agent' not in st.session_state:
        st.session_state.selected_agent = None
    
    if 'total_requests' not in st.session_state:
        st.session_state.total_requests = 0
    
    if 'successful_requests' not in st.session_state:
        st.session_state.successful_requests = 0
    
    st.markdown('<h1 class="main-header">🚀 AI Agent Suite</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="suite-description">
        Your Ultimate AI-Powered Content Creation Suite<br>
        Transform any content into engaging podcasts, video scripts, brand insights, study plans, and social media campaigns - all powered by cutting-edge AI technology!
    </div>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown('<div class="sidebar">', unsafe_allow_html=True)
        
        st.markdown("### 🔐 Authentication")
        
        openai_key = st.text_input(
            "OpenAI API Key",
            type="password",
            key="openai_key_input",
            help="Enter your OpenAI API key for GPT-4 access"
        )
        
        elevenlabs_key = st.text_input(
            "ElevenLabs API Key",
            type="password",
            key="elevenlabs_key_input",
            help="Enter your ElevenLabs API key for voice synthesis"
        )
        
        firecrawl_key = st.text_input(
            "Firecrawl API Key",
            type="password",
            key="firecrawl_key_input",
            help="Enter your Firecrawl API key for web scraping"
        )

        st.session_state["AUTO_CLEAR_KEYS"] = st.checkbox(
            "Auto-clear keys after each run",
            value=st.session_state.get("AUTO_CLEAR_KEYS", True),
        )
        
        keys_ok = secure_environment_setup(openai_key, elevenlabs_key, firecrawl_key)
        if not keys_ok:
            st.warning("⚠️ Please check your API key formats")
        
        st.markdown("### 👤 Agent Selection")
        
        selected_agent = st.selectbox(
            "Choose Your AI Agent:",
            [
                "🎙️ Podcast Creator",
                "🎬 Video Script Generator", 
                "🎯 Brand Voice Agent",
                "📚 Study Plan Agent",
                "📱 Social Media Agent"
            ],
            help="Select the AI tool you want to use"
        )
        
        st.markdown("### 📊 Usage Statistics")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Requests", st.session_state.total_requests)
        with col2:
            st.metric("Successful", st.session_state.successful_requests)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    if selected_agent and keys_ok:
        st.session_state.selected_agent = selected_agent
        
        if "🎙️ Podcast Creator" in selected_agent:
            podcast_agent = PodcastAgent()
            podcast_agent.render_interface(openai_key, elevenlabs_key, firecrawl_key)
            
        elif "🎬 Video Script Generator" in selected_agent:
            video_script_agent = VideoScriptAgent()
            video_script_agent.render_interface(openai_key, elevenlabs_key, firecrawl_key)
            
        elif "🎯 Brand Voice Agent" in selected_agent:
            brand_voice_agent = BrandVoiceAgent()
            brand_voice_agent.render_interface(openai_key, elevenlabs_key, firecrawl_key)
            
        elif "📚 Study Plan Agent" in selected_agent:
            study_plan_agent = StudyPlanAgent()
            study_plan_agent.render_interface(openai_key, elevenlabs_key, firecrawl_key)
            
        elif "📱 Social Media Agent" in selected_agent:
            social_media_agent = SocialMediaAgent()
            social_media_agent.render_interface(openai_key, elevenlabs_key, firecrawl_key)
    elif selected_agent and not keys_ok:
        st.info("Enter valid API keys to enable this app.")
    
    st.markdown("""
    <div class="footer">
        <p>🚀 AI Agent Suite - Powered by OpenAI GPT-4, ElevenLabs, and Firecrawl</p>
        <p>Transform your content creation workflow with the power of AI</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
