from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.mongo.hooks.mongo import MongoHook
from airflow.providers.clickhouse.operators.clickhouse import ClickHouseOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'batch_processing',
    default_args=default_args,
    description='Batch processing of online store data',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False
)

# Task to process PostgreSQL data
process_postgres_data = PostgresOperator(
    task_id='process_postgres_data',
    postgres_conn_id='postgres_default',
    sql="""
    INSERT INTO clickhouse.products
    SELECT 
        product_id,
        seller_id,
        name,
        description,
        main_category_id,
        sub_category_id,
        price,
        discount_price,
        image_url,
        product_url,
        created_at,
        updated_at
    FROM products
    WHERE updated_at >= CURRENT_DATE - INTERVAL '1 day'
    """,
    dag=dag
)

# Task to process MongoDB data
def process_mongodb_data():
    mongo_hook = MongoHook(conn_id='mongodb_default')
    clickhouse_hook = ClickHouseHook(conn_id='clickhouse_default')
    
    # Get events from MongoDB
    events = mongo_hook.find(
        mongo_collection='events',
        mongo_db='online_store',
        query={'timestamp': {'$gte': datetime.now() - timedelta(days=1)}}
    )
    
    # Insert events into ClickHouse
    for event in events:
        clickhouse_hook.run(
            """
            INSERT INTO events
            VALUES (
                %(event_id)s,
                %(event_type)s,
                %(user_id)s,
                %(product_id)s,
                %(quantity)s,
                %(price)s,
                %(rating)s,
                %(review)s,
                %(timestamp)s
            )
            """,
            parameters=event
        )

process_mongodb = PythonOperator(
    task_id='process_mongodb_data',
    python_callable=process_mongodb_data,
    dag=dag
)

# Task to refresh materialized views
refresh_views = ClickHouseOperator(
    task_id='refresh_views',
    clickhouse_conn_id='clickhouse_default',
    sql="""
    OPTIMIZE TABLE product_analytics FINAL;
    OPTIMIZE TABLE seller_analytics FINAL;
    OPTIMIZE TABLE category_analytics FINAL;
    """,
    dag=dag
)

# Set task dependencies
process_postgres_data >> process_mongodb >> refresh_views 