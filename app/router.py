from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from . import models, schemas, database, auth, email, dependencies

router = APIRouter()


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pass = auth.get_password_hash(user.password)
    new_user = models.User(
        email=user.email, username=user.username, hashed_password=hashed_pass
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    verify_token = auth.create_token(
        data={"sub": new_user.email}, token_type="verification"
    )
    email.send_verification_email(new_user.email, verify_token)

    return {"message": "Registration successful. Please verify your email."}


@router.post("/auth/verify-email")
def verify_email(
    payload: schemas.VerifyEmailRequest, db: Session = Depends(database.get_db)
):
    try:
        decoded_payload = jwt.decode(
            payload.token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM]
        )
        user_email: str = decoded_payload.get("sub")
        token_type: str = decoded_payload.get("type")

        if user_email is None or token_type != "verification":
            raise HTTPException(status_code=400, detail="Invalid or expired token")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = db.query(models.User).filter(models.User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    user.is_verified = True
    db.commit()

    return {"message": "Email verified successfully"}


@router.post("/auth/login", response_model=schemas.Token)
def login(login_data: schemas.UserLogin, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == login_data.email).first()
    if not user or not auth.verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    access_token = auth.create_token(data={"sub": user.email})
    refresh_token = auth.create_token(data={"sub": user.email}, token_type="refresh")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/users/", response_model=list[schemas.UserOut])
def list_users(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(dependencies.get_current_user),
):
    return db.query(models.User).all()
