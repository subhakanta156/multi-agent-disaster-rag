from langchain_core.messages import HumanMessage, SystemMessage

class UserQueryAgent:
    """
    GENERAL FALLBACK AGENT
    
    Role:
    - Handle general questions that don't fit other agents
    - Use LLM reasoning for conversational queries
    - NO routing responsibility (routing handled by RoutingPolicy)
    
    This agent is called when:
    - Query doesn't match weather/disaster/rag patterns
    - No specific tool needed
    - General conversational queries
    """

    def __init__(self, llm, tools=None):
        """
        Args:
            llm: LangChain LLM instance (e.g., ChatGroq)
            tools: Optional dict of tools (not used for routing anymore)
        """
        self.llm = llm
        self.tools = tools or {}

    def __call__(self, state):
        """
        LangGraph node handler.
        
        Args:
            state: Dict with "query" key
            
        Returns:
            Dict with "agent_response" key
        """
        query = state.get("query", "")
        
        if not query:
            return {
                "agent_response": "I didn't receive a query. Please ask me something!",
                "selected_agent": "user_query"
            }
        
        # Use LLM for general reasoning
        response = self._get_llm_response(query)
        
        return {
            "agent_response": response,
            "selected_agent": "user_query"
        }
    
    def run(self, query: str, metadata: dict = None):
        """
        Direct execution method (for non-LangGraph usage).
        
        Args:
            query: User question
            metadata: Optional context
            
        Returns:
            Dict with response details
        """
        response = self._get_llm_response(query)
        
        return {
            "agent": "user_query",
            "answer": response,
            "metadata": metadata or {}
        }

    def _get_llm_response(self, query: str) -> str:
        """
        Generate LLM response for general queries.
        
        Args:
            query: User question
            
        Returns:
            LLM-generated response
        """
        system_prompt = (
            "You are a helpful assistant for Odisha disaster management. "
            "Provide clear, concise, and accurate information. "
            "If you don't know something, admit it honestly. "
            "For time-sensitive data (weather, news), suggest the user "
            "ask more specifically so the system can use real-time tools."
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query)
        ]
        
        try:
            llm_output = self.llm.invoke(messages)
            return llm_output.content
        
        except Exception as e:
            return f"I encountered an error processing your request: {str(e)}"

    def __str__(self):
        return "UserQueryAgent (General Fallback)"