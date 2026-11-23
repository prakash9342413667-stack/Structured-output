import os
import time
from typing import Literal

from dotenv import load_dotenv
from google import genai
from google.genai import errors
from pydantic import BaseModel, ConfigDict, ValidationError


# =====================================
# 1. LOAD GEMINI API KEY
# =====================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found. Please check your .env file.")

client = genai.Client(api_key=API_KEY)

# Tried in order. If one is overloaded (503) or unavailable (404),
# the program automatically moves on to the next one.
MODELS = [
    "gemini-3.8-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
]
ATTEMPTS_PER_MODEL = 3
RETRYABLE_CODES = (429, 500, 503, 504)   # temporary server-side problems
SKIP_MODEL_CODES = (404,)                # model retired / not available to you


# =====================================
# 2. DEFINE PYDANTIC SCHEMAS
# =====================================

class StructuredOutput(BaseModel):
    # Sent to Gemini as the response schema (must stay plain)
    topic: str
    category: str
    difficulty: Literal["Easy", "Medium", "Hard"]
    summary: str


class StrictOutput(StructuredOutput):
    # Used only for validation: rejects unexpected fields
    model_config = ConfigDict(extra="forbid")


# =====================================
# 3. GENERATE AND VALIDATE JSON
# =====================================

def generate_data(user_input: str) -> StructuredOutput:
    repair_hint = ""

    for model_name in MODELS:
        print(f"\n=== Using model: {model_name} ===")

        for attempt in range(1, ATTEMPTS_PER_MODEL + 1):
            print(f"\nAttempt {attempt}/{ATTEMPTS_PER_MODEL}")

            prompt = (
                "Convert the given input into structured JSON.\n"
                "Fields: topic, category, difficulty (Easy, Medium, or Hard), summary.\n"
                "Do not include extra fields.\n\n"
                f"Input: {user_input}\n\n"
                f"{repair_hint}"
            )

            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json",
                        "response_schema": StructuredOutput,
                    },
                )

                if not response.text:
                    raise ValueError("Empty response from Gemini.")

                print("\nRaw AI Response:")
                print(response.text)

                result = StrictOutput.model_validate_json(response.text)

                print("\nSUCCESS! VALID JSON OUTPUT")
                print("=" * 35)
                print(result.model_dump_json(indent=4))
                return result

            except (ValidationError, ValueError) as error:
                print("\nVALIDATION FAILED:")
                print(error)
                repair_hint = (
                    f"Your previous output was invalid.\nError: {error}\n"
                    "Correct the JSON and try again."
                )
                wait = 2

            except errors.APIError as error:
                print(f"\nAPI ERROR {error.code}: {error.message}")

                if error.code in SKIP_MODEL_CODES:
                    print("Model not available. Trying the next one...")
                    break                      # go to next model immediately

                if error.code not in RETRYABLE_CODES:
                    raise                      # bad key / bad request: stop

                wait = 2 ** attempt            # 2s, 4s, 8s

            if attempt < ATTEMPTS_PER_MODEL:
                print(f"Retrying in {wait} seconds...")
                time.sleep(wait)

    raise RuntimeError("All models failed. Please try again in a few minutes.")


# =====================================
# 4. MAIN PROGRAM
# =====================================

if __name__ == "__main__":

    print("=" * 45)
    print("       AI STRUCTURED OUTPUT VALIDATOR")
    print("=" * 45)

    user_input = input("\nEnter a topic: ").strip()

    if not user_input:
        print("Please enter a valid topic.")
    else:
        try:
            generate_data(user_input)
        except Exception as error:
            print("\nFINAL ERROR:", error)