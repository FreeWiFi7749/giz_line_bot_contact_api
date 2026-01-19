"""
Contact API - LINE Bot Contact Form Backend
"""
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database import get_db, init_db
from .models import Inquiry
from .schemas import InquiryCreate, InquiryResponse, HealthResponse
from .services import verify_id_token, send_inquiry_emails

# Configure logging (Railwayでログレベルが正しく表示されるようにする)
# INFO/DEBUG → stdout(Railwayで通常ログとして表示)
# WARNING/ERROR/CRITICAL → stderr(Railwayでエラーログとして表示)
class InfoFilter(logging.Filter):
    def filter(self, record):
        return record.levelno <= logging.INFO

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.addFilter(InfoFilter())

stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setLevel(logging.WARNING)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[stdout_handler, stderr_handler],
    force=True,
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    logger.info("Starting Contact API...")
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down Contact API...")


app = FastAPI(
    title="Gizmodo Japan LINE Bot Contact API",
    description="API for handling contact form submissions from LINE LIFF",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
allowed_origins = [settings.LIFF_ORIGIN]
if settings.ALLOWED_ORIGINS:
    allowed_origins.extend([
        origin.strip() 
        for origin in settings.ALLOWED_ORIGINS.split(",") 
        if origin.strip() and origin.strip() not in allowed_origins
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/inquiry", response_model=InquiryResponse)
async def submit_inquiry(
    data: InquiryCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a contact form inquiry
    
    - Verifies LINE ID token (if provided)
    - Saves inquiry to database
    - Sends confirmation email to user
    - Sends notification email to admin
    """
    line_user_id = None
    
    # Verify LINE ID token if provided
    if data.idToken:
        line_user_id = verify_id_token(data.idToken)
        if not line_user_id:
            raise HTTPException(
                status_code=401,
                detail="LINE認証に失敗しました。再度お試しください。"
            )
    
    # Save to database
    try:
        inquiry = Inquiry(
            name=data.name,
            email=data.email,
            category=data.category,
            message=data.message,
            line_user_id=line_user_id,
        )
        db.add(inquiry)
        await db.commit()
        await db.refresh(inquiry)
        logger.info(f"Inquiry saved: id={inquiry.id}, category={data.category}")
    except Exception as e:
        logger.error(f"Failed to save inquiry: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="お問い合わせの保存に失敗しました。"
        )
    
    # Send emails in background
    background_tasks.add_task(send_inquiry_emails, data)
    
    return InquiryResponse(
        ok=True,
        message="お問い合わせを受け付けました。確認メールをお送りしました。"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="ok")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Gizmodo Japan LINE Bot Contact API",
        "version": "1.0.0",
        "status": "running",
    }
