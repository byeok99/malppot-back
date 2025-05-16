import sys
import uvicorn
from pathlib import Path
from malppot import create_app
from fastapi.staticfiles import StaticFiles
from malppot.utils.middleware import JWTMiddleware
from fastapi.middleware.cors import CORSMiddleware

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

app = create_app()

# app.add_middleware(JWTMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],                      # 모든 HTTP 메서드 허용
    allow_headers=["*"],                      # 모든 헤더 허용
)
# 임시
app.mount("/static", StaticFiles(directory=f"{PROJECT_ROOT}/malppot/static"), name="static")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)

# uvicorn malppot.main:app --host 0.0.0.0 --port 8000 --reload