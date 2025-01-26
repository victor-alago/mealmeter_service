from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.security import OAuth2PasswordBearer
from app.services.api_ninjas_service import ApiNinjasService
from app.services.firebase_service import verify_token

router = APIRouter(
    prefix="/food_ninjas",
    tags=["food_ninjas"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.get("/search")
async def search_food_ninjas(
    query: str,
    authorization: str = Header(None),
    api_ninjas_service: ApiNinjasService = Depends()
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header",
        )

    token = authorization[7:]
    current_user = verify_token(token)
    try:
        results = api_ninjas_service.search_foods(query)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
