from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.schemas.event import EventCreate, EventResponse
from app.services.event_ingestion import ingest_event


router = APIRouter(prefix="/events", tags=["events"])


@router.post(
    "",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_event(
    event_data: EventCreate,
    db: AsyncSession = Depends(get_db),
):
    event, duplicate = await ingest_event(db, event_data)

    if duplicate:
        # FastAPI doesn't allow changing the decorator's status dynamically,
        # so return a response with the appropriate status explicitly.
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=EventResponse.model_validate(event).model_dump(mode="json"),
        )

    return event