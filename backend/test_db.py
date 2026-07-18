import asyncio
import asyncpg
import ssl

async def test():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        conn = await asyncpg.connect(
            user='postgres.jcyffwpfdurxyypfqmqg',
            password='Assam$786[]',
            host='aws-0-ap-southeast-2.pooler.supabase.com',
            port=6543,
            database='postgres',
            ssl=ctx,
            statement_cache_size=0,
        )
        val = await conn.fetchval('SELECT 1')
        print(f"SUCCESS: {val}")
        await conn.close()
    except Exception as e:
        print(f"FAILED: {e}")

asyncio.run(test())
