from fastapi import APIRouter

from app.services.news_service import get_news_for_today

router = APIRouter(prefix="/api/v1/news", tags=["news"])


@router.get("/today")
async def get_today_news():
    snippets = await get_news_for_today()
    return {"snippets": snippets, "count": len(snippets)}
