from server import config  # noqa: F401  (import triggers the fail-fast env check)

import pathlib

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from server.db.migrate import ensure_schema
from server.routes import auth as auth_routes
from server.routes import bookings as bookings_routes
from server.routes import resources as resources_routes

ROOT = pathlib.Path(__file__).resolve().parent.parent


class SPAStaticFiles(StaticFiles):
    """Serves the built Angular app and falls back to index.html for any
    path that isn't a real file - this is what makes client-side routing
    (Angular Router) work on a hard refresh of /resource/3, the same job
    Express's catch-all `app.get(/^(?!\\/api).*/, ...)` does in the parent
    skill's React version.
    """

    async def get_response(self, path, scope):
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code == 404:
                return await super().get_response("index.html", scope)
            raise


def create_app() -> FastAPI:
    ensure_schema()

    app = FastAPI(title="Booking App API")

    # Routers are included before the static-file mount below - order
    # matters here the same way it does in Express: Starlette matches
    # routes in registration order, so /api/* must be registered first or
    # the "/" static mount (which matches everything as a prefix) would
    # shadow it.
    app.include_router(auth_routes.router, prefix="/api/auth", tags=["auth"])
    app.include_router(resources_routes.router, prefix="/api/resources", tags=["resources"])
    app.include_router(bookings_routes.router, prefix="/api/bookings", tags=["bookings"])

    # In development, Angular's own dev server (`ng serve`, via `npm
    # start`) serves the frontend on its own port and proxies /api to this
    # process (see proxy.conf.json) - so this process serves nothing at
    # "/" in dev. In production, this process serves the Angular build
    # output directly, so there's a single origin and no CORS
    # configuration anywhere in this app - see references/architecture.md.
    if config.IS_PRODUCTION:
        dist_dir = ROOT / "dist" / "booking-app" / "browser"
        app.mount("/", SPAStaticFiles(directory=str(dist_dir), html=True), name="spa")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server.main:app",
        host="0.0.0.0",
        port=config.PORT,
        reload=not config.IS_PRODUCTION,
    )
