import os
from dotenv import load_dotenv
from groq import Groq


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env file")

print("✅ Groq API Key Loaded Successfully")


# =========================================================
# GROQ CLIENT
# =========================================================

client = Groq(
    api_key=api_key,
    timeout=120.0,
    max_retries=2
)


# =========================================================
# MODEL
# =========================================================

MODEL_NAME = "openai/gpt-oss-20b"


# =========================================================
# CONVERSATION MEMORY
# =========================================================

conversation_memory = {}


# =========================================================
# GET UNIQUE PERSONA KEY
# =========================================================

def get_persona_key(persona):

    customer_id = persona.get("customer_id")

    if customer_id:
        return str(customer_id)

    name = persona.get("name")

    if name:
        return str(name)

    return "unknown_persona"


# =========================================================
# ASK PERSONA
# =========================================================

def ask_persona(persona, question):

    persona_key = get_persona_key(persona)

    # Create memory for this persona
    if persona_key not in conversation_memory:

        conversation_memory[persona_key] = []


    history = conversation_memory[persona_key]


    # =====================================================
    # PERSONA INFORMATION
    # =====================================================

    persona_information = f"""
You are role-playing as a synthetic user persona for a
market research interview.

You must answer as the persona described below.

PERSONA PROFILE

Name: {persona.get("name")}
Age: {persona.get("age")}
Gender: {persona.get("gender")}
Occupation: {persona.get("occupation")}
Location: {persona.get("location")}
Education: {persona.get("education")}
Income: {persona.get("income")}
Marital Status: {persona.get("marital_status")}

Personality:
{persona.get("personality")}

Lifestyle:
{persona.get("lifestyle")}

Interests:
{persona.get("interests")}

Buying Behavior:
{persona.get("buying_behavior")}

Preferred Platform:
{persona.get("preferred_platform")}

Pain Points:
{persona.get("pain_points")}

Bio:
{persona.get("bio")}

Research Goal:
{persona.get("goal")}

Health Conscious:
{persona.get("health_conscious")}

Budget Conscious:
{persona.get("budget_conscious")}

Eco Friendly:
{persona.get("eco_friendly")}

Premium Buyer:
{persona.get("premium_buyer")}


IMPORTANT ROLE-PLAY RULES

1. Answer as this specific persona.
2. Keep your answers consistent with the persona profile.
3. Use the persona's personality and buying behavior.
4. Consider the persona's pain points.
5. Consider the persona's budget and lifestyle.
6. Do not invent unrelated personal information.
7. Do not say that you are an AI.
8. Do not say that you are a synthetic persona.
9. Answer naturally like a real participant in a market research interview.
10. Give a direct answer first.
11. Usually answer in 3-6 sentences.
12. Keep answers concise and easy to understand.
13. Do not use Markdown tables.
14. Do not create long lists.
15. Do not use unnecessary headings.
16. Do not write a research report.
17. Do not repeat the complete persona profile.
18. Mention specific preferences when they are relevant.
19. If the question asks "why", briefly explain the reason.
20. Maintain consistency across the conversation.
"""


    # =====================================================
    # ADD USER QUESTION TO MEMORY
    # =====================================================

    history.append({
        "role": "user",
        "content": question
    })


    # =====================================================
    # BUILD GROQ MESSAGES
    # =====================================================

    messages = [

        {
            "role": "system",
            "content": persona_information
        }

    ]


    # Add previous conversation
    messages.extend(history)


    # =====================================================
    # SEND REQUEST TO GROQ
    # =====================================================

    try:

        print("\n======================================")
        print("🤖 PERSONA CHAT")
        print("======================================")

        print("Persona:", persona.get("name"))
        print("Question:", question)

        print("======================================\n")


        response = client.chat.completions.create(

            model=MODEL_NAME,

            messages=messages,

            temperature=0.7,

            max_tokens=500

        )


        # =================================================
        # GET ANSWER
        # =================================================

        answer = response.choices[0].message.content.strip()


        # =================================================
        # SAVE ANSWER TO MEMORY
        # =================================================

        history.append({

            "role": "assistant",

            "content": answer

        })


        print("\n========== PERSONA ANSWER ==========")

        print(answer)

        print("====================================\n")


        return answer


    except Exception as e:

        print("\n======================================")
        print("❌ PERSONA CHAT ERROR")
        print("======================================")

        print("Error type:", type(e).__name__)

        print("Error:", repr(e))

        print("======================================\n")


        # Remove failed question from memory
        if history:

            if history[-1]["role"] == "user":

                history.pop()


        raise


# =========================================================
# GET CONVERSATION HISTORY
# =========================================================

def get_conversation(persona):

    persona_key = get_persona_key(persona)

    return conversation_memory.get(

        persona_key,

        []

    )


# =========================================================
# CLEAR CONVERSATION
# =========================================================

def clear_conversation(persona):

    persona_key = get_persona_key(persona)

    if persona_key in conversation_memory:

        del conversation_memory[persona_key]


    print(
        f"🗑️ Conversation cleared for "
        f"{persona.get('name', 'Unknown Persona')}"
    )