# aip-provider

A package providing AI interface provider functionalities. It allows integration with various AI services, offering features like model management, request handling, and response processing.

## Installation

```bash
uv add aip-provider
```

## Usage

To use the package, import and initialize the provider:

```python
from aip_provider import AIPProvider

provider = AIPProvider(api_key="your_api_key")
response = provider.query("What is the capital of France?")
print(response)
```

## Features

- Seamless integration with multiple AI backends
- Robust request/response handling
- Configurable API key management
- Easy-to-use Python interface

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This package is licensed under the MIT License. See [LICENSE](LICENSE) for details.