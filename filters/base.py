"""
Base filter interface
"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class FilterQuery(ABC):
    """
    Base class for reusable table filters.

    Subclasses should implement the build() method to generate
    SQL SELECT queries for filtering table data.
    """

    @abstractmethod
    def build(self, table_name: str, **params) -> str:
        """
        Build SQL SELECT query for filtering table

        Args:
            table_name: Name of the table to filter
            **params: Additional parameters for query building

        Returns:
            str: Complete SELECT query

        Example:
            >>> filter = MyFilter()
            >>> query = filter.build('users')
            >>> print(query)
            SELECT * FROM users WHERE status = 'active'
        """
        raise NotImplementedError("Subclasses must implement build() method")

    def validate(self, table_name: str, **params) -> bool:
        """
        Validate filter before execution (optional)

        Args:
            table_name: Table to validate against
            **params: Additional parameters

        Returns:
            bool: True if valid, False otherwise
        """
        return True

    def __str__(self):
        """String representation of filter"""
        return f"{self.__class__.__name__}()"
