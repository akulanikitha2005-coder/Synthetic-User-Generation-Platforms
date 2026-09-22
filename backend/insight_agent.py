import os
import json
from dotenv import load_dotenv
from groq import Groq


# =========================
# LOAD ENVIRONMENT VARIABLES
# =========================

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env file")


# =========================
# GROQ CLIENT
# =========================

client = Groq(
    api_key=api_key,
    timeout=120.0,
    max_retries=2
)

MODEL_NAME = "openai/gpt-oss-20b"


# =========================
# INSIGHT EXTRACTION
# =========================

def extract_insights(personas, interviews):

    prompt = f"""
You are an expert market research insight extraction agent.

Analyze the synthetic user personas and their interview responses.

PERSONAS:
{json.dumps(personas, indent=2)}

INTERVIEW RESPONSES:
{json.dumps(interviews, indent=2)}

Identify:

1. Recurring themes
2. Sentiment breakdown
3. Agreement patterns
4. Behavioral trends
5. Key findings

Return ONLY valid JSON using exactly this structure:

{{
    "recurring_themes": [
        {{
            "theme": "...",
            "frequency": 0,
            "description": "..."
        }}
    ],

    "sentiment": {{
        "positive": 0,
        "neutral": 0,
        "negative": 0
    }},

    "agreement_patterns": [
        {{
            "topic": "...",
            "agreement_percentage": 0,
            "description": "..."
        }}
    ],

    "behavioral_trends": [
        "..."
    ],

    "key_findings": [
        "..."
    ]
}}

Rules:

- Return only JSON.
- Do not include markdown.
- recurring_themes must contain important themes found across responses.
- frequency should represent approximately how many personas mentioned the theme.
- sentiment values must be percentages.
- The three sentiment percentages should add up to 100.
- agreement_percentage must be between 0 and 100.
- behavioral_trends should describe meaningful user behavior.
- key_findings should summarize the most important research conclusions.
"""


    try:

        print("\n======================================")
        print("🔎 INSIGHT EXTRACTION AGENT")
        print("======================================")

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert market research analyst. "
                        "Analyze interview data and return structured JSON."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=5000,
            response_format={
                "type": "json_object"
            }
        )

        text = response.choices[0].message.content.strip()

        print("\n========== INSIGHT RESPONSE ==========")
        print(text)
        print("======================================\n")

        insights = json.loads(text)

        return insights


    except json.JSONDecodeError as e:

        print("\n========== JSON ERROR ==========")
        print(e)
        print("================================\n")

        raise Exception(
            "Insight Agent returned invalid JSON."
        )


    except Exception as e:

        print("\n========== INSIGHT AGENT ERROR ==========")
        print("Error type:", type(e).__name__)
        print("Error:", repr(e))
        print("=========================================\n")

        raise