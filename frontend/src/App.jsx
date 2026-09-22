import { useState } from "react";
import axios from "axios";

const API_URL = "http://127.0.0.1:8000";

function App() {
  // =========================================================
  // BASIC STATE
  // =========================================================

  const [product, setProduct] = useState("");
  const [audience, setAudience] = useState("");
  const [objective, setObjective] = useState("");
  const [count, setCount] = useState(6);

  const [personas, setPersonas] = useState([]);
  const [loading, setLoading] = useState(false);

  // =========================================================
  // PERSONA SURVEY
  // =========================================================

  const [selectedPersona, setSelectedPersona] = useState(null);
  const [question, setQuestion] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [interviewsByPersona, setInterviewsByPersona] = useState({});

  // =========================================================
  // INSIGHTS
  // =========================================================

  const [insights, setInsights] = useState(null);
  const [insightLoading, setInsightLoading] = useState(false);

  // =========================================================
  // PRODUCT USAGE
  // =========================================================

  const [usageScores, setUsageScores] = useState(null);
  const [usageLoading, setUsageLoading] = useState(false);

  // =========================================================
  // REPORT
  // =========================================================

  const [reportLoading, setReportLoading] = useState(false);

  // =========================================================
  // GENERATE PERSONAS
  // =========================================================

  const generatePersona = async () => {
    if (!product.trim()) {
      alert("Please enter a product description.");
      return;
    }

    if (!audience.trim()) {
      alert("Please enter the target audience.");
      return;
    }

    if (!objective.trim()) {
      alert("Please enter the research objective.");
      return;
    }

    const requestedCount = Number(count);

    if (
      !Number.isInteger(requestedCount) ||
      requestedCount < 1 ||
      requestedCount > 100
    ) {
      alert("Please choose between 1 and 100 personas.");
      return;
    }

    try {
      setLoading(true);
      setPersonas([]);

      // Clear previous research
      setSelectedPersona(null);
      setQuestion("");
      setChatHistory([]);
      setInterviewsByPersona({});
      setInsights(null);
      setUsageScores(null);

      console.log("=================================");
      console.log("GENERATING PERSONAS");
      console.log("Product:", product);
      console.log("Audience:", audience);
      console.log("Objective:", objective);
      console.log("Count:", requestedCount);
      console.log("=================================");

      const response = await axios.post(
        `${API_URL}/generate-personas`,
        {
          product: product.trim(),
          audience: audience.trim(),
          objective: objective.trim(),
          count: requestedCount,
        },
        {
          timeout: 300000,
        }
      );

      console.log("Backend response:", response.data);

      // =====================================================
      // SUPPORT BOTH RESPONSE FORMATS
      //
      // Old:
      // [
      //   {...},
      //   {...}
      // ]
      //
      // New:
      // {
      //   success: true,
      //   count: 100,
      //   personas: [...]
      // }
      // =====================================================

      let generatedPersonas = [];

      if (Array.isArray(response.data)) {
        generatedPersonas = response.data;
      } else if (
        response.data &&
        Array.isArray(response.data.personas)
      ) {
        generatedPersonas = response.data.personas;
      }

      if (generatedPersonas.length === 0) {
        console.error(
          "No personas found in response:",
          response.data
        );

        alert(
          response.data?.detail ||
            response.data?.error ||
            "The backend returned no personas."
        );

        return;
      }

      console.log(
        `SUCCESS: ${generatedPersonas.length} personas received`
      );

      setPersonas(generatedPersonas);

    } catch (error) {
      console.error(
        "Persona generation error:",
        error
      );

      if (error.response) {
        console.error(
          "Server status:",
          error.response.status
        );

        console.error(
          "Server response:",
          error.response.data
        );

        alert(
          error.response.data?.detail ||
            error.response.data?.error ||
            `Backend error (${error.response.status}).`
        );
      } else if (error.code === "ECONNABORTED") {
        alert(
          "The request took too long. Please check the backend terminal."
        );
      } else {
        alert(
          "Cannot connect to backend. Make sure FastAPI is running on port 8000."
        );
      }

    } finally {
      setLoading(false);
    }
  };

  // =========================================================
  // ASK PERSONA
  // =========================================================

  const askPersona = async () => {
    if (!selectedPersona) {
      alert("Please select a persona.");
      return;
    }

    if (!question.trim()) {
      alert("Please enter a research question.");
      return;
    }

    try {
      setChatLoading(true);

      const currentQuestion = question.trim();

      const response = await axios.post(
        `${API_URL}/persona-chat`,
        {
          persona: selectedPersona,
          question: currentQuestion,
        },
        {
          timeout: 120000,
        }
      );

      console.log(
        "Persona response:",
        response.data
      );

      const answer =
        response.data?.answer ||
        "The synthetic persona did not return an answer.";

      const newInterview = {
        question: currentQuestion,
        answer: answer,
      };

      const updatedHistory = [
        ...chatHistory,
        newInterview,
      ];

      setChatHistory(updatedHistory);

      setInterviewsByPersona(
        (previous) => ({
          ...previous,
          [selectedPersona.customer_id]:
            updatedHistory,
        })
      );

      setQuestion("");

    } catch (error) {
      console.error(
        "Persona chat error:",
        error
      );

      alert(
        error.response?.data?.detail ||
          "Could not connect to persona chat."
      );

    } finally {
      setChatLoading(false);
    }
  };

  // =========================================================
  // SELECT PERSONA
  // =========================================================

  const handlePersonaChange = (customerId) => {
    const persona = personas.find(
      (p) =>
        String(p.customer_id) ===
        String(customerId)
    );

    if (!persona) {
      setSelectedPersona(null);
      setChatHistory([]);
      setQuestion("");
      return;
    }

    const savedHistory =
      interviewsByPersona[
        persona.customer_id
      ] || [];

    setSelectedPersona(persona);
    setChatHistory(savedHistory);
    setQuestion("");
  };

  // =========================================================
  // CLEAR PERSONA CHAT
  // =========================================================

  const clearPersonaChat = async () => {
    if (!selectedPersona) {
      return;
    }

    try {
      await axios.post(
        `${API_URL}/persona-chat/clear`
      );
    } catch (error) {
      console.warn(
        "Backend clear failed:",
        error
      );
    }

    setChatHistory([]);

    setInterviewsByPersona(
      (previous) => {
        const updated = {
          ...previous,
        };

        delete updated[
          selectedPersona.customer_id
        ];

        return updated;
      }
    );

    setQuestion("");
  };

  // =========================================================
  // BUILD ALL INTERVIEWS
  // =========================================================

  const buildAllInterviews = () => {
    return Object.entries(
      interviewsByPersona
    ).flatMap(
      ([customerId, history]) => {
        const persona = personas.find(
          (p) =>
            String(p.customer_id) ===
            String(customerId)
        );

        return (history || []).map(
          (chat) => ({
            persona:
              persona?.name ||
              "Persona",

            persona_name:
              persona?.name ||
              "Persona",

            customer_id:
              customerId,

            persona_id:
              customerId,

            question:
              chat.question,

            answer:
              chat.answer,
          })
        );
      }
    );
  };

  // =========================================================
  // EXTRACT INSIGHTS
  // =========================================================

  const extractInsights = async () => {
    if (personas.length === 0) {
      alert("Generate personas first.");
      return;
    }

    const allInterviews =
      buildAllInterviews();

    if (allInterviews.length === 0) {
      alert(
        "Complete at least one interview first."
      );
      return;
    }

    try {
      setInsightLoading(true);

      const response = await axios.post(
        `${API_URL}/extract-insights`,
        {
          personas: personas,
          interviews: allInterviews,
        },
        {
          timeout: 120000,
        }
      );

      console.log(
        "Insight response:",
        response.data
      );

      // =====================================================
      // NEW BACKEND RETURNS DIRECT OBJECT
      //
      // {
      //   success: true,
      //   recurring_themes: [],
      //   sentiment: {},
      //   ...
      // }
      //
      // Also support old:
      //
      // {
      //   insights: {...}
      // }
      // =====================================================

      const insightData =
        response.data?.insights ||
        response.data;

      setInsights(
        normalizeInsightData(insightData)
      );

    } catch (error) {
      console.error(
        "Insight extraction error:",
        error
      );

      alert(
        error.response?.data?.detail ||
          "Could not extract insights."
      );

    } finally {
      setInsightLoading(false);
    }
  };

  // =========================================================
  // PRODUCT USAGE SCORING
  // =========================================================

  const scoreProductUsage = async () => {
    if (personas.length === 0) {
      alert("Generate personas first.");
      return;
    }

    const allInterviews =
      buildAllInterviews();

    if (allInterviews.length === 0) {
      alert(
        "Complete at least one interview first."
      );
      return;
    }

    const interviewedPersonas =
      personas.filter(
        (persona) =>
          (
            interviewsByPersona[
              persona.customer_id
            ] || []
          ).length > 0
      );

    if (interviewedPersonas.length === 0) {
      alert(
        "Interview at least one persona first."
      );
      return;
    }

    try {
      setUsageLoading(true);

      const response = await axios.post(
        `${API_URL}/score-product-usage`,
        {
          personas:
            interviewedPersonas,

          interviews:
            allInterviews,
        },
        {
          timeout: 120000,
        }
      );

      console.log(
        "Usage score response:",
        response.data
      );

      // Support both:
      // response.data.scores
      // and response.data
      const scoreData =
        response.data?.scores ||
        response.data;

      setUsageScores(scoreData);

    } catch (error) {
      console.error(
        "Product usage scoring error:",
        error
      );

      alert(
        error.response?.data?.detail ||
          "Could not score product usage."
      );

    } finally {
      setUsageLoading(false);
    }
  };

  // =========================================================
  // GENERATE RESEARCH REPORT
  // =========================================================

  const generateResearchReport = async () => {
    if (personas.length === 0) {
      alert("Generate personas first.");
      return;
    }

    const allInterviews =
      buildAllInterviews();

    try {
      setReportLoading(true);

      const response = await axios.post(
        `${API_URL}/generate-research-report`,
        {
          product:
            product.trim(),

          audience:
            audience.trim(),

          objective:
            objective.trim(),

          personas:
            personas,

          interviews:
            allInterviews,

          insights:
            insights,

          usage_scores:
            usageScores,
        },
        {
          responseType: "blob",
          timeout: 120000,
        }
      );

      const blob = new Blob(
        [response.data],
        {
          type: "application/pdf",
        }
      );

      const url =
        window.URL.createObjectURL(
          blob
        );

      const link =
        document.createElement("a");

      link.href = url;

      link.download =
        "synthetic-user-research-report.pdf";

      document.body.appendChild(link);

      link.click();

      document.body.removeChild(link);

      window.URL.revokeObjectURL(
        url
      );

    } catch (error) {
      console.error(
        "Research report error:",
        error
      );

      alert(
        "Could not generate the research report. Check the backend terminal."
      );

    } finally {
      setReportLoading(false);
    }
  };

  // =========================================================
  // DOWNLOAD JSON
  // =========================================================

  const downloadJSON = () => {
    if (personas.length === 0) {
      alert("Generate personas first.");
      return;
    }

    const data =
      JSON.stringify(
        personas,
        null,
        2
      );

    const blob = new Blob(
      [data],
      {
        type:
          "application/json",
      }
    );

    const url =
      URL.createObjectURL(
        blob
      );

    const link =
      document.createElement(
        "a"
      );

    link.href = url;

    link.download =
      "synthetic-personas.json";

    document.body.appendChild(
      link
    );

    link.click();

    document.body.removeChild(
      link
    );

    URL.revokeObjectURL(
      url
    );
  };

  // =========================================================
  // DOWNLOAD CSV
  // =========================================================

  const downloadCSV = () => {
    if (personas.length === 0) {
      alert("Generate personas first.");
      return;
    }

    const fields = [
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
      "premium_buyer",
    ];

    const escapeCSV = (
      value
    ) => {
      if (
        Array.isArray(
          value
        )
      ) {
        value =
          value.join(", ");
      }

      value =
        String(
          value ?? ""
        );

      return `"${value.replace(
        /"/g,
        '""'
      )}"`;
    };

    const header =
      fields.join(",");

    const rows =
      personas.map(
        (persona) =>
          fields
            .map(
              (field) =>
                escapeCSV(
                  persona[
                    field
                  ]
                )
            )
            .join(",")
      );

    const csv = [
      header,
      ...rows,
    ].join("\n");

    const blob =
      new Blob(
        [csv],
        {
          type:
            "text/csv;charset=utf-8;",
        }
      );

    const url =
      URL.createObjectURL(
        blob
      );

    const link =
      document.createElement(
        "a"
      );

    link.href = url;

    link.download =
      "synthetic-personas.csv";

    document.body.appendChild(
      link
    );

    link.click();

    document.body.removeChild(
      link
    );

    URL.revokeObjectURL(
      url
    );
  };

  // =========================================================
  // INSIGHT NORMALIZATION
  // =========================================================

  // The AI/local backend may return insights in slightly different
  // shapes (arrays, strings, or objects). Normalize them here so the
  // UI always renders readable research results.
  const normalizeInsightData = (raw) => {
    const data = raw && typeof raw === "object" ? raw : {};

    const rawThemes = Array.isArray(data.recurring_themes)
      ? data.recurring_themes
      : [];

    const recurringThemes = rawThemes.map((item) => {
      if (typeof item === "string") {
        return {
          theme: item,
          count: null,
          percentage: null,
          description: "",
        };
      }

      return {
        theme:
          item?.theme ||
          item?.name ||
          item?.topic ||
          item?.title ||
          "Theme",
        count:
          item?.count ??
          item?.frequency ??
          item?.mentions ??
          item?.mentioned_by ??
          null,
        percentage:
          item?.percentage ??
          item?.agreement_percentage ??
          null,
        description:
          item?.description ||
          item?.details ||
          item?.summary ||
          "",
      };
    });

    const rawSentiment = data.sentiment || data.sentiment_breakdown || {};
    const sentimentValue = (keys) => {
      if (Array.isArray(rawSentiment)) {
        const found = rawSentiment.find((item) =>
          keys.some(
            (key) =>
              String(
                item?.label ||
                item?.sentiment ||
                item?.name ||
                ""
              ).toLowerCase() === key.toLowerCase()
          )
        );
        return (
          found?.percentage ??
          found?.percent ??
          found?.value ??
          found?.count ??
          0
        );
      }

      for (const key of keys) {
        if (rawSentiment[key] !== undefined) {
          return rawSentiment[key];
        }

        const matchingKey = Object.keys(rawSentiment).find(
          (existingKey) =>
            existingKey.toLowerCase() === key.toLowerCase()
        );

        if (matchingKey) {
          return rawSentiment[matchingKey];
        }
      }

      return 0;
    };

    let positive = Number(
      sentimentValue(["positive", "positivity"])
    );
    let neutral = Number(
      sentimentValue(["neutral", "neutrality"])
    );
    let negative = Number(
      sentimentValue(["negative", "negativity"])
    );

    // If the backend returns counts instead of percentages,
    // convert them using response_count.
    const responseCount =
      Number(data.response_count) ||
      buildAllInterviews().length ||
      0;

    const sentimentLooksLikeCounts =
      responseCount > 0 &&
      positive + neutral + negative <= responseCount;

    if (sentimentLooksLikeCounts) {
      positive = Math.round((positive / responseCount) * 100);
      neutral = Math.round((neutral / responseCount) * 100);
      negative = Math.round((negative / responseCount) * 100);
    }

    // Keep percentages consistent when the backend provides only
    // two categories or minor rounding differences.
    const total = positive + neutral + negative;
    if (total > 0 && total !== 100) {
      const scale = 100 / total;
      positive = Math.round(positive * scale);
      neutral = Math.round(neutral * scale);
      negative = Math.max(0, 100 - positive - neutral);
    }

    const rawAgreement =
      data.agreement_patterns ||
      data.agreement ||
      [];

    let agreementPatterns = [];

    if (Array.isArray(rawAgreement)) {
      agreementPatterns = rawAgreement.map((item) => ({
        topic:
          typeof item === "string"
            ? item
            : item?.topic ||
              item?.theme ||
              item?.name ||
              item?.title ||
              "Topic",
        description:
          typeof item === "string"
            ? ""
            : item?.description ||
              item?.details ||
              item?.summary ||
              "",
        agreement:
          typeof item === "string"
            ? null
            : item?.agreement_percentage ??
              item?.agreement ??
              item?.percentage ??
              item?.percent ??
              null,
      }));
    } else if (
      rawAgreement &&
      typeof rawAgreement === "object"
    ) {
      agreementPatterns = Object.entries(rawAgreement).map(
        ([topic, value]) => {
          if (
            value &&
            typeof value === "object"
          ) {
            return {
              topic,
              description:
                value.description ||
                value.details ||
                "",
              agreement:
                value.agreement_percentage ??
                value.agreement ??
                value.percentage ??
                value.percent ??
                value.value ??
                null,
            };
          }

          return {
            topic,
            description: "",
            agreement: value,
          };
        }
      );
    }

    const rawTrends = Array.isArray(data.behavioral_trends)
      ? data.behavioral_trends
      : [];

    const behavioralTrends = rawTrends.map((trend) => {
      if (typeof trend === "string") {
        return { text: trend };
      }

      const personaName =
        trend?.persona ||
        trend?.persona_name ||
        trend?.name ||
        "";

      const platforms = Array.isArray(trend?.platforms)
        ? trend.platforms.join(", ")
        : trend?.platforms || "";

      const buyingBehavior =
        trend?.buying_behavior ||
        trend?.behavior ||
        trend?.trend ||
        "";

      const keyAction =
        trend?.key_action ||
        trend?.action ||
        trend?.description ||
        trend?.summary ||
        "";

      let text = "";

      if (personaName) {
        text += `${personaName}: `;
      }

      if (buyingBehavior) {
        text += buyingBehavior;
      }

      if (platforms) {
        text += `${text ? " " : ""}Platforms: ${platforms}.`;
      }

      if (keyAction) {
        text += `${text ? " " : ""}${keyAction}`;
      }

      return {
        text:
          text.trim() ||
          JSON.stringify(trend),
      };
    });

    const rawFindings = Array.isArray(data.key_findings)
      ? data.key_findings
      : [];

    const keyFindings = rawFindings.map((finding) =>
      typeof finding === "string"
        ? finding
        : finding?.finding ||
          finding?.description ||
          finding?.summary ||
          JSON.stringify(finding)
    );

    return {
      ...data,
      recurring_themes: recurringThemes,
      sentiment: {
        positive,
        neutral,
        negative,
      },
      agreement_patterns: agreementPatterns,
      behavioral_trends: behavioralTrends,
      key_findings: keyFindings,
      response_count: responseCount,
    };
  };

  // =========================================================
  // RESEARCH SUMMARY
  // =========================================================

  const averageAge =
    personas.length > 0
      ? Math.round(
          personas.reduce(
            (
              sum,
              p
            ) =>
              sum +
              Number(
                p.age || 0
              ),
            0
          ) /
            personas.length
        )
      : 0;

  const femaleUsers =
    personas.filter(
      (p) =>
        String(
          p.gender || ""
        ).toLowerCase() ===
        "female"
    ).length;

  const maleUsers =
    personas.filter(
      (p) =>
        String(
          p.gender || ""
        ).toLowerCase() ===
        "male"
    ).length;

  const getText = (
    p
  ) => `
    ${p.personality || ""}
    ${p.lifestyle || ""}
    ${
      Array.isArray(
        p.interests
      )
        ? p.interests.join(" ")
        : p.interests || ""
    }
    ${p.buying_behavior || ""}
    ${p.pain_points || ""}
    ${p.bio || ""}
  `.toLowerCase();

  const healthConscious =
    personas.filter(
      (p) => {
        if (
          typeof p.health_conscious ===
          "boolean"
        ) {
          return p.health_conscious;
        }

        const text =
          getText(p);

        return (
          text.includes(
            "health"
          ) ||
          text.includes(
            "fitness"
          ) ||
          text.includes(
            "yoga"
          ) ||
          text.includes(
            "wellness"
          ) ||
          text.includes(
            "organic"
          ) ||
          text.includes(
            "skincare"
          ) ||
          text.includes(
            "healthy"
          )
        );
      }
    ).length;

  const budgetConscious =
    personas.filter(
      (p) => {
        if (
          typeof p.budget_conscious ===
          "boolean"
        ) {
          return p.budget_conscious;
        }

        const text =
          getText(p);

        return (
          text.includes(
            "budget"
          ) ||
          text.includes(
            "price-sensitive"
          ) ||
          text.includes(
            "price sensitive"
          ) ||
          text.includes(
            "affordable"
          ) ||
          text.includes(
            "discount"
          ) ||
          text.includes(
            "value-focused"
          ) ||
          text.includes(
            "value focused"
          ) ||
          text.includes(
            "cost-conscious"
          ) ||
          text.includes(
            "cost conscious"
          ) ||
          text.includes(
            "deals"
          )
        );
      }
    ).length;

  const ecoFriendly =
    personas.filter(
      (p) => {
        if (
          typeof p.eco_friendly ===
          "boolean"
        ) {
          return p.eco_friendly;
        }

        const text =
          getText(p);

        return (
          text.includes(
            "eco"
          ) ||
          text.includes(
            "sustainable"
          ) ||
          text.includes(
            "environment"
          ) ||
          text.includes(
            "natural"
          ) ||
          text.includes(
            "organic"
          ) ||
          text.includes(
            "cruelty-free"
          ) ||
          text.includes(
            "cruelty free"
          )
        );
      }
    ).length;

  const premiumBuyers =
    personas.filter(
      (p) => {
        if (
          typeof p.premium_buyer ===
          "boolean"
        ) {
          return p.premium_buyer;
        }

        const text =
          getText(p);

        return (
          text.includes(
            "premium"
          ) ||
          text.includes(
            "luxury"
          ) ||
          text.includes(
            "high quality"
          ) ||
          text.includes(
            "high-quality"
          ) ||
          text.includes(
            "quality over price"
          ) ||
          text.includes(
            "willing to pay more"
          )
        );
      }
    ).length;

  const percentage = (
    value
  ) => {
    if (
      personas.length ===
      0
    ) {
      return "0%";
    }

    return `${Math.round(
      (value /
        personas.length) *
        100
    )}%`;
  };

  // =========================================================
  // COMMON STYLES
  // =========================================================

  const inputStyle = {
    width: "100%",
    padding: "12px",
    marginTop: "10px",
    borderRadius: "8px",
    border:
      "1px solid #ccc",
    fontSize: "15px",
    boxSizing:
      "border-box",
  };

  const sectionStyle = {
    marginTop: "35px",
    padding: "25px",
    background:
      "#ffffff",
    borderRadius:
      "12px",
    border:
      "1px solid #ddd",
    boxShadow:
      "0 4px 10px rgba(0,0,0,0.08)",
  };

  // =========================================================
  // UI
  // =========================================================

  return (
    <div
      style={{
        maxWidth:
          "1200px",
        margin:
          "30px auto",
        padding:
          "20px",
        fontFamily:
          "Arial, sans-serif",
        color: "#111",
      }}
    >
      {/* =====================================================
          HEADER
      ===================================================== */}

      <div
        style={{
          background:
            "#2563eb",
          color: "white",
          padding:
            "30px",
          borderRadius:
            "14px",
          textAlign:
            "center",
          marginBottom:
            "30px",
          boxShadow:
            "0 5px 15px rgba(0,0,0,0.15)",
        }}
      >
        <h1
          style={{
            marginBottom:
              "10px",
          }}
        >
          🧠 Persona Generation Agent
        </h1>

        <p
          style={{
            fontSize:
              "18px",
          }}
        >
          AI Powered Synthetic User Generation Platform
        </p>
      </div>

      {/* =====================================================
          WORKSPACE
      ===================================================== */}

      <div
        style={{
          background:
            "#f8fafc",
          padding:
            "25px",
          borderRadius:
            "14px",
          boxShadow:
            "0 4px 10px rgba(0,0,0,0.1)",
        }}
      >
        <h2>
          Workspace
        </h2>

        <label>
          <b>
            Product Description
          </b>
        </label>

        <textarea
          rows="5"
          value={product}
          onChange={(e) =>
            setProduct(
              e.target.value
            )
          }
          placeholder="Example: Herbal Soap for Sensitive Skin with Natural Ingredients"
          style={{
            ...inputStyle,
            resize:
              "vertical",
          }}
        />

        <div
          style={{
            display:
              "flex",
            gap:
              "20px",
            flexWrap:
              "wrap",
            marginTop:
              "10px",
          }}
        >
          <div
            style={{
              flex:
                "1 1 300px",
            }}
          >
            <label>
              <b>
                Target Audience
              </b>
            </label>

            <input
              type="text"
              value={
                audience
              }
              onChange={(e) =>
                setAudience(
                  e.target
                    .value
                )
              }
              placeholder="Women aged 25-45 who care about skincare"
              style={
                inputStyle
              }
            />
          </div>

          <div
            style={{
              flex:
                "1 1 300px",
            }}
          >
            <label>
              <b>
                Research Objective
              </b>
            </label>

            <input
              type="text"
              value={
                objective
              }
              onChange={(e) =>
                setObjective(
                  e.target
                    .value
                )
              }
              placeholder="Understand buying preferences and skincare needs"
              style={
                inputStyle
              }
            />
          </div>
        </div>
      </div>

      {/* =====================================================
          COUNT
      ===================================================== */}

      <h2
        style={{
          marginTop:
            "30px",
        }}
      >
        Personas to Generate
      </h2>

      <h3>
        Number of Personas
      </h3>

      <input
        type="number"
        min="1"
        max="100"
        value={
          count
        }
        onChange={(e) => {
          const raw =
            e.target.value;

          if (
            raw === ""
          ) {
            setCount("");
            return;
          }

          const value =
            Number(
              raw
            );

          if (
            value >=
              1 &&
            value <=
              100
          ) {
            setCount(
              value
            );
          }
        }}
        onBlur={() => {
          if (
            !count ||
            count < 1
          ) {
            setCount(1);
          }

          if (
            count >
            100
          ) {
            setCount(100);
          }
        }}
        style={{
          width:
            "220px",
          padding:
            "12px",
          fontSize:
            "18px",
          borderRadius:
            "8px",
          border:
            "2px solid #2563eb",
          marginBottom:
            "20px",
          boxSizing:
            "border-box",
        }}
      />

      <br />

      {/* =====================================================
          GENERATE BUTTON
      ===================================================== */}

      <button
        onClick={
          generatePersona
        }
        disabled={
          loading
        }
        style={{
          background:
            loading
              ? "#777"
              : "#16a34a",
          color:
            "white",
          padding:
            "13px 30px",
          border:
            "none",
          borderRadius:
            "7px",
          fontSize:
            "16px",
          cursor:
            loading
              ? "not-allowed"
              : "pointer",
          fontWeight:
            "bold",
        }}
      >
        {loading
          ? "Generating Personas..."
          : `Generate ${count || 0} Personas`}
      </button>

      {/* =====================================================
          GENERATED PERSONAS
      ===================================================== */}

      {personas.length >
        0 && (
        <>
          <h2
            style={{
              marginTop:
                "40px",
              color:
                "#2563eb",
            }}
          >
            Generated Personas (
            {
              personas.length
            }
            )
          </h2>

          <p
            style={{
              color:
                "#555",
            }}
          >
            AI-generated synthetic users based on your product,
            audience and research objective.
          </p>

          <div
            style={{
              padding:
                "12px 15px",
              marginBottom:
                "20px",
              background:
                "#ecfdf5",
              border:
                "1px solid #86efac",
              borderRadius:
                "8px",
              color:
                "#166534",
              fontWeight:
                "bold",
            }}
          >
            ✅ Successfully generated{" "}
            {
              personas.length
            }{" "}
            synthetic personas.
          </div>

          {/* PERSONA GRID */}

          <div
            style={{
              display:
                "grid",
              gridTemplateColumns:
                "repeat(auto-fit,minmax(340px,1fr))",
              gap:
                "20px",
              marginTop:
                "20px",
            }}
          >
            {personas.map(
              (
                p,
                index
              ) => (
                <div
                  key={
                    p.customer_id ||
                    index
                  }
                  style={{
                    background:
                      "white",
                    borderRadius:
                      "12px",
                    padding:
                      "20px",
                    border:
                      "1px solid #ddd",
                    boxShadow:
                      "0 4px 8px rgba(0,0,0,0.1)",
                  }}
                >
                  <img
                    src={`https://ui-avatars.com/api/?name=${encodeURIComponent(
                      p.name ||
                        "User"
                    )}&background=2563eb&color=fff&size=128`}
                    alt={
                      p.name ||
                      "User"
                    }
                    style={{
                      width:
                        "80px",
                      height:
                        "80px",
                      borderRadius:
                        "50%",
                      display:
                        "block",
                      margin:
                        "0 auto 15px",
                    }}
                  />

                  <h2
                    style={{
                      textAlign:
                        "center",
                      color:
                        "#2563eb",
                    }}
                  >
                    {p.name ||
                      `Synthetic User ${
                        index +
                        1
                      }`}
                  </h2>

                  <hr />

                  <p>
                    <b>
                      Age:
                    </b>{" "}
                    {p.age}
                  </p>

                  <p>
                    <b>
                      Gender:
                    </b>{" "}
                    {p.gender}
                  </p>

                  <p>
                    <b>
                      Occupation:
                    </b>{" "}
                    {
                      p.occupation
                    }
                  </p>

                  <p>
                    <b>
                      Location:
                    </b>{" "}
                    {
                      p.location
                    }
                  </p>

                  <p>
                    <b>
                      Education:
                    </b>{" "}
                    {
                      p.education
                    }
                  </p>

                  <p>
                    <b>
                      Annual Income:
                    </b>{" "}
                    {
                      p.income
                    }
                  </p>

                  <p>
                    <b>
                      Marital Status:
                    </b>{" "}
                    {
                      p.marital_status
                    }
                  </p>

                  <p>
                    <b>
                      Personality:
                    </b>{" "}
                    {
                      p.personality
                    }
                  </p>

                  <p>
                    <b>
                      Lifestyle:
                    </b>{" "}
                    {
                      p.lifestyle
                    }
                  </p>

                  <p>
                    <b>
                      Interests:
                    </b>{" "}
                    {Array.isArray(
                      p.interests
                    )
                      ? p.interests.join(
                          ", "
                        )
                      : p.interests}
                  </p>

                  <p>
                    <b>
                      Buying Behavior:
                    </b>{" "}
                    {
                      p.buying_behavior
                    }
                  </p>

                  <p>
                    <b>
                      Preferred Platform:
                    </b>{" "}
                    {
                      p.preferred_platform
                    }
                  </p>

                  <p>
                    <b>
                      Pain Points:
                    </b>{" "}
                    {
                      p.pain_points
                    }
                  </p>

                  <p>
                    <b>
                      Email:
                    </b>{" "}
                    {p.email}
                  </p>

                  <p>
                    <b>
                      Phone:
                    </b>{" "}
                    {p.phone}
                  </p>

                  <p>
                    <b>
                      Customer ID:
                    </b>{" "}
                    {
                      p.customer_id
                    }
                  </p>

                  <p>
                    <b>
                      Bio:
                    </b>{" "}
                    {p.bio}
                  </p>

                  <div
                    style={{
                      marginTop:
                        "15px",
                      padding:
                        "12px",
                      background:
                        "#eff6ff",
                      borderRadius:
                        "8px",
                      borderLeft:
                        "4px solid #2563eb",
                    }}
                  >
                    <b>
                      Goal:
                    </b>{" "}
                    {p.goal ||
                      objective ||
                      "Understand buying preferences"}
                  </div>

                  <div
                    style={{
                      display:
                        "flex",
                      flexWrap:
                        "wrap",
                      gap:
                        "8px",
                      marginTop:
                        "15px",
                    }}
                  >
                    {p.health_conscious && (
                      <Flag
                        text="❤️ Health Conscious"
                        background="#dcfce7"
                        color="#166534"
                      />
                    )}

                    {p.budget_conscious && (
                      <Flag
                        text="💰 Budget Conscious"
                        background="#fef3c7"
                        color="#92400e"
                      />
                    )}

                    {p.eco_friendly && (
                      <Flag
                        text="🌱 Eco Friendly"
                        background="#dcfce7"
                        color="#166534"
                      />
                    )}

                    {p.premium_buyer && (
                      <Flag
                        text="⭐ Premium Buyer"
                        background="#ede9fe"
                        color="#5b21b6"
                      />
                    )}
                  </div>
                </div>
              )
            )}
          </div>

          {/* =================================================
              RESEARCH SUMMARY
          ================================================= */}

          <h2
            style={{
              marginTop:
                "45px",
              color:
                "#2563eb",
            }}
          >
            Research Summary
          </h2>

          <div
            style={{
              display:
                "grid",
              gridTemplateColumns:
                "repeat(auto-fit,minmax(180px,1fr))",
              gap:
                "20px",
              marginTop:
                "20px",
            }}
          >
            <SummaryCard
              title="Sample Size"
              value={
                personas.length
              }
            />

            <SummaryCard
              title="Average Age"
              value={
                averageAge
              }
            />

            <SummaryCard
              title="Female Users"
              value={
                femaleUsers
              }
            />

            <SummaryCard
              title="Male Users"
              value={
                maleUsers
              }
            />

            <SummaryCard
              title="Health Conscious"
              value={percentage(
                healthConscious
              )}
            />

            <SummaryCard
              title="Budget Conscious"
              value={percentage(
                budgetConscious
              )}
            />

            <SummaryCard
              title="Eco Friendly"
              value={percentage(
                ecoFriendly
              )}
            />

            <SummaryCard
              title="Premium Buyers"
              value={percentage(
                premiumBuyers
              )}
            />
          </div>

          {/* =================================================
              EXPORT
          ================================================= */}

          <div
            style={{
              ...sectionStyle,
              background:
                "#f8fafc",
            }}
          >
            <h2
              style={{
                color:
                  "#2563eb",
              }}
            >
              Export Personas
            </h2>

            <p
              style={{
                color:
                  "#555",
              }}
            >
              Download your generated synthetic personas for
              further analysis.
            </p>

            <div
              style={{
                display:
                  "flex",
                gap:
                  "15px",
                flexWrap:
                  "wrap",
              }}
            >
              <button
                onClick={
                  downloadCSV
                }
                style={buttonStyle(
                  "#2563eb"
                )}
              >
                📥 Download CSV
              </button>

              <button
                onClick={
                  downloadJSON
                }
                style={buttonStyle(
                  "#16a34a"
                )}
              >
                📄 Download JSON
              </button>

              <button
                onClick={
                  generateResearchReport
                }
                disabled={
                  reportLoading
                }
                style={buttonStyle(
                  reportLoading
                    ? "#777"
                    : "#7c3aed"
                )}
              >
                {reportLoading
                  ? "Generating Report..."
                  : "📄 Generate Research Report"}
              </button>
            </div>
          </div>

          {/* =================================================
              PERSONA SURVEY MODE
          ================================================= */}

          <div
            style={
              sectionStyle
            }
          >
            <h2
              style={{
                color:
                  "#2563eb",
              }}
            >
              🤖 Persona Survey Mode
            </h2>

            <p
              style={{
                color:
                  "#555",
              }}
            >
              Ask questions to a synthetic user and maintain
              conversation memory.
            </p>

            <label>
              <b>
                Select Persona
              </b>
            </label>

            <select
              value={
                selectedPersona
                  ? selectedPersona.customer_id
                  : ""
              }
              onChange={(e) =>
                handlePersonaChange(
                  e.target.value
                )
              }
              style={
                inputStyle
              }
            >
              <option value="">
                -- Select a Persona --
              </option>

              {personas.map(
                (
                  p,
                  index
                ) => (
                  <option
                    key={
                      p.customer_id ||
                      index
                    }
                    value={
                      p.customer_id
                    }
                  >
                    {p.name ||
                      `Persona ${
                        index +
                        1
                      }`}
                  </option>
                )
              )}
            </select>

            {selectedPersona && (
              <div
                style={{
                  display:
                    "flex",
                  alignItems:
                    "center",
                  gap:
                    "15px",
                  padding:
                    "15px",
                  marginTop:
                    "20px",
                  marginBottom:
                    "20px",
                  background:
                    "#eff6ff",
                  borderRadius:
                    "10px",
                }}
              >
                <img
                  src={`https://ui-avatars.com/api/?name=${encodeURIComponent(
                    selectedPersona.name ||
                      "User"
                  )}&background=2563eb&color=fff&size=128`}
                  alt={
                    selectedPersona.name
                  }
                  style={{
                    width:
                      "60px",
                    height:
                      "60px",
                    borderRadius:
                      "50%",
                  }}
                />

                <div>
                  <h3
                    style={{
                      margin:
                        0,
                      color:
                        "#2563eb",
                    }}
                  >
                    {
                      selectedPersona.name
                    }
                  </h3>

                  <p
                    style={{
                      margin:
                        "5px 0 0",
                    }}
                  >
                    {
                      selectedPersona.age
                    }{" "}
                    years old •{" "}
                    {
                      selectedPersona.occupation
                    }
                  </p>
                </div>
              </div>
            )}

            <label>
              <b>
                Research Question
              </b>
            </label>

            <textarea
              rows="4"
              value={
                question
              }
              onChange={(e) =>
                setQuestion(
                  e.target.value
                )
              }
              placeholder="Example: What is most important to you when buying soap?"
              style={{
                ...inputStyle,
                resize:
                  "vertical",
              }}
            />

            <div
              style={{
                display:
                  "flex",
                gap:
                  "10px",
                flexWrap:
                  "wrap",
                marginTop:
                  "15px",
              }}
            >
              <button
                onClick={
                  askPersona
                }
                disabled={
                  chatLoading
                }
                style={buttonStyle(
                  chatLoading
                    ? "#777"
                    : "#2563eb"
                )}
              >
                {chatLoading
                  ? "Thinking..."
                  : "💬 Ask Persona"}
              </button>

              {chatHistory.length >
                0 && (
                <button
                  onClick={
                    clearPersonaChat
                  }
                  style={buttonStyle(
                    "#dc2626"
                  )}
                >
                  🗑️ Clear Conversation
                </button>
              )}
            </div>

            {/* =================================================
                CONVERSATION
            ================================================= */}

            {chatHistory.length >
              0 && (
              <div
                style={{
                  marginTop:
                    "30px",
                }}
              >
                <h3
                  style={{
                    color:
                      "#2563eb",
                  }}
                >
                  💬 Conversation
                </h3>

                {chatHistory.map(
                  (
                    chat,
                    index
                  ) => (
                    <div
                      key={
                        index
                      }
                      style={{
                        marginBottom:
                          "20px",
                      }}
                    >
                      <div
                        style={{
                          background:
                            "#eff6ff",
                          padding:
                            "15px",
                          borderRadius:
                            "10px",
                          marginBottom:
                            "10px",
                        }}
                      >
                        <b>
                          You:
                        </b>

                        <p
                          style={{
                            marginBottom:
                              0,
                            marginTop:
                              "8px",
                          }}
                        >
                          {
                            chat.question
                          }
                        </p>
                      </div>

                      <div
                        style={{
                          background:
                            "#f0fdf4",
                          padding:
                            "15px",
                          borderRadius:
                            "10px",
                          borderLeft:
                            "4px solid #16a34a",
                        }}
                      >
                        <b>
                          {selectedPersona?.name ||
                            "Persona"}
                          :
                        </b>

                        <p
                          style={{
                            marginBottom:
                              0,
                            marginTop:
                              "8px",
                            lineHeight:
                              "1.6",
                          }}
                        >
                          {
                            chat.answer
                          }
                        </p>
                      </div>
                    </div>
                  )
                )}

                <div
                  style={{
                    display:
                      "flex",
                    gap:
                      "10px",
                    flexWrap:
                      "wrap",
                  }}
                >
                  <button
                    onClick={
                      extractInsights
                    }
                    disabled={
                      insightLoading
                    }
                    style={buttonStyle(
                      insightLoading
                        ? "#777"
                        : "#7c3aed"
                    )}
                  >
                    {insightLoading
                      ? "Analyzing Interviews..."
                      : "🔎 Extract Insights"}
                  </button>

                  <button
                    onClick={
                      scoreProductUsage
                    }
                    disabled={
                      usageLoading
                    }
                    style={buttonStyle(
                      usageLoading
                        ? "#777"
                        : "#ea580c"
                    )}
                  >
                    {usageLoading
                      ? "Scoring Product Usage..."
                      : "📊 Would Use This Product?"}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* =================================================
              INSIGHTS
          ================================================= */}

          {insights && (
            <div
              style={{
                ...sectionStyle,
                background: "#faf5ff",
              }}
            >
              <h2
                style={{
                  color: "#7c3aed",
                  marginTop: 0,
                }}
              >
                🔎 Research Insights
              </h2>

              {/* RECURRING THEMES */}
              <h3>📌 Recurring Themes</h3>

              {insights.recurring_themes?.length > 0 ? (
                insights.recurring_themes.map(
                  (theme, index) => (
                    <div
                      key={index}
                      style={{
                        background: "white",
                        padding: "15px",
                        marginBottom: "10px",
                        borderRadius: "8px",
                        borderLeft: "4px solid #7c3aed",
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          gap: "10px",
                          flexWrap: "wrap",
                        }}
                      >
                        <b style={{ fontSize: "17px" }}>
                          {theme.theme}
                        </b>

                        {theme.count !== null &&
                          theme.count !== undefined && (
                            <span
                              style={{
                                background: "#ede9fe",
                                color: "#5b21b6",
                                padding: "5px 9px",
                                borderRadius: "15px",
                                fontSize: "13px",
                                fontWeight: "bold",
                              }}
                            >
                              Mentioned by {theme.count}{" "}
                              {Number(theme.count) === 1
                                ? "persona"
                                : "personas"}
                            </span>
                          )}
                      </div>

                      {theme.description && (
                        <p
                          style={{
                            margin: "8px 0 0",
                            lineHeight: "1.5",
                          }}
                        >
                          {theme.description}
                        </p>
                      )}

                      {theme.percentage !== null &&
                        theme.percentage !== undefined && (
                          <small>
                            {theme.percentage}% of interview responses
                          </small>
                        )}
                    </div>
                  )
                )
              ) : (
                <p>No recurring themes found.</p>
              )}

              {/* SENTIMENT */}
              <h3 style={{ marginTop: "25px" }}>
                😊 Sentiment Breakdown
              </h3>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns:
                    "repeat(auto-fit,minmax(180px,1fr))",
                  gap: "15px",
                }}
              >
                <SummaryCard
                  title="Positive"
                  value={`${insights.sentiment?.positive ?? 0}%`}
                />

                <SummaryCard
                  title="Neutral"
                  value={`${insights.sentiment?.neutral ?? 0}%`}
                />

                <SummaryCard
                  title="Negative"
                  value={`${insights.sentiment?.negative ?? 0}%`}
                />
              </div>

              {/* AGREEMENT */}
              <h3 style={{ marginTop: "25px" }}>
                🤝 Agreement Patterns
              </h3>

              {insights.agreement_patterns?.length > 0 ? (
                insights.agreement_patterns.map(
                  (pattern, index) => (
                    <div
                      key={index}
                      style={{
                        background: "white",
                        padding: "15px",
                        marginBottom: "10px",
                        borderRadius: "8px",
                        borderLeft: "4px solid #2563eb",
                      }}
                    >
                      <b style={{ fontSize: "17px" }}>
                        {pattern.topic}
                      </b>

                      {pattern.description && (
                        <p
                          style={{
                            margin: "8px 0",
                            lineHeight: "1.5",
                          }}
                        >
                          {pattern.description}
                        </p>
                      )}

                      {pattern.agreement !== null &&
                        pattern.agreement !== undefined && (
                          <strong>
                            Agreement: {pattern.agreement}%
                          </strong>
                        )}
                    </div>
                  )
                )
              ) : (
                <p>No agreement patterns found.</p>
              )}

              {/* BEHAVIORAL TRENDS */}
              <h3 style={{ marginTop: "25px" }}>
                📈 Behavioral Trends
              </h3>

              {insights.behavioral_trends?.length > 0 ? (
                <ul>
                  {insights.behavioral_trends.map(
                    (trend, index) => (
                      <li
                        key={index}
                        style={{
                          marginBottom: "10px",
                          lineHeight: "1.5",
                        }}
                      >
                        {trend.text}
                      </li>
                    )
                  )}
                </ul>
              ) : (
                <p>No behavioral trends found.</p>
              )}

              {/* KEY FINDINGS */}
              <h3 style={{ marginTop: "25px" }}>
                💡 Key Findings
              </h3>

              {insights.key_findings?.length > 0 ? (
                <ul>
                  {insights.key_findings.map(
                    (finding, index) => (
                      <li
                        key={index}
                        style={{
                          marginBottom: "10px",
                          lineHeight: "1.5",
                        }}
                      >
                        {finding}
                      </li>
                    )
                  )}
                </ul>
              ) : (
                <p>No key findings found.</p>
              )}

              {/* DATA NOTE */}
              {insights.response_count !== undefined && (
                <div
                  style={{
                    marginTop: "20px",
                    padding: "12px 15px",
                    background: "#f3e8ff",
                    borderRadius: "8px",
                    color: "#581c87",
                    fontSize: "14px",
                  }}
                >
                  <b>Interview responses analyzed:</b>{" "}
                  {insights.response_count}
                </div>
              )}
            </div>
          )}

          {/* =================================================
              PRODUCT USAGE
          ================================================= */}

          {usageScores && (
            <div
              style={{
                ...sectionStyle,
                background:
                  "#fff7ed",
                border:
                  "1px solid #fed7aa",
              }}
            >
              <h2
                style={{
                  color:
                    "#ea580c",
                  marginTop:
                    0,
                }}
              >
                📊 Would Use This Product?
              </h2>

              <div
                style={{
                  display:
                    "grid",
                  gridTemplateColumns:
                    "repeat(auto-fit,minmax(220px,1fr))",
                  gap:
                    "15px",
                  marginBottom:
                    "25px",
                }}
              >
                <SummaryCard
                  title="Overall Score"
                  value={`${usageScores.overall_score ?? usageScores.overall_usage_score ?? 0}/100`}
                />

                <SummaryCard
                  title="Overall Would Use"
                  value={`${usageScores.overall_would_use ?? usageScores.overall_would_use_percentage ?? 0}%`}
                />
              </div>

              {usageScores.overall_summary && (
                <div
                  style={{
                    background:
                      "white",
                    padding:
                      "15px",
                    borderRadius:
                      "8px",
                    marginBottom:
                      "20px",
                  }}
                >
                  <b>
                    Overall Summary
                  </b>

                  <p>
                    {
                      usageScores.overall_summary
                    }
                  </p>
                </div>
              )}

              <h3>
                👥 Persona-Level Scores
              </h3>

              {usageScores.persona_scores?.length >
              0 ? (
                usageScores.persona_scores.map(
                  (
                    item,
                    index
                  ) => (
                    <div
                      key={
                        index
                      }
                      style={{
                        background:
                          "white",
                        padding:
                          "15px",
                        marginBottom:
                          "10px",
                        borderRadius:
                          "8px",
                        borderLeft:
                          "4px solid #ea580c",
                      }}
                    >
                      <h4
                        style={{
                          margin:
                            "0 0 8px",
                        }}
                      >
                        {item.name ||
                          item.persona ||
                          "Persona"}
                      </h4>

                      <p>
                        <b>
                          Would Use:
                        </b>{" "}
                        {
                          item.would_use ||
                          item.decision ||
                          "N/A"
                        }
                      </p>

                      <p>
                        <b>
                          Score:
                        </b>{" "}
                        {
                          item.score ??
                          item.usage_score ??
                          0
                        }
                        /100
                      </p>

                      <p>
                        <b>
                          Segment:
                        </b>{" "}
                        {
                          item.segment ||
                          "General customers"
                        }
                      </p>

                      {item.reasoning && (
                        <p>
                          <b>
                            Reasoning:
                          </b>{" "}
                          {
                            item.reasoning
                          }
                        </p>
                      )}
                    </div>
                  )
                )
              ) : (
                <p>
                  No persona-level scores available.
                </p>
              )}

              <h3
                style={{
                  marginTop:
                    "25px",
                }}
              >
                📈 Segment Summary
              </h3>

              {usageScores.segment_summary?.length >
              0 ? (
                usageScores.segment_summary.map(
                  (
                    segment,
                    index
                  ) => (
                    <div
                      key={
                        index
                      }
                      style={{
                        background:
                          "white",
                        padding:
                          "15px",
                        marginBottom:
                          "10px",
                        borderRadius:
                          "8px",
                      }}
                    >
                      <h4>
                        {
                          segment.segment
                        }
                      </h4>

                      <p>
                        <b>
                          Personas:
                        </b>{" "}
                        {
                          segment.count ??
                          segment.persona_count ??
                          0
                        }
                      </p>

                      <p>
                        <b>
                          Yes:
                        </b>{" "}
                        {
                          segment.yes ??
                          segment.yes_count ??
                          0
                        }
                        {"  "}
                        <b>
                          Maybe:
                        </b>{" "}
                        {
                          segment.maybe ??
                          segment.maybe_count ??
                          0
                        }
                        {"  "}
                        <b>
                          No:
                        </b>{" "}
                        {
                          segment.no ??
                          segment.no_count ??
                          0
                        }
                      </p>

                      <p>
                        <b>
                          Average Score:
                        </b>{" "}
                        {
                          segment.average_score ??
                          0
                        }
                        /100
                      </p>

                      {segment.would_use_percentage !==
                        undefined && (
                        <p>
                          <b>
                            Would Use:
                          </b>{" "}
                          {
                            segment.would_use_percentage
                          }
                          %
                        </p>
                      )}

                      {segment.reasoning && (
                        <p>
                          {
                            segment.reasoning
                          }
                        </p>
                      )}
                    </div>
                  )
                )
              ) : (
                <p>
                  No segment summary available.
                </p>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

// =========================================================
// SUMMARY CARD
// =========================================================

function SummaryCard({
  title,
  value,
}) {
  return (
    <div
      style={{
        background:
          "#f8fafc",
        padding:
          "20px",
        borderRadius:
          "12px",
        textAlign:
          "center",
        boxShadow:
          "0 3px 8px rgba(0,0,0,0.1)",
      }}
    >
      <h3
        style={{
          color:
            "#2563eb",
          marginBottom:
            "10px",
        }}
      >
        {title}
      </h3>

      <h2
        style={{
          color:
            "#111",
          margin: 0,
        }}
      >
        {value}
      </h2>
    </div>
  );
}

// =========================================================
// FLAG
// =========================================================

function Flag({
  text,
  background,
  color,
}) {
  return (
    <span
      style={{
        background,
        color,
        padding:
          "6px 10px",
        borderRadius:
          "20px",
        fontSize:
          "13px",
        fontWeight:
          "bold",
      }}
    >
      {text}
    </span>
  );
}

// =========================================================
// BUTTON STYLE
// =========================================================

function buttonStyle(
  background
) {
  return {
    background,
    color: "white",
    padding:
      "13px 25px",
    border: "none",
    borderRadius:
      "7px",
    fontSize:
      "16px",
    cursor:
      background ===
      "#777"
        ? "not-allowed"
        : "pointer",
    fontWeight:
      "bold",
  };
}

export default App;