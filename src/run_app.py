from agents.workflow.workflow import app  

def run_chat():
    print("\n🚀 Odisha Disaster Management Assistant")
    print("=" * 50)
    print("Type 'exit' to quit\n")

    while True:
        query = input("You: ").strip()

        if query.lower() in ["exit", "quit", "bye"]:
            print("👋 Goodbye!")
            break

        if not query:
            continue

        # Prepare initial state
        init_state = {
            "query": query,
            "route": None,
            "selected_agent": None,
            "agent_response": None,
            "evaluation": None,
            "response": None,
            "metadata": {}
        }

        try:
            # Run graph
            result = app.invoke(init_state)

            # Extract final response
            final_response = result.get("response", "No response generated")
            
            print(f"\n🤖 Assistant: {final_response}\n")
            print("-" * 50)

        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")


if __name__ == "__main__":
    run_chat()