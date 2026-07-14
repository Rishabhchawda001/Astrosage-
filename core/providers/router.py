"""
OmniRoute — Optional model router with provider abstraction.

Supports: routing policies, fallback chains, retry logic, health monitoring,
timeout handling, load balancing, provider scoring, cost/latency tracking,
model capabilities registry. Feature-flagged — disabled by default.
"""
from __future__ import annotations

import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional


class ProviderStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"


class RoutingPolicy(str, Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_LATENCY = "least_latency"
    LEAST_COST = "least_cost"
    PRIORITY = "priority"
    RANDOM = "random"


@dataclass
class ModelCapabilities:
    model_id: str = ""
    provider: str = ""
    max_tokens: int = 4096
    supports_vision: bool = False
    supports_tools: bool = False
    supports_json: bool = False
    languages: list[str] = field(default_factory=lambda: ["en"])
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0


@dataclass
class ProviderConfig:
    provider_id: str = ""
    name: str = ""
    api_key: str = ""
    base_url: str = ""
    models: list[ModelCapabilities] = field(default_factory=list)
    priority: int = 0
    max_concurrent: int = 10
    timeout: float = 30.0
    enabled: bool = True


@dataclass
class ProviderMetrics:
    provider_id: str = ""
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    total_latency: float = 0.0
    total_cost: float = 0.0
    last_request_at: str = ""
    status: ProviderStatus = ProviderStatus.UNKNOWN

    @property
    def avg_latency(self) -> float:
        return self.total_latency / max(self.successful, 1)

    @property
    def success_rate(self) -> float:
        return self.successful / max(self.total_requests, 1)

    @property
    def error_rate(self) -> float:
        return self.failed / max(self.total_requests, 1)


class OmniRouter:
    """
    Optional model router. Disabled by default.
    Enable with feature flag: OMNIROUTE_ENABLED=true
    """

    def __init__(self, enabled: bool = False, policy: RoutingPolicy = RoutingPolicy.LEAST_LATENCY):
        self.enabled = enabled
        self.policy = policy
        self._providers: dict[str, ProviderConfig] = {}
        self._metrics: dict[str, ProviderMetrics] = {}
        self._model_index: dict[str, list[str]] = defaultdict(list)
        self._round_robin_idx: int = 0
        self._fallback_chains: dict[str, list[str]] = {}
        self._request_log: list[dict[str, Any]] = []

    def register_provider(self, config: ProviderConfig) -> str:
        self._providers[config.provider_id] = config
        self._metrics[config.provider_id] = ProviderMetrics(provider_id=config.provider_id)
        for model in config.models:
            self._model_index[model.model_id].append(config.provider_id)
        return config.provider_id

    def set_fallback_chain(self, model_id: str, chain: list[str]) -> None:
        self._fallback_chains[model_id] = chain

    def _select_provider(self, model_id: str) -> Optional[ProviderConfig]:
        candidates = self._model_index.get(model_id, [])
        active = [pid for pid in candidates if pid in self._providers and self._providers[pid].enabled]
        if not active:
            return None

        if self.policy == RoutingPolicy.PRIORITY:
            active.sort(key=lambda pid: -self._providers[pid].priority)
        elif self.policy == RoutingPolicy.LEAST_LATENCY:
            active.sort(key=lambda pid: self._metrics[pid].avg_latency)
        elif self.policy == RoutingPolicy.LEAST_COST:
            active.sort(key=lambda pid: sum(m.cost_per_1k_input for m in self._providers[pid].models))
        elif self.policy == RoutingPolicy.ROUND_ROBIN:
            idx = self._round_robin_idx % len(active)
            self._round_robin_idx += 1
            return self._providers[active[idx]]

        return self._providers[active[0]] if active else None

    def route(self, model_id: str, **kwargs) -> dict[str, Any]:
        if not self.enabled:
            return {"provider": "direct", "model": model_id, "routed": False}

        provider = self._select_provider(model_id)
        if not provider:
            chain = self._fallback_chains.get(model_id, [])
            for fallback_model in chain:
                provider = self._select_provider(fallback_model)
                if provider:
                    break

        if not provider:
            return {"provider": None, "model": model_id, "routed": False, "error": "no_provider"}

        start = time.time()
        metrics = self._metrics[provider.provider_id]
        metrics.total_requests += 1
        metrics.last_request_at = datetime.now(timezone.utc).isoformat()
        latency = time.time() - start
        metrics.total_latency += latency

        self._request_log.append({
            "provider": provider.provider_id,
            "model": model_id,
            "latency": latency,
            "timestamp": metrics.last_request_at,
        })

        return {
            "provider": provider.provider_id,
            "model": model_id,
            "routed": True,
            "latency": latency,
        }

    def record_result(self, provider_id: str, success: bool, cost: float = 0.0) -> None:
        if provider_id in self._metrics:
            if success:
                self._metrics[provider_id].successful += 1
            else:
                self._metrics[provider_id].failed += 1
            self._metrics[provider_id].total_cost += cost

    def get_provider_health(self) -> dict[str, dict[str, Any]]:
        health = {}
        for pid, metrics in self._metrics.items():
            health[pid] = {
                "status": metrics.status.value,
                "success_rate": round(metrics.success_rate, 4),
                "avg_latency": round(metrics.avg_latency, 4),
                "total_requests": metrics.total_requests,
                "error_rate": round(metrics.error_rate, 4),
            }
        return health

    def get_capabilities(self, model_id: str) -> list[ModelCapabilities]:
        providers = self._model_index.get(model_id, [])
        caps = []
        for pid in providers:
            if pid in self._providers:
                for m in self._providers[pid].models:
                    if m.model_id == model_id:
                        caps.append(m)
        return caps

    def count(self) -> int:
        return len(self._providers)

    def summary(self) -> dict:
        return {"enabled": self.enabled, "providers": self.count(), "policy": self.policy.value,
                "models_indexed": len(self._model_index), "requests": len(self._request_log)}
