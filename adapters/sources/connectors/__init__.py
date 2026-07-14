# Source connectors — production implementations
from adapters.sources.connectors.internet_archive import InternetArchiveAdapter
from adapters.sources.connectors.open_library import OpenLibraryAdapter
from adapters.sources.connectors.crossref import CrossrefAdapter
from adapters.sources.connectors.openalex import OpenAlexAdapter
from adapters.sources.connectors.wikidata import WikidataAdapter
from adapters.sources.connectors.github import GitHubAdapter
from adapters.sources.connectors.arxiv import ArxivAdapter
from adapters.sources.connectors.google_books import GoogleBooksAdapter

CONNECTOR_REGISTRY = {
    "internet_archive": InternetArchiveAdapter,
    "open_library": OpenLibraryAdapter,
    "crossref": CrossrefAdapter,
    "openalex": OpenAlexAdapter,
    "wikidata": WikidataAdapter,
    "github": GitHubAdapter,
    "arxiv": ArxivAdapter,
    "google_books": GoogleBooksAdapter,
}

def get_connector(name: str):
    """Get a configured connector by name."""
    cls = CONNECTOR_REGISTRY.get(name)
    if cls:
        return cls()
    raise ValueError(f"Unknown connector: {name}")

def get_all_connectors():
    """Get all available connectors."""
    return {name: cls() for name, cls in CONNECTOR_REGISTRY.items()}
