import os, re, json, random
from io import BytesIO
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

try:
    from groq import Groq
except ImportError:
    Groq = None

load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")
MODEL="openai/gpt-oss-20b"
client=None
if Groq and API_KEY:
    try: client=Groq(api_key=API_KEY,timeout=120.0,max_retries=2)
    except Exception: client=None

app=FastAPI(title="Synthetic User Generation Platform",version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
histories={}

class PersonaRequest(BaseModel):
    product:str
    audience:str
    objective:str
    count:int
class PersonaChatRequest(BaseModel):
    persona:dict
    question:str
class InsightRequest(BaseModel):
    personas:list[dict]
    interviews:list[dict]
class UsageScoringRequest(BaseModel):
    personas:list[dict]
    interviews:list[dict]
class ReportRequest(BaseModel):
    product:str
    audience:str
    objective:str
    personas:list[dict]
    interviews:list[dict]
    insights:dict|None=None
    usage_scores:dict|None=None

FIRST=["Ava","Lena","Maya","Sofia","Nina","Olivia","Emma","Aria","Chloe","Mia","Zoe","Grace","Ella","Amelia","Harper","Isla","Layla","Nora","Emily","Anika","Priya","Riya","Sara","Meera"]
LAST=["Rossi","Johnson","Wilson","Sharma","Patel","Mehta","Singh","Miller","Chen","Brown","Garcia","Lee","Davis","Taylor","Kumar","Shah","Verma","Kim","Thomas","Anderson"]
OCC=["Marketing Manager","Graphic Designer","Software Engineer","Data Analyst","Research Associate","Product Designer","HR Specialist","Entrepreneur","UX Researcher","Teacher","Financial Analyst","Project Manager"]
LOC=["Mumbai, India","Delhi, India","Bengaluru, India","Hyderabad, India","Pune, India","New York, USA","Boston, USA","Austin, USA","Chicago, USA","Seattle, USA","San Francisco, USA","Denver, USA"]
PERS=["Practical and organized","Social and energetic","Thoughtful and research-oriented","Environmentally conscious and deliberate","Technology-oriented and curious","Health-focused and disciplined","Creative and experimental","Analytical and curious","Budget-conscious and practical"]
LIFE=["Fitness-oriented lifestyle","Health-focused lifestyle","Technology-focused lifestyle","Eco-conscious lifestyle","Family-oriented lifestyle","Active urban lifestyle","Balanced work-life lifestyle"]
INT=[["Cooking","Family","Health"],["Technology","Shopping","Entertainment"],["Photography","Travel","Lifestyle"],["Books","Fitness","Self Improvement"],["Running","Outdoor Activities","Healthy Food"],["Fashion","Beauty","Social Media"],["Yoga","Wellness","Nutrition"],["Sustainability","Organic Products","Wellness"]]
BUY=["Researches extensively before buying","Checks reviews and compares alternatives","Values transparent product information","Looks for trusted brands and proven results","Compares prices and specifications","Prefers convenient online shopping"]
PAIN=["Unclear ingredients or specifications","Difficulty finding trustworthy reviews","High prices and too many choices","Concern about product quality","Lack of transparent information","Difficulty comparing alternatives"]
PLAT=["YouTube and brand websites","Instagram and online stores","TikTok and online stores","Amazon and Google Search","Reddit and Google Search"]

def clean(v):
    if v is None:return ""
    if isinstance(v,list):return ", ".join(clean(x) for x in v)
    return re.sub(r"\s+"," ",re.sub(r"<[^>]+>","",str(v))).strip()
def esc(v):
    return clean(v).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
def intval(v,d=25):
    try:return int(float(v))
    except:return d
def boolean(v,d=False):
    if isinstance(v,bool):return v
    s=clean(v).lower()
    return True if s in ("true","yes","1") else False if s in ("false","no","0") else d

def groq_json(system,user,tokens=3000):
    if not client:return None
    try:
        r=client.chat.completions.create(model=MODEL,messages=[{"role":"system","content":system},{"role":"user","content":user}],temperature=.7,max_tokens=tokens)
        s=(r.choices[0].message.content or "").strip()
        s=re.sub(r"^```(?:json)?\s*|\s*```$","",s,flags=re.I)
        try:return json.loads(s)
        except:
            m=re.search(r"(\{.*\}|\[.*\])",s,re.S)
            return json.loads(m.group(1)) if m else None
    except Exception as e:
        print("Groq unavailable:",e)
        return None

def fallback_personas(product,audience,objective,n,start=1):
    out=[]
    for i in range(start,start+n):
        out.append({
            "name":f"{FIRST[(i-1)%len(FIRST)]} {LAST[((i-1)//len(FIRST))%len(LAST)]}",
            "age":25+i%16,"gender":"Female" if i%2 else "Male","occupation":OCC[(i-1)%len(OCC)],
            "location":LOC[(i-1)%len(LOC)],"education":"Bachelor's degree","income":[35000,42000,50000,62000,75000,90000][(i-1)%6],
            "marital_status":"Single","personality":PERS[(i-1)%len(PERS)],"lifestyle":LIFE[(i-1)%len(LIFE)],
            "interests":INT[(i-1)%len(INT)],"buying_behavior":BUY[(i-1)%len(BUY)],
            "preferred_platform":PLAT[(i-1)%len(PLAT)],"pain_points":PAIN[(i-1)%len(PAIN)],
            "email":f"synthetic.user{i}@example.com","phone":f"+1-555-010-{i:04d}","customer_id":f"CUST-{i:04d}",
            "bio":f"{FIRST[(i-1)%len(FIRST)]} is a fictional synthetic customer interested in {product}.",
            "goal":objective,"health_conscious":True,"budget_conscious":i%3==0,"eco_friendly":i%2==0,"premium_buyer":i%5==0})
    return out

@app.get("/")
def root(): return {"success":True,"message":"Synthetic User Generation Platform API","status":"running"}
@app.get("/health")
def health(): return {"status":"healthy","groq_available":client is not None}

@app.post("/generate-personas")
def generate(req:PersonaRequest):
    if not req.product.strip():raise HTTPException(400,"Product is required.")
    if not req.audience.strip():raise HTTPException(400,"Target audience is required.")
    n=max(1,min(req.count,100)); objective=req.objective.strip() or "Understand customer needs and preferences."
    generated=[]
    for start in range(1,n+1,5):
        size=min(5,n-start+1)
        ai=groq_json("Generate fictional synthetic customer personas. Return ONLY JSON: {\"personas\":[...]}.",
                      json.dumps({"product":req.product,"audience":req.audience,"objective":objective,"count":size}),6000)
        if not isinstance(ai,dict) or not isinstance(ai.get("personas"),list):break
        generated.extend(ai["personas"])
    if len(generated)<n:generated.extend(fallback_personas(req.product,req.audience,objective,n-len(generated),len(generated)+1))
    final=[];names=set()
    for i,p in enumerate(generated[:n],1):
        p=p if isinstance(p,dict) else {}
        base=clean(p.get("name")) or f"{FIRST[(i-1)%len(FIRST)]} {LAST[((i-1)//len(FIRST))%len(LAST)]}"
        name=base;k=2
        while name.lower() in names:name=f"{base} {k}";k+=1
        names.add(name.lower())
        interests=p.get("interests") if isinstance(p.get("interests"),list) else [x.strip() for x in clean(p.get("interests")).split(",") if x.strip()]
        final.append({"name":name,"age":intval(p.get("age")),"gender":clean(p.get("gender")) or "Female","occupation":clean(p.get("occupation")) or OCC[(i-1)%len(OCC)],
                      "location":clean(p.get("location")) or LOC[(i-1)%len(LOC)],"education":clean(p.get("education")) or "Bachelor's degree","income":intval(p.get("income"),50000),
                      "marital_status":clean(p.get("marital_status")) or "Single","personality":clean(p.get("personality")) or PERS[(i-1)%len(PERS)],
                      "lifestyle":clean(p.get("lifestyle")) or LIFE[(i-1)%len(LIFE)],"interests":interests or INT[(i-1)%len(INT)],
                      "buying_behavior":clean(p.get("buying_behavior")) or BUY[(i-1)%len(BUY)],"preferred_platform":clean(p.get("preferred_platform")) or PLAT[(i-1)%len(PLAT)],
                      "pain_points":clean(p.get("pain_points")) or PAIN[(i-1)%len(PAIN)],"email":clean(p.get("email")) or f"synthetic.user{i}@example.com",
                      "phone":clean(p.get("phone")) or f"+1-555-010-{i:04d}","customer_id":clean(p.get("customer_id")) or f"CUST-{i:04d}",
                      "bio":clean(p.get("bio")) or f"{name} is a fictional synthetic customer.","goal":objective,
                      "health_conscious":boolean(p.get("health_conscious"),True),"budget_conscious":boolean(p.get("budget_conscious"),i%3==0),
                      "eco_friendly":boolean(p.get("eco_friendly"),i%2==0),"premium_buyer":boolean(p.get("premium_buyer"),i%5==0)})
    return {"success":True,"count":len(final),"personas":final}

def local_answer(p,q):
    if any(x in q.lower() for x in ["concern","stop","worry","problem","risk"]):
        return f"My main concern would be {clean(p.get('pain_points')).lower()}. I would want trustworthy information and credible reviews before committing. I would probably compare the product with alternatives first."
    if any(x in q.lower() for x in ["price","pay","cost","willing"]):
        return "I would consider the price in relation to quality, ingredients, and expected results. I would compare it with alternatives before deciding."
    return f"I would focus on product quality, clear information, and whether it fits my needs. I usually {clean(p.get('buying_behavior')).lower()}."

@app.post("/persona-chat")
def chat(req:PersonaChatRequest):
    q=clean(req.question)
    if not q:raise HTTPException(400,"Question is required.")
    p=req.persona;key=clean(p.get("customer_id")) or clean(p.get("name")) or "unknown"
    h=histories.setdefault(key,[])
    ai=groq_json("Role-play as the fictional persona. Return ONLY JSON: {\"answer\":\"...\"}.",json.dumps({"persona":p,"question":q}),1200)
    ans=clean(ai.get("answer")) if isinstance(ai,dict) else ""
    if not ans:ans=local_answer(p,q)
    h.append({"question":q,"answer":ans})
    return {"success":True,"persona":p,"question":q,"answer":ans,"history":h}

@app.get("/persona-chat/history")
def get_history(customer_id:str):return {"success":True,"customer_id":customer_id,"history":histories.get(customer_id,[])}
@app.post("/persona-chat/clear")
def clear(customer_id:str):histories.pop(customer_id,None);return {"success":True,"customer_id":customer_id,"history":[]}

def iname(x):
    p=x.get("persona")
    return clean(p.get("name")) if isinstance(p,dict) else clean(x.get("persona_name") or x.get("name") or "Unknown Persona")
def ianswer(x):return clean(x.get("answer") or x.get("response") or "")

def local_insights(interviews):
    answers = [clean(x.get("answer") or x.get("response") or "") for x in interviews]
    answers = [x for x in answers if x]
    total = len(answers)

    if not answers:
        return {
            "recurring_themes": [],
            "sentiment": {"positive": 0, "neutral": 0, "negative": 0},
            "agreement_patterns": [],
            "behavioral_trends": [],
            "key_findings": [],
            "response_count": 0,
        }

    keys = {
        "Eco-friendliness / recyclable packaging":
            ["eco-friendly", "eco friendly", "recyclable", "recyclable packaging", "sustainable", "sustainability"],
        "Natural, plant-based ingredients":
            ["natural ingredients", "plant-based", "plant based", "natural"],
        "Skin health & softness":
            ["soft", "softness", "hydrated", "hydration", "skin health", "healthy skin", "moistur"],
        "Brand trust & transparency":
            ["trust", "trusted", "transparent", "transparency", "proven brands", "product information"],
        "Avoidance of harsh chemicals":
            ["harsh chemicals", "chemicals", "clean ingredients"],
        "Lifestyle alignment":
            ["active lifestyle", "social lifestyle", "routine", "everyday use"],
    }

    themes = []
    for name, words in keys.items():
        count = sum(
            any(w in answer.lower() for w in words)
            for answer in answers
        )
        if count:
            themes.append({
                "theme": name,
                "count": count,
                "percentage": round(count / total * 100),
            })

    themes.sort(key=lambda x: (-x["count"], x["theme"]))

    positive_words = [
        "love", "great", "good", "excellent", "benefit", "useful",
        "trust", "trusted", "confidence", "healthy", "soft", "clean",
        "important", "fits", "choose", "chooses", "appreciate"
    ]
    negative_words = [
        "stop", "problem", "difficulty", "lack", "risk", "unclear",
        "worry", "worried", "bad", "dislike", "hate", "expensive"
    ]

    positive_count = neutral_count = negative_count = 0

    for answer in answers:
        low = answer.lower()
        p = sum(word in low for word in positive_words)
        n = sum(word in low for word in negative_words)

        if n > p:
            negative_count += 1
        elif p > n:
            positive_count += 1
        else:
            neutral_count += 1

    positive = round(positive_count / total * 100)
    neutral = round(neutral_count / total * 100)
    negative = 100 - positive - neutral

    agreement_patterns = [
        {
            "topic": t["theme"],
            "agreement_percentage": t["percentage"],
            "description": f"Mentioned by {t['count']} of {total} interviewed personas."
        }
        for t in themes
    ]

    behavioral_trends = []
    for interview in interviews:
        persona = (
            interview.get("persona")
            or interview.get("persona_name")
            or interview.get("name")
            or "Participant"
        )
        answer = clean(
            interview.get("answer")
            or interview.get("response")
            or ""
        )
        if answer:
            behavioral_trends.append(
                f"{persona}: Discussed product benefits, preferences, "
                f"and purchase considerations based on their interview response."
            )

    key_findings = []
    if themes:
        key_findings.append(
            f"{themes[0]['theme']} was the most frequently discussed theme, "
            f"mentioned by {themes[0]['count']} of {total} interviewed personas."
        )
    key_findings.append(
        f"Sentiment was {positive}% positive, {neutral}% neutral, "
        f"and {negative}% negative across the analyzed responses."
    )
    key_findings.append(
        f"{total} interview responses were analyzed."
    )

    return {
        "recurring_themes": themes,
        "sentiment": {
            "positive": positive,
            "neutral": neutral,
            "negative": negative,
        },
        "agreement_patterns": agreement_patterns,
        "behavioral_trends": behavioral_trends,
        "key_findings": key_findings,
        "response_count": total,
    }


def normalize_insights(ai, interviews):
    """
    Normalize Groq output before sending it to the frontend/PDF.
    If an AI field is missing, malformed, empty, or clearly unusable,
    use the deterministic local analysis for that field.
    """
    fallback = local_insights(interviews)
    if not isinstance(ai, dict):
        return fallback

    result = dict(ai)
    result["response_count"] = len(interviews)

    # Themes: convert strings to objects and fill missing counts/percentages.
    raw_themes = result.get("recurring_themes")
    normalized_themes = []

    if isinstance(raw_themes, list):
        for item in raw_themes:
            if isinstance(item, str):
                name = clean(item)
                match = next(
                    (x for x in fallback["recurring_themes"]
                     if x["theme"].lower() == name.lower()),
                    None
                )
                normalized_themes.append(
                    match or {"theme": name, "count": 0, "percentage": 0}
                )
            elif isinstance(item, dict):
                name = clean(
                    item.get("theme")
                    or item.get("name")
                    or item.get("topic")
                    or item.get("title")
                    or ""
                )
                if not name:
                    continue

                match = next(
                    (x for x in fallback["recurring_themes"]
                     if x["theme"].lower() == name.lower()),
                    None
                )

                count = item.get("count")
                if count is None:
                    count = item.get("frequency")
                if count is None and match:
                    count = match["count"]

                pct = item.get("percentage")
                if pct is None:
                    pct = item.get("percent")
                if pct is None and match:
                    pct = match["percentage"]

                normalized_themes.append({
                    "theme": name,
                    "count": count if count is not None else 0,
                    "percentage": pct if pct is not None else 0,
                })

    if not normalized_themes:
        normalized_themes = fallback["recurring_themes"]

    # If AI returned theme names but no useful counts, use deterministic counts.
    if normalized_themes and all(
        int(x.get("count") or 0) == 0 and
        int(x.get("percentage") or 0) == 0
        for x in normalized_themes
    ):
        normalized_themes = fallback["recurring_themes"]

    result["recurring_themes"] = normalized_themes

    # Sentiment: use AI only if it contains a real non-zero distribution.
    sent = result.get("sentiment")
    if not isinstance(sent, dict):
        sent = {}

    positive = sent.get("positive", sent.get("Positive", 0))
    neutral = sent.get("neutral", sent.get("Neutral", 0))
    negative = sent.get("negative", sent.get("Negative", 0))

    try:
        positive = float(positive)
        neutral = float(neutral)
        negative = float(negative)
    except (TypeError, ValueError):
        positive = neutral = negative = 0

    if positive + neutral + negative == 0:
        sent = fallback["sentiment"]
    else:
        sent = {
            "positive": round(positive),
            "neutral": round(neutral),
            "negative": round(negative),
        }

    result["sentiment"] = sent

    # Agreement: always turn it into readable percentage records.
    raw_agreement = result.get("agreement_patterns") or result.get("agreement")
    normalized_agreement = []

    if isinstance(raw_agreement, dict):
        for topic, value in raw_agreement.items():
            match = next(
                (x for x in fallback["agreement_patterns"]
                 if x["topic"].lower() == clean(topic).lower()),
                None
            )

            if isinstance(value, dict):
                pct = (
                    value.get("agreement_percentage")
                    if value.get("agreement_percentage") is not None
                    else value.get("agreement")
                )
                if pct is None:
                    pct = value.get("percentage")
                if pct is None:
                    pct = value.get("percent")
            else:
                pct = value

            # Boolean values such as True are not percentages.
            if isinstance(pct, bool) or pct is None:
                pct = match["agreement_percentage"] if match else 0

            try:
                pct = round(float(pct))
            except (TypeError, ValueError):
                pct = match["agreement_percentage"] if match else 0

            normalized_agreement.append({
                "topic": clean(topic),
                "agreement_percentage": pct,
                "description": (
                    match["description"]
                    if match
                    else ""
                ),
            })

    elif isinstance(raw_agreement, list):
        for item in raw_agreement:
            if isinstance(item, dict):
                topic = clean(
                    item.get("topic")
                    or item.get("theme")
                    or item.get("name")
                    or ""
                )
                pct = (
                    item.get("agreement_percentage")
                    if item.get("agreement_percentage") is not None
                    else item.get("agreement")
                )
                if pct is None:
                    pct = item.get("percentage")
                if pct is None:
                    pct = item.get("percent")

                if isinstance(pct, bool) or pct is None:
                    match = next(
                        (x for x in fallback["agreement_patterns"]
                         if x["topic"].lower() == topic.lower()),
                        None
                    )
                    pct = match["agreement_percentage"] if match else 0

                try:
                    pct = round(float(pct))
                except (TypeError, ValueError):
                    pct = 0

                normalized_agreement.append({
                    "topic": topic or "Topic",
                    "agreement_percentage": pct,
                    "description": clean(
                        item.get("description")
                        or item.get("details")
                        or ""
                    ),
                })
            elif isinstance(item, str):
                normalized_agreement.append({
                    "topic": clean(item),
                    "agreement_percentage": 0,
                    "description": "",
                })

    if not normalized_agreement:
        normalized_agreement = fallback["agreement_patterns"]

    # Behavioral trends: discard empty dicts/raw unusable values.
    raw_trends = result.get("behavioral_trends")
    normalized_trends = []

    if isinstance(raw_trends, list):
        for item in raw_trends:
            if isinstance(item, str) and item.strip():
                normalized_trends.append(item.strip())
            elif isinstance(item, dict):
                persona = clean(
                    item.get("persona")
                    or item.get("persona_name")
                    or item.get("name")
                    or ""
                )
                behavior = clean(
                    item.get("buying_behavior")
                    or item.get("behavior")
                    or item.get("trend")
                    or ""
                )
                action = clean(
                    item.get("key_action")
                    or item.get("action")
                    or item.get("description")
                    or ""
                )
                platforms = item.get("platforms")
                if isinstance(platforms, list):
                    platforms = ", ".join(clean(x) for x in platforms)
                else:
                    platforms = clean(platforms or "")

                parts = []
                if persona:
                    parts.append(f"{persona}:")
                if behavior:
                    parts.append(behavior)
                if platforms:
                    parts.append(f"Platforms: {platforms}.")
                if action:
                    parts.append(action)

                if parts:
                    normalized_trends.append(" ".join(parts))

    if not normalized_trends:
        normalized_trends = fallback["behavioral_trends"]

    result["agreement_patterns"] = normalized_agreement
    result["behavioral_trends"] = normalized_trends

    # Key findings: preserve useful AI findings; fall back if missing/empty.
    raw_findings = result.get("key_findings")
    if not isinstance(raw_findings, list):
        raw_findings = []

    findings = []
    for item in raw_findings:
        if isinstance(item, str) and item.strip():
            findings.append(item.strip())
        elif isinstance(item, dict):
            value = clean(
                item.get("finding")
                or item.get("description")
                or item.get("summary")
                or ""
            )
            if value:
                findings.append(value)

    result["key_findings"] = findings or fallback["key_findings"]

    return result

@app.post("/extract-insights")
def insights(req:InsightRequest):
    ai = groq_json(
        "Analyze synthetic interviews. Return JSON with recurring_themes, sentiment, agreement_patterns, behavioral_trends, key_findings and response_count.",
        json.dumps({"personas": req.personas, "interviews": req.interviews}),
        3000
    )
    normalized = normalize_insights(ai, req.interviews)
    return {"success": True, "insights": normalized}

def score_one(p,a):
    s=60
    s+=5*sum(w in a.lower() for w in ["buy","purchase","use","interested","important","quality","benefit","good","willing"])
    s-=5*sum(w in a.lower() for w in ["concern","stop","difficulty","lack","unclear","risk","expensive","problem","worry"])
    if boolean(p.get("health_conscious")):s+=3
    if boolean(p.get("eco_friendly")):s+=3
    if boolean(p.get("budget_conscious")):s-=2
    s=max(0,min(100,s));decision="Yes" if s>=80 else "Maybe" if s>=55 else "No"
    segment="Health & Eco-conscious" if boolean(p.get("eco_friendly")) and boolean(p.get("health_conscious")) else "Health-conscious customers" if boolean(p.get("health_conscious")) else "Budget-conscious customers" if boolean(p.get("budget_conscious")) else "General customers"
    return s,decision,segment

@app.post("/score-product-usage")
def usage(req:UsageScoringRequest):
    by={iname(x).lower():ianswer(x) for x in req.interviews}; rows=[]
    for p in req.personas:
        n=clean(p.get("name"));a=by.get(n.lower(),"")
        if a:
            s,d,g=score_one(p,a);rows.append({"persona":n,"name":n,"score":s,"would_use":d,"segment":g})
    overall=round(sum(x["score"] for x in rows)/len(rows)) if rows else 0
    use=round(sum(x["would_use"]=="Yes" for x in rows)/len(rows)*100) if rows else 0
    groups={}
    for x in rows:groups.setdefault(x["segment"],[]).append(x)
    summary=[{"segment":g,"count":len(v),"yes":sum(x["would_use"]=="Yes" for x in v),"maybe":sum(x["would_use"]=="Maybe" for x in v),"no":sum(x["would_use"]=="No" for x in v),"average_score":round(sum(x["score"] for x in v)/len(v))} for g,v in groups.items()]
    return {"success":True,"scores":{"overall_score":overall,"overall_would_use":use,"persona_scores":rows,"segment_summary":summary}}

styles=getSampleStyleSheet()
TITLE=ParagraphStyle("title",parent=styles["Title"],fontSize=20,alignment=TA_CENTER,spaceAfter=10)
H=ParagraphStyle("h",parent=styles["Heading2"],fontSize=14,spaceBefore=9,spaceAfter=6)
SH=ParagraphStyle("sh",parent=styles["Heading3"],fontSize=11,spaceBefore=6,spaceAfter=4)
BODY=ParagraphStyle("body",parent=styles["BodyText"],fontSize=9,leading=13,spaceAfter=4)
SMALL=ParagraphStyle("small",parent=styles["BodyText"],fontSize=7.5,leading=10)
def P(v,style=BODY):return Paragraph(esc(v),style)
def make_table(data,widths):
    t=Table([[P(v,SMALL) for v in row] for row in data],colWidths=widths,repeatRows=1)
    t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.4,colors.grey),("BACKGROUND",(0,0),(-1,0),colors.HexColor("#E8E8E8")),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5)]))
    return t

