from langgraph.prebuilt import ToolNode
from langchain_groq import ChatGroq
import json


class WeatherAgent:
    """
    Weather Agent:
    - Detect location
    - Map IMD station
    - Scrape IMD weather OR read IMD bulletin PDF
    - Summarize response using LLM
    """

    def __init__(self, tools: dict):
        self.tools = tools
        self.llm = ChatGroq(model="llama-3.1-8b-instant")

    def __call__(self, state):
        query = state["query"].lower()

        # ---------------------------
        # STEP 0 — CHECK IF PDF IS REQUESTED
        # ---------------------------
        pdf_keywords = [
            "pdf", "bulletin", "warning", "advisory", "coastal",
            "fishermen", "rainfall", "weekly", "composite"
        ]

        if any(k in query for k in pdf_keywords):
            # Determine PDF type
            pdf_type = "evening"  # default
            for key in ["coastal", "fishermen", "rainfall", "weekly", "composite"]:
                if key in query:
                    pdf_type = key

            try:
                pdf_output = self.tools["imd_pdf_reader"].invoke({"pdf_type": pdf_type})
                return {
                    "response": f"📄 IMD {pdf_type.upper()} BULLETIN:\n\n{pdf_output}"
                }
            except Exception as e:
                return {"response": f"❌ PDF Error: {str(e)}"}

        # ---------------------------
        # STEP 1 — LOCATION DETECTION
        # ---------------------------
        try:
            location = self.tools["weather_location_detector"].invoke({"query": query})
        except Exception as e:
            return {"response": f"❌ Location detection error: {str(e)}"}

        # ---------------------------
        # STEP 2 — STATION MAPPING
        # ---------------------------
        try:
            station_id = self.tools["weather_station_mapper"].invoke({"location": location})
        except Exception as e:
            return {"response": f"❌ Station mapping error: {str(e)}"}

        if not station_id:
            return {"response": f"❌ IMD station not found for: {location}"}

        # ---------------------------
        # STEP 3 — IMD SCRAPER
        # ---------------------------
        try:
            weather_data_json = self.tools["imd_weather_fetcher"].invoke({"station_id": station_id})
            weather_data = json.loads(weather_data_json)
        except Exception as e:
            return {"response": f"❌ Weather scraping error: {str(e)}"}

        if "error" in weather_data:
            return {"response": f"❌ IMD Scraper Error: {weather_data['error']}"}

        # ---------------------------
        # STEP 4 — LLM SUMMARY
        # ---------------------------
        prompt = f"""
You are an expert IMD forecaster. Summarize the weather conditions based on this data.

Location: {location}
Station ID: {station_id}

Weather Data (JSON):
{json.dumps(weather_data, indent=2)}

User Query: "{state['query']}"

Write a simple, accurate 4–6 sentence weather summary.
"""

        try:
            summary = self.llm.invoke(prompt).content
            return {"response": summary}
        except:
            return {"response": json.dumps(weather_data, indent=2)}
