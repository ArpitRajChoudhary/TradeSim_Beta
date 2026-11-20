import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

print("Sending test request...", flush=True)

start = time.time()

try:
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents="Reply with exactly: TradeSim connection successful."
    )

    print("Response:", response.text)
    print("Time taken:", round(time.time() - start, 2), "seconds")

except Exception as error:
    print("Error:", repr(error))