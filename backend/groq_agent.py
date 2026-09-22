# ============================================================
# groq_agent.py
# Synthetic User Generation Platform
# ============================================================

import os
import json
import time
import random
import re
from copy import deepcopy

from dotenv import load_dotenv
from groq import Groq


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")


# ============================================================
# GROQ CLIENT
# ============================================================

client = None

if api_key:
    client = Groq(
        api_key=api_key,
        timeout=120.0,
        max_retries=1
    )


MODEL_NAME = "openai/gpt-oss-20b"


# ============================================================
# PERSONA FIELDS
# ============================================================

PERSONA_FIELDS = [
    "name",
    "age",
    "gender",
    "occupation",
    "location",
    "education",
    "income",
    "marital_status",
    "personality",
    "lifestyle",
    "interests",
    "buying_behavior",
    "preferred_platform",
    "pain_points",
    "email",
    "phone",
    "customer_id",
    "bio",
    "goal",
    "health_conscious",
    "budget_conscious",
    "eco_friendly",
    "premium_buyer"
]


# ============================================================
# LOCAL DATA
# ============================================================

FIRST_NAMES = [
    "Ava",
    "Lena",
    "Maya",
    "Sofia",
    "Nina",
    "Olivia",
    "Emma",
    "Aria",
    "Chloe",
    "Mia",
    "Zoe",
    "Grace",
    "Ella",
    "Lily",
    "Amelia",
    "Harper",
    "Isla",
    "Layla",
    "Nora",
    "Emily",
    "Anika",
    "Priya",
    "Riya",
    "Sara",
    "Meera",
    "Kavya",
    "Isha",
    "Diya",
    "Neha",
    "Tara"
]


LAST_NAMES = [
    "Martinez",
    "Patel",
    "Chen",
    "Rossi",
    "Kim",
    "Brown",
    "Johnson",
    "Sharma",
    "Garcia",
    "Wilson",
    "Thomas",
    "Lee",
    "Singh",
    "Williams",
    "Davis",
    "Miller",
    "Anderson",
    "Taylor",
    "Moore",
    "Jackson",
    "Kumar",
    "Mehta",
    "Kapoor",
    "Shah",
    "Verma"
]


OCCUPATIONS = [
    "Software Engineer",
    "Product Designer",
    "Marketing Manager",
    "Data Analyst",
    "Teacher",
    "Healthcare Professional",
    "Financial Analyst",
    "Content Creator",
    "Business Consultant",
    "Project Manager",
    "UX Researcher",
    "Entrepreneur",
    "Sales Manager",
    "HR Specialist",
    "Graphic Designer",
    "Research Associate"
]


LOCATIONS = [
    "New York, USA",
    "Austin, Texas",
    "San Francisco, California",
    "Seattle, Washington",
    "Chicago, Illinois",
    "Boston, Massachusetts",
    "Los Angeles, California",
    "Denver, Colorado",
    "Atlanta, Georgia",
    "Dallas, Texas",
    "Hyderabad, India",
    "Bengaluru, India",
    "Mumbai, India",
    "Pune, India",
    "Delhi, India"
]


EDUCATION = [
    "Bachelor's degree",
    "Master's degree",
    "MBA",
    "Engineering degree",
    "Graduate degree",
    "Professional certification"
]


MARITAL_STATUS = [
    "Single",
    "Married",
    "In a relationship"
]


PERSONALITIES = [
    "Analytical and curious",
    "Practical and organized",
    "Social and energetic",
    "Thoughtful and research-oriented",
    "Independent and confident",
    "Budget-conscious and practical",
    "Health-focused and disciplined",
    "Creative and experimental",
    "Technology-oriented and curious",
    "Environmentally conscious and deliberate"
]


