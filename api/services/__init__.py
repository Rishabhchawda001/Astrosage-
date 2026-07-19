"""API service layer — business logic and external integrations."""
from api.services.knowledge import KnowledgeGraphService, BM25SearchService, AnswerService

# Module-level singletons (lazy-loaded)
_graph_service: KnowledgeGraphService | None = None
_search_service: BM25SearchService | None = None
_answer_service: AnswerService | None = None


def get_graph_service() -> KnowledgeGraphService:
    global _graph_service
    if _graph_service is None:
        _graph_service = KnowledgeGraphService().load()
    return _graph_service


def get_search_service() -> BM25SearchService:
    global _search_service
    if _search_service is None:
        _search_service = BM25SearchService().load()
    return _search_service


def get_answer_service() -> AnswerService:
    global _answer_service
    if _answer_service is None:
        _answer_service = AnswerService(get_graph_service(), get_search_service())
    return _answer_service
