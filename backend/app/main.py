"""Điểm vào ứng dụng FastAPI. Chạy: uvicorn app.main:app --reload"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints.business_verifications import router as business_verifications_router

# Import các router nhóm A (Freelancer / Business Accounts)
from app.api.v1.endpoints.client_accounts import router as client_accounts_router
from app.api.v1.endpoints.files import router as files_router
from app.api.v1.endpoints.mou_agreements import router as mou_agreements_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.routers import api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="Nền tảng kết nối Sinh viên – Doanh nghiệp – Nhà trường",
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url="/docs",
        redoc_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    
    # Đăng ký router tổng cũ của hệ thống
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # Đăng ký các endpoint nhóm A vào tiền tố API v1
    app.include_router(client_accounts_router, prefix=settings.API_V1_PREFIX)
    app.include_router(business_verifications_router, prefix=settings.API_V1_PREFIX)
    app.include_router(mou_agreements_router, prefix=settings.API_V1_PREFIX)
    app.include_router(files_router, prefix=settings.API_V1_PREFIX)

    @app.get("/health", tags=["Health"], summary="Kiểm tra server sống")
    def health() -> dict:
        return {"status": "ok", "env": settings.ENV}

    return app


app = create_app()