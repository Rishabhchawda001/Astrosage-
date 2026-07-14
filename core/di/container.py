"""
Dependency Injection Container — Wires services together.

Usage:
    container = Container()
    container.register("config", ConfigLoader)
    container.register("plugin_registry", PluginRegistry)
    container.register("service_registry", ServiceRegistry)
    config = container.resolve("config")
"""
from __future__ import annotations

from typing import Any, Type


class Container:
    """Simple dependency injection container."""

    def __init__(self):
        self._singletons: dict[str, Any] = {}
        self._factories: dict[str, callable] = {}
        self._types: dict[str, Type] = {}

    def register_singleton(self, name: str, instance: Any) -> None:
        self._singletons[name] = instance

    def register_factory(self, name: str, factory: callable) -> None:
        self._factories[name] = factory

    def register_type(self, name: str, cls: Type) -> None:
        self._types[name] = cls

    def resolve(self, name: str) -> Any:
        if name in self._singletons:
            return self._singletons[name]
        if name in self._factories:
            instance = self._factories[name]()
            self._singletons[name] = instance
            return instance
        if name in self._types:
            instance = self._types[name]()
            self._singletons[name] = instance
            return instance
        raise KeyError(f"Service '{name}' not registered in container")

    def has(self, name: str) -> bool:
        return name in self._singletons or name in self._factories or name in self._types

    def list_services(self) -> list[str]:
        return list(set(list(self._singletons.keys()) + list(self._factories.keys()) + list(self._types.keys())))
