from __future__ import annotations

import hmac
import re
from pathlib import Path
from typing import Annotated, Any, Literal

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .config import Settings
from .storage import Storage

STATIC_DIR = Path(__file__).parent / "static"
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


class ClientCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(min_length=2, max_length=100)
    company: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=200)
    project_name: str = Field(min_length=2, max_length=160)
    status: Literal["active", "paused", "complete"] = "active"
    progress: int = Field(default=0, ge=0, le=100)
    due_date: str = Field(default="", max_length=20)
    plan: str = Field(default="Standard", min_length=2, max_length=60)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if not EMAIL_RE.match(value):
            raise ValueError("Enter a valid email address")
        return value.lower()


class ClientUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    status: Literal["active", "paused", "complete"] | None = None
    progress: int | None = Field(default=None, ge=0, le=100)
    due_date: str | None = Field(default=None, max_length=20)
    project_name: str | None = Field(default=None, min_length=2, max_length=160)
    plan: str | None = Field(default=None, min_length=2, max_length=60)


class MilestoneCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str = Field(min_length=2, max_length=160)
    detail: str = Field(default="", max_length=500)
    status: Literal["upcoming", "in_progress", "complete"] = "upcoming"
    due_date: str = Field(default="", max_length=20)
    sort_order: int = Field(default=0, ge=0, le=100)


class MilestoneUpdate(BaseModel):
    status: Literal["upcoming", "in_progress", "complete"]


class DeliverableCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str = Field(min_length=2, max_length=160)
    url: str = Field(min_length=8, max_length=500)
    note: str = Field(default="", max_length=500)
    kind: Literal["file", "document", "preview", "video", "link"] = "file"

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        if not value.startswith(("https://", "http://")):
            raise ValueError("URL must begin with https:// or http://")
        return value


class ApprovalCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str = Field(min_length=2, max_length=160)
    details: str = Field(default="", max_length=1000)


