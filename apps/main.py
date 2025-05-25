from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config.database import DatabaseManager
from config.routers import RouterManager
from config.settings import MEDIA_DIR
#from config.elasticsearch import es

from apps.search.routers import router as search_router


# -------------------
# --- Init Models ---
# -------------------

DatabaseManager().create_database_tables()

# --------------------
# --- Init FastAPI ---
# --------------------

app = FastAPI()

# ------------------
# --- Middleware ---
# ------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])

# -------------------
# --- Static File ---
# -------------------

# add static-file support, for see images by URL
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

# --------------------
# --- Init Routers ---
# --------------------

RouterManager(app).import_routers()
app.include_router(search_router)

@app.on_event("startup")
async def startup_event():
    
    # Синхронизация данных
    from apps.analytics.etl.products_etl import sync_products_to_elasticsearch
    try:
        await sync_products_to_elasticsearch()
    except Exception as e:
        print(f"⚠️ Ошибка синхронизации с Elasticsearch: {e}")