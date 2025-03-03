import sys
import uvicorn
from pathlib import Path
from malppot import create_app
from fastapi.staticfiles import StaticFiles
from malppot.utils.middleware import JWTMiddleware

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

app = create_app()

app.add_middleware(JWTMiddleware)
# 임시
app.mount("/static", StaticFiles(directory=f"{PROJECT_ROOT}/malppot/static"), name="static")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)

# uvicorn malppot.main:app --host 0.0.0.0 --port 8000 --reload