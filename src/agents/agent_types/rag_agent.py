from agents.base_agent import BaseAgent


class RAGAgent(BaseAgent):
    """
    Retrieval-Augmented Agent.
    Uses vector DB → retrieved chunks → answers via GROQ LLM.
    """

    def __init__(self, llm_client=None, tools=None):
        super().__init__(name="RAGAgent", llm_client=llm_client, tools=tools)

    def run(self, query: str, metadata: dict = None):
        # 1) Tool → Retriever (returns formatted string)
        try:
            retrieved_text = self.use_tool("rag", query=query, k=5)
            
            # Check if it's an error
            if "error" in retrieved_text.lower():
                return {
                    "agent": "rag",
                    "answer": "RAG Tool failed to retrieve relevant information.",
                    "reason": retrieved_text,
                    "context_used": 0
                }
            
            # Use the formatted text directly as context
            context = retrieved_text

        except Exception as e:
            return {
                "agent": "rag",
                "answer": f"RAG retrieval error: {str(e)}",
                "context_used": 0
            }

        # 2) Ask LLM
        messages = [
            {
                "role": "system",
                "content": (
                    "You answer ONLY using the given context.\n"
                    "Do NOT hallucinate. Cite filenames/pages.\n"
                    "If answer not found → respond: 'Information not present in retrieved documents'."
                )
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion:\n{query}"
            }
        ]

        try:
            llm_response = self.ask_llm(messages, model="llama-3.1-8b-instant")
        except Exception as e:
            llm_response = f"LLM error: {str(e)}"

        return {
            "agent": "rag",
            "answer": llm_response,
            "context_used": context.count("Document"),  # Count how many docs
            "raw_context": context[:500] + "...",  # Preview
            "metadata": metadata or {}
        }