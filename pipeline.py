import os
import subprocess
from dotenv import load_dotenv
import snowflake.connector
import pandas as pd

load_dotenv()

ACC = os.getenv("SNOWFLAKE_ACCOUNT")
USR = os.getenv("SNOWFLAKE_USER")
PWD = os.getenv("SNOWFLAKE_PASSWORD")
ROL = os.getenv("SNOWFLAKE_ROLE")
WH  = os.getenv("SNOWFLAKE_WAREHOUSE")
DB  = os.getenv("SNOWFLAKE_DATABASE")
SC  = os.getenv("SNOWFLAKE_SCHEMA")

def sf_conn():
    return snowflake.connector.connect(
        account=ACC, user=USR, password=PWD,
        role=ROL, warehouse=WH, database=DB, schema=SC
    )

def run(cmd):
    print(f"\n$ {' '.join(cmd)}")
    subprocess.check_call(cmd)

def query_df(sql):
    with sf_conn() as con:
        cur = con.cursor()
        cur.execute(sql)
        cols = [c[0] for c in cur.description]
        rows = cur.fetchall()
        return pd.DataFrame(rows, columns=cols)

def main():
    # 1) Make sure context exists (idempotent)
    with sf_conn() as con:
        cur = con.cursor()
        cur.execute(f"CREATE WAREHOUSE IF NOT EXISTS {WH}")
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB}")
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {SC}")

    # 2) dbt: load the CSV as a table
    run(["dbt", "seed"])

    # 3) dbt: build models (stg_orders, customer_order_counts)
    run(["dbt", "run"])

    print("\n== Current customer_order_counts ==")
    print(query_df("select * from customer_order_counts").to_string(index=False))

    # 4) Simulate new data arriving (Python → Snowflake)
    with sf_conn() as con:
        cur = con.cursor()
        cur.execute("""
            INSERT INTO raw_orders(order_id, customer_id, order_date, status, amount)
            VALUES (5, 101, '2024-03-01', 'shipped', 12.34)
        """)

    # 5) Re-run dbt to recompute aggregates
    run(["dbt", "run"])

    print("\n== After new row, customer_order_counts ==")
    print(query_df("select * from customer_order_counts").to_string(index=False))

if __name__ == "__main__":
    main()
