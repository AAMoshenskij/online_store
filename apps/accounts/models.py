from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, ForeignKey, ARRAY
from sqlalchemy.orm import relationship

from config.database import FastModel
from sqlalchemy.orm import Session


class User(FastModel):
    """
    User represents registered users in the application.

    Attributes:
        id (int): Unique identifier for the user.
        email (str): User's email address used for authentication and communication.
        password (str): Hashed password for user authentication.
        first_name (str, optional): User's first name. Default is None.
        last_name (str, optional): User's last name. Default is None.
        is_verified_email (bool): Flag indicating whether the user's email address has been verified.
        is_active (bool): Flag indicating whether the user's account is active.
        is_superuser (bool): Flag indicating whether the user has superuser privileges.
        role (str): User's role in the system, represented as a short string.
        date_joined (datetime): Timestamp indicating when the user account was created.
        updated_at (datetime, optional): Timestamp indicating when the user account was last updated. Default is None.
        last_login (datetime, optional): Timestamp indicating the user's last login time. Default is None.
        change (relationship): Relationship attribute linking this user to change requests initiated by the user.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(256), nullable=False, unique=True)
    password = Column(String, nullable=False)

    first_name = Column(String(256), nullable=True)
    last_name = Column(String(256), nullable=True)
    
    age = Column(Integer, default=21)

    is_verified_email = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)

    # TODO add unittest and check the default role is 'user', also move role to permissions table
    role = Column(String(6), default="user")

    date_joined = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    last_login = Column(DateTime, nullable=True)

    change = relationship("UserVerification", back_populates="user", cascade="all, delete-orphan")
    seller_profile = relationship("Seller", back_populates="user", cascade="all, delete-orphan", lazy="selectin")


class UserVerification(FastModel):
    """
    UserVerification represents change requests initiated by users, such as email or phone number changes,
    that require OTP verification.

    Attributes:
        id (int): Unique identifier for the verification request.
        user_id (int): ID of the user who initiated the verification request.
        request_type (str): Indicates the type of verification request (register /reset-password /change-email
        /change-phone).
        new_email (str): New email address requested by the user.
        new_phone (str): New phone number requested by the user.
        active_access_token (str, optional): Last valid access token used for JWT authentication. Default is None.
        created_at (datetime): Timestamp indicating when the verification request was created.
        updated_at (datetime): Timestamp indicating when the verification request was last updated.
    """

    __tablename__ = "users_verifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    request_type = Column(String, nullable=True)
    new_email = Column(String(256), nullable=True)
    new_phone = Column(String(256), nullable=True)
    active_access_token = Column(String, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    user = relationship("User", back_populates="change")

class Seller(FastModel):
    """
    Seller represents users who sell products in the marketplace.
    
    Attributes:
        id (int): Unique identifier for the seller
        user_id (int): Reference to the User who is the seller
        product_ids (list[int]): List of product IDs associated with this seller
        is_active (bool): Whether the seller account is active
        created_at (datetime): When the seller account was created
    """
    __tablename__ = "sellers"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    first_name = Column(String(256), nullable=True)
    last_name = Column(String(256), nullable=True)

    product_ids = Column(ARRAY(Integer), default=[])
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="seller_profile")
