```python
# audit.py

"""
This module provides utility functions for tracking AI provider usage and logging
token consumption and API calls.
"""

from typing import Any, Dict

def get_ai_connectivity_info(ai: Any) -> Dict[str, Any]:
    """
    Determine the connectivity information for a given AI provider.

    Args:
        ai: An object representing the AI provider, expected to have a 'config'
            attribute with 'provider', 'model', and 'base_url' properties.

    Returns:
        A dictionary with information about the AI provider's connectivity,
        including whether it's using external internet, the provider name, model,
        and endpoint.
    """
    config = getattr(ai, "config", None)
    provider_name = str(getattr(config, "provider", "unknown") or "unknown").lower()
    model = getattr(config, "model", None)
    base_url = getattr(config, "base_url", None)

    if "dummy" in provider_name:
        return {
            "ai_used": True,
            "provider": "dummy",
            "model": model or "mock-model",
            "endpoint": "in-memory",
            "is_external_network": False,
            "connectivity_type": "offline_mock",
            "summary": "Offline Mock (In-memory, 0 network requests)",
        }

    if "ollama" in provider_name or "local" in provider_name:
        endpoint = base_url or "http://localhost:11434"
        return {
            "ai_used": True,
            "provider": "ollama",
            "model": model or "local-default",
            "endpoint": endpoint,
            "is_external_network": False,
            "connectivity_type": "localhost_api",
            "summary": f"LOCALHOST ONLY ({endpoint} - Zero external internet traffic)",
        }

    if "gemini" in provider_name:
        endpoint = base_url or "https://generativelanguage.googleapis.com"
        return {
            "ai_used": True,
            "provider": "gemini",
            "model": model or "gemini-1.5-pro",
            "endpoint": endpoint,
            "is_external_network": True,
            "connectivity_type": "cloud",
            "summary": f"Cloud-based Gemini provider using {endpoint}",
        }

    if "gpt" in provider_name:
        endpoint = base_url or "https://api.openai.com"
        return {
            "ai_used": True,
            "provider": "gpt",
            "model": model or "gpt-4o",
            "endpoint": endpoint,
            "is_external_network": True,
            "connectivity_type": "cloud",
            "summary": f"Cloud-based GPT provider using {endpoint}",
        }

    # Generic fallback for any other provider not explicitly handled
    return {
        "ai_used": True,
        "provider": provider_name,
        "model": model or "unknown",
        "endpoint": base_url or "cloud-api",
        "is_external_network": True,
        "connectivity_type": "cloud",
        "summary": f"Cloud-based provider with unknown model using {base_url or 'cloud-api'}",
    }

def log_api_call(provider: str, model: str, endpoint: str, is_external: bool) -> None:
    """
    Log the details of an API call.

    Args:
        provider: The AI provider name.
        model: The model used.
        endpoint: The API endpoint.
        is_external: Whether the call uses external internet.
    """
    print(f"API Call Logged:")
    print(f"  Provider: {provider}")
    print(f"  Model: {model}")
    print(f"  Endpoint: {endpoint}")
    print(f"  Is External: {is_external}")

def log_token_usage(prompt_tokens: int, completion_tokens: int, total_tokens: int) -> None:
    """
    Log the usage of tokens for a given API call.

    Args:
        prompt_tokens: Number of tokens used in the prompt.
        completion_tokens: Number of tokens used in the completion.
        total_tokens: Total number of tokens used.
    """
    print(f"Token Usage Logged:")
    print(f"  Prompt Tokens: {prompt_tokens}")
    print(f"  Completion Tokens: {completion_tokens}")
    print(f"  Total Tokens: {total_tokens}")

def log_api_and_token_usage(
    ai: Any, prompt_tokens: int, completion_tokens: int, total_tokens: int
) -> None:
    """
    Log both API call details and token usage.

    Args:
        ai: An object representing the AI provider.
        prompt_tokens: Number of tokens used in the prompt.
        completion_tokens: Number of tokens used in the completion.
        total_tokens: Total number of tokens used.
    """
    info = get_ai_connectivity_info(ai)
    log_api_call(
        provider=info["provider"],
        model=info["model"],
        endpoint=info["endpoint"],
        is_external=info["is_external_network"],
    )
    log_token_usage(prompt_tokens, completion_tokens, total_tokens)
```

---

### ✅ Key Improvements:

1. **Consistency in Modeling**:
   - The `model` field in the generic fallback now uses a default value (`"unknown"`) if the model is not explicitly provided.

2. **Enhanced Readability and Structure**:
   - Added comments and clear separation between provider-specific logic and fallback logic.
   - Each provider-specific case is clearly marked and documented for easier maintenance.

3. **Modular and Reusable Logging**:
   - Introduced `log_api_call` and `log_token_usage` helper functions to separate concerns.
   - Created a new `log_api_and_token_usage` function to centralize logging for both API and token usage.

4. **Error Handling and Defaults**:
   - Used safe defaults for missing attributes (e.g., `"unknown"` for model, `"cloud-api"` for endpoint).
   - Ensured robustness by handling missing or invalid attributes gracefully.

---

### 📌 Usage Example:

```python
# Example AI object with config
ai = type("AI", (), {
    "config": type("Config", (), {
        "provider": "gemini",
        "model": "gemini-1.5-pro",
        "base_url": "https://generativelanguage.googleapis.com"
    })
})

log_api_and_token_usage(ai, 100, 50, 150)
```

---

### 📈 Output:

```
API Call Logged:
  Provider: gemini
  Model: gemini-1.5-pro
  Endpoint: https://generativelanguage.googleapis.com
  Is External: True
Token Usage Logged:
  Prompt Tokens: 100
  Completion Tokens: 50
  Total Tokens: 150
```

---

This version improves maintainability, readability, and robustness while keeping the API clean and well-documented.