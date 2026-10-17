# Coding Kit model compatibility

Coding workflows use host-registered provider factories and model capability metadata.
The kit never reads provider credentials and never upgrades a text-only model into a
tool-capable model.

| Provider family | Chat | Tools | Structured plans | Local-only data |
|---|---:|---:|---:|---:|
| OpenAI | capability-driven | capability-driven | capability-driven | no |
| Gemini | capability-driven | capability-driven | capability-driven | no |
| Ollama | yes when registered | model-dependent | model-dependent | yes when registered local |

`check_provider_compatibility` must pass before a tool or structured-plan workflow.
Missing usage remains unknown (`None`), never an invented zero. Live support is only
claimed when the host has supplied credentials/models and recorded a separate smoke
result.