LIFESTYLES = [
    "Active urban lifestyle",
    "Busy professional lifestyle",
    "Health-focused lifestyle",
    "Family-oriented lifestyle",
    "Minimalist lifestyle",
    "Social and active lifestyle",
    "Eco-conscious lifestyle",
    "Technology-focused lifestyle",
    "Fitness-oriented lifestyle",
    "Balanced work-life lifestyle"
]


INTEREST_GROUPS = [
    [
        "Fitness",
        "Travel",
        "Technology"
    ],
    [
        "Yoga",
        "Wellness",
        "Nutrition"
    ],
    [
        "Fashion",
        "Beauty",
        "Social Media"
    ],
    [
        "Running",
        "Outdoor Activities",
        "Healthy Food"
    ],
    [
        "Technology",
        "Shopping",
        "Entertainment"
    ],
    [
        "Sustainability",
        "Organic Products",
        "Wellness"
    ],
    [
        "Cooking",
        "Family",
        "Health"
    ],
    [
        "Photography",
        "Travel",
        "Lifestyle"
    ],
    [
        "Personal Finance",
        "Shopping",
        "Technology"
    ],
    [
        "Books",
        "Fitness",
        "Self Improvement"
    ]
]


BUYING_BEHAVIORS = [
    "Researches products extensively before purchasing",
    "Compares prices and reviews before purchasing",
    "Prefers trusted brands with proven results",
    "Looks for recommendations from friends and online communities",
    "Usually purchases after checking product ingredients and specifications",
    "Prefers convenient online shopping",
    "Watches demonstrations and reviews before buying",
    "Looks for products that fit an active lifestyle",
    "Values transparent product information",
    "Is willing to pay more for products perceived as higher quality"
]


PLATFORMS = [
    "Instagram and online stores",
    "Amazon and Google Search",
    "YouTube and Instagram",
    "TikTok and online stores",
    "Reddit and Google Search",
    "Facebook and online stores",
    "YouTube and brand websites",
    "Instagram and brand websites"
]


