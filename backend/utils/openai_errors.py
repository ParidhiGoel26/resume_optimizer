from openai import APIConnectionError, APIStatusError, AuthenticationError, RateLimitError


def format_openai_error(exc):
    if isinstance(exc, AuthenticationError):
        return (
            "Invalid OpenAI API key. Check OPENAI_API_KEY in your .env file."
        )

    if isinstance(exc, RateLimitError):
        body = getattr(exc, "body", None) or {}
        error_info = body.get("error", {}) if isinstance(body, dict) else {}
        if error_info.get("code") == "insufficient_quota":
            return (
                "Your OpenAI API quota is exhausted. Add billing or credits at "
                "https://platform.openai.com/account/billing then try again."
            )
        return "OpenAI rate limit reached. Please wait a moment and try again."

    if isinstance(exc, APIConnectionError):
        return "Could not connect to OpenAI. Check your internet connection and try again."

    if isinstance(exc, APIStatusError):
        return f"OpenAI API error ({exc.status_code}). Please try again later."

    return "An unexpected OpenAI error occurred. Please try again later."
