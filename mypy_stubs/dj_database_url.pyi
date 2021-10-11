from typing import Any

DEFAULT_ENV: str
SCHEMES: Any

def config(env=..., default: Any | None = ..., engine: Any | None = ..., conn_max_age: int = ..., ssl_require: bool = ...): ...
def parse(url, engine: Any | None = ..., conn_max_age: int = ..., ssl_require: bool = ...): ...
