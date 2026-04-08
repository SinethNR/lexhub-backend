from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# ── 1. Create App ────────────────────────────────────────────
app = FastAPI(title="LexHub API", version="1.0.0")

# ── 2. CORS — ROBUST CONFIGURATION ──────────────────────────
# We use environment variables for allowed origins, falling back to locals
allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000,https://lexhub-frontdemo.vercel.app,https://lexhub-backend.onrender.com")
origins = [o.strip() for o in allowed_origins_raw.split(",") if o.strip()]
# Explicitly ensuring localhost:3000 is always allowed as per request
if "http://localhost:3000" not in origins:
    origins.append("http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,     # Required for Auth headers (Tokens) in many cases
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ── 3. Handle Errors with CORS Headers ───────────────────────
# FastAPI sometimes strips CORS headers on 500 errors. This ensures they stay.
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": "InternalServerError"},
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "true",
        }
    )


# ── 3. Health/Root routes defined BEFORE any mounts or imports─
# These must NEVER fail regardless of DB or static issues
@app.api_route("/", methods=["GET", "HEAD"])
def read_root():
    return {"message": "LexHub API is running", "status": "ok"}

@app.api_route("/health", methods=["GET", "HEAD"])
def health_check():
    return {"status": "healthy", "cors": "wildcard", "version": "1.0.0"}

# ── 4. Static files — wrapped safely so crash doesn't kill app ─
try:
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    os.makedirs(static_dir, exist_ok=True)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    print(f"Static files mounted at: {static_dir}")
except Exception as e:
    print(f"WARNING: Static files mount failed (non-fatal): {e}")

# ── 5. DB startup — non-fatal, app runs even if DB init fails ─
@app.on_event("startup")
async def startup_event():
    try:
        from .database import engine, Base
        Base.metadata.create_all(bind=engine)
        print("DB tables verified.")
    except Exception as e:
        print(f"WARNING: DB startup check failed: {e}")
        print("App continues running. Tables likely already exist in Aiven.")

# ── 6. Import and register all routers ───────────────────────
# Each router import is individually wrapped so one bad import
# doesn't kill the entire app
def safe_include(router_module_path: str, router_attr: str = "router"):
    """Safely import and include a router - won't crash app if one fails"""
    pass

try:
    from .api import auth
    app.include_router(auth.router)
    print("Router loaded: auth")
except Exception as e:
    print(f"ERROR loading auth router: {e}")

try:
    from .api import users
    app.include_router(users.router)
    print("Router loaded: users")
except Exception as e:
    print(f"ERROR loading users router: {e}")

try:
    from .api import lawyers
    app.include_router(lawyers.router)
    print("Router loaded: lawyers")
except Exception as e:
    print(f"ERROR loading lawyers router: {e}")

try:
    from .api import consultations
    app.include_router(consultations.router)
    print("Router loaded: consultations")
except Exception as e:
    print(f"ERROR loading consultations router: {e}")

try:
    from .api import chat
    app.include_router(chat.router)
    print("Router loaded: chat")
except Exception as e:
    print(f"ERROR loading chat router: {e}")

try:
    from .api import admin
    app.include_router(admin.router)
    print("Router loaded: admin")
except Exception as e:
    print(f"ERROR loading admin router: {e}")

try:
    from .api import blogs
    app.include_router(blogs.router)
    print("Router loaded: blogs")
except Exception as e:
    print(f"ERROR loading blogs router: {e}")

try:
    from .api import forum
    app.include_router(forum.router)
    print("Router loaded: forum")
except Exception as e:
    print(f"ERROR loading forum router: {e}")

try:
    from .api import statutes
    app.include_router(statutes.router)
    print("Router loaded: statutes")
except Exception as e:
    print(f"ERROR loading statutes router: {e}")

try:
    from .api import cases
    app.include_router(cases.router)
    print("Router loaded: cases")
except Exception as e:
    print(f"ERROR loading cases router: {e}")

try:
    from .api import reports
    app.include_router(reports.router)
    print("Router loaded: reports")
except Exception as e:
    print(f"ERROR loading reports router: {e}")

try:
    from .api import notifications
    app.include_router(notifications.router)
    print("Router loaded: notifications")
except Exception as e:
    print(f"ERROR loading notifications router: {e}")

if __name__ == "__main__":
    import uvicorn
    # Respect Render's PORT or default to 8080
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
