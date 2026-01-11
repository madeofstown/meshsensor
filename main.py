"""
MeshSensor Main Entry Point
Orchestrates listener service and web dashboard.
"""

import subprocess
import threading
import sys
import signal
import time
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Commands to run
LISTENER_CMD = ["python", "listener_service.py"]
DASHBOARD_CMD = ["python", "app.py"]

# Global process references
listener_proc = None
dashboard_proc = None


def stream_output(prefix, process):
    """Stream process output to console."""
    try:
        for line in process.stdout:
            sys.stdout.write(f"[{prefix}] {line.decode()}")
        sys.stdout.flush()
    except Exception as e:
        logger.debug(f"Error streaming output from {prefix}: {e}")


def shutdown(signum=None, frame=None):
    """Graceful shutdown of both services."""
    global listener_proc, dashboard_proc
    
    logger.info("Shutting down MeshSensor services...")
    
    # Terminate processes
    if listener_proc:
        try:
            listener_proc.terminate()
            listener_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning("Listener service did not terminate gracefully, killing...")
            listener_proc.kill()
    
    if dashboard_proc:
        try:
            dashboard_proc.terminate()
            dashboard_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning("Dashboard service did not terminate gracefully, killing...")
            dashboard_proc.kill()
    
    logger.info("MeshSensor services stopped")
    sys.exit(0)


def main():
    """Start all services."""
    global listener_proc, dashboard_proc
    
    logger.info("=" * 70)
    logger.info("MeshSensor Starting")
    logger.info("=" * 70)
    logger.info("Dashboard: http://localhost:5000")
    logger.info("API: http://localhost:5001")
    logger.info("=" * 70)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    
    try:
        # Start listener service (backend)
        logger.info("Starting listener service...")
        listener_proc = subprocess.Popen(
            LISTENER_CMD,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        listener_thread = threading.Thread(
            target=stream_output,
            args=("Listener", listener_proc),
            daemon=True
        )
        listener_thread.start()
        
        # Give listener a moment to start
        time.sleep(1)
        
        # Start dashboard (frontend)
        logger.info("Starting dashboard...")
        dashboard_proc = subprocess.Popen(
            DASHBOARD_CMD,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        dashboard_thread = threading.Thread(
            target=stream_output,
            args=("Dashboard", dashboard_proc),
            daemon=True
        )
        dashboard_thread.start()
        
        logger.info("All services started successfully")
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if listener_proc and listener_proc.poll() is not None:
                logger.error(f"Listener service crashed with code {listener_proc.returncode}")
            
            if dashboard_proc and dashboard_proc.poll() is not None:
                logger.error(f"Dashboard service crashed with code {dashboard_proc.returncode}")
    
    except KeyboardInterrupt:
        shutdown()
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        shutdown()


if __name__ == "__main__":
    main()
