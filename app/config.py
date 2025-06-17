from dotenv import load_dotenv
import os
from pathlib import Path

# Get the project root directory
ROOT_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
env_path = ROOT_DIR / '.env'
if not env_path.exists():
    raise FileNotFoundError(f".env file not found at {env_path}")

load_dotenv(env_path)

def get_env_var(name: str, required: bool = True) -> str:
    """Get environment variable with validation."""
    value = os.getenv(name)
    if required and not value:
        raise ValueError(f"Required environment variable {name} is not set")
    return value

# Base URL
BASE_URL = "/"

# Connection
DB_URL = get_env_var("DB_URL")

# Authentication
SECRET_KEY = get_env_var("SECRET_KEY")
ALGORITHM = get_env_var("ALGORITHM", required=False) or "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(get_env_var("ACCESS_TOKEN_EXPIRE_MINUTES", required=False) or "3600")

# Stripe Configuration
STRIPE_PUBLISHABLE_KEY = get_env_var("STRIPE_PUBLISHABLE_KEY", required=False)
STRIPE_SECRET_KEY = get_env_var("STRIPE_SECRET_KEY", required=False)
# STRIPE_WEBHOOK_SECRET = get_env_var("STRIPE_WEBHOOK_SECRET")  # Commented out as not currently used

# Mailgun API config
MAILGUN_API_KEY = get_env_var("MAILGUN_API_KEY", required=False)
MAILGUN_SANDBOX_DOMAIN = get_env_var("MAILGUN_SANDBOX_DOMAIN", required=False)
MAILGUN_URL = get_env_var("MAILGUN_URL", required=False)

# Cloudinary configuration (now only using CLOUDINARY_URL)
CLOUDINARY_URL = get_env_var("CLOUDINARY_URL")