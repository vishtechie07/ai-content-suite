import time
import hashlib
import secrets
import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import streamlit as st

class SecurityConfig:
    RATE_LIMIT_REQUESTS = 5
    RATE_LIMIT_WINDOW = 60
    MAX_INPUT_LENGTH = 6000
    MAX_URL_LENGTH = 2048
    MAX_FILENAME_LENGTH = 255
    BLOCKED_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
        r'<form[^>]*>',
        r'<input[^>]*>',
        r'<textarea[^>]*>',
        r'<select[^>]*>',
        r'<button[^>]*>',
        r'<link[^>]*>',
        r'<meta[^>]*>',
        r'<style[^>]*>',
        r'<base[^>]*>',
        r'<bgsound[^>]*>',
        r'<xmp[^>]*>',
        r'<plaintext[^>]*>',
        r'<listing[^>]*>',
    ]
    PRIVATE_IP_RANGES = [
        ('10.0.0.0', '10.255.255.255'),
        ('172.16.0.0', '172.31.255.255'),
        ('192.168.0.0', '192.168.255.255'),
        ('127.0.0.0', '127.255.255.255'),
        ('169.254.0.0', '169.254.255.255'),
        ('224.0.0.0', '239.255.255.255'),
        ('240.0.0.0', '255.255.255.255'),
    ]

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
    
    def is_allowed(self, user_id: str) -> bool:
        current_time = time.time()
        user_requests = self.requests[user_id]
        user_requests = [req for req in user_requests 
                        if current_time - req < SecurityConfig.RATE_LIMIT_WINDOW]
        if len(user_requests) >= SecurityConfig.RATE_LIMIT_REQUESTS:
            return False
        user_requests.append(current_time)
        self.requests[user_id] = user_requests
        return True
    
    def get_remaining_requests(self, user_id: str) -> int:
        current_time = time.time()
        user_requests = self.requests[user_id]
        user_requests = [req for req in user_requests 
                        if current_time - req < SecurityConfig.RATE_LIMIT_WINDOW]
        return max(0, SecurityConfig.RATE_LIMIT_REQUESTS - len(user_requests))

class InputValidator:
    @staticmethod
    def is_safe_url(url: str) -> bool:
        try:
            if not url or len(url) > SecurityConfig.MAX_URL_LENGTH:
                return False
            
            parsed = urlparse(url)
            if parsed.scheme not in ['http', 'https']:
                return False
            url_lower = url.lower()
            for pattern in SecurityConfig.BLOCKED_PATTERNS:
                if re.search(pattern, url_lower, re.IGNORECASE):
                    return False
            if InputValidator._is_private_ip(parsed.netloc):
                return False
            if re.search(r'[<>"\']', url):
                return False
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def _is_private_ip(hostname: str) -> bool:
        try:
            if hostname in ['localhost', '127.0.0.1', '::1']:
                return True
            if hostname.startswith(('192.168.', '10.')):
                return True
            
            if hostname.startswith('172.'):
                parts = hostname.split('.')
                if len(parts) == 4 and 16 <= int(parts[1]) <= 31:
                    return True
            
            return False
        except Exception:
            return True
    
    @staticmethod
    def sanitize_input(text: str, max_length: Optional[int] = None) -> str:
        if not text or not isinstance(text, str):
            return ""

        max_len = max_length or SecurityConfig.MAX_INPUT_LENGTH
        if len(text) > max_len:
            return ""
        if re.search(r'[<>"\']', text):
            return ""

        text_lower = text.lower()
        for pattern in SecurityConfig.BLOCKED_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return ""

        sanitized = re.sub(r'[<>"\']', '', text)
        for pattern in SecurityConfig.BLOCKED_PATTERNS:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)

        return sanitized
    
    @staticmethod
    def validate_filename(filename: str) -> bool:
        if not filename or len(filename) > SecurityConfig.MAX_FILENAME_LENGTH:
            return False
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
        if re.search(r'[<>:"|?*]', filename):
            return False
        
        return True
    
    @staticmethod
    def validate_api_key(api_key: str, service_name: str) -> bool:
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

class SecurityHeaders:
    @staticmethod
    def get_security_headers() -> str:
        return """
        <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https:;">
        <meta http-equiv="X-Content-Type-Options" content="nosniff">
        <meta http-equiv="X-Frame-Options" content="DENY">
        <meta http-equiv="X-XSS-Protection" content="1; mode=block">
        <meta http-equiv="Referrer-Policy" content="strict-origin-when-cross-origin">
        <meta http-equiv="Permissions-Policy" content="geolocation=(), microphone=(), camera=()">
        """
    
    @staticmethod
    def get_csp_policy() -> str:
        return "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https:;"

class SecurityLogger:
    @staticmethod
    def log_security_event(event_type: str, details: str, user_id: Optional[str] = None):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        user_info = f"User: {user_id}" if user_id else "User: Unknown"
        
        safe_details = details or ""
        safe_details = safe_details.replace("\n", " ").replace("\r", " ")
        safe_details = re.sub(r"sk-[A-Za-z0-9]{10,}", "[REDACTED_KEY]", safe_details)
        if len(safe_details) > 120:
            safe_details = safe_details[:120] + "..."
        
        log_entry = f"[{timestamp}] SECURITY: {event_type} - {safe_details} - {user_info}"
        
        if st.session_state.get('security_log'):
            st.session_state.security_log.append(log_entry)
        else:
            st.session_state.security_log = [log_entry]

class SecurityManager:
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.validator = InputValidator()
    
    def check_request_security(self, user_id: str, input_data: Dict) -> Tuple[bool, str]:
        try:
            if not self.rate_limiter.is_allowed(user_id):
                SecurityLogger.log_security_event("RATE_LIMIT_EXCEEDED", f"User {user_id} exceeded rate limit", user_id)
                return False, "Rate limit exceeded. Please try again later."
            for key, value in input_data.items():
                if isinstance(value, str):
                    if not self.validator.sanitize_input(value):
                        SecurityLogger.log_security_event("INVALID_INPUT", f"Invalid input in field {key}", user_id)
                        return False, f"Invalid input in field {key}"
            if 'url' in input_data:
                if not self.validator.is_safe_url(input_data['url']):
                    SecurityLogger.log_security_event("UNSAFE_URL", f"Unsafe URL attempted: {input_data['url']}", user_id)
                    return False, "Invalid or unsafe URL provided"
            
            return True, "Security check passed"
            
        except Exception as e:
            SecurityLogger.log_security_event("SECURITY_CHECK_ERROR", str(e), user_id)
            return False, "Security validation failed"
    
    def get_user_id(self) -> str:
        if 'user_id' not in st.session_state:
            st.session_state.user_id = secrets.token_hex(16)
        return st.session_state.user_id

security_manager = SecurityManager()

def secure_function(func):
    def wrapper(*args, **kwargs):
        user_id = security_manager.get_user_id()
        input_data = {k: v for k, v in kwargs.items() if isinstance(v, str)}
        is_secure, message = security_manager.check_request_security(user_id, input_data)
        if not is_secure:
            st.error(f"Security Error: {message}")
            return None
        
        return func(*args, **kwargs)
    return wrapper
