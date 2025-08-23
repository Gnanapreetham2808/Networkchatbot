from transformers import pipeline

# Load the fine-tuned model (after you run train_model.py once)
generator = pipeline("text2text-generation", model="nlp_engine/cli_model")

def nl_to_cli(query: str) -> str:
    """
    Convert natural language query to CLI command.
    """
    try:
        result = generator(query, max_length=50, num_return_sequences=1)
        return result[0]["generated_text"]
    except Exception as e:
        return f"[Error] Failed to generate command: {e}"

# Quick test (remove later in production)
if __name__ == "__main__":
    test_queries = [
        "Show me all interfaces",
        "Check device version",
        "Display routing table"
    ]
    for q in test_queries:
        print(f"Query: {q}")
        print(f"CLI : {nl_to_cli(q)}\n")
