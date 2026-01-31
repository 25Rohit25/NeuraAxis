import asyncio
import os
import sys

# Make sure we can import from app if needed, though this is standalone script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not set")
    # Setup dummy for generation verification if env missing
    DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/neuraxis"


async def check_database_performance():
    print(f"Connecting to {DATABASE_URL}...")
    try:
        engine = create_async_engine(DATABASE_URL)
        async with engine.connect() as conn:
            # 1. Check Cache Hit Ratio (Should be > 99%)
            print("\n--- Cache Hit Ratio ---")
            res = await conn.execute(
                text("""
                SELECT sum(heap_blks_read) as heap_read, sum(heap_blks_hit)  as heap_hit,
                       sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as ratio
                FROM pg_statio_user_tables;
            """)
            )
            for row in res:
                print(f"Hit Ratio: {row.ratio:.4f}")

            # 2. Check Missing Indexes (High Seq Scans)
            print("\n--- Potential Missing Indexes (High Sequential Scans) ---")
            res = await conn.execute(
                text("""
                SELECT schemaname, relname, seq_scan, seq_tup_read, idx_scan, idx_tup_fetch
                FROM pg_stat_user_tables
                WHERE seq_scan > 100 -- Threshold
                ORDER BY seq_scan DESC
                LIMIT 10;
            """)
            )
            rows = res.fetchall()
            if not rows:
                print("No major continuous sequential scans detected.")
            for row in rows:
                print(
                    f"Table: {row.relname} | Seq Scans: {row.seq_scan} | Idx Scans: {row.idx_scan}"
                )

            # 3. Check Unused Indexes
            print("\n--- Unused Indexes (Overhead) ---")
            res = await conn.execute(
                text("""
                SELECT schemaname, relname, indexrelname, idx_scan
                FROM pg_stat_user_indexes
                WHERE idx_scan = 0 AND indexrelname NOT LIKE '%_pkey'
                ORDER BY relname LIMIT 10;
            """)
            )
            for row in res:
                print(f"Index: {row.indexrelname} (Table: {row.relname}) - 0 scans")

        await engine.dispose()
    except Exception as e:
        print(f"Error checking DB: {e}")


if __name__ == "__main__":
    asyncio.run(check_database_performance())
