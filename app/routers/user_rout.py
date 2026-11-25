from fastapi import APIRouter
from schemas.models import user_schema
from schemas.models import login_schema
from database.db import get_connection
from utils.jwt_handler import create_access_token
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends

router = APIRouter(
    prefix = "/user",
    tags= ["Login / Creation of User"]
)

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(
        plain_password,
        hashed_password
    )


@router.post("/register")
def create_user(user : user_schema):
    hashed_password = hash_password(
    user.password)
    print(user.password)
    print(hashed_password)
    conn = get_connection()
    cursor = conn.cursor()
    
    sql = """
        INSERT INTO users(username , email , password)
        VALUES (%s, %s , %s)
        """
    
    values = (
            user.username,
            user.email,
            hashed_password
        )
    
    cursor.execute(sql, values)
    conn.commit()
    
    print(f"user register successfully! ID: {cursor.lastrowid}")
    
    cursor.close()
            

    return {
        "message": "user created",
    }

@router.get("/{id}")
def get_user(id : int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
        
            # Insert a document chunk
    sql = """
            select * from users WHERE id = %s
            """
    cursor.execute(sql,(id,))
    documents = cursor.fetchone()
    cursor.close()
    conn.commit()
    return documents


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    email = form_data.username
    password = form_data.password
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    sql = """
    SELECT *
    FROM users
    WHERE email = %s
    """

    cursor.execute(
        sql,
        (email,)
    )

    db_user = cursor.fetchone()

    cursor.close()
    conn.close()

    if not db_user:
        return {
            "message": "User not found"
        }

    if not verify_password(
        password,
        db_user["password"] # type: ignore
    ):
        return {
            "message": "Invalid password"
        }
    token = create_access_token(
        {
            "user_id": db_user["id"], # type: ignore
            "email": db_user["email"] # type: ignore
        }
        )
    return {
        "access_token": token,
        "token_type": "bearer",
        "message": "Login successful"
    }
    