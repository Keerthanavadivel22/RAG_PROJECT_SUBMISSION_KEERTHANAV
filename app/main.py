from fastapi import FastAPI 
from routers.document_rout import router as doc_router
from routers.user_rout import router as usr_router
from routers.upload_rout import router as upload_router
from routers.chat import router as chat_router
from logging_config import logger
app = FastAPI()

app.include_router(doc_router)
app.include_router(usr_router)
app.include_router(upload_router)
#app.include_router(search_router)
app.include_router(chat_router)


@app.get("/")
def home():
    logger.info("Root endpoint accessed")
    
    return{
        "application" : "rag api",
        "status" : "running"
           }
