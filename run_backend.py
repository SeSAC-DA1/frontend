#!/usr/bin/env python3
"""
CarFin AI Backend Server Launcher
"""
import os
import sys
import uvicorn
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """Start the CarFin AI FastAPI backend server"""

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    # Configuration
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    reload = os.environ.get("ENVIRONMENT", "development") == "development"

    logger.info(f"Starting CarFin AI Backend Server on {host}:{port}")
    logger.info(f"Reload mode: {reload}")

    # Start server
    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()