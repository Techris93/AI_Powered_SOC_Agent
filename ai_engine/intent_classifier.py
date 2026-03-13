"""Intent Classification for Security Queries"""
import json
from typing import Dict, Literal
from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel, Field, ValidationError
from config.llm_config import LLMConfig


class QueryIntent(BaseModel):
    """Structured output for query intent classification"""
    intent: Literal[
        "search_logs",
        "investigate_incident",
        "threat_intel_lookup",
        "generate_report",
        "analyze_behavior",
        "hunt_threats"
    ] = Field(description="The primary intent of the security query")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    entities: Dict[str, str] = Field(
        description="Extracted entities like IP addresses, domains, usernames, time ranges",
        default={}
    )
    keywords: list[str] = Field(
        description="Important security-related keywords from the query",
        default=[]
    )


class IntentClassifier:
    """Classifies user queries to determine intent and extract entities"""

    def __init__(self):
        self.async_client = AsyncOpenAI(api_key=LLMConfig.OPENAI_API_KEY)
        self.sync_client = OpenAI(api_key=LLMConfig.OPENAI_API_KEY)

    def _build_messages(self, query_text: str) -> list[dict[str, str]]:
        return [
            {
                "role": "system",
                "content": (
                    "You are a security analyst assistant. Analyze the user's security query and "
                    "return only JSON with this shape: "
                    '{"intent":"search_logs|investigate_incident|threat_intel_lookup|generate_report|analyze_behavior|hunt_threats",'
                    '"confidence":0.0,"entities":{},"keywords":[]}.'
                )
            },
            {
                "role": "user",
                "content": (
                    f"Query: {query_text}\n\n"
                    "Classify the intent as one of:\n"
                    "- search_logs: User wants to search security logs for specific events\n"
                    "- investigate_incident: User wants to investigate a specific security incident\n"
                    "- threat_intel_lookup: User wants information about IPs, domains, or file hashes\n"
                    "- generate_report: User wants to generate a security report\n"
                    "- analyze_behavior: User wants to analyze behavioral patterns or anomalies\n"
                    "- hunt_threats: User wants to proactively hunt for threats\n\n"
                    "Extract relevant entities such as IP addresses, domains, usernames, time ranges, "
                    "attack types, and file hashes. Also extract important security-related keywords."
                )
            }
        ]

    def _parse_intent(self, content: str, query_text: str) -> QueryIntent:
        try:
            payload = json.loads(content)
            return QueryIntent.model_validate(payload)
        except (json.JSONDecodeError, ValidationError, TypeError):
            return self._fallback_intent(query_text)

    def _fallback_intent(self, query_text: str) -> QueryIntent:
        lowered_query = query_text.lower()

        if any(keyword in lowered_query for keyword in ["report", "summary", "summarize"]):
            intent = "generate_report"
        elif any(keyword in lowered_query for keyword in ["threat", "hunt", "ioc"]):
            intent = "hunt_threats"
        elif any(keyword in lowered_query for keyword in ["intel", "domain", "hash", "ip"]):
            intent = "threat_intel_lookup"
        elif any(keyword in lowered_query for keyword in ["incident", "investigate", "breach"]):
            intent = "investigate_incident"
        elif any(keyword in lowered_query for keyword in ["behavior", "anomaly", "pattern"]):
            intent = "analyze_behavior"
        else:
            intent = "search_logs"

        keywords = [token.strip(".,?!") for token in query_text.split() if len(token.strip(".,?!")) > 2]

        return QueryIntent(
            intent=intent,
            confidence=0.5,
            entities={},
            keywords=keywords[:10]
        )

    async def classify(self, query_text: str) -> QueryIntent:
        """
        Classify the intent of a security query

        Args:
            query_text: Natural language security query

        Returns:
            QueryIntent with classified intent, confidence, entities, and keywords
        """
        response = await self.async_client.chat.completions.create(
            model=LLMConfig.get_model_name(),
            temperature=LLMConfig.OPENAI_TEMPERATURE,
            response_format={"type": "json_object"},
            messages=self._build_messages(query_text)
        )
        content = response.choices[0].message.content or "{}"
        return self._parse_intent(content, query_text)

    def classify_sync(self, query_text: str) -> QueryIntent:
        """
        Synchronous version of classify

        Args:
            query_text: Natural language security query

        Returns:
            QueryIntent with classified intent, confidence, entities, and keywords
        """
        response = self.sync_client.chat.completions.create(
            model=LLMConfig.get_model_name(),
            temperature=LLMConfig.OPENAI_TEMPERATURE,
            response_format={"type": "json_object"},
            messages=self._build_messages(query_text)
        )
        content = response.choices[0].message.content or "{}"
        return self._parse_intent(content, query_text)


# Example usage
if __name__ == "__main__":
    classifier = IntentClassifier()

    # Test queries
    test_queries = [
        "Show me all failed login attempts from IP 192.168.1.100 in the last 24 hours",
        "What can you tell me about the domain evil.com?",
        "Analyze suspicious PowerShell executions from yesterday",
        "Generate a summary report of all phishing incidents this week"
    ]

    for query in test_queries:
        result = classifier.classify_sync(query)
        print(f"\nQuery: {query}")
        print(f"Intent: {result.intent} (confidence: {result.confidence})")
        print(f"Entities: {result.entities}")
        print(f"Keywords: {result.keywords}")