PAIN_POINTS = [
    "High prices and too many product choices",
    "Difficulty comparing products",
    "Lack of transparent product information",
    "Limited time for product research",
    "Concerns about product quality",
    "Unclear ingredients or specifications",
    "Difficulty finding trustworthy reviews",
    "Concern about value for money",
    "Products that do not fit an active lifestyle",
    "Lack of environmentally friendly options"
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_string(value, default=""):
    """
    Safely convert a value into a string.
    """

    if value is None:
        return default

    if isinstance(value, str):
        value = value.strip()

        if value:
            return value

        return default

    return str(value).strip()


def clean_bool(value, default=False):
    """
    Convert different AI representations into bool.
    """

    if isinstance(value, bool):
        return value

    if isinstance(value, str):

        value = value.strip().lower()

        if value in [
            "true",
            "yes",
            "y",
            "1"
        ]:
            return True

        if value in [
            "false",
            "no",
            "n",
            "0"
        ]:
            return False

    if isinstance(value, (int, float)):
        return bool(value)

    return default


def clean_age(value):
    """
    Safely convert age into an integer.
    """

    try:

        age = int(value)

        if age < 18:
            return 18

        if age > 100:
            return 100

        return age

    except Exception:

        return 25


def clean_income(value):
    """
    Safely convert income into an integer.
    """

    try:

        if isinstance(value, str):

            value = (
                value
                .replace("$", "")
                .replace(",", "")
                .replace("₹", "")
                .strip()
            )

        return int(float(value))

    except Exception:

        return 60000


def clean_interests(value):
    """
    Always return interests as a list.
    """

    if isinstance(value, list):

        return [
            clean_string(item)
            for item in value
            if clean_string(item)
        ]

    if isinstance(value, str):

        if "," in value:

            return [
                item.strip()
                for item in value.split(",")
                if item.strip()
            ]

        if value.strip():

            return [value.strip()]

    return []


def parse_json_response(content):
    """
    Parse JSON returned by Groq.
    """

    if not content:

        raise ValueError(
            "Groq returned an empty response."
        )

    content = content.strip()

    # Remove markdown fences if model accidentally adds them.
    if content.startswith("```"):

        content = re.sub(
            r"^```(?:json)?",
            "",
            content,
            flags=re.IGNORECASE
        )

        content = re.sub(
            r"```$",
            "",
            content
        )

        content = content.strip()

    try:

        return json.loads(content)

    except json.JSONDecodeError:

        # Try extracting the JSON object.
        start = content.find("{")
        end = content.rfind("}")

        if start != -1 and end != -1:

            possible_json = content[
                start:end + 1
            ]

            try:

                return json.loads(
                    possible_json
                )

            except Exception:
                pass

        raise ValueError(
            "Groq returned invalid JSON."
        )


# ============================================================
# NORMALIZE PERSONA
# ============================================================

def normalize_persona(
    persona,
    product,
    audience,
    objective,
    index
):
    """
    Normalize one persona and guarantee all required fields.
    """

    if not isinstance(persona, dict):

        persona = {}

    normalized = {}

    normalized["name"] = clean_string(
        persona.get("name"),
        f"Synthetic User {index}"
    )

    normalized["age"] = clean_age(
        persona.get("age")
    )

    normalized["gender"] = clean_string(
        persona.get("gender"),
        "Not specified"
    )

    normalized["occupation"] = clean_string(
        persona.get("occupation"),
        "Professional"
    )

    normalized["location"] = clean_string(
        persona.get("location"),
        "United States"
    )

    normalized["education"] = clean_string(
        persona.get("education"),
        "Bachelor's degree"
    )

    normalized["income"] = clean_income(
        persona.get("income")
    )

    normalized["marital_status"] = clean_string(
        persona.get("marital_status"),
        "Single"
    )

    normalized["personality"] = clean_string(
        persona.get("personality"),
        "Practical and curious"
    )

    normalized["lifestyle"] = clean_string(
        persona.get("lifestyle"),
        "Balanced lifestyle"
    )

    normalized["interests"] = clean_interests(
        persona.get("interests")
    )

    normalized["buying_behavior"] = clean_string(
        persona.get("buying_behavior"),
        "Researches products before purchasing"
    )

    normalized["preferred_platform"] = clean_string(
        persona.get("preferred_platform"),
        "Online stores"
    )

    normalized["pain_points"] = clean_string(
        persona.get("pain_points"),
        "Limited time and too many product choices"
    )

    # Synthetic contact information.
    normalized["email"] = (
        f"synthetic.user{index}@example.com"
    )

    normalized["phone"] = (
        f"+1-555-010-{index:04d}"
    )

    normalized["customer_id"] = (
        f"CUST-{index:04d}"
    )

    normalized["bio"] = clean_string(
        persona.get("bio"),
        (
            f"A synthetic customer representing "
            f"the {audience} audience interested "
            f"in {product}."
        )
    )

    # Always use the user's actual objective.
    normalized["goal"] = objective

    normalized["health_conscious"] = clean_bool(
        persona.get("health_conscious"),
        False
    )

    normalized["budget_conscious"] = clean_bool(
        persona.get("budget_conscious"),
        False
    )

    normalized["eco_friendly"] = clean_bool(
        persona.get("eco_friendly"),
        False
    )

    normalized["premium_buyer"] = clean_bool(
        persona.get("premium_buyer"),
        False
    )

    # Guarantee every field.
    for field in PERSONA_FIELDS:

        if field not in normalized:

            normalized[field] = ""

    return normalized


# ============================================================
# GROQ BATCH GENERATION
# ============================================================

def generate_persona_batch(
    product,
    audience,
    objective,
    batch_size,
    batch_number
):
    """
    Ask Groq for a small number of base personas.

    This function should only be used for a small number
    of personas so that API token usage remains low.
    """

    if client is None:

        raise ValueError(
            "GROQ_API_KEY is not configured."
        )

    system_prompt = """
You are an expert synthetic user research assistant.

Generate fictional customer personas for product research.

IMPORTANT:

- Return ONLY valid JSON.
- Do not return Markdown.
- Do not explain your answer.
- Generate exactly the requested number.
- Every persona must be different.
- Personas must match the product.
- Personas must match the target audience.
- Personas must match the research objective.
- Do not use real people's private information.
- Email, phone and customer_id may be left blank.
- The application will create synthetic contact information.

The JSON must have this structure:

{
  "personas": [
    {
      "name": "...",
      "age": 25,
      "gender": "...",
      "occupation": "...",
      "location": "...",
      "education": "...",
      "income": 60000,
      "marital_status": "...",
      "personality": "...",
      "lifestyle": "...",
      "interests": ["...", "..."],
      "buying_behavior": "...",
      "preferred_platform": "...",
      "pain_points": "...",
      "email": "",
      "phone": "",
      "customer_id": "",
      "bio": "...",
      "goal": "...",
      "health_conscious": true,
      "budget_conscious": false,
      "eco_friendly": true,
      "premium_buyer": false
    }
  ]
}
"""

    user_prompt = f"""
Generate exactly {batch_size} fictional synthetic personas.

PRODUCT:
{product}

TARGET AUDIENCE:
{audience}

RESEARCH OBJECTIVE:
{objective}

BATCH:
{batch_number}

Make the personas meaningfully different in their:
- occupation
- location
- personality
- lifestyle
- interests
- buying behavior
- pain points
- spending behavior
- digital behavior

Keep them relevant to the target audience.

Return ONLY JSON.
"""

    print(
        f"🤖 Groq generating "
        f"batch {batch_number}: "
        f"{batch_size} base personas"
    )

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        temperature=0.8,
        max_tokens=4500,
        response_format={
            "type": "json_object"
        }
    )

    if not response.choices:

        raise ValueError(
            "Groq returned no choices."
        )

    content = response.choices[0].message.content

    data = parse_json_response(content)

    if not isinstance(data, dict):

        raise ValueError(
            "Groq response was not a JSON object."
        )

    personas = data.get("personas")

    if not isinstance(personas, list):

        raise ValueError(
            "Groq response does not contain "
            "a personas array."
        )

    if len(personas) == 0:

        raise ValueError(
            "Groq returned zero personas."
        )

    return personas


