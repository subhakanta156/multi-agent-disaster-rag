import re

class RoutingPolicy:
    """
    PRIMARY ROUTER for the entire system.
    Decides which agent/tool should handle each query.
    
    Routes:
    - calculator → direct calculator execution
    - web_search → direct web search execution  
    - weather → WeatherAgent
    - disaster → DisasterAgent
    - rag → RAGAgent
    - general → General LLM fallback
    """

    def __init__(self, client=None, debug=False):
        self.debug = debug
        self.client = client  # Optional LLM fallback

        # ==========================================
        # TOOL DETECTION PATTERNS (highest priority)
        # ==========================================
        self.calculator_keywords = [
            "calculate", "compute", "math", "percentage", 
            "addition", "subtraction", "multiply", "divide"
        ]
        
        self.calculator_symbols = ["+", "-", "*", "/", "=", "%"]
        
        self.web_search_keywords = [
            "search", "google", "find", "look up", 
            "latest", "news", "current", "today",
            "what is happening", "recent", "update"
        ]

        # ==========================================
        # AGENT ROUTING PATTERNS
        # ==========================================
        
        # Disaster patterns (regex for precise matching)


        # Weather keywords
        self.weather_keywords = [
            "weather", "temperature", "rain", "rainfall", 
            "wind", "humidity", "cloud", "climate", 
            "forecast", "imd", "heat", "cold", "sunny", 
            "visibility", "today", "tomorrow", "live",
            "coastal", "sea", "fishermen"
        ]

        # RAG/Historical keywords
        self.rag_keywords = [
            "history", "past", "historical", "report", 
            "paper", "document", "study", "research",
            "previous cyclone", "previous disaster",
            "fani", "phailin", "impact", "damage assessment"
        ]

        # Historical intent words
        self.historical_intents = [
            "was", "were", "happened", "occurred", 
            "previous", "last year", "ago"
        ]

    # ==========================================
    # HELPER METHODS
    # ==========================================
    
    def _contains(self, query, keywords):
        """Check if any keyword exists in query"""
        return any(kw in query for kw in keywords)
    
    def _match_regex(self, query, patterns):
        """Check if any regex pattern matches"""
        return any(re.search(p, query, re.IGNORECASE) for p in patterns)
    
    def _has_math_symbols(self, query):
        """Detect mathematical expressions"""
        return any(sym in query for sym in self.calculator_symbols)

    # ==========================================
    # MAIN ROUTING LOGIC
    # ==========================================
    
    def route(self, query: str) -> str:
        """
        PRIMARY ROUTING DECISION
        
        Returns:
        - "calculator" → direct tool execution
        - "web_search" → direct tool execution
        - "weather" → WeatherAgent 
        - "rag" → RAGAgent
        - "general" → General LLM fallback
        """
        q = query.lower().strip()
        
        if self.debug:
            print(f"[RoutingPolicy] Analyzing: {q}")
        
        # ==========================================
        # PRIORITY 1: TOOL DETECTION (fastest)
        # ==========================================
        
        # Calculator check
        if self._has_math_symbols(query) or self._contains(q, self.calculator_keywords):
            if self.debug:
                print("[RoutingPolicy] → calculator")
            return "calculator"
        
        # Web search check (live/latest/news)
        if self._contains(q, self.web_search_keywords):
            if self.debug:
                print("[RoutingPolicy] → web_search")
            return "web_search"
        
        # ==========================================
        # PRIORITY 2: AGENT ROUTING (knowledge-based)
        # ==========================================
        
        # RAG check (historical queries)
        if self._contains(q, self.rag_keywords) or any(word in q for word in self.historical_intents):
            if self.debug:
                print("[RoutingPolicy] → rag")
            return "rag"
        
        
        # Weather check (live weather data)
        if self._contains(q, self.weather_keywords):
            if self.debug:
                print("[RoutingPolicy] → weather")
            return "weather"
        
        # ==========================================
        # PRIORITY 3: LLM FALLBACK (if available)
        # ==========================================
        
        if self.client:
            llm_route = self.llm_fallback(query)
            if self.debug:
                print(f"[RoutingPolicy] → {llm_route} (via LLM)")
            return llm_route
        
        # ==========================================
        # DEFAULT: GENERAL FALLBACK
        # ==========================================
        
        if self.debug:
            print("[RoutingPolicy] → general (default)")
        return "general"

    # ==========================================
    # OPTIONAL: LLM-BASED ROUTING FOR AMBIGUOUS QUERIES
    # ==========================================
    
    def llm_fallback(self, query: str) -> str:
        """
        Use LLM to classify ambiguous queries.
        Only called if no keyword match found.
        """
        try:
            response = self.client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a query classifier. "
                            "Classify the user query into exactly ONE category: "
                            "weather, disaster, rag, general. "
                            "Respond with ONLY the category name, nothing else."
                        )
                    },
                    {"role": "user", "content": query}
                ],
                temperature=0.0,
                max_tokens=10
            )

            label = response.choices[0].message.content.strip().lower()
            
            # Validate LLM output
            valid_routes = ["weather", "disaster", "rag", "general"]
            if label in valid_routes:
                return label
            
            return "general"

        except Exception as e:
            if self.debug:
                print(f"[RoutingPolicy] LLM fallback error: {e}")
            return "general"


# ==========================================
# LANGGRAPH COMPATIBLE WRAPPER (if needed)
# ==========================================

def routing_node(state):
    """
    LangGraph node wrapper for RoutingPolicy.
    Input: state with "query" key
    Output: state with "route" key
    """
    query = state.get("query", "")
    policy = state.get("routing_policy")
    
    if not policy:
        policy = RoutingPolicy()
    
    route = policy.route(query)
    
    return {"route": route}