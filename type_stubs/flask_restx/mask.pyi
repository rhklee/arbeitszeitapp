from .errors import RestError as RestError
from _typeshed import Incomplete
from collections import OrderedDict

log: Incomplete
LEXER: Incomplete

class MaskError(RestError): ...
class ParseError(MaskError): ...

class Mask(OrderedDict):
    skip: Incomplete
    def __init__(self, mask: Incomplete | None = ..., skip: bool = ..., **kwargs) -> None: ...
    def parse(self, mask) -> None: ...
    def clean(self, mask): ...
    def apply(self, data): ...
    def filter_data(self, data): ...

def apply(data, mask, skip: bool = ...): ...