# ============================================================
# GENERATE BASE PERSONAS
# ============================================================

def generate_base_personas(
    product,
    audience,
    objective,
    base_count
):
    """
    Generate a small number of AI personas.

    For 100 personas, only 10 are requested from Groq.
    """

    base_personas = []

    batch_size = 5

    total_batches = (
        (base_count + batch_size - 1)
        // batch_size
    )

    for batch_number in range(
        1,
        total_batches + 1
    ):

        remaining = (
            base_count -
            len(base_personas)
        )

        current_size = min(
            batch_size,
            remaining
        )

        max_attempts = 2

        successful_batch = None

        for attempt in range(
            1,
            max_attempts + 1
        ):

            try:

                print(
                    f"🔄 AI batch "
                    f"{batch_number}/{total_batches} "
                    f"attempt "
                    f"{attempt}/{max_attempts}"
                )

                successful_batch = (
                    generate_persona_batch(
                        product=product,
                        audience=audience,
                        objective=objective,
                        batch_size=current_size,
                        batch_number=batch_number
                    )
                )

                break

            except Exception as error:

                error_text = str(error)

                print(
                    f"⚠️ AI batch "
                    f"{batch_number} failed:"
                )

                print(error_text)

                # Rate limit errors should not be
                # repeatedly hammered.
                if (
                    "429" in error_text
                    or "rate limit" in error_text.lower()
                    or "rate_limit" in error_text.lower()
                ):

                    print(
                        "🚦 Groq rate limit detected."
                    )

                    break

                if attempt < max_attempts:

                    time.sleep(3)

        if successful_batch is None:

            raise RuntimeError(
                "AI generation unavailable."
            )

        base_personas.extend(
            successful_batch
        )

        # Keep exactly requested amount.
        base_personas = base_personas[
            :base_count
        ]

    return base_personas


