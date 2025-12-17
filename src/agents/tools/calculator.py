"""
Calculator Tool - Evaluates mathematical expressions safely
Uses LangChain @tool decorator for LangGraph compatibility
"""

from langchain.tools import tool
import numexpr as ne


@tool
def calculator_tool(expression: str) -> str:
    """
    Safely evaluate mathematical expressions.
    
    Supports:
    - Basic arithmetic: +, -, *, /
    - Percentages: "15% of 200"
    - Complex expressions: "(2+3)*4"
    
    Args:
        expression: Mathematical expression to evaluate
        
    Returns:
        String result of calculation or error message
        
    Examples:
        calculator_tool("2 + 2") -> "4"
        calculator_tool("15% of 200") -> "30"
        calculator_tool("(10+5)*3") -> "45"
    """
    if not expression:
        return "Error: No expression provided"
    
    expr = str(expression).strip()
    
    # Handle percentage calculations
    if "%" in expr and "of" in expr.lower():
        result = _handle_percentage(expr)
        if result:
            return result
    
    # Evaluate using numexpr (safe evaluation)
    try:
        result = ne.evaluate(expr)
        
        # Format output
        if isinstance(result, float):
            # Remove unnecessary decimals
            if result.is_integer():
                return str(int(result))
            return f"{result:.4f}".rstrip('0').rstrip('.')
        
        return str(result)
    
    except Exception as e:
        return f"Calculator error: {str(e)}"


def _handle_percentage(expr: str) -> str:
    """
    Handle percentage calculations like "15% of 200"
    
    Args:
        expr: Expression containing percentage
        
    Returns:
        Calculated result or None
    """
    try:
        # Parse "X% of Y" pattern
        parts = expr.lower().replace("%", "").split("of")
        
        if len(parts) != 2:
            return None
        
        percentage = float(parts[0].strip())
        value = float(parts[1].strip())
        
        result = (percentage / 100) * value
        
        if result.is_integer():
            return str(int(result))
        return f"{result:.2f}"
    
    except Exception:
        return None