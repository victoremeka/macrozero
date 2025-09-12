import os
import dotenv
from litellm import completion

dotenv.load_dotenv()

KIMI_API_KEY = os.getenv("KIMI_API_KEY")
KIMI_API_BASE_URL = os.getenv("KIMI_API_BASE_URL")

response = completion(
    model="moonshot/kimi-k2-0905-preview",
    messages=[{"content": "Hello, how are you?", "role": "user"}],
    # input="how's the weather today?",
    base_url=KIMI_API_BASE_URL,
    api_key=KIMI_API_KEY
)

print(response)