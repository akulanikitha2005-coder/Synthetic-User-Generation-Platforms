import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env file")

client = Groq(
    api_key=api_key,
    timeout=120.0,
    max_retries=2
)

MODEL_NAME = "openai/gpt-oss-20b"


def score_product_usage(personas, interviews):
    """
    Analyze persona interview responses and determine
    whether each persona would use the product.
    """

    prompt = f"""
You are an expert market research analyst.

Your task is to determine whether each synthetic persona
would use the proposed product based on their interview responses.

PERSONAS:
{json.dumps(personas, indent=2)}

INTERVIEW RESPONSES:
{json.dumps(interviews, indent=2)}

For every persona, determine:

1. Persona name
2. Customer ID if available
3. Whether they would use the product:
   - "Yes"
   - "Maybe"
   - "No"
4. A score from 0 to 100
5. A short reasoning explaining the score
6. Their relevant audience segment

Scoring guidance:

90-100 = Very strong likelihood of using the product
75-89  = Strong likelihood
50-74  = Moderate / uncertain likelihood
25-49  = Low likelihood
0-24   = Very unlikely

Important:
- Base the score on the persona profile and their actual interview responses.
- Do not invent interview responses.
- Consider product needs, preferences, price sensitivity,
  interests, concerns, and stated willingness to use or buy.
- Keep the reasoning specific to each persona.

After scoring individual personas, provide segment-level
aggregation.

Return ONLY valid JSON using exactly this structure:

{{
    "persona_scores": [
        {{
            "persona": "...",
            "customer_id": "...",
            "would_use": "Yes",
            "score": 0,
            "reasoning": "...",
            "segment": "..."
        }}
    ],

    "segment_summary": [
        {{
            "segment": "...",
            "persona_count": 0,
            "yes_count": 0,
            "maybe_count": 0,
            "no_count": 0,
            "average_score": 0,
            "would_use_percentage": 0,
            "reasoning": "..."
        }}
    ],

    "overall_score": 0,
    "overall_would_use_percentage": 0,
    "overall_summary": "..."
}}

Rules:

- Return only JSON.
- Do not include markdown.
- Score must be between 0 and 100.
- would_use must be exactly "Yes", "Maybe", or "No".
- average_score must be between 0 and 100.
- would_use_percentage must be between 0 and 100.
- overall_score must be between 0 and 100.
- overall_would_use_percentage must be between 0 and 100.
- Give reasoning for every persona.
- Give reasoning for every segment.
- The overall summary should explain the main reasons
  personas would or would not use the product.
"""

    try:
        print("\n======================================")
        print("📊 PRODUCT USAGE SCORING AGENT")
        print("======================================")

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert market research analyst. "
                        "Evaluate product adoption likelihood "
                        "from persona and interview data and "
                        "return structured JSON."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=5000,
            response_format={"type": "json_object"}
        )

        text = response.choices[0].message.content.strip()

        print("\n========== USAGE SCORE RESPONSE ==========")
        print(text)
        print("==========================================\n")

        scores = json.loads(text)

        return scores

    except json.JSONDecodeError as e:
        print("\n========== JSON ERROR ==========")
        print(e)
        print("================================\n")

        raise Exception(
            "Usage Scoring Agent returned invalid JSON."
        )

    except Exception as e:
        print("\n========== USAGE SCORING ERROR ==========")
        print("Error type:", type(e).__name__)
        print("Error:", repr(e))
        print("==========================================\n")

        raise