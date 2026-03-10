from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from . import models, database, router

app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    # Check if the error is related to password or email for return 400 as per user requirement
    for error in exc.errors():
        if "password" in error["loc"]:
            return JSONResponse(
                status_code=400, content={"detail": f"Password error: {error['msg']}"}
            )
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


# Create tables
models.Base.metadata.create_all(bind=database.engine)


@app.get("/")
def read_root():  # pragma: no cover
    return {"message": "Welcome to the testing practice project"}


app.include_router(router.router)
