from confluent_kafka import Consumer, KafkaError
import clickhouse_driver
import json
import logging
from datetime import datetime
import re
from decimal import Decimal
import time
import os
from confluent_kafka.admin import AdminClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Kafka configuration
KAFKA_CONFIG = {
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'clickhouse_etl_group',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': 'false',
    'client.id': 'etl_processor',
    'security.protocol': 'PLAINTEXT',
    'sasl.mechanisms': 'PLAIN',
    'sasl.username': '',
    'sasl.password': '',
    'ssl.endpoint.identification.algorithm': 'none',
    'broker.address.family': 'v4',
    'client.dns.lookup': 'use_all_dns_ips',
    'reconnect.backoff.ms': 1000,
    'reconnect.backoff.max.ms': 5000
}

logger.info(f"Kafka config: {KAFKA_CONFIG}")
logger.info(f"Environment variables: KAFKA_BOOTSTRAP_SERVERS={os.getenv('KAFKA_BOOTSTRAP_SERVERS')}")

# ClickHouse configuration
CLICKHOUSE_CONFIG = {
    'host': os.getenv("CLICKHOUSE_HOST", 'clickhouse'),
    'port': int(os.getenv("CLICKHOUSE_PORT", 9000)),
    'user': os.getenv("CLICKHOUSE_USER", 'default'),
    'password': os.getenv("CLICKHOUSE_PASSWORD", ''),
    'database': os.getenv("CLICKHOUSE_DB", 'online_store')
}

# Table mappings (PostgreSQL -> ClickHouse)
TABLE_MAPPINGS = {
    'users': {
        'table': 'users',
        'fields': {
            'id': 'user_id',
            'age': 'user_age',
            'first_name': 'first_name',
            'last_name': 'last_name',
            'is_verified_email': 'is_verified_email',
            'is_active': 'is_active',
            'date_joined': 'date_joined',
            'last_login': 'last_login'
        }
    },
    'sellers': {
        'table': 'sellers',
        'fields': {
            'id': 'seller_id',
            'first_name': 'first_name',
            'last_name': 'last_name'
        }
    },
    'products': {
        'table': 'products',
        'fields': {
            'id': 'product_id',
            'product_name': 'product_name',
            'main_category': 'main_category',
            'sub_category': 'sub_category',
            'external_ratings': 'external_ratings',
            'external_ratings_count': 'external_ratings_count',
            'external_price': 'external_price'
        },
        'transformations': {
            'external_price': lambda x: Decimal(re.sub(r'[^\d.]', '', x)) if x else Decimal('0')
        }
    },
    'order_items': {
        'table': 'order_items',
        'fields': {
            'order_id': 'order_id',
            'product_id': 'product_id',
            'seller_id': 'seller_id',
            'quantity': 'quantity'
        }
    },
    'payments': {
        'table': 'payments',
        'fields': {
            'order_id': 'order_id',
            'amount': 'amount',
            'currency': 'currency',
            'status': 'status',
            'payment_method': 'payment_method',
            'created_at': 'created_at'
        }
    },
    'orders': {
        'table': 'orders',
        'fields': {
            'id': 'order_id',
            'user_id': 'user_id',
            'status': 'status',
            'created_at': 'order_date'
        }
    }
}

