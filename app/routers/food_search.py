from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.security import OAuth2PasswordBearer
from app.services.fatsecret_service import FatSecretService
from app.services.firebase_service import verify_token

router = APIRouter(
    prefix="/food",
    tags=["food"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.get("/search")
async def search_food(
    query: str,
    authorization: str = Header(None),
    fatsecret_service: FatSecretService = Depends()
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header",
        )

    token = authorization[7:]
    verify_token(token)
    try:
        results = fatsecret_service.search_foods(query)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
