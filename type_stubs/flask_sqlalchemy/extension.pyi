import sqlalchemy as sa
import typing as t
from .model import DefaultMeta as DefaultMeta, Model as Model
from .pagination import Pagination as Pagination, SelectPagination as SelectPagination
from .query import Query as Query
from .session import Session as Session
from _typeshed import Incomplete
from flask import Flask as Flask

class SQLAlchemy:
    Query: Incomplete
    session: Incomplete
    metadatas: Incomplete
    Table: Incomplete
    Model: Incomplete
    def __init__(self, app: Flask | None = ..., *, metadata: sa.MetaData | None = ..., session_options: dict[str, t.Any] | None = ..., query_class: type[Query] = ..., model_class: type[Model] | sa.orm.DeclarativeMeta = ..., engine_options: dict[str, t.Any] | None = ..., add_models_to_shell: bool = ...) -> None: ...
    def init_app(self, app: Flask) -> None: ...
    @property
    def metadata(self) -> sa.MetaData: ...
    @property
    def engines(self) -> t.Mapping[str | None, sa.engine.Engine]: ...
    @property
    def engine(self) -> sa.engine.Engine: ...
    def get_engine(self, bind_key: str | None = ...) -> sa.engine.Engine: ...
    def get_tables_for_bind(self, bind_key: str | None = ...) -> list[sa.Table]: ...
    def get_binds(self) -> dict[sa.Table, sa.engine.Engine]: ...
    def get_or_404(self, entity: type[t.Any], ident: t.Any, *, description: str | None = ...) -> t.Any: ...
    def first_or_404(self, statement: sa.sql.Select[t.Any], *, description: str | None = ...) -> t.Any: ...
    def one_or_404(self, statement: sa.sql.Select[t.Any], *, description: str | None = ...) -> t.Any: ...
    def paginate(self, select: sa.sql.Select[t.Any], *, page: int | None = ..., per_page: int | None = ..., max_per_page: int | None = ..., error_out: bool = ..., count: bool = ...) -> Pagination: ...
    def create_all(self, bind_key: str | None | list[str | None] = ...) -> None: ...
    def drop_all(self, bind_key: str | None | list[str | None] = ...) -> None: ...
    def reflect(self, bind_key: str | None | list[str | None] = ...) -> None: ...
    def relationship(self, *args: t.Any, **kwargs: t.Any) -> sa.orm.RelationshipProperty[t.Any]: ...
    def dynamic_loader(self, argument: t.Any, **kwargs: t.Any) -> sa.orm.RelationshipProperty[t.Any]: ...
    def __getattr__(self, name: str) -> t.Any: ...
