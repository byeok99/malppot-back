import sys
import uvicorn
from pathlib import Path
from malppot import create_app
from malppot.di.config import ConfigContainer

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

app = create_app()
config = ConfigContainer()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)

# uvicorn malppot.app:app --host 0.0.0.0 --port 8000 --reload