To improve the readability, maintainability, and scalability of the function that determines AI-related information based on the provider name and configuration, we can refactor it using a structured and modular approach.

---

### ✅ **Refactored Function Overview**

We will:

- Use a **configuration list** to define known providers and their associated attributes.
- Dynamically match the provider based on the configuration.
- Use a **generic fallback** for unknown or custom providers.
- Use **string formatting** to create consistent summaries.

This approach eliminates redundancy, improves clarity, and makes it easier to add or modify provider configurations in the future.

---

### 🛠️ **Refactored Code**

```python
def get_ai_info(provider_name, config):
    # Normalize provider name
    provider_name = provider_name.lower()

    # Configuration for known providers
    PROVIDER_CONFIGS = [
        (["dummy"], "dummy", "mock-model", "in-memory", False, "offline_mock"),
        (["ollama", "local"], "ollama", "local-default", "http://localhost:11434", False, "localhost_api"),
        (["gemini"], "gemini", "gemini-3.5-flash", "https://generativelanguage.googleapis.com", True, "cloud_internet"),
        (["openai"], "openai", "gpt-4o", "https://api.openai.com/v1", True, "cloud_internet"),
        (["anthropic"], "anthropic", "claude-3-7-sonnet", "https://api.anthropic.com", True, "cloud_internet"),
    ]

    # Check against known providers
    for keywords, provider, model, endpoint, is_external, connectivity_type in PROVIDER_CONFIGS:
        if any(keyword in provider_name for keyword in keywords):
            return {
                "ai_used": True,
                "provider": provider,
                "model": model,
                "endpoint": endpoint,
                "is_external_network": is_external,
                "connectivity_type": connectivity_type,
                "summary": f"{connectivity_type} ({endpoint} - {'Zero external internet traffic' if not is_external else 'External internet traffic'})"
            }

    # Fallback for unknown providers
    return {
        "ai_used": True,
        "provider": provider_name,
        "model": config.get("model", "unknown"),
        "endpoint": config.get("endpoint", "unknown"),
        "is_external_network": config.get("is_external", True),
        "connectivity_type": "unknown",
        "summary": f"unknown ({config.get('endpoint', 'N/A')} - {'External internet traffic' if config.get('is_external', True) else 'Zero external internet traffic'})"
    }
```

---

### ✅ **Benefits of This Refactoring**

- **Readability**: The configuration is centralized and easy to understand.
- **Maintainability**: Adding a new provider only requires adding a new entry to the list.
- **Consistency**: The summary is generated dynamically using a common format.
- **Flexibility**: The fallback supports custom or unknown providers with defaults from the config.

---

### 📌 **Example Usage**

```python
config = {
    "model": "custom-model",
    "endpoint": "https://custom.ai",
    "is_external": False
}

result = get_ai_info("ollama", config)
print(result)
```

**Output**:
```python
{
    "ai_used": True,
    "provider": "ollama",
    "model": "local-default",
    "endpoint": "http://localhost:11434",
    "is_external_network": False,
    "connectivity_type": "localhost_api",
    "summary": "localhost_api (http://localhost:11434 - Zero external internet traffic)"
}
```

---

### ✅ **Conclusion**

This refactored function is more robust, scalable, and easier to maintain. It uses a declarative style to define known providers, and gracefully handles unknown cases using a fallback mechanism. This is a great example of how to structure functions for clarity and flexibility.