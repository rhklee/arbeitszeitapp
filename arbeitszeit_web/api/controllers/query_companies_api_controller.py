from dataclasses import dataclass
from typing import List

from arbeitszeit.use_cases.query_companies import CompanyFilter, QueryCompaniesRequest
from arbeitszeit_web.api.controllers import query_parser
from arbeitszeit_web.api.controllers.expected_input import ExpectedInput, InputLocation
from arbeitszeit_web.request import Request

DEFAULT_OFFSET: int = 0
DEFAULT_LIMIT: int = 30


@dataclass
class QueryCompaniesApiController:
    @classmethod
    def create_expected_inputs(cls) -> List[ExpectedInput]:
        return [
            ExpectedInput(
                name="offset",
                type=str,
                description="The query offset.",
                default=DEFAULT_OFFSET,
                location=InputLocation.query,
            ),
            ExpectedInput(
                name="limit",
                type=str,
                description="The query limit.",
                default=DEFAULT_LIMIT,
                location=InputLocation.query,
            ),
        ]

    request: Request

    def create_request(self) -> QueryCompaniesRequest:
        offset = self._parse_offset(self.request)
        limit = self._parse_limit(self.request)
        return QueryCompaniesRequest(
            query_string=None,
            filter_category=CompanyFilter.by_name,
            offset=offset,
            limit=limit,
        )

    def _parse_offset(self, request: Request) -> int:
        offset_string = request.query_string().get("offset")
        if not offset_string:
            return DEFAULT_OFFSET
        offset = query_parser.string_to_non_negative_integer(offset_string)
        return offset

    def _parse_limit(self, request: Request) -> int:
        limit_string = request.query_string().get("limit")
        if not limit_string:
            return DEFAULT_LIMIT
        limit = query_parser.string_to_non_negative_integer(limit_string)
        return limit
