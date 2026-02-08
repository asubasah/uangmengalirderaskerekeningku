from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.session import get_db
from app.db.models import Run, Video, Template
from app.services.youtube_collector import collect_youtube_data
from datetime import datetime, timedelta
import uuid
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class CollectRequest(BaseModel):
    keyword: str
    force_refresh: bool = False

class CollectResponse(BaseModel):
    job_id: uuid.UUID
    status: str
    cached: bool
    result: Optional[dict] = None

class VideoObject(BaseModel):
    source: str
    rank: int
    title: str
    channel_name: Optional[str]
    video_id: str
    video_url: str
    views_raw: Optional[str]
    views_num: Optional[int]
    published_raw: Optional[str]
    duration_raw: Optional[str]

class TemplateObject(BaseModel):
    template_text: str
    example_1: Optional[str]
    example_2: Optional[str]

class StatusResponse(BaseModel):
    job_id: uuid.UUID
    keyword: str
    status: str
    hl: str
    gl: str
    search_top: List[VideoObject]
    people_also_watched_top: List[VideoObject]
    related_fallback_top: List[VideoObject]
    templates: List[TemplateObject]
    error_message: Optional[str]

@router.post("/collect/youtube", response_model=CollectResponse)
async def trigger_collection(
    req: CollectRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Check cache (24 hours)
    if not req.force_refresh:
        yesterday = datetime.utcnow() - timedelta(hours=24)
        cached_run = db.query(Run).filter(
            Run.keyword == req.keyword,
            Run.status == "success",
            Run.finished_at >= yesterday
        ).order_by(desc(Run.finished_at)).first()

        if cached_run:
            # Build result for cached response
            return CollectResponse(
                job_id=cached_run.id,
                status="success",
                cached=True,
                result=construct_status_response(cached_run, db).dict()
            )

    # Create new run
    new_run = Run(
        keyword=req.keyword,
        status="queued"
    )
    db.add(new_run)
    db.commit()
    db.refresh(new_run)
    
    # Enqueue background task
    background_tasks.add_task(collect_youtube_data, new_run.id, req.keyword)
    
    return CollectResponse(
        job_id=new_run.id,
        status="queued",
        cached=False
    )

@router.get("/collect/status/{job_id}", response_model=StatusResponse)
def get_status(job_id: uuid.UUID, db: Session = Depends(get_db)):
    run = db.query(Run).filter(Run.id == job_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return construct_status_response(run, db)

def construct_status_response(run: Run, db: Session) -> StatusResponse:
    # Fetch videos/templates (handled by relationship ideally, but explicit query safe)
    # Using relationship defined in models: run.videos, run.templates
    
    search_top = []
    people_also_watched = []
    related_fallback = []
    
    for v in run.videos:
        vo = VideoObject(
            source=v.source_type,
            rank=v.rank,
            title=v.title,
            channel_name=v.channel_name,
            video_id=v.video_id,
            video_url=v.video_url,
            views_raw=v.views_raw,
            views_num=v.views_num,
            published_raw=v.published_raw,
            duration_raw=v.duration_raw
        )
        if v.source_type == "search":
            search_top.append(vo)
        elif v.source_type == "people_also_watched":
            people_also_watched.append(vo)
        elif v.source_type == "related_fallback":
            related_fallback.append(vo)
            
    # Sort by rank
    search_top.sort(key=lambda x: x.rank)
    people_also_watched.sort(key=lambda x: x.rank)
    related_fallback.sort(key=lambda x: x.rank)
    
    templates = []
    for t in run.templates:
        templates.append(TemplateObject(
            template_text=t.template_text,
            example_1=t.example_1,
            example_2=t.example_2
        ))
        
    return StatusResponse(
        job_id=run.id,
        keyword=run.keyword,
        status=run.status,
        hl=run.hl,
        gl=run.gl,
        search_top=search_top,
        people_also_watched_top=people_also_watched,
        related_fallback_top=related_fallback,
        templates=templates,
        error_message=run.error_message
    )
