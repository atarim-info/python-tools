# python-tools-fastapi

Import root: `python_tools.web` (distribution name `python-tools-fastapi`).

## Wave 1

App factory, standard error envelope, request-ID middleware, ETag /
Idempotency-Key helpers, and `/healthz` `/readyz` `/metrics` (closes PT-08 T8.2).

```python
from python_tools.config import BaseServiceSettings
from python_tools.web import create_app, api_error, NOT_FOUND

settings = BaseServiceSettings(service_name="demo")
app = create_app(title="demo", settings=settings)

@app.get("/items/{item_id}")
async def get_item(item_id: str):
    raise api_error(404, NOT_FOUND, "missing", item_id=item_id)
```

Auth FastAPI dependencies are optional (`python-tools-fastapi[auth]`); JWT waits
for Wave 3. Soft dependency — this package does not require `python-tools-auth`
at runtime for the Wave 1 factory.

Depends on: `fastapi`, `python-tools-observability`, `python-tools-logging`.
