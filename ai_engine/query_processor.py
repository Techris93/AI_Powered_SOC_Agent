"""Advanced Query Processing with OpenAI"""
import json
from typing import Dict, Any, Optional
from openai import AsyncOpenAI, OpenAI
from config.llm_config import LLMConfig
from ai_engine.intent_classifier import IntentClassifier, QueryIntent


class ElasticsearchQueryGenerator:
    """Generates Elasticsearch queries from natural language using LLM"""

    def __init__(self):
        self.async_client = AsyncOpenAI(api_key=LLMConfig.OPENAI_API_KEY)
        self.sync_client = OpenAI(api_key=LLMConfig.OPENAI_API_KEY)

    def _build_messages(self, user_query: str, intent: QueryIntent) -> list[dict[str, str]]:
        return [
            {
                "role": "system",
                "content": (
                    "You are an expert in Elasticsearch query generation for security operations. "
                    "Return only a valid Elasticsearch query as JSON. Do not include explanations."
                )
            },
            {
                "role": "user",
                "content": (
                    f"User Query: {user_query}\n"
                    f"Intent: {intent.intent}\n"
                    f"Entities: {json.dumps(intent.entities)}\n"
                    f"Keywords: {json.dumps(intent.keywords)}\n\n"
                    "Generate an Elasticsearch query that:\n"
                    "1. Uses the appropriate query type (match, multi_match, range, bool, etc.)\n"
                    "2. Searches across relevant fields for security logs (e.g., @timestamp, source.ip, destination.ip, event.action, message)\n"
                    "3. Handles time ranges appropriately\n"
                    "4. Uses filters for exact matches and queries for full-text search\n"
                    "5. Returns results sorted by @timestamp in descending order\n\n"
                    "Common field mappings:\n"
                    "- IP addresses: source.ip, destination.ip, client.ip, server.ip\n"
                    "- Timestamps: @timestamp, event.created, event.start\n"
                    "- Users: user.name, user.id, related.user\n"
                    "- Actions: event.action, event.outcome\n"
                    "- Attack types: event.category, event.type, threat.technique.name\n\n"
                    "Return JSON with query, sort, and size keys."
                )
            }
        ]

    def _extract_query(self, content: str, user_query: str, intent: QueryIntent) -> Dict[str, Any]:
        cleaned = content.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return self._fallback_query(user_query, intent)

    async def generate_query(
        self,
        user_query: str,
        intent: QueryIntent
    ) -> Dict[str, Any]:
        """
        Generate an Elasticsearch query from natural language

        Args:
            user_query: Original user query
            intent: Classified intent with entities and keywords

        Returns:
            Elasticsearch query as dictionary
        """
        response = await self.async_client.chat.completions.create(
            model=LLMConfig.get_model_name(),
            temperature=0.0,
            response_format={"type": "json_object"},
            messages=self._build_messages(user_query, intent)
        )
        content = response.choices[0].message.content or "{}"
        return self._extract_query(content, user_query, intent)

    def generate_query_sync(
        self,
        user_query: str,
        intent: QueryIntent
    ) -> Dict[str, Any]:
        """
        Synchronous version of generate_query

        Args:
            user_query: Original user query
            intent: Classified intent with entities and keywords

        Returns:
            Elasticsearch query as dictionary
        """
        response = self.sync_client.chat.completions.create(
            model=LLMConfig.get_model_name(),
            temperature=0.0,
            response_format={"type": "json_object"},
            messages=self._build_messages(user_query, intent)
        )
        content = response.choices[0].message.content or "{}"
        return self._extract_query(content, user_query, intent)

    def _fallback_query(self, user_query: str, intent: QueryIntent) -> Dict[str, Any]:
        """
        Generate a basic Elasticsearch query as fallback

        Args:
            user_query: Original user query
            intent: Classified intent

        Returns:
            Basic Elasticsearch query
        """
        # Build a simple multi_match query with keywords
        query_string = " ".join(intent.keywords) if intent.keywords else user_query

        es_query = {
            "query": {
                "multi_match": {
                    "query": query_string,
                    "fields": [
                        "message",
                        "event.action",
                        "event.category",
                        "source.ip",
                        "destination.ip",
                        "user.name"
                    ]
                }
            },
            "sort": [
                {"@timestamp": {"order": "desc"}}
            ],
            "size": LLMConfig.MAX_RESULTS
        }

        # Add time range filter if present in entities
        if "time_range" in intent.entities:
            time_filter = self._parse_time_range(intent.entities["time_range"])
            if time_filter:
                es_query["query"] = {
                    "bool": {
                        "must": [es_query["query"]],
                        "filter": [time_filter]
                    }
                }

        return es_query

    def _parse_time_range(self, time_range: str) -> Optional[Dict[str, Any]]:
        """
        Parse natural language time range into Elasticsearch range query

        Args:
            time_range: Natural language time range (e.g., "last 24 hours")

        Returns:
            Elasticsearch range filter or None
        """
        # Common time range mappings
        time_mapping = {
            "last 24 hours": "now-24h",
            "last hour": "now-1h",
            "today": "now/d",
            "yesterday": "now-1d/d",
            "last 7 days": "now-7d",
            "last week": "now-7d",
            "last 30 days": "now-30d",
            "last month": "now-30d"
        }

        time_range_lower = time_range.lower()

        for key, value in time_mapping.items():
            if key in time_range_lower:
                return {
                    "range": {
                        "@timestamp": {
                            "gte": value,
                            "lte": "now"
                        }
                    }
                }

        return None


