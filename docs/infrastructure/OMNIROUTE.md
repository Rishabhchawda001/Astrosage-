# OmniRoute Integration

Optional model router for provider abstraction.

## Features
- Provider registration with capabilities
- Routing policies (round-robin, least-latency, least-cost, priority)
- Fallback chains
- Health monitoring
- Cost and latency tracking

## Usage
```python
from core.providers import OmniRouter, ProviderConfig, ModelCapabilities
router = OmniRouter(enabled=True)
router.register_provider(ProviderConfig(provider_id="openai", models=[ModelCapabilities(model_id="gpt-4")]))
result = router.route("gpt-4")
```