class ApprovalResponse(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    status: Literal["approved", "changes_requested"]
    response: str = Field(default="", max_length=1500)


class InvoiceCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    reference: str = Field(min_length=2, max_length=60)
    amount: float = Field(gt=0, le=10_000_000)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    status: Literal["pending", "paid", "overdue", "void"] = "pending"
    due_date: str = Field(default="", max_length=20)
    payment_url: str = Field(default="", max_length=500)

    @field_validator("payment_url")
    @classmethod
    def validate_payment_url(cls, value: str) -> str:
        if value and not value.startswith(("https://", "http://")):
            raise ValueError("URL must begin with https:// or http://")
        return value


class UpdateCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    body: str = Field(min_length=2, max_length=2000)
    visibility: Literal["client", "internal"] = "client"


class BusinessUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(min_length=2, max_length=120)
    short_name: str = Field(min_length=1, max_length=60)
    logo_text: str = Field(min_length=1, max_length=3)
    tagline: str = Field(min_length=2, max_length=180)
    primary_color: str
    accent_color: str
    support_email: str = Field(max_length=200)
    welcome_message: str = Field(min_length=10, max_length=500)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    privacy_url: str = Field(default="", max_length=500)

    @field_validator("primary_color", "accent_color")
    @classmethod
    def validate_color(cls, value: str) -> str:
        if not HEX_RE.match(value):
            raise ValueError("Use a six-digit hex color such as #18281f")
        return value

    @field_validator("support_email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if value and not EMAIL_RE.match(value):
            raise ValueError("Enter a valid email address")
        return value.lower()

    @field_validator("privacy_url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        if value and not value.startswith(("https://", "http://")):
            raise ValueError("URL must begin with https:// or http://")
        return value


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = settings or Settings.from_env()
    active_settings.validate()
    storage = Storage(active_settings.database_path)
    storage.initialize(active_settings.load_business(), active_settings.seed_demo_data)

    app = FastAPI(
        title="ClientDesk",
        version="1.0.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.settings = active_settings
    app.state.storage = storage
    app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")

    if active_settings.app_env == "development":
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
            allow_credentials=False,
            allow_methods=["GET", "POST", "PUT"],
            allow_headers=["Content-Type", "X-Admin-Token"],
        )

    @app.middleware("http")
    async def security_headers(request: Request, call_next: Any) -> Any:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; img-src 'self' data:; connect-src 'self'; "
            "frame-ancestors 'none'; form-action 'self'"
        )
        if request.url.path.startswith(("/admin", "/api/admin", "/p/")):
            response.headers["Cache-Control"] = "no-store"
        return response

    def require_admin(
        request: Request,
        x_admin_token: Annotated[str | None, Header(alias="X-Admin-Token")] = None,
    ) -> None:
        if x_admin_token and hmac.compare_digest(x_admin_token, active_settings.admin_token):
            return
        if (
            active_settings.seed_demo_data
            and request.method == "GET"
            and x_admin_token == "clientdesk-demo-view"
        ):
            return
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    def existing_client(client_id: int) -> dict[str, Any]:
        client = storage.get_client(client_id)
        if client is None:
            raise HTTPException(status_code=404, detail="Client not found")
        return client

    @app.get("/", include_in_schema=False)
    async def home() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/p/{token}", include_in_schema=False)
    async def portal_page(token: str) -> FileResponse:
        if storage.get_client_by_token(token) is None:
            raise HTTPException(status_code=404, detail="Portal not found")
        return FileResponse(STATIC_DIR / "portal.html")

    @app.get("/admin", include_in_schema=False)
    async def admin_page() -> FileResponse:
        return FileResponse(STATIC_DIR / "admin.html")

    @app.get("/health")
    async def health() -> dict[str, Any]:
        if not storage.ping():
            raise HTTPException(status_code=503, detail="Storage is unavailable")
        return {
            "status": "ok",
            "product": "ClientDesk",
            "version": "1.0.0",
            "storage": "ok",
            "environment": active_settings.app_env,
        }

    @app.get("/api/public/config")
    async def public_config() -> dict[str, Any]:
        business = storage.get_settings()
        clients = storage.list_clients()
        demo_token = (
            clients[0]["portal_token"] if active_settings.seed_demo_data and clients else ""
        )
        return {**business, "demo_token": demo_token, "demo": active_settings.seed_demo_data}

    @app.get("/api/portal/{token}")
    async def portal(token: str) -> dict[str, Any]:
        payload = storage.portal(token)
        if payload is None:
            raise HTTPException(status_code=404, detail="Portal not found")
        return {"business": storage.get_settings(), **payload}

    @app.post("/api/portal/{token}/approvals/{approval_id}")
    async def respond_to_approval(
        token: str, approval_id: int, payload: ApprovalResponse
    ) -> dict[str, Any]:
        client = storage.get_client_by_token(token)
        if client is None:
            raise HTTPException(status_code=404, detail="Portal not found")
        if active_settings.seed_demo_data:
            return {
                "demo": True,
                "message": "Demo response received but not stored.",
                "status": payload.status,
            }
        result = storage.respond_to_approval(
            client["id"], approval_id, payload.status, payload.response
        )
        if result is None:
            raise HTTPException(status_code=404, detail="Approval not found")
        return result

    @app.get("/api/admin/overview", dependencies=[Depends(require_admin)])
    async def admin_overview() -> dict[str, Any]:
        return {
            "metrics": storage.overview(),
            "clients": storage.list_clients(),
            "business": storage.get_settings(),
            "demo": active_settings.seed_demo_data,
        }

    @app.get("/api/admin/clients/{client_id}", dependencies=[Depends(require_admin)])
    async def admin_client(client_id: int) -> dict[str, Any]:
        client = existing_client(client_id)
        return storage.portal(client["portal_token"])

    @app.post(
        "/api/admin/clients",
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(require_admin)],
    )
    async def create_client(payload: ClientCreate) -> dict[str, Any]:
        return storage.create_client(payload.model_dump())

    @app.put("/api/admin/clients/{client_id}", dependencies=[Depends(require_admin)])
    async def update_client(client_id: int, payload: ClientUpdate) -> dict[str, Any]:
        existing_client(client_id)
        values = payload.model_dump(exclude_none=True)
        return storage.update_client(client_id, values) or {}

    @app.post(
        "/api/admin/clients/{client_id}/milestones",
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(require_admin)],
    )
    async def create_milestone(client_id: int, payload: MilestoneCreate) -> dict[str, Any]:
        existing_client(client_id)
        return storage.create_milestone(client_id, payload.model_dump())

    @app.put(
        "/api/admin/milestones/{milestone_id}", dependencies=[Depends(require_admin)]
    )
    async def update_milestone(
        milestone_id: int, payload: MilestoneUpdate
    ) -> dict[str, Any]:
        result = storage.update_milestone(milestone_id, payload.status)
        if result is None:
            raise HTTPException(status_code=404, detail="Milestone not found")
        return result

    @app.post(
        "/api/admin/clients/{client_id}/deliverables",
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(require_admin)],
    )
    async def create_deliverable(
        client_id: int, payload: DeliverableCreate
    ) -> dict[str, Any]:
        existing_client(client_id)
        return storage.create_deliverable(client_id, payload.model_dump())

    @app.post(
        "/api/admin/clients/{client_id}/approvals",
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(require_admin)],
    )
    async def create_approval(client_id: int, payload: ApprovalCreate) -> dict[str, Any]:
        existing_client(client_id)
        return storage.create_approval(client_id, payload.model_dump())

    @app.post(
        "/api/admin/clients/{client_id}/invoices",
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(require_admin)],
    )
    async def create_invoice(client_id: int, payload: InvoiceCreate) -> dict[str, Any]:
        existing_client(client_id)
        values = payload.model_dump()
        values["currency"] = values["currency"].upper()
        return storage.create_invoice(client_id, values)

    @app.post(
        "/api/admin/clients/{client_id}/updates",
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(require_admin)],
    )
    async def create_update(client_id: int, payload: UpdateCreate) -> dict[str, Any]:
        existing_client(client_id)
        return storage.create_update(client_id, payload.model_dump())

    @app.put("/api/admin/business", dependencies=[Depends(require_admin)])
    async def update_business(payload: BusinessUpdate) -> dict[str, Any]:
        return storage.update_settings(payload.model_dump())

    return app


app = create_app()


def run() -> None:
    uvicorn.run("clientdesk.app:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    run()