# ============================================================
# LOCAL PERSONA GENERATOR
# ============================================================

def create_local_persona(
    product,
    audience,
    objective,
    index
):
    """
    Create a completely synthetic persona locally.

    This is used as a fallback when Groq is unavailable.
    """

    random.seed(
        1000 + index
    )

    name = (
        FIRST_NAMES[
            (index - 1) % len(FIRST_NAMES)
        ]
        + " "
        + LAST_NAMES[
            (index * 3) % len(LAST_NAMES)
        ]
    )

    occupation = random.choice(
        OCCUPATIONS
    )

    location = random.choice(
        LOCATIONS
    )

    education = random.choice(
        EDUCATION
    )

    personality = random.choice(
        PERSONALITIES
    )

    lifestyle = random.choice(
        LIFESTYLES
    )

    interests = random.choice(
        INTEREST_GROUPS
    )

    buying_behavior = random.choice(
        BUYING_BEHAVIORS
    )

    platform = random.choice(
        PLATFORMS
    )

    pain_point = random.choice(
        PAIN_POINTS
    )

    # Keep age aligned with "women aged 25"
    # or similar explicit age requests.
    age = extract_requested_age(
        audience
    )

    if age is None:
        age = random.randint(
            22,
            40
        )

    income = random.choice([
        35000,
        42000,
        48000,
        55000,
        62000,
        70000,
        78000,
        85000,
        95000,
        110000
    ])

    health_conscious = (
        "health" in lifestyle.lower()
        or random.random() > 0.45
    )

    budget_conscious = (
        random.random() > 0.60
    )

    eco_friendly = (
        "eco" in lifestyle.lower()
        or "sustain" in " ".join(interests).lower()
        or random.random() > 0.55
    )

    premium_buyer = (
        income >= 78000
        and random.random() > 0.45
    )

    bio = (
        f"{name} is a fictional {age}-year-old "
        f"{occupation.lower()} based in {location}. "
        f"They have a {lifestyle.lower()} and "
        f"tend to be {personality.lower()}. "
        f"When evaluating {product}, they "
        f"{buying_behavior.lower()}."
    )

    persona = {
        "name": name,
        "age": age,
        "gender": "Female",
        "occupation": occupation,
        "location": location,
        "education": education,
        "income": income,
        "marital_status": random.choice(
            MARITAL_STATUS
        ),
        "personality": personality,
        "lifestyle": lifestyle,
        "interests": interests,
        "buying_behavior": buying_behavior,
        "preferred_platform": platform,
        "pain_points": pain_point,
        "email": "",
        "phone": "",
        "customer_id": "",
        "bio": bio,
        "goal": objective,
        "health_conscious": health_conscious,
        "budget_conscious": budget_conscious,
        "eco_friendly": eco_friendly,
        "premium_buyer": premium_buyer
    }

    return persona


# ============================================================
# EXTRACT AGE FROM AUDIENCE
# ============================================================

def extract_requested_age(audience):
    """
    Extract an explicit age from the target audience.

    Example:
        "women aged 25"
        -> 25

    If no clear age exists, return None.
    """

    if not audience:
        return None

    patterns = [
        r"\bage\s*(?:of)?\s*(\d{2})\b",
        r"\baged\s*(\d{2})\b",
        r"\b(\d{2})\s*years?\s*old\b",
        r"\b(\d{2})[- ]year[- ]old\b"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            audience.lower()
        )

        if match:

            age = int(
                match.group(1)
            )

            if 18 <= age <= 100:

                return age

    return None


# ============================================================
# CREATE VARIATION FROM BASE PERSONA
# ============================================================

