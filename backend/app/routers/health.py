from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/health-records", tags=["Health Records"])

@router.get("/demo-timeline")
def demo_timeline():
    return {
        "patient": "Demo Patient",
        "timeline": [
            {
                "date": "2026-10-03",
                "type": "consultation",
                "title": "General Medicine Consultation",
            },
            {
                "date": "2026-09-29",
                "type": "laboratory",
                "title": "Blood Test",
                "flag": "Review requested",
            },
            {
                "date": "2026-09-21",
                "type": "medication",
                "title": "Medication prescribed",
            },
        ],
    }
