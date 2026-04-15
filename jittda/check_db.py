
import asyncio
import os
import json
import uuid
import psycopg

async def check_data():
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/jittda")
    target_job_id = "4aa88308-5c8e-4ccd-9a16-05e09bc544d9"
    target_email = "maxman306@gmail.com"
    
    print(f"Connecting to DB...")
    try:
        async with await psycopg.AsyncConnection.connect(db_url) as conn:
            # 1. Check Job
            print(f"Checking Job ID: {target_job_id}")
            row = await conn.execute(
                "SELECT id, user_id, status, created_at FROM jobs WHERE id = %s::uuid",
                (target_job_id,)
            )
            job = await row.fetchone()
            if job:
                print(f"FOUND JOB: id={job[0]}, user_id={job[1]}, status={job[2]}, created_at={job[3]}")
            else:
                print(f"JOB NOT FOUND: {target_job_id}")
            
            # 2. Check User
            print(f"Checking User Email: {target_email}")
            row = await conn.execute(
                "SELECT id, email, name FROM users WHERE email = %s",
                (target_email,)
            )
            user = await row.fetchone()
            if user:
                print(f"FOUND USER: id={user[0]}, email={user[1]}, name={user[2]}")
            else:
                print(f"USER NOT FOUND: {target_email}")
                
    except Exception as e:
        print(f"Error connecting to DB: {e}")

if __name__ == "__main__":
    asyncio.run(check_data())