def make_pdf(req):
    b=BytesIO();doc=SimpleDocTemplate(b,pagesize=A4,leftMargin=15*mm,rightMargin=15*mm,topMargin=15*mm,bottomMargin=15*mm,title="Synthetic User Research Report")
    s=[];product=clean(req.product);aud=clean(req.audience);obj=clean(req.objective) or "Understand customer needs and preferences."
    ps=req.personas or [];iv=req.interviews or [];ins=req.insights or {};sc=req.usage_scores or {}
    s += [P("Synthetic User Research Report",TITLE),P("AI-powered synthetic customer research and validation",BODY)]
    s += [P("1. Research Information",H),make_table([["Field","Value"],["Product",product],["Target Audience",aud],["Research Objective",obj],["Generated Personas",len(ps)],["Interviews",len(iv)]],[50*mm,125*mm])]
    s += [P("2. Persona Overview",H),P(f"{len(ps)} fictional synthetic personas were generated. A compact overview is shown below; detailed profiles are limited to interviewed personas.",BODY)]
    ov=[["Name","Age","Occupation","Location","Research Goal"]]
    for p in ps[:25]:ov.append([p.get("name",""),p.get("age",""),p.get("occupation",""),p.get("location",""),p.get("goal",obj)])
    s.append(make_table(ov,[30*mm,12*mm,35*mm,40*mm,55*mm]))
    if len(ps)>25:s.append(P(f"Showing 25 of {len(ps)} generated personas in the compact overview.",SMALL))
    names={iname(x).lower() for x in iv};details=[p for p in ps if clean(p.get("name")).lower() in names]
    if iv:
        s.append(P("3. Interviewed Persona Details",H))
        for p in details:
            s += [P(p.get("name","Persona"),SH),make_table([["Field","Value"],["Age",p.get("age","")],["Gender",p.get("gender","")],["Occupation",p.get("occupation","")],["Location",p.get("location","")],["Education",p.get("education","")],["Income",p.get("income","")],["Personality",p.get("personality","")],["Lifestyle",p.get("lifestyle","")],["Interests",clean(p.get("interests"))],["Buying Behavior",p.get("buying_behavior","")],["Pain Points",p.get("pain_points","")],["Research Goal",p.get("goal",obj)]],[50*mm,125*mm]),Spacer(1,5)]
        s.append(P("4. Interview Responses",H))
        for i,x in enumerate(iv,1): s += [P(f"Interview {i}: {iname(x)}",SH),P(f"Question: {clean(x.get('question',''))}"),P(f"Response: {ianswer(x)}")]
        insights_heading = "5. Research Insights"
        validation_heading = "6. Product Validation / Usage Score"
        conclusion_heading = "7. Conclusion"
    else:
        insights_heading = "3. Research Insights"
        validation_heading = "4. Product Validation / Usage Score"
        conclusion_heading = "5. Conclusion"
    s.append(P(insights_heading,H))
    themes=ins.get("recurring_themes",[]) or []
    if themes:
        theme_rows=[["Theme","Mentions","Percentage"]]
        for x in themes:
            if isinstance(x,dict):
                name=x.get("theme") or x.get("name") or x.get("topic") or "Theme"
                count=x.get("count") if x.get("count") is not None else x.get("frequency","")
                pct=x.get("percentage") if x.get("percentage") is not None else ""
            else:
                name=clean(x);count="";pct=""
            theme_rows.append([name,count,f"{pct}%" if pct != "" else ""])
        s += [P("Recurring Themes",SH),make_table(theme_rows,[90*mm,40*mm,45*mm])]
    sent=ins.get("sentiment",{}) or {}
    if sent:
        s += [P("Sentiment Breakdown",SH),make_table([["Positive","Neutral","Negative"],[f"{sent.get('positive',0)}%",f"{sent.get('neutral',0)}%",f"{sent.get('negative',0)}%"]],[58*mm,58*mm,59*mm])]
    agreement=ins.get("agreement_patterns") or ins.get("agreement") or []
    if agreement:
        s.append(P("Agreement Patterns",SH))
        if isinstance(agreement,dict):
            for k,v in agreement.items():
                if isinstance(v,dict):
                    pct=v.get("agreement_percentage") or v.get("agreement") or v.get("percentage") or v.get("percent") or 0
                    desc=v.get("description") or v.get("details") or ""
                    s.append(P(f"{clean(k)}: {pct}% agreement" + (f" — {clean(desc)}" if desc else "")))
                else:
                    s.append(P(f"{clean(k)}: {clean(v)}% agreement"))
        elif isinstance(agreement,list):
            for item in agreement:
                if isinstance(item,dict):
                    topic=item.get("topic") or item.get("theme") or item.get("name") or "Topic"
                    pct=item.get("agreement_percentage") if item.get("agreement_percentage") is not None else item.get("agreement")
                    if pct is None:pct=item.get("percentage") if item.get("percentage") is not None else item.get("percent")
                    desc=item.get("description") or item.get("details") or ""
                    line=f"{clean(topic)}"
                    if pct is not None:line += f": {clean(pct)}% agreement"
                    if desc:line += f" — {clean(desc)}"
                    s.append(P(line))
                else:
                    s.append(P(clean(item)))
    for title,key in [("Behavioral Trends","behavioral_trends"),("Key Findings","key_findings")]:
        values=ins.get(key) or []
        if values:
            s.append(P(title,SH))
            for x in values:
                if isinstance(x,dict):
                    if key=="behavioral_trends":
                        persona=x.get("persona") or x.get("persona_name") or x.get("name") or ""
                        behavior=x.get("buying_behavior") or x.get("behavior") or x.get("trend") or ""
                        platforms=x.get("platforms")
                        action=x.get("key_action") or x.get("action") or x.get("description") or ""
                        if isinstance(platforms,list):platforms=", ".join(clean(v) for v in platforms)
                        line=f"{clean(persona)}: " if persona else ""
                        line += clean(behavior)
                        if platforms:line += f" Platforms: {clean(platforms)}."
                        if action:line += f" {clean(action)}"
                    else:
                        line=x.get("finding") or x.get("description") or x.get("summary") or clean(x)
                else:
                    line=clean(x)
                s.append(P("• "+line))
    if not iv:
        s += [P("No interviews were conducted for this study. Interview-based insights and product validation are not available because no persona interviews were completed.",BODY)]
    s += [P("6. Product Validation / Usage Score",H),make_table([["Metric","Result"],["Overall Usage Score",f"{sc.get('overall_score',0)}/100"],["Overall Would Use",f"{sc.get('overall_would_use',0)}%"],["Interviewed Personas",len(iv)]],[80*mm,95*mm])]
    rows=sc.get("persona_scores",[])
    if rows:s += [P("Persona-Level Validation",SH),make_table([["Persona","Score","Would Use","Segment"]]+[[x.get("persona") or x.get("name",""),f"{x.get('score',0)}/100",x.get("would_use",""),x.get("segment","")] for x in rows],[40*mm,25*mm,30*mm,80*mm])]
    seg=sc.get("segment_summary",[])
    if seg:s += [P("Segment Summary",SH),make_table([["Segment","Personas","Yes","Maybe","No","Average Score"]]+[[x.get("segment",""),x.get("count",0),x.get("yes",0),x.get("maybe",0),x.get("no",0),f"{x.get('average_score',0)}/100"] for x in seg],[62*mm,23*mm,18*mm,22*mm,18*mm,32*mm])]
    s += [P("7. Conclusion",H),P(f"This synthetic research study generated {len(ps)} fictional customer personas for the target audience '{aud}'. The research objective was '{obj}'. The interview, insight, and validation sections summarize patterns observed within the synthetic dataset."),P("Important: These personas and results are synthetic outputs intended for research demonstration, experimentation, and hypothesis generation. They should not be interpreted as representative evidence about a real-world population.",SMALL)]
    doc.build(s);b.seek(0);return b

@app.post("/generate-research-report")
def report(req:ReportRequest):
    try:return StreamingResponse(make_pdf(req),media_type="application/pdf",headers={"Content-Disposition":'attachment; filename="synthetic-user-research-report.pdf"'})
    except Exception as e:raise HTTPException(500,f"Could not generate research report: {e}")

if __name__=="__main__":
    import uvicorn
    uvicorn.run("main:app",host="127.0.0.1",port=8000,reload=True)
