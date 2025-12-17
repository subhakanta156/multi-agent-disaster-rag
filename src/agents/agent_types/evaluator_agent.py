"""
EvaluatorAgent (LangGraph node)
- Receives state containing:
    state["query"]           : original user query
    state["plan"]            : planner output (dict)
    state["selected_agent"]  : agent that executed
    state["agent_response"]  : response produced by that agent

- Responsibilities:
  1) Score/approve planner decision if needed (simple check)
  2) Evaluate answer quality (accuracy / hallucination risk / completeness)
  3) If evaluation suggests improvement and web_search or rag tool available,
     optionally call them to augment/improve the answer, and return improved_answer.
- Output stored in state["evaluation"]
"""

from langchain_groq import ChatGroq
import json
import re

class EvaluatorAgent:
    def __init__(self, llm=None, tools: dict = None, auto_improve_confidence: float = 0.75):
        self.llm = llm or ChatGroq(model="llama-3.1-8b-instant")
        self.tools = tools or {}
        # if planner confidence < this, evaluator is stricter
        self.auto_improve_confidence = auto_improve_confidence

    def __call__(self, state: dict):
        query = state.get("query", "")
        plan = state.get("plan", {}) or {}
        selected_agent = state.get("selected_agent")
        agent_response = state.get("agent_response", "")

        # 1) Basic planner approval check
        planner_conf = float(plan.get("confidence", 0.0))
        planner_agent = plan.get("next_agent", "general")

        planner_ok = planner_conf >= 0.6  # threshold for trust
        planner_note = "approved" if planner_ok else "low_confidence"

        # 2) LLM-based evaluation of the agent's response quality
        system_prompt = (
            "You are an evaluator. Score the assistant's answer on three aspects: "
            "factuality (does it contradict known context), "
            "completeness (did it answer user's question), "
            "safety (no harmful or misleading instructions). "
            "Return JSON with keys: score (0.0-1.0), issues (list of strings), suggestion (short)."
        )

        user_prompt = (
            f"User query: {query}\n\n"
            f"Selected agent: {selected_agent}\n\n"
            f"Agent response:\n{agent_response}\n\n"
            "Evaluate and return JSON."
        )

        try:
            resp = self.llm.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])
            eval_json = {}
            try:
                eval_json = json.loads(resp.content)
            except Exception:
                # If LLM doesn't return strict JSON, do fuzzy parsing
                # We'll set a default evaluation
                eval_json = {"score": 0.7, "issues": [], "suggestion": "No strict JSON from LLM; default 0.7"}

        except Exception as e:
            eval_json = {"score": 0.5, "issues": [f"Evaluator LLM error: {str(e)}"], "suggestion": "Evaluator LLM error"}

        score = float(eval_json.get("score", 0.0))
        issues = eval_json.get("issues", [])
        suggestion = eval_json.get("suggestion", "")

        approved = (score >= 0.7) and planner_ok

        result = {
            "approved": approved,
            "score": score,
            "issues": issues,
            "suggestion": suggestion,
            "planner_check": {"planner_agent": planner_agent, "planner_confidence": planner_conf, "planner_note": planner_note}
        }

        # 3) AUTO-IMPROVE: If not approved or score low + web_search available, try to improve
        if (not approved or score < self.auto_improve_confidence) and ("web_search" in self.tools or "rag" in self.tools):
            # Decide which augmentation to use
            improved_text = None
            augmentation_note = None

            # Prefer RAG when query is historical/knowledge and tool exists
            if planner_agent == "rag" and "rag" in self.tools:
                try:
                    # call rag tool to fetch better context
                    docs = self.tools["rag"].execute(query=query, k=5)
                    augmentation_note = "RAG augmentation used"
                    # simple concat improvement: ask LLM to rewrite using docs
                    context = "\n\n".join([d.get("content","") for d in docs if isinstance(d, dict)])
                    improve_prompt = (
                        "Rewrite and improve the previous answer using the context below. "
                        "Be concise and cite filenames/pages if available.\n\n"
                        f"Context:\n{context}\n\n"
                        f"Original answer:\n{agent_response}"
                    )
                    improved_resp = self.llm.invoke([{"role":"user","content":improve_prompt}])
                    improved_text = improved_resp.content

                except Exception as e:
                    issues.append(f"RAG augmentation failed: {str(e)}")

            # Otherwise use web search if available
            elif "web_search" in self.tools:
                try:
                    search_output = self.tools["web_search"].execute(query=query)
                    augmentation_note = "WebSearch augmentation used"
                    improve_prompt = (
                        "Using the search snippets below, improve the original answer. "
                        "If snippets contradict the original answer, prefer factual snippets and correct the response.\n\n"
                        f"Snippets:\n{search_output}\n\nOriginal answer:\n{agent_response}"
                    )
                    improved_resp = self.llm.invoke([{"role":"user","content":improve_prompt}])
                    improved_text = improved_resp.content

                except Exception as e:
                    issues.append(f"WebSearch augmentation failed: {str(e)}")

            # If improved_text found, update result
            if improved_text:
                result["improved_answer"] = improved_text
                result["augmentation"] = augmentation_note
                result["approved_after_improve"] = True
            else:
                result["approved_after_improve"] = False

        # Save evaluation into state
        return {"evaluation": result}
