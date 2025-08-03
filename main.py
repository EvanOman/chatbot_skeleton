import uvicorn
import os
from dotenv import load_dotenv
from src.main import app
from src.infrastructure.config.ports import PortConfig

# Load environment variables
load_dotenv()


def main():
    # Print port configuration on startup
    PortConfig.print_config()
    
    uvicorn.run(
        "src.main:app",
        host=PortConfig.APP_HOST,
        port=PortConfig.APP_PORT,
        reload=True,
    )


if __name__ == "__main__":
    main()
