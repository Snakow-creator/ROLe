from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from authx import AuthXDependency

from models.models import User
from models.schemas import UserSchema, RegisterUserSchema
from users.object import UserObj
from repositories import user_repo

from api.core.crypt import hash_password, verify_password
from api.auth.service import auth
from api.core.config import test_data
from api.core.security import security

from levels.data import which_my_role

router = APIRouter(tags=["auth"])


@router.post("/login")
async def login(creds: UserSchema):
    if creds.name == "test" and creds.password == "testtest":
        user_id = "test"
        data = test_data

    else:
        user = await user_repo.get_by_name(creds.name)
        if await verify_password(creds.password, user.hashed_password):
            user_id = user.name
            user_obj = await UserObj.init_object(user_id)
            data = user_obj.data

        else:
            return JSONResponse(
                status_code=400,
                content={"message": "Invalid credentials", "error": "Invalid credentials"},
            )

    tokens = await auth.authenticate_user(user_id, data)
    return {**data, "access_token": tokens["access_token"]}


@router.post("/logout", dependencies=[Depends(security.get_dependency)])
async def logout(deps: AuthXDependency = Depends(security.get_dependency)):
    return auth.logout_user(deps)


@router.post("/register")
async def register(creds: RegisterUserSchema):
    errors = []

    user_names = await user_repo.get_all_names()
    if creds.name in user_names:
        errors.append({
            "message": "User name already exists",
            "field": "name",
            "code": "user_exists",
        })

    if creds.password1 != creds.password2:
        errors.append({
            "message": "Passwords do not match",
            "field": "password",
            "code": "passwords_mismatch",
        })
    print(errors)
    if errors:
        raise HTTPException(status_code=400, detail=errors)

    hashed_password = await hash_password(creds.password1)
    await user_repo.insert_user(creds.name, hashed_password)

    return {"message": "register"}


@router.get("/protected")
async def protected(
    request: Request,
    res = Depends(auth.safe_access_token_getter),
):
    if isinstance(res, JSONResponse):
        return res

    return {"message": "AUTHORIZED", "auth": True, "expire": False}


@router.get("/profile", dependencies=[Depends(security.access_token_required)])
async def profile(
    user: User = Depends(security.get_current_subject),
):
    try:
        data = {
            "name": user["name"],
            "level": user["level"],
            "role": which_my_role.get(user["level"], "Бог"),
            "avatar": user["current_avatar"],
            "xp": user["xp"],
            "Spoints": user["Spoints"],
            "days_streak": user["days_streak"],
            "mul": user["mul"],
            "sale_shop": user["sale_shop"],
            "last_streak": user["last_streak"],
            "last_mul": user["last_mul"],
            "complete_simple_tasks": user["complete_simple_tasks"],
            "complete_common_tasks": user["complete_common_tasks"],
            "complete_hard_tasks": user["complete_hard_tasks"],
            "complete_expert_tasks": user["complete_expert_tasks"],
            "complete_hardcore_tasks": user["complete_hardcore_tasks"],
        }
        return data
    except Exception:
        raise HTTPException(status_code=404, detail="Not authorized")
