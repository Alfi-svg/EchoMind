def build_system_prompt(mood: str) -> str:
    if mood == "tutor":
        return (
            "You are a calm AI tutor. Explain step by step, clearly, politely."
        )

    if mood == "analyst":
        return (
            "You are an analytical AI. Answer with reasoning and structured logic."
        )

    if mood == "friendly":
        return (
            "You are a friendly AI assistant. Be helpful and conversational."
        )

    # default
    return (
        "You are a professional AI assistant. Be accurate and helpful."
    )
