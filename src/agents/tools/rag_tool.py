from typing import List, Dict


class RAGTool:
    def __init__(self, retriever):
        self.retriever = retriever
        self.name = "rag_retriever"
        self.description = "Retrieve relevant documents from knowledge base"
    
    def invoke(self, input_dict: dict) -> str:
        query = input_dict.get("query", "")
        k = input_dict.get("k", 5)
        return self.retrieve(query, k)
    
    def retrieve(self, query: str, k: int = 5) -> str:
        if not query:
            return "Error: No query provided"
        
        try:
            results = self.retriever.get_top_k(query, k=k)
            
            if not results:
                return "No relevant documents found"
            
            formatted = self._format_documents(results)
            return formatted
        
        except Exception as e:
            return f"RAG retrieval error: {str(e)}"
    
    def _format_documents(self, docs: List) -> str:
        if not docs:
            return "No documents retrieved"
        
        output = []
        output.append("=" * 60)
        output.append("RETRIEVED DOCUMENTS")
        output.append("=" * 60)
        
        for i, doc in enumerate(docs, 1):
            if isinstance(doc, dict):
                content = doc.get("content", doc.get("text", ""))
                source = doc.get("file", doc.get("source", "Unknown"))
                page = doc.get("page", "N/A")
                score = doc.get("score", 0.0)
            else:
                content = str(doc)
                source = "Unknown"
                page = "N/A"
                score = 0.0
            
            doc_text = (
                f"\n--- Document {i} ---\n"
                f"Source: {source} (Page: {page})\n"
                f"Relevance: {score:.3f}\n"
                f"{'-' * 60}\n"
                f"{content}\n"
            )
            output.append(doc_text)
        
        return "\n".join(output)
    
    def __call__(self, query: str = None, k: int = 5, **kwargs) -> str:
        if isinstance(query, dict):
            return self.invoke(query)
        else:
            return self.retrieve(query or kwargs.get("query", ""), k)