import mysql.connector.pooling

from server import config

# Money is stored as integer cents (price_cents) specifically to avoid
# MySQL DECIMAL/NUMERIC columns coming back as decimal.Decimal, which needs
# explicit conversion before arithmetic downstream. mysql-connector-python
# returns INTEGER columns as plain Python ints, no conversion needed.
# If you add a column that genuinely needs decimal precision (ratings,
# measurements), convert Decimal -> float explicitly at the point you read
# it rather than storing money that way.
pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="booking_app_pool",
    pool_size=5,
    host=config.DB_HOST,
    port=config.DB_PORT,
    user=config.DB_USER,
    password=config.DB_PASSWORD,
    database=config.DB_NAME,
    autocommit=False,
)


def get_connection():
    return pool.get_connection()
