import os
import redis
import psycopg2
from flask import Flask, jsonify

app = Flask(__name__)

# Подключение к Redis
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=6379,
    decode_responses=True
)

# Подключение к PostgreSQL
def get_db():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DB", "appdb"),
        user=os.getenv("POSTGRES_USER", "appuser"),
        password=os.getenv("POSTGRES_PASSWORD", "apppass")
    )

# Создаём таблицу если не существует
def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY DEFAULT 1,
            count INTEGER DEFAULT 0
        )
    """)
    cur.execute("""
        INSERT INTO visits (id, count)
        VALUES (1, 0)
        ON CONFLICT (id) DO NOTHING
    """)
    conn.commit()
    cur.close()
    conn.close()

@app.route("/")
def index():
    # Проверяем кэш
    cached = redis_client.get("visit_count")
    if cached:
        return f"Визитов: {cached} (из кэша)"

    # Кэша нет — идём в БД
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE visits SET count = count + 1 WHERE id = 1 RETURNING count")
    count = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    # Сохраняем в кэш на 10 секунд
    redis_client.setex("visit_count", 10, count)

    return f"Визитов: {count} (из БД)"

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
