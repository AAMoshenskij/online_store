from fastapi import HTTPException, status, Depends

from apps.accounts.models import User
from apps.accounts.services.authenticate import AccountService
from config.database import DatabaseManager
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload



class Permission:
    @classmethod
    async def is_admin(cls, current_user: User = Depends(AccountService.current_user)):
        if current_user.role != 'admin' and current_user.role != 'seller':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this resource.")

    @classmethod
    async def is_seller(cls, current_user: User = Depends(AccountService.current_user)):
        if not hasattr(current_user, 'seller_profile') or not current_user.seller_profile:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You need to be a seller to perform this action.")
        return current_user

    @classmethod    
    async def is_authenticated(cls, current_user: User = Depends(AccountService.current_user)):
        if current_user.role != 'admin' and current_user.role != 'seller' and current_user.role != 'user':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this resource.")
        return current_user