# Start app

- `docker compose up`
- ждем debezium
- `curl -X POST -H "Content-Type: application/json" --data @debezium/postgres-connector.json http://localhost:8083/connectors`
- заполняем бдщку чем-то (можно смотреть логи etl): пробные покупки можно сразу в postgreSQL занести, используя [скрипт](./scripts/test_queries/02_load_test_data.sql)
- можно проверить топики в кафке и посмотреть таблицы в clickhouse:
  - список топиков: `docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list`
  - выбираем топик (postgres.public.users) и смотрим из него сообщения: `docker compose exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic postgres.public.users --from-beginning`
  - `docker compose exec clickhouse clickhouse-client --query "SELECT * FROM online_store.orders LIMIT 5;"`
- заходим в [grafana](http://localhost:3000/), открываем дашборды
