import asyncio
import time
import httpx

API_URL = "http://localhost:8000/api/v1"
CONCURRENCY = 20
TOTAL_REQUESTS = 100

async def fetch_health(client, i):
    try:
        start = time.time()
        resp = await client.get(f"{API_URL}/")
        duration = time.time() - start
        return {"id": i, "status": resp.status_code, "duration": duration}
    except Exception as e:
        return {"id": i, "status": 0, "error": str(e)}

async def main():
    print(f"Bắt đầu load test với {TOTAL_REQUESTS} requests, concurrency {CONCURRENCY}...")
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        tasks = []
        for i in range(TOTAL_REQUESTS):
            tasks.append(fetch_health(client, i))
            if len(tasks) >= CONCURRENCY:
                results = await asyncio.gather(*tasks)
                tasks = []
                # Print stats optionally
                
        if tasks:
             await asyncio.gather(*tasks)
             
    print(f"Hoàn thành trong {time.time() - start_time:.2f} giây")

if __name__ == "__main__":
    asyncio.run(main())
