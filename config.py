import os

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "idea2build-sessions")
S3_BUCKET = os.getenv("S3_BUCKET", "idea2build")
USER_TABLE = os.getenv("USER_TABLE", "idea2build-users")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3-haiku")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

FREE_TIER_LIMIT = 50

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_SOg8XJuvHfu2Hd")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "KLFKQyUpOTlVMTsGTnIw1wbo")