class ETLProcessor:
    def __init__(self):
        logger.info(f"Creating Kafka consumer with config: {KAFKA_CONFIG}")
        try:
            self.consumer = Consumer(KAFKA_CONFIG)
            logger.info(f"Kafka consumer created. Broker: {KAFKA_CONFIG['bootstrap.servers']}")
        except Exception as e:
            logger.error(f"Failed to create Kafka consumer: {str(e)}")
            raise
        self.clickhouse_client = clickhouse_driver.Client(**CLICKHOUSE_CONFIG)
        self.topic_pattern = re.compile(r'postgres\.public\.(\w+)')
        
        # Создаем таблицу для отслеживания прочитанных сообщений
        self._create_processed_messages_table()

    def _create_processed_messages_table(self):
        """Создает таблицу для отслеживания прочитанных сообщений"""
        try:
            self.clickhouse_client.execute("""
                CREATE TABLE IF NOT EXISTS processed_messages (
                    topic String,
                    partition UInt32,
                    offset UInt64,
                    processed_at DateTime DEFAULT now()
                ) ENGINE = ReplacingMergeTree()
                ORDER BY (topic, partition, offset)
            """)
            logger.info("Created processed_messages table")
        except Exception as e:
            logger.error(f"Failed to create processed_messages table: {str(e)}")
            raise

    def _is_message_processed(self, topic, partition, offset):
        """Проверяет, было ли сообщение уже обработано"""
        try:
            result = self.clickhouse_client.execute("""
                SELECT 1 FROM processed_messages 
                WHERE topic = %(topic)s 
                AND partition = %(partition)s 
                AND offset = %(offset)s
            """, {
                'topic': str(topic),
                'partition': int(partition),
                'offset': int(offset)
            })
            return len(result) > 0
        except Exception as e:
            logger.error(f"Failed to check if message was processed: {str(e)}")
            return False

    def _mark_message_processed(self, topic, partition, offset):
        """Отмечает сообщение как обработанное"""
        try:
            self.clickhouse_client.execute("""
                INSERT INTO processed_messages (topic, partition, offset)
                VALUES (%(topic)s, %(partition)s, %(offset)s)
            """, {
                'topic': str(topic),
                'partition': int(partition),
                'offset': int(offset)
            })
            logger.info(f"Marked message as processed: topic={topic}, partition={partition}, offset={offset}")
        except Exception as e:
            logger.error(f"Failed to mark message as processed: {str(e)}")
            raise

    def process_message(self, msg):
        try:
            # Parse message
            value = json.loads(msg.value().decode('utf-8'))
            payload = value.get('payload', {})
            
            # Extract table name from topic
            topic = msg.topic()
            match = self.topic_pattern.match(topic)
            if not match:
                logger.warning(f"Unknown topic format: {topic}")
                return
            
            table_name = match.group(1)
            logger.info(f"Processing table: {table_name}")
            if table_name not in TABLE_MAPPINGS:
                logger.warning(f"Unmapped table: {table_name}")
                return

            # Get table mapping
            mapping = TABLE_MAPPINGS[table_name]
            target_table = mapping['table']
            fields = mapping['fields']
            transformations = mapping.get('transformations', {})

            # Process based on operation type
            op = value.get('op')
            logger.info(f"Operation type: {op}")
            if op in ['r', 'c', 'u']:  # Read (initial load), Create, Update
                data = value.get('after', {})
                if data:
                    logger.info(f"Data to insert: {data}")
                    self._handle_insert(data, target_table, fields, transformations)
                else:
                    logger.warning(f"No data in 'after' field for operation {op}")
            elif op == 'd':  # Delete
                logger.info(f"Skipping delete operation for table {table_name}")

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            raise

    def _handle_insert(self, data, table, fields, transformations):
        if not data:
            logger.warning(f"No data to insert into {table}")
            return

        # Transform data according to mapping
        transformed_data = {}
        for pg_field, ch_field in fields.items():
            value = data.get(pg_field)
            if pg_field in transformations:
                value = transformations[pg_field](value)
            # Преобразуем строковые даты в datetime
            elif isinstance(value, str) and any(date_field in pg_field.lower() for date_field in ['date', 'created', 'updated', 'joined', 'login']):
                try:
                    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except (ValueError, AttributeError) as e:
                    logger.error(f"Failed to parse date {value} for field {pg_field}: {str(e)}")
                    continue
            transformed_data[ch_field] = value

        # Add ETL timestamp
        transformed_data['etl_updated_at'] = datetime.now()

        # Prepare columns and values for insert
        columns = list(transformed_data.keys())
        values = [transformed_data[col] for col in columns]

        # Insert into ClickHouse
        try:
            query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES"
            logger.info(f"Executing query: {query}")
            logger.info(f"Values: {values}")
            self.clickhouse_client.execute(query, [values])
            logger.info(f"Successfully inserted data into {table}")
        except Exception as e:
            logger.error(f"Failed to insert data into {table}: {str(e)}")
            raise

    def run(self):
        # Subscribe to all relevant topics
        topics = [f'postgres.public.{table}' for table in TABLE_MAPPINGS.keys()]
        self.consumer.subscribe(topics)
        logger.info(f"Subscribed to topics: {topics}")

        try:
            while True:
                msg = self.consumer.poll(timeout=1.0)
                if msg is None:
                    logger.debug("No message received within timeout")
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.debug(f"Reached end of partition for topic {msg.topic()}")
                        continue
                    else:
                        logger.error(f"Kafka error: {msg.error()}")
                        break

                try:
                    # Проверяем, не обрабатывали ли мы уже это сообщение
                    if self._is_message_processed(msg.topic(), msg.partition(), msg.offset()):
                        logger.info(f"Skipping already processed message: topic={msg.topic()}, partition={msg.partition()}, offset={msg.offset()}")
                        self.consumer.commit(msg)
                        continue

                    logger.info(f"Processing new message from topic {msg.topic()}, partition {msg.partition()}, offset {msg.offset()}")
                    self.process_message(msg)
                    
                    # Отмечаем сообщение как обработанное
                    self._mark_message_processed(msg.topic(), msg.partition(), msg.offset())
                    
                    # Коммитим offset только после успешной обработки сообщения
                    self.consumer.commit(msg)
                    logger.info(f"Committed offset for topic {msg.topic()}, partition {msg.partition()}, offset {msg.offset()}")
                except Exception as e:
                    logger.error(f"Failed to process message: {str(e)}")
                    # В случае ошибки не коммитим offset, чтобы попробовать обработать сообщение позже
                    continue

        except KeyboardInterrupt:
            logger.info("Stopping ETL processor...")
        finally:
            self.consumer.close()
            self.clickhouse_client.disconnect()

if __name__ == "__main__":
    # Wait for Kafka to be ready
    logger.info("Waiting for Kafka to be ready...")
    
    def wait_for_topics():
        admin_client = AdminClient({'bootstrap.servers': KAFKA_CONFIG['bootstrap.servers']})
        expected_topics = [f'postgres.public.{table}' for table in TABLE_MAPPINGS.keys()]
        
        while True:
            try:
                # Get list of topics
                metadata = admin_client.list_topics(timeout=10)
                existing_topics = set(metadata.topics.keys())
                
                # Check if all expected topics exist
                missing_topics = set(expected_topics) - existing_topics
                if not missing_topics:
                    logger.info("All required topics are available!")
                    return True
                
                logger.info(f"Waiting for topics to be created. Missing topics: {missing_topics}")
                time.sleep(5)
            except Exception as e:
                logger.error(f"Error checking topics: {str(e)}")
                time.sleep(5)
    
    # Wait for topics to be created
    wait_for_topics()
    
    processor = ETLProcessor()
    processor.run() 