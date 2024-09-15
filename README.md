<<<<<<< HEAD
# Kafka_Youtube
=======
# Init Setting
1. To run this project, please run this command:

    **`cd <your project directory containing docker-compose.yaml file>`**

    **`docker-compose up -d`**
# Database Setup
## 1. Create Tables for Source Connector (MySQL)
To set up the necessary tables in MySQL for the source connector, follow these steps:
1. **Run the `create_tables.py` Script**  
   This script will create a database named `youtube` with two tables: `Channel` and `Video`.
2. **Table Structure:**
   - **`Channel` Table:**
     - **Primary Key (`PK`)**: `channel_id`
   - **`Video` Table:**
     - **Primary Key (`PK`)**: `video_id`
     - **Foreign Key (`FK`)**: `channel_id` (references the `Channel` table)

## 2. Create your own Youtube API key
Follow this [Video](https://www.youtube.com/watch?v=LLAZUTbc97I&pp=ygUOeW91dHViZSBhcGkgdjM%3D) to get your key

Then put your key as `API_KEY` in .env file

## 3. Start crawling data
Run the file `youtube_generator.py` to get top 100 game video (you can switch to any type of video you want by changing `type`)

## 4. Simulating real time Youtube data
1. **First, run the file `mysql_insert_data.py`**

    This file will insert data of 100 youtube videos as well as its channels to Mysql. Then it update the status(view,..) of 100 youtube videos as well as its channels by inserting new rows with different update_at
2. **Then uncomment all commented line bellow `if __name__ == '__main__':` because Video table has FK to Channel table**
3. **Rerun the file `mysql_insert_data.py` to get real time data**

# Kafka Connect Setup
This README provides instructions for setting up and using Kafka Connect with MySQL and PostgreSQL.
## 1. Wait for Kafka Connect to Start
### Run the following bash script to wait for Kafka Connect to start listening on localhost:
    bash -c ' \
    echo -e "\n\n=============\nWaiting for Kafka Connect to start listening on localhost ⏳\n=============\n"
    while [ $(curl -s -o /dev/null -w %{http_code} http://localhost:8083/connectors) -ne 200 ] ; do
      echo -e "\t" $(date) " Kafka Connect listener HTTP state: " $(curl -s -o /dev/null -w %{http_code} http://localhost:8083/connectors) " (waiting for 200)"
      sleep 5
    done
    echo -e $(date) "\n\n--------------\n\o/ Kafka Connect is ready! Listener HTTP state: " $(curl -s -o /dev/null -w %{http_code} http://localhost:8083/connectors) "\n--------------\n"
    '

## 2. Check Connector Availability and Status
### Check MySQL Debezium and JDBC Connector Source/Sink availability:
    curl -s localhost:8083/connector-plugins|jq '.[].class'|egrep 'JdbcSinkConnector|MySqlConnector|JdbcSourceConnector'

### Check connector status:
    curl -s "http://localhost:8083/connectors?expand=info&expand=status" | \
       jq '. | to_entries[] | [ .value.info.type, .key, .value.status.connector.state,.value.status.tasks[].state,.value.info.config."connector.class"]|join(":|:")' | \
       column -s : -t| sed 's/\"//g'| sort

### Show data with kafkacat (no Avro encryption):
    docker exec kafkacat kafkacat \
        -b broker:29092 \
        -t mysql-debezium-json-with-schema-hieuminh.youtube.Video \
        -C -o -10 -q | jq

### Show data with kafkacat (with Avro encryption):
    docker exec kafkacat kafkacat \
        -b broker:29092 \
        -r http://schema-registry:8081 \
        -t mysql-debezium-json-with-schema-hieuminh.youtube.Video \
        -C -o -10 -q | jq

### Check topics
    docker exec kafka-connect kafka-topics --list --bootstrap-server broker:29092

### Delete topic
    docker exec kafka-connect kafka-topics --delete --topic postgres-debezium.public.person --bootstrap-server broker:29092

### Pause the connector
    curl -X PUT http://localhost:8083/connectors/source-debezium-video-01/pause
    curl -X PUT http://localhost:8083/connectors/sink-jdbc-postgres-video-01/pause

### Resume the connector
    curl -X PUT http://localhost:8083/connectors/source-debezium-video-01/resume
    curl -X PUT http://localhost:8083/connectors/sink-jdbc-postgres-video-01/resume

### Delete the connector
    curl -X DELETE http://localhost:8083/connectors/source-debezium-video-01
    curl -X DELETE http://localhost:8083/connectors/sink-jdbc-postgres-video-01

## 3. Create MySQL Source Connectors
### Create source-debezium-video-01:
    curl -i -X POST -H "Accept:application/json" \
    -H  "Content-Type:application/json" http://localhost:8083/connectors/ \
    -d '{
      "name": "source-debezium-video-01",
      "config": {
            "connector.class": "io.debezium.connector.mysql.MySqlConnector",
            "database.hostname": "mysql",
            "database.port": "3306",
            "database.user": "debezium",
            "database.password": "dbz",
            "database.server.id": "43",
            "database.server.name": "hieuminh",
            "table.whitelist": "youtube.Video",
            "database.history.kafka.bootstrap.servers": "broker:29092",
            "database.history.kafka.topic": "dbhistory.demo" ,
            "decimal.handling.mode": "double",
            "include.schema.changes": "true",
            "value.converter": "org.apache.kafka.connect.json.JsonConverter",
            "value.converter.schemas.enable": "true",
            "key.converter": "org.apache.kafka.connect.json.JsonConverter",
            "key.converter.schemas.enable": "true",
            "transforms": "unwrap,addTopicPrefix",
            "transforms.unwrap.type": "io.debezium.transforms.ExtractNewRecordState",
            "transforms.addTopicPrefix.type":"org.apache.kafka.connect.transforms.RegexRouter",
            "transforms.addTopicPrefix.regex":"(.*)",
            "transforms.addTopicPrefix.replacement":"mysql-debezium-json-with-schema-$1"
       }
    }'

## 4. Create PostgreSQL Sink Connector
### Create a sink connector for PostgreSQL:
    curl -X POST http://localhost:8083/connectors -H "Content-Type: application/json" -d '{
          "name": "sink-jdbc-postgres-video-01",
          "config": {
            "connector.class": "io.confluent.connect.jdbc.JdbcSinkConnector",
            "tasks.max": "1",
            "topics": "mysql-debezium-json-with-schema-hieuminh.youtube.Video",
            "value.converter": "org.apache.kafka.connect.json.JsonConverter",
            "value.converter.schemas.enable": "true",
            "key.converter": "org.apache.kafka.connect.json.JsonConverter",
            "key.converter.schemas.enable": "true",
            "connection.url": "jdbc:postgresql://192.168.1.6:5433/postgres",
            "connection.user": "postgres",
            "connection.password": "26102002",
            "auto.create": "true",
            "auto.evolve":"true",
            "pk.mode":"none",
            "errors.tolerance": "all",
            "auto.offset.reset": "earliest",
            "transforms": "TimestampConverter",
            "transforms.TimestampConverter.type": "org.apache.kafka.connect.transforms.TimestampConverter$Value",
            "transforms.tsConverter.field": "update_at",
            "transforms.TimestampConverter.format": "yyyy-MM-dd",
            "transforms.TimestampConverter.target.type": "string",
            "table.name.format": "Video"
            }
          }'
          
## 5. Update Connector Configuration
### To update a connector configuration, use the following example command for postgres sink connector:
    curl -X PUT http://localhost:8083/connectors/sink-jdbc-postgres-video-01/config -H "Content-Type: application/json" -d '{
        "connector.class": "io.confluent.connect.jdbc.JdbcSinkConnector",
        "tasks.max": "1",
        "topics": "mysql-debezium-json-with-schema-hieuminh.youtube.Video",
        "value.converter": "org.apache.kafka.connect.json.JsonConverter",
        "value.converter.schemas.enable": "true",
        "key.converter": "org.apache.kafka.connect.json.JsonConverter",
        "key.converter.schemas.enable": "true",
        "connection.url": "jdbc:postgresql://192.168.1.6:5433/postgres",
        "connection.user": "postgres",
        "connection.password": "26102002",
        "auto.create": "true",
        "auto.evolve": "true",
        "pk.mode": "none",
        "errors.tolerance": "all",
        "auto.offset.reset": "earliest",
        "transforms": "TimestampConverter",
        "transforms.TimestampConverter.type": "org.apache.kafka.connect.transforms.TimestampConverter$Value",
        "transforms.TimestampConverter.field": "update_at",
        "transforms.TimestampConverter.target.type": "string",
        "transforms.TimestampConverter.unix.precision": "seconds",
        "table.name.format": "Video"
    }'
>>>>>>> 2c644a1 (Initial commit)