def create_persona_variation(
    base,
    product,
    audience,
    objective,
    index,
    variation_number
):
    """
    Create a unique synthetic variation of an AI persona.

    The AI persona provides the research foundation.
    Local variation prevents excessive API usage.
    """

    random.seed(
        5000 + index
    )

    persona = deepcopy(
        base
    )

    # --------------------------------------------------------
    # Name
    # --------------------------------------------------------

    name_index = (
        index - 1
    ) % len(FIRST_NAMES)

    last_index = (
        index * 7
    ) % len(LAST_NAMES)

    persona["name"] = (
        FIRST_NAMES[name_index]
        + " "
        + LAST_NAMES[last_index]
    )

    # --------------------------------------------------------
    # Age
    # --------------------------------------------------------

    requested_age = extract_requested_age(
        audience
    )

    if requested_age is not None:

        persona["age"] = requested_age

    else:

        original_age = clean_age(
            persona.get("age")
        )

        variation = random.choice([
            -2,
            -1,
            0,
            0,
            1,
            2
        ])

        persona["age"] = max(
            18,
            min(
                70,
                original_age + variation
            )
        )

    # --------------------------------------------------------
    # Demographic variation
    # --------------------------------------------------------

    persona["occupation"] = random.choice(
        OCCUPATIONS
    )

    persona["location"] = random.choice(
        LOCATIONS
    )

    persona["education"] = random.choice(
        EDUCATION
    )

    persona["marital_status"] = random.choice(
        MARITAL_STATUS
    )

    # --------------------------------------------------------
    # Financial variation
    # --------------------------------------------------------

    persona["income"] = random.choice([
        35000,
        42000,
        48000,
        55000,
        62000,
        70000,
        78000,
        85000,
        95000,
        110000
    ])

    # --------------------------------------------------------
    # Personality
    # --------------------------------------------------------

    persona["personality"] = random.choice(
        PERSONALITIES
    )

    persona["lifestyle"] = random.choice(
        LIFESTYLES
    )

    # --------------------------------------------------------
    # Interests
    # --------------------------------------------------------

    persona["interests"] = random.choice(
        INTEREST_GROUPS
    )

    # --------------------------------------------------------
    # Buying behavior
    # --------------------------------------------------------

    persona["buying_behavior"] = random.choice(
        BUYING_BEHAVIORS
    )

    persona["preferred_platform"] = random.choice(
        PLATFORMS
    )

    persona["pain_points"] = random.choice(
        PAIN_POINTS
    )

    # --------------------------------------------------------
    # Behavioral flags
    # --------------------------------------------------------

    persona["health_conscious"] = (
        random.random() > 0.35
    )

    persona["budget_conscious"] = (
        random.random() > 0.55
    )

    persona["eco_friendly"] = (
        random.random() > 0.45
    )

    persona["premium_buyer"] = (
        persona["income"] >= 78000
        and random.random() > 0.35
    )

    # --------------------------------------------------------
    # Goal
    # --------------------------------------------------------

    persona["goal"] = objective

    # --------------------------------------------------------
    # Bio
    # --------------------------------------------------------

    persona["bio"] = (
        f"{persona['name']} is a fictional "
        f"{persona['age']}-year-old "
        f"{persona['occupation'].lower()} "
        f"living in {persona['location']}. "
        f"They have a {persona['lifestyle'].lower()} "
        f"and are {persona['personality'].lower()}. "
        f"They are evaluating {product} as part of "
        f"a synthetic research audience."
    )

    return persona


# ============================================================
# GUARANTEE CONTACT INFORMATION
# ============================================================

def add_unique_identifiers(
    persona,
    index
):
    """
    Add guaranteed unique synthetic identifiers.
    """

    persona["customer_id"] = (
        f"CUST-{index:04d}"
    )

    persona["email"] = (
        f"synthetic.user"
        f"{index}"
        f"@example.com"
    )

    persona["phone"] = (
        f"+1-555-010-{index:04d}"
    )

    return persona


# ============================================================
# FINAL NORMALIZATION
# ============================================================

def finalize_persona(
    persona,
    product,
    audience,
    objective,
    index
):
    """
    Final validation and normalization.
    """

    persona = normalize_persona(
        persona=persona,
        product=product,
        audience=audience,
        objective=objective,
        index=index
    )

    persona = add_unique_identifiers(
        persona,
        index
    )

    # Make sure objective is always correct.
    persona["goal"] = objective

    # Make sure interests is a list.
    persona["interests"] = clean_interests(
        persona.get("interests")
    )

    # Make sure numeric fields are valid.
    persona["age"] = clean_age(
        persona.get("age")
    )

    persona["income"] = clean_income(
        persona.get("income")
    )

    # Make sure booleans are valid.
    persona["health_conscious"] = clean_bool(
        persona.get("health_conscious")
    )

    persona["budget_conscious"] = clean_bool(
        persona.get("budget_conscious")
    )

    persona["eco_friendly"] = clean_bool(
        persona.get("eco_friendly")
    )

    persona["premium_buyer"] = clean_bool(
        persona.get("premium_buyer")
    )

    # Final field guarantee.
    for field in PERSONA_FIELDS:

        if field not in persona:

            persona[field] = ""

    return persona


# ============================================================
# MAIN FUNCTION
# ============================================================

def generate_personas(
    product,
    audience,
    objective,
    count
):
    """
    Main persona generation function.

    Supports 1-100 personas.

    Strategy:

        1-10 personas:
            Generate with Groq.

        11-100 personas:
            Generate a small AI base set.
            Create additional local variations.

        If Groq is unavailable:
            Generate all personas locally.
    """

    # --------------------------------------------------------
    # Validate input
    # --------------------------------------------------------

    try:

        count = int(count)

    except Exception:

        raise ValueError(
            "Persona count must be a number."
        )

    if count < 1:

        raise ValueError(
            "Persona count must be at least 1."
        )

    if count > 100:

        raise ValueError(
            "Maximum supported persona count is 100."
        )

    product = clean_string(
        product
    )

    audience = clean_string(
        audience
    )

    objective = clean_string(
        objective
    )

    if not product:

        raise ValueError(
            "Product is required."
        )

    if not audience:

        raise ValueError(
            "Target audience is required."
        )

    if not objective:

        raise ValueError(
            "Research objective is required."
        )

    print("")
    print("=" * 70)
    print("🚀 SYNTHETIC USER GENERATION")
    print("=" * 70)
    print(
        f"Product: {product}"
    )
    print(
        f"Audience: {audience}"
    )
    print(
        f"Objective: {objective}"
    )
    print(
        f"Requested personas: {count}"
    )
    print("=" * 70)

    # ========================================================
    # SMALL REQUESTS
    # ========================================================

    if count <= 10:

        try:

            print(
                "🤖 Generating personas with Groq..."
            )

            raw_personas = generate_base_personas(
                product=product,
                audience=audience,
                objective=objective,
                base_count=count
            )

            personas = []

            for index, raw_persona in enumerate(
                raw_personas[:count],
                start=1
            ):

                persona = finalize_persona(
                    persona=raw_persona,
                    product=product,
                    audience=audience,
                    objective=objective,
                    index=index
                )

                personas.append(
                    persona
                )

            if len(personas) == count:

                print(
                    f"✅ Generated {count} "
                    f"AI personas."
                )

                return personas

        except Exception as error:

            print(
                "⚠️ Groq generation failed."
            )

            print(
                f"Reason: {str(error)}"
            )

            print(
                "🔄 Switching to local "
                "synthetic generation."
            )

    # ========================================================
    # LARGE REQUEST
    # ========================================================

    # For large requests, only ask AI for a small
    # foundation set.
    base_count = min(
        10,
        count
    )

    base_personas = []

    try:

        print("")
        print(
            "🤖 Creating "
            f"{base_count} AI base personas..."
        )

        base_personas = generate_base_personas(
            product=product,
            audience=audience,
            objective=objective,
            base_count=base_count
        )

        print(
            f"✅ Received "
            f"{len(base_personas)} AI base personas."
        )

    except Exception as error:

        print("")
        print(
            "⚠️ AI base generation unavailable."
        )

        print(
            f"Reason: {str(error)}"
        )

        print(
            "🔄 Using local synthetic persona "
            "generation for this request."
        )

        base_personas = []

    # ========================================================
    # BUILD FINAL PERSONAS
    # ========================================================

    personas = []

    for index in range(
        1,
        count + 1
    ):

        # ----------------------------------------------------
        # Use AI persona as foundation when available.
        # ----------------------------------------------------

        if base_personas:

            base_index = (
                (index - 1)
                % len(base_personas)
            )

            base = base_personas[
                base_index
            ]

            persona = create_persona_variation(
                base=base,
                product=product,
                audience=audience,
                objective=objective,
                index=index,
                variation_number=index
            )

        # ----------------------------------------------------
        # Otherwise create locally.
        # ----------------------------------------------------

        else:

            persona = create_local_persona(
                product=product,
                audience=audience,
                objective=objective,
                index=index
            )

        # ----------------------------------------------------
        # Finalize.
        # ----------------------------------------------------

        persona = finalize_persona(
            persona=persona,
            product=product,
            audience=audience,
            objective=objective,
            index=index
        )

        personas.append(
            persona
        )

        # ----------------------------------------------------
        # Progress display.
        # ----------------------------------------------------

        if (
            index <= 10
            or index % 10 == 0
            or index == count
        ):

            print(
                f"📊 Progress: "
                f"{index}/{count}"
            )

    # ========================================================
    # FINAL VALIDATION
    # ========================================================

    if len(personas) != count:

        raise Exception(
            f"Generation incomplete. "
            f"Expected {count}, "
            f"got {len(personas)}."
        )

    # --------------------------------------------------------
    # Validate IDs.
    # --------------------------------------------------------

    customer_ids = [
        p["customer_id"]
        for p in personas
    ]

    emails = [
        p["email"]
        for p in personas
    ]

    phones = [
        p["phone"]
        for p in personas
    ]

    if len(set(customer_ids)) != count:

        raise Exception(
            "Duplicate customer IDs detected."
        )

    if len(set(emails)) != count:

        raise Exception(
            "Duplicate email addresses detected."
        )

    if len(set(phones)) != count:

        raise Exception(
            "Duplicate phone numbers detected."
        )

    # --------------------------------------------------------
    # Validate fields.
    # --------------------------------------------------------

    for index, persona in enumerate(
        personas,
        start=1
    ):

        missing = [
            field
            for field in PERSONA_FIELDS
            if field not in persona
        ]

        if missing:

            raise Exception(
                f"Persona {index} is missing fields: "
                f"{missing}"
            )

    # ========================================================
    # COMPLETE
    # ========================================================

    print("")
    print("=" * 70)
    print("🎉 GENERATION COMPLETE")
    print("=" * 70)
    print(
        f"👥 Total personas: {len(personas)}"
    )
    print(
        f"🎯 Objective: {objective}"
    )

    if base_personas:

        print(
            f"🤖 AI base personas: "
            f"{len(base_personas)}"
        )

        print(
            "🧬 Additional personas: "
            "locally generated variations"
        )

    else:

        print(
            "💻 Generation mode: "
            "local synthetic fallback"
        )

    print("=" * 70)

    return personas


# ============================================================
# OPTIONAL TEST
# ============================================================

if __name__ == "__main__":

    print(
        "Testing synthetic persona generator..."
    )

    test_personas = generate_personas(
        product="Organic skincare product",
        audience="women aged 25",
        objective="understand their product preferences",
        count=10
    )

    print("")
    print(
        json.dumps(
            test_personas[:2],
            indent=2
        )
    )