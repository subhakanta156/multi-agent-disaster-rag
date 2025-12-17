from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseAgent(ABC):
    """
    Parent class for all agents.
    Compatible with LangGraph workflow and @tool decorated tools.
    
    All child agents must implement run() method.
    """

    def __init__(self, name: str, llm_client=None, tools: Dict = None):
        """
        Initialize base agent.
        
        Args:
            name: Agent name for logging
            llm_client: LangChain LLM instance (e.g., ChatGroq)
            tools: Dict of tool_name -> tool_function/instance
        """
        self.name = name
        self.client = llm_client  # LangChain LLM (ChatGroq)
        self.tools = tools or {}  # dict: tool_name -> @tool function or class

    # =========================================
    # MUST BE IMPLEMENTED IN CHILD AGENTS
    # =========================================
    
    @abstractmethod
    def run(self, query: str, metadata: Dict = None) -> Dict:
        """
        Main execution logic of each agent.
        
        This method is called by LangGraph nodes.
        
        Args:
            query: User query string
            metadata: Optional metadata dict
            
        Returns:
            Dict with agent response
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement run() method."
        )

    # =========================================
    # TOOL CALLING INTERFACE (UPDATED FOR @tool)
    # =========================================
    
    def use_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Call a registered tool by its name.
        
        Supports both:
        - @tool decorated functions (use .invoke())
        - Class-based tools (use .invoke() or direct call)
        
        Args:
            tool_name: Name of the tool to call
            **kwargs: Tool-specific parameters
            
        Returns:
            Tool output
            
        Raises:
            ValueError: If tool not found
            TypeError: If tool doesn't support calling
        """
        tool = self.tools.get(tool_name)

        if not tool:
            raise ValueError(
                f"[{self.name}] Tool '{tool_name}' not found. "
                f"Available tools: {list(self.tools.keys())}"
            )

        # Try different calling methods in order of preference
        try:
            # Method 1: .invoke() - LangChain @tool standard
            if hasattr(tool, "invoke"):
                return tool.invoke(kwargs)
            
            # Method 2: Direct call - for callable tools
            elif callable(tool):
                return tool(**kwargs)
            
            # Method 3: .execute() - legacy class-based tools
            elif hasattr(tool, "execute"):
                return tool.execute(**kwargs)
            
            else:
                raise TypeError(
                    f"[{self.name}] Tool '{tool_name}' is not callable. "
                    f"Type: {type(tool)}"
                )
        
        except Exception as e:
            return f"[Tool Error in {self.name}] {tool_name}: {str(e)}"

    # =========================================
    # UNIVERSAL LLM CALL FOR ALL AGENTS
    # =========================================
    
    def ask_llm(
        self,
        messages: list,
        model: str = "mixtral-8x7b-32768",
        temperature: float = 0.2
    ) -> str:
        """
        Call LLM using LangChain interface.
        
        All agents use this method for LLM reasoning.
        Compatible with LangGraph workflow.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (default: mixtral-8x7b-32768)
            temperature: Sampling temperature (default: 0.2)
            
        Returns:
            LLM response content as string
            
        Example:
            messages = [
                {"role": "system", "content": "You are helpful"},
                {"role": "user", "content": "Hello"}
            ]
            response = self.ask_llm(messages)
        """
        if not self.client:
            raise RuntimeError(
                f"[{self.name}] No LLM client assigned. "
                f"Pass ChatGroq instance when initializing agent."
            )

        try:
            # LangChain LLM.invoke() expects list of message objects
            # Convert dict format to LangChain format if needed
            from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
            
            formatted_messages = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "system":
                    formatted_messages.append(SystemMessage(content=content))
                elif role == "assistant" or role == "ai":
                    formatted_messages.append(AIMessage(content=content))
                else:  # user or default
                    formatted_messages.append(HumanMessage(content=content))
            
            # Call LLM using LangChain interface
            response = self.client.invoke(formatted_messages)
            
            # Extract content from response
            return response.content

        except Exception as e:
            return f"[LLM Error in {self.name}] {str(e)}"
    
    # =========================================
    # UTILITY METHODS
    # =========================================
    
    def get_available_tools(self) -> list:
        """Get list of available tool names"""
        return list(self.tools.keys())
    
    def has_tool(self, tool_name: str) -> bool:
        """Check if tool is available"""
        return tool_name in self.tools
    
    def __str__(self) -> str:
        tools_str = ", ".join(self.tools.keys()) if self.tools else "None"
        return f"{self.name} (Tools: {tools_str})"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"