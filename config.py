"""
Configuration Management
Centralizes all environment variables and configuration
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# API Configuration
# ============================================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
STUDENT_SECRET = os.getenv("STUDENT_SECRET")

# ============================================================================
# Server Configuration
# ============================================================================

API_PORT = int(os.getenv("API_PORT", "8000"))
API_HOST = os.getenv("API_HOST", "0.0.0.0")
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", f"http://localhost:{API_PORT}")

# ============================================================================
# Database Configuration
# ============================================================================

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./llm_deployment.db")
DATABASE_URL_REMOTE = os.getenv("DATABASE_URL_REMOTE")

# ============================================================================
# Evaluation Configuration
# ============================================================================

EVALUATION_TIMEOUT_SECONDS = int(os.getenv("EVALUATION_TIMEOUT_SECONDS", "600"))
MAX_RETRY_ATTEMPTS = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
GITHUB_PAGES_WAIT_TIME = int(os.getenv("GITHUB_PAGES_WAIT_TIME", "30"))

# ============================================================================
# Validation
# ============================================================================

def validate_config():
    """Validate that all required environment variables are set"""
    required = ["OPENAI_API_KEY", "GITHUB_TOKEN", "GITHUB_USERNAME", "STUDENT_SECRET"]
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        raise ValueError(
            f"❌ Missing required environment variables: {', '.join(missing)}\n"
            f"Please set them in your .env file or system environment."
        )
    
    print("✅ Configuration validated successfully!")
    return True

# Auto-validate on import
try:
    validate_config()
except ValueError as e:
    print(f"⚠️ Config Error: {e}")
