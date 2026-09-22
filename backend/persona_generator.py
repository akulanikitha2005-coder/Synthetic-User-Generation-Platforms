import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env file")

print("Groq API Key Loaded Successfully")

client = Groq(api_key=api_key)

MODEL_NAME = "openai/gpt-oss-20b"


def generate_personas(product, audience, objective, count):

    prompt = f"""
You are an expert AI Persona Generator.

Generate exactly {count} unique synthetic user personas.

Return ONLY a valid JSON array.
Do not include markdown.
Do not include explanations.

Each persona MUST contain:

name
age
gender
occupation
location
education
income
marital_status
personality
lifestyle
interests
buying_behavior
preferred_platform
pain_points
email
phone
customer_id
bio
goal

Product:
{product}

Target Audience:
{audience}

Research Objective:
{objective}

Rules:

- Generate exactly {count} personas.
- Every persona must be unique.
- Every email must be unique.
- Every phone must be unique.
- Every customer_id must be unique.
- Goal must exactly equal "{objective}".
- Bio must contain 2-3 sentences.
- Interests must be a JSON array.
- Personas must match the target audience.
- Return only JSON.
"""

    try:

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert market research assistant. "
                        "Generate realistic synthetic personas. "
                        "Return only valid JSON."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.8,
            max_tokens=8192
        )

        text = response.choices[0].message.content.strip()

        print("\n========== GROQ RESPONSE ==========")
        print(text)
        print("===================================\n")

        if text.startswith("```"):
            text = text.replace("```json", "")
            text = text.replace("```", "")
            text = text.strip()

        start = text.find("[")
        end = text.rfind("]")

        if start == -1 or end == -1:
            raise Exception("Groq did not return a JSON array.")

        clean_json = text[start:end + 1]

        personas = json.loads(clean_json)

        if not isinstance(personas, list):
            raise Exception("Groq response is not a JSON array.")

        if len(personas) != count:
            raise Exception(
                f"Expected {count} personas, but received {len(personas)}."
            )

        for persona in personas:
            persona["goal"] = objective

        return personas

    except json.JSONDecodeError as e:

        print("JSON ERROR:", e)
        raise Exception("Groq returned invalid JSON.")

    except Exception as e:

        print("GROQ ERROR:", e)
        raise