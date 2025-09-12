import os
import dotenv
# from google.adk.models.lite_llm import LiteLlm
import litellm

dotenv.load_dotenv()

KIMI_API_KEY = os.getenv("KIMI_API_KEY")
KIMI_API_BASE_URL = os.getenv("KIMI_API_BASE_URL")

client = litellm.responses(
    model="moonshot/kimi-k2-0905-preview"

)
