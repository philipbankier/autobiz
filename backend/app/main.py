from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import auth, companies, departments, activity, chat, tasks, billing, dashboard, knowledge, site

app = FastAPI(
    title="AutoBiz API",
    description="AI-powered business automation platform",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(departments.router)
app.include_router(activity.router)
app.include_router(chat.router)
app.include_router(tasks.router)
app.include_router(billing.router)
app.include_router(dashboard.router)
app.include_router(knowledge.router)
app.include_router(site.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "data": None,
            "error": str(exc),
            "meta": None,
        },
    )


@app.get("/api/health")
async def health():
    return {"data": {"status": "ok"}, "error": None, "meta": None}
