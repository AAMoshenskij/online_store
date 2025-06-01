from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import PrometheusFastApiInstrumentator

from config.database import DatabaseManager
from config.routers import RouterManager
from config.settings import MEDIA_DIR, AppConfig
from config.elasticsearch import es

try:
    from .core.metrics import APP_VERSION
except ImportError:
    from apps.core.metrics import APP_VERSION

from apps.search.routers import router as search_router
from apps.orders.routers import router as orders_router


# -------------------
# --- Init Models ---
# -------------------

DatabaseManager().create_database_tables()

# --------------------
# --- Init FastAPI ---
# --------------------

app = FastAPI()

instrumentator = PrometheusFastApiInstrumentator().instrument(app)

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

app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

# --------------------
# --- Init Routers ---
# --------------------

RouterManager(app).import_routers()
app.include_router(search_router)
app.include_router(orders_router)

@app.on_event("startup")
async def startup_event():
    instrumentator.expose(app, include_in_schema=False, should_gzip=True)
    
    app_config = AppConfig.get_config()
    APP_VERSION.labels(version=app_config.app_version).set(1)

    from apps.analytics.etl.products_etl import sync_products_to_elasticsearch
    try:
        await sync_products_to_elasticsearch()
    except Exception as e:
        print(f"⚠️ Ошибка синхронизации с Elasticsearch: {e}")

    print(f"ID of USER_REGISTRATIONS_TOTAL in app at startup: {id(USER_REGISTRATIONS_TOTAL)}")
    print(f"ID of ORDERS_CREATED_TOTAL in app at startup: {id(ORDERS_CREATED_TOTAL)}")

# --- Ручка для дебага ---
# --- Нужна для искусственного заполнения метрик ---
import random
import time
from apps.core.metrics import (
    USER_REGISTRATIONS_TOTAL,
    USER_LOGINS_TOTAL,
    USER_PROFILE_UPDATES_TOTAL,
    ORDERS_CREATED_TOTAL,
    ORDERS_STATUS_CHANGED_TOTAL,
    ORDERS_COMPLETED_TOTAL,
    ORDERS_AMOUNT_HISTOGRAM,
    PAYMENTS_PROCESSED_TOTAL,
    ITEMS_ADDED_TO_CART_TOTAL,
    PRODUCTS_VIEWED_TOTAL
)

def _populate_metrics_logic(num_iterations=(2400 * 7)):
    days_to_simulate = num_iterations / 2400
    expected_duration_minutes = num_iterations * 0.05 / 60
    print(f"Populating metrics for {days_to_simulate:.1f} days ({num_iterations} iterations), ~{expected_duration_minutes:.1f} minutes to finish...")

    HOURLY_ACTIVITY_PROFILE = [
        # 00:00 - 05:00 (ночь - низкая активность)
        0.05, 0.05, 0.05, 0.05, 0.05, 0.1,
        # 06:00 - 11:00 (утро - активность начинает подниматься)
        0.2, 0.3, 0.5, 0.7, 0.8, 0.9,
        # 12:00 - 17:00 (день - пик акивности и начало снижения)
        1.0, 0.95, 0.9, 0.8, 0.7, 0.6,
        # 18:00 - 23:00 (вечер - активность продолжает снижаться)
        0.5, 0.4, 0.3, 0.2, 0.1, 0.05
    ]

    login_statuses = ["success", "failure"]
    order_statuses_full = ["pending", "processing", "shipped", "delivered", "cancelled", "created"]
    payment_methods = ["card", "paypal", "bank_transfer", "cod"]
    product_ids_sample = [str(random.randint(1, 1000)) for _ in range(20)]
    category_ids_sample = [str(random.randint(1,100)) for _ in range(5)]


    for i in range(num_iterations):
        progress_total_week = i / num_iterations
        total_simulated_hours_in_week = progress_total_week * (days_to_simulate * 24.0)
        
        simulated_hour_of_day_for_profile = total_simulated_hours_in_week % 24.0
        
        hour_idx1 = int(simulated_hour_of_day_for_profile) % 24
        hour_idx2 = (hour_idx1 + 1) % 24
        
        interp_fraction = simulated_hour_of_day_for_profile - int(simulated_hour_of_day_for_profile)
        
        activity_multiplier = (HOURLY_ACTIVITY_PROFILE[hour_idx1] * (1 - interp_fraction) +
                               HOURLY_ACTIVITY_PROFILE[hour_idx2] * interp_fraction)
        
        if i % (num_iterations // 200) == 0:
            print(f"DEBUG: i == {i}, simulated time of day: {simulated_hour_of_day_for_profile:.2f}, activity_multiplier: {activity_multiplier:.4f}")

        if random.random() < activity_multiplier:
            USER_REGISTRATIONS_TOTAL.inc(random.randint(1, 3))
        
        if random.random() < activity_multiplier:
            USER_LOGINS_TOTAL.labels(status=random.choice(login_statuses)).inc(random.randint(1, 5))
        
        if random.random() < activity_multiplier:
            USER_PROFILE_UPDATES_TOTAL.inc(random.randint(1, 2))
        
        if random.random() < activity_multiplier:
            ORDERS_CREATED_TOTAL.inc(random.randint(1, 3))

        if random.random() < activity_multiplier:
            old_s = random.choice(order_statuses_full)
            possible_new_s = [s for s in order_statuses_full if s != old_s]
            if not possible_new_s:
                possible_new_s = order_statuses_full

            new_s = random.choice(possible_new_s)
            ORDERS_STATUS_CHANGED_TOTAL.labels(old_status=old_s, new_status=new_s).inc()
            if new_s == "delivered":
                ORDERS_COMPLETED_TOTAL.inc(random.randint(1, 2))
        
        if random.random() < activity_multiplier:
            PAYMENTS_PROCESSED_TOTAL.labels(
                status=random.choice(login_statuses),
                payment_method=random.choice(payment_methods)
            ).inc(random.randint(1, 3))
        
        if random.random() < activity_multiplier:
            ITEMS_ADDED_TO_CART_TOTAL.labels(product_id=random.choice(product_ids_sample)).inc()
        
        if random.random() < activity_multiplier:
            PRODUCTS_VIEWED_TOTAL.labels(
                product_id=random.choice(product_ids_sample), 
                category_id=random.choice(category_ids_sample)
            ).inc(random.randint(1, 5))

        if random.random() < activity_multiplier:
            ORDERS_AMOUNT_HISTOGRAM.observe(random.uniform(5.0, 350.0))

        time.sleep(0.05)

        if (i + 1) % 600 == 0 or i == num_iterations - 1:
            current_simulated_day = int(total_simulated_hours_in_week // 24) + 1
            current_simulated_hour = total_simulated_hours_in_week % 24
            print(f"iteration {i+1}/{num_iterations}. Simulated day #{current_simulated_day}/{int(days_to_simulate)}, {current_simulated_hour:.2f}h")
            
    print("Metrics populated")

@app.get("/debug/populate-metrics")
async def debug_populate_metrics(background_tasks: BackgroundTasks, num_iterations: int = (2400 * 7)):
    background_tasks.add_task(_populate_metrics_logic, num_iterations=num_iterations)
    days_to_simulate = num_iterations / 2400
    return {"message": f"Заполнение метриками на {days_to_simulate:.1f} дней ({num_iterations} итераций) началось. Проверьте логи сервера. Примерное время исполнения: ~{num_iterations * 0.05 / 60:.1f} минут"}
