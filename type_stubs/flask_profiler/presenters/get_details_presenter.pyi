from . import table as table
from .formatting import format_duration_in_ms as format_duration_in_ms
from .pagination import Paginator as Paginator
from .urls import get_url_with_query as get_url_with_query
from _typeshed import Incomplete
from flask_profiler.pagination import PaginationContext as PaginationContext
from flask_profiler.request import HttpRequest as HttpRequest
from flask_profiler.use_cases import get_details_use_case as use_case

HEADERS: Incomplete

class ViewModel:
    table: table.Table
    pagination: Paginator
    method_filter_text: str
    name_filter_text: str
    requested_after_filter_text: str
    requested_before_filter_text: str
    def __init__(self, table, pagination, method_filter_text, name_filter_text, requested_after_filter_text, requested_before_filter_text) -> None: ...

class GetDetailsPresenter:
    http_request: HttpRequest
    def present_response(self, response: use_case.Response, pagination: PaginationContext) -> ViewModel: ...
    def __init__(self, http_request) -> None: ...
