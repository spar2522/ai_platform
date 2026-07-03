# AI Platform

A modular Python platform for building production-ready AI applications.

## Packages

| Package | Purpose |
|----------|---------|
| ai-provider | Unified AI Provider API |
| ai-observability | Prompt logging and tracing |
| ai-config | Configuration management |
| ai-memory | Memory abstractions |
| ai-evals | Evaluation framework |
| ai-utils | Shared utilities |
| ai-platform | Umbrella package |

## Design Principles

- Async First
- Type Safe
- Framework Agnostic
- Production Ready
- Small Focused Libraries

## Setup

uv sync --all-packages

## Run tests

pytest

## Add a dependency to a package

cd packages/ai-provider
uv add httpx

## Sync workspace

cd ../../
uv sync --all-packages