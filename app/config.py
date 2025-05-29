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
MAILGUN_API_KEY = "da42b9bd5579054489ca67d71d218399-7c5e3295-ca3aecf8"
