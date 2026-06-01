import uvicorn
import os
from dotenv import load_dotenv
# this is the first file Python executes
# load the environment variables (API keys from the .env file
load_dotenv()

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
