"""API service layer — business logic and external integrations."""
import logging
import json

logger = logging.getLogger("astrosage.services")
from api.services.knowledge import KnowledgeGraphService, BM25SearchService, AnswerService

# Module-level singletons (lazy-loaded)
_graph_service: KnowledgeGraphService | None = None
_search_service: BM25SearchService | None = None
_answer_service: AnswerService | None = None


def get_graph_service() -> KnowledgeGraphService | None:
    global _graph_service
    if _graph_service is None:
        try:
            _graph_service = KnowledgeGraphService().load()
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load knowledge graph: {e}")
            _graph_service = None  # Will be None, services must handle
    return _graph_service


def get_search_service() -> BM25SearchService | None:
    global _search_service
    if _search_service is None:
        try:
            _search_service = BM25SearchService().load()
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load search index: {e}")
            _search_service = None
    return _search_service


def get_answer_service() -> AnswerService:
    global _answer_service
    if _answer_service is None:
        graph = get_graph_service()
        search = get_search_service()
        if graph is None and search is None:
            logger.warning("Knowledge services unavailable — answer service will fail gracefully")
        _answer_service = AnswerService(graph, search)
    return _answer_service
