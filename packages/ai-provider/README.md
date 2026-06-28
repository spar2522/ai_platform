# ai-provider

A package that provides interfaces and utilities for interacting with AI models and services.

## Installation

```bash
uv add ai-provider
```

## Usage

To use the package, import it into your project and initialize the required AI provider:

```python
from ai_provider import AIProvider

provider = AIProvider(model="gpt-4", api_key="your_api_key")
response = provider.generate("What is the capital of France?")
print(response)
```

## API Reference

The package provides the following core classes and functions:

- `AIProvider`: Main class for interacting with AI models.
- `generate(text: str) -> str`: Method to generate responses from the AI model.
- `set_api_key(api_key: str)`: Static method to set the API key for the provider.

For detailed API documentation, refer to the [official documentation](https://example.com/ai-provider/docs).

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This package is licensed under the MIT License. See [LICENSE](LICENSE) for details.