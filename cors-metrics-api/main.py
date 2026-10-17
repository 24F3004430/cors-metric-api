
import time
import uuid

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware


ALLOWED_ORIGIN = "https://dash-1hhuh8.example.com"
EMAIL = "24f3004430@ds.study.iitm.ac.in"

app = FastAPI()


class RequestHeadersMiddleware:
    """Add request ID and processing time to every HTTP response."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.perf_counter()
        request_id = str(uuid.uuid4())

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                elapsed = time.perf_counter() - start_time

                headers = list(message.get("headers", []))
                headers.append(
                    (b"x-request-id", request_id.encode("ascii"))
                )
                headers.append(
                    (b"x-process-time", f"{elapsed:.6f}".encode("ascii"))
                )

                message["headers"] = headers

            await send(message)

        await self.app(scope, receive, send_with_headers)


# The outer middleware adds required headers even to CORS preflight errors.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["Content-Type"],
)

app.add_middleware(RequestHeadersMiddleware)


@app.get("/stats")
def get_stats(values: str = Query(...)):
    try:
        numbers = [int(value.strip()) for value in values.split(",")]
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="values must be comma-separated integers",
        )

    if not numbers or any(value == "" for value in values.split(",")):
        raise HTTPException(
            status_code=400,
            detail="Provide at least one integer",
        )

    return {
        "email": EMAIL,
        "count": len(numbers),
        "sum": sum(numbers),
        "min": min(numbers),
        "max": max(numbers),
        "mean": sum(numbers) / len(numbers),
    }


@app.get("/")
def home():
    return {"message": "CORS Metrics API is running"}
