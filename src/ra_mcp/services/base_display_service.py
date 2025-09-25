"""
Base display service interface defining common formatting operations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Any

from ..models import SearchHit, SearchOperation, BrowseOperation


class BaseDisplayService(ABC):
    """Abstract base class for display services."""

    @abstractmethod
    def format_search_results(
        self,
        search_operation: SearchOperation,
        maximum_documents_to_display: int = 20,
        show_full_context: bool = False,
    ) -> Any:
        """Format search results for the specific interface."""
        pass

    @abstractmethod
    def format_browse_results(
        self, operation: BrowseOperation, highlight_term: Optional[str] = None
    ) -> Any:
        """Format browse results for the specific interface."""
        pass

    @abstractmethod
    def format_show_pages_results(
        self,
        search_op: SearchOperation,
        enriched_hits: List[SearchHit],
        no_grouping: bool = False,
    ) -> Any:
        """Format show-pages results for the specific interface."""
        pass

    @abstractmethod
    def format_document_structure(
        self, collection_info: Dict[str, Union[str, List[Dict[str, str]]]]
    ) -> Any:
        """Format document structure information."""
        pass

    @abstractmethod
    def format_error_message(
        self, error_message: str, error_suggestions: List[str] = None
    ) -> Any:
        """Format error messages for the specific interface."""
        pass

    def get_search_summary(self, search_operation: SearchOperation) -> Dict[str, Any]:
        """Get search summary for display - common implementation."""
        from . import analysis

        return analysis.extract_search_summary(search_operation)