class AdvancedQueryProcessor:
    """Main query processor combining intent classification and query generation"""

    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.query_generator = ElasticsearchQueryGenerator()

    async def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Process natural language query and generate Elasticsearch query

        Args:
            user_query: Natural language security query

        Returns:
            Dictionary containing:
            - intent: Classified intent
            - es_query: Generated Elasticsearch query
            - confidence: Confidence score
        """
        # Step 1: Classify intent
        intent = await self.intent_classifier.classify(user_query)

        # Step 2: Generate Elasticsearch query
        es_query = await self.query_generator.generate_query(user_query, intent)

        return {
            "intent": intent.intent,
            "confidence": intent.confidence,
            "entities": intent.entities,
            "keywords": intent.keywords,
            "es_query": es_query
        }

    def process_query_sync(self, user_query: str) -> Dict[str, Any]:
        """
        Synchronous version of process_query

        Args:
            user_query: Natural language security query

        Returns:
            Dictionary containing intent, es_query, and confidence
        """
        # Step 1: Classify intent
        intent = self.intent_classifier.classify_sync(user_query)

        # Step 2: Generate Elasticsearch query
        es_query = self.query_generator.generate_query_sync(user_query, intent)

        return {
            "intent": intent.intent,
            "confidence": intent.confidence,
            "entities": intent.entities,
            "keywords": intent.keywords,
            "es_query": es_query
        }


# Example usage
if __name__ == "__main__":
    import asyncio

    async def main():
        processor = AdvancedQueryProcessor()

        test_queries = [
            "Show me all failed SSH login attempts from IP 192.168.1.100 in the last 24 hours",
            "Find all phishing emails received yesterday",
            "What are the most common attack patterns this week?",
            "Show me ransomware activity targeting finance department"
        ]

        for query in test_queries:
            print(f"\n{'='*80}")
            print(f"User Query: {query}")
            print(f"{'='*80}")

            result = await processor.process_query(query)

            print(f"\nIntent: {result['intent']} (confidence: {result['confidence']})")
            print(f"Entities: {result['entities']}")
            print(f"Keywords: {result['keywords']}")
            print("\nElasticsearch Query:")
            print(json.dumps(result['es_query'], indent=2))

    asyncio.run(main())
