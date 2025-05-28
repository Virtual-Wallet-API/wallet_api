import os

# Base URL
BASE_URL = "/fe"

# Connection
DB_URL = "postgresql+psycopg2://siso:siso@172.245.56.116:6789/wallet_test"

# Authentication
SECRET_KEY = "ahf807gt087TG)87tgB*^Tv8B^vrb*^*&BNT8B7T*B^T86BVR&VI^%R75V75VR5IR7R(67r9v^R&^AR^dr9^RDB^O*^"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 3600

# Stripe Configuration
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY",
                                   "pk_test_51RT1Qx4CifUjVaUzYmM09yyumjpR1GS6pS0RwsiTcvkpEGrGMH7rw3lTksZKswyxFdAnF8xxc0tiucjd7NnQNcPk00DxMVbyPn")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY",
                              "sk_test_51RT1Qx4CifUjVaUzRu8Nv8htWrmS91inHDpkEGdncJxnUzZuhbn1zCKtjkAOczQY2Hyak0y80dDX2yc4Erei3FXz00ihSFLEPj")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")  # Will be set when webhook is configured

# Mailjet API config
MAILJET_API_KEY = "a2c12e99dc915a4ab71a30d148740183"
MAILJET_SECRET = "dded18c64b347adcffcb3b8ed07f2887"
MAILJET_FROM_EMAIL = "steliyan.slavov31@icloud.com"
