from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any


class GroundMotionInputParser(ABC):
    """
    The Parser interface declares a method for building a chain of Parsers.
    """

    _next_parser: GroundMotionInputParser = None

    def set_next(self, parser: GroundMotionInputParser) -> \
            GroundMotionInputParser:
        """
        Assign a object which will recieve the request and will try
        and parse the request if the current one does not return.
        """
        self._next_parser = parser
        return parser

    @abstractmethod
    def parse(self, request: Any) -> str:
        """
        Overwrite this method to implement a strategy to identify and parse
        the request object.

        This method should never raise an error and end execution but instead
        call its super().parse() function to pass the request on to the next
        function in the Chain.
        """
        if self._next_parser:
            return self._next_parser.parse(request)
        return None
