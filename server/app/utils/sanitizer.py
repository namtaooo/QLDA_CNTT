import re

def sanitize_input(text: str) -> str:
    """
    Sanitize input to prevent basic injections and system prompt override attempts.
    """
    if not text:
        return ""
        
    # 1. Strip basic HTML/script tags
    text = re.sub(r'<[^>]*>', '', text)
    
    # 2. Neutralize classic SQLi payloads (though SQLAlchemy ORM protects us, this is extra defense)
    # Just avoiding blatant raw fragments, but let's keep it simple to not break normal text.
    # We'll just escape single quotes if needed, but parameterization is better.
    # Actually, ORM handles SQLi. Let's focus on Prompt Injection.
    
    # 3. Prompt injection heuristic checks
    # Try to block attempts to override the primary instruction
    injection_patterns = [
        r"(?i)\bignore previous instructions\b",
        r"(?i)\bdisregard previous instructions\b",
        r"(?i)\bsystem prompt\b",
        r"(?i)\byou are no longer\b",
        r"(?i)\bforget everything\b"
    ]
    
    for pattern in injection_patterns:
        text = re.sub(pattern, "[CENSORED_INSTRUCTION]", text)
        
    return text.strip()
