FROM apache/spark:3.5.1-python3

USER root

# PostgreSQL JDBC driver for Spark ↔ Postgres via JDBC
RUN curl -fL -o /opt/spark/jars/postgresql-42.7.3.jar \
    https://jdbc.postgresql.org/download/postgresql-42.7.3.jar

# Our Spark defaults (path matches the official Apache Spark image layout)
COPY conf/spark-defaults.conf /opt/spark/conf/spark-defaults.conf

USER spark