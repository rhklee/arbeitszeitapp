from _typeshed import Incomplete

def abort(code=..., message: Incomplete | None = ..., **kwargs) -> None: ...

class RestError(Exception):
    msg: Incomplete
    def __init__(self, msg) -> None: ...

class ValidationError(RestError): ...
class SpecsError(RestError): ...
