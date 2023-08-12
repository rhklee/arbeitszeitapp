import matplotlib.patches as mpatches
from _typeshed import Incomplete
from collections.abc import MutableMapping
from matplotlib.artist import allow_rasterization as allow_rasterization

class Spine(mpatches.Patch):
    axes: Incomplete
    spine_type: Incomplete
    axis: Incomplete
    def __init__(self, axes, spine_type, path, **kwargs) -> None: ...
    stale: bool
    def set_patch_arc(self, center, radius, theta1, theta2) -> None: ...
    def set_patch_circle(self, center, radius) -> None: ...
    def set_patch_line(self) -> None: ...
    def get_patch_transform(self): ...
    def get_window_extent(self, renderer: Incomplete | None = ...): ...
    def get_path(self): ...
    def register_axis(self, axis) -> None: ...
    def clear(self) -> None: ...
    def draw(self, renderer): ...
    def set_position(self, position) -> None: ...
    def get_position(self): ...
    def get_spine_transform(self): ...
    def set_bounds(self, low: Incomplete | None = ..., high: Incomplete | None = ...) -> None: ...
    def get_bounds(self): ...
    @classmethod
    def linear_spine(cls, axes, spine_type, **kwargs): ...
    @classmethod
    def arc_spine(cls, axes, spine_type, center, radius, theta1, theta2, **kwargs): ...
    @classmethod
    def circular_spine(cls, axes, center, radius, **kwargs): ...
    def set_color(self, c) -> None: ...

class SpinesProxy:
    def __init__(self, spine_dict) -> None: ...
    def __getattr__(self, name): ...
    def __dir__(self): ...

class Spines(MutableMapping):
    def __init__(self, **kwargs) -> None: ...
    @classmethod
    def from_dict(cls, d): ...
    def __getattr__(self, name): ...
    def __getitem__(self, key): ...
    def __setitem__(self, key, value) -> None: ...
    def __delitem__(self, key) -> None: ...
    def __iter__(self): ...
    def __len__(self) -> int: ...
