from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from passlib.hash import bcrypt
import re
from app.user.authentication import authenticate_user, create_token, get_current_user, get_admin_user
from app.user.models_user import UserModel
from app.user.schemas_user import User, UserIn

router1 = APIRouter()
admin_router = APIRouter()

@admin_router.post("/api/change-role-admin/{user_id}")
async def change_role(user_id: int, new_role: str, admin_user: UserModel = Depends(get_admin_user)):
    user = await UserModel.get(id=user_id)
    user.role = new_role
    await user.save()
    return {"msg": "Role updated successfully"}

@admin_router.post("/api/change-fullname-admin/{user_id}")
async def change_fullname(user_id: int, new_fullname: str, admin_user: UserModel = Depends(get_admin_user)):
    user = await UserModel.get(id=user_id)
    if not re.fullmatch(r"[A-Za-zА-Яа-яёЁ\s\-]+", new_fullname):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Fullname должен содержать только буквы, пробелы и дефисы.",
        )
    user.fullname = new_fullname
    await user.save()
    return {"msg": "Role updated successfully"}

@admin_router.post("/api/change-password-admin/{user_id}")
async def change_password(user_id: int, new_password: str, admin_user: UserModel = Depends(get_admin_user)):
    user = await UserModel.get(id=user_id)
    if len(new_password) > 20:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пароль должен быть не длиннее 20 символов.",
        )
    user.password = bcrypt.hash(new_password)
    await user.save()
    return {"msg": "Role updated successfully"}

@router1.get("/api/get_users")
async def get_users():
    users = await UserModel.all().values("id", "fullname", "role")
    return users

@router1.get("/api/get_user/{user_id}")
async def get_user(user_id: int):  
    user = await UserModel.get(id=user_id).values("fullname", "role", "about")
    return user

@router1.post("/api/users")
async def create_user(user_in: UserIn):
    
    if not re.fullmatch(r"[A-Za-zА-Яа-яёЁ\s\-]+", user_in.fullname):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Fullname должен содержать только буквы, пробелы и дефисы.",
        )
    if len(user_in.password1) > 20:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пароль должен быть не длиннее 20 символов.",
        )
    user = await UserModel.create(
        fullname = user_in.fullname, login=user_in.login, password=bcrypt.hash(user_in.password1)
    )
    

    return {"access_token": await create_token(user)}

@router1.post("/api/change-about/{user_id}")
async def change_about(user_id: int, new_about: str):
    user = await UserModel.get(id=user_id)
    if user.role == "guest":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "Нет прав",
        )
    user.about = new_about
    await user.save()
    return {"msg": "About updated successfully"}

@router1.post("/api/token")
async def generate_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid email or password",
        )

    return {"access_token": await create_token(user), "id": user.id, "role": user.role}
