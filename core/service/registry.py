"""
Service Registry — Central dependency injection container.

Nothing imports concrete implementations.
Everything depends on interfaces (abstract base classes).

Usage:
    registry = ServiceRegistry()
    registry.register("retrieval", MyRetrievalImpl)
    impl = registry.resolve("retrieval")
"""
from __future__ import annotations

import logging
from typing import Any, Type, TypeVar, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class Service:
    """A registered service descriptor."""
    name: str
    interface: Type
    implementation: Any = None
    factory: Callable | None = None
    singleton: bool = True
    _instance: Any = field(default=None, repr=False)

    def resolve(self) -> Any:
        if self.singleton and self._instance is not None:
            return self._instance
        if self.implementation is not None:
            self._instance = self.implementation
            return self._instance
        if self.factory is not None:
            self._instance = self.factory()
            return self._instance
        raise RuntimeError(f"Service '{self.name}' has no implementation or factory")


class ServiceRegistry:
    """
    Central service registry for dependency injection.

    Components register interfaces and implementations.
    Consumers resolve by interface name.
    """

    def __init__(self):
        self._services: dict[str, Service] = {}

    def register(
        self,
        name: str,
        interface: Type,
        implementation: Any = None,
        factory: Callable | None = None,
        singleton: bool = True,
    ) -> None:
        """Register a service by name."""
        self._services[name] = Service(
            name=name,
            interface=interface,
            implementation=implementation,
            factory=factory,
            singleton=singleton,
        )
        logger.debug(f"Registered service: {name}")

    def register_instance(self, name: str, interface: Type, instance: Any) -> None:
        """Register a pre-built instance."""
        self._services[name] = Service(
            name=name,
            interface=interface,
            implementation=instance,
            singleton=True,
        )

    def resolve(self, name: str) -> Any:
        """Resolve a service by name."""
        if name not in self._services:
            raise KeyError(f"Service '{name}' not registered")
        return self._services[name].resolve()

    def has(self, name: str) -> bool:
        return name in self._services

    def list_services(self) -> list[str]:
        return list(self._services.keys())

    def summary(self) -> dict:
        return {
            "total": len(self._services),
            "services": {s.name: s.interface.__name__ for s in self._services.values()},
        }
