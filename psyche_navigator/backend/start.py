"""
Application Entry Point for the Backend.

This is the first file Python executes. Loads environment variables
(API keys) from the .env file, then starts the FastAPI server with
Uvicorn on port 8000 with hot-reload enabled.
"""

import uvicorn
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
