#!/usr/bin/env python3
"""
============================================================
MONEY MACHINE AI - WEBHOOK BRIDGE SERVER
============================================================
THE SPINE: n8n Cloud → Local Python → Back to Cloud

This Flask server receives webhooks from n8n Cloud and:
1. Executes the Money Machine Python pipeline
2. Returns JSON results
3. Enables distributed orchestration

Endpoints:
    POST /run-job     - Execute any job (shorts, longform, etc.)
    GET  /health      - System health check
    POST /webhook     - Generic webhook receiver
    GET  /status/:id  - Check job status

Run:
    python webhook_bridge.py --port 5000
============================================================
"""

import os
import sys
import json
import asyncio
import argparse
import uuid
import threading
from pathlib import Path
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from functools import wraps

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env", override=True)

# Import job executor
from workflows.run_job import JobExecutor

app = Flask(__name__)

# Job tracking
JOBS = {}
LOGS_DIR = PROJECT_ROOT / "data" / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# AUTHENTICATION (Optional)
# ============================================================

def require_auth(f):
    """Optional API key authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = os.getenv("WEBHOOK_API_KEY")
        if api_key:
            provided_key = request.headers.get("X-API-Key") or request.args.get("api_key")
            if provided_key != api_key:
                return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


# ============================================================
# ENDPOINTS
# ============================================================

@app.route("/health", methods=["GET"])
def health():
    """System health check."""
    executor = JobExecutor()
    result = executor._execute_health({})
    return jsonify(result)


@app.route("/run-job", methods=["POST"])
@require_auth
def run_job():
    """
    Execute a Money Machine job.
    
    Expected POST body:
    {
        "job_id": "optional-uuid",
        "mode": "shorts|longform|replicate|analytics|health",
        "topic": "optional topic override",
        "script": "optional pre-generated script",
        "visual_intent": "power_finance|tech_disrupt|etc",
        "force_upload": true,
        "elite": true,
        "async": false  // If true, returns immediately with job_id
    }
    """
    try:
        payload = request.get_json() or {}
        job_id = payload.get("job_id", uuid.uuid4().hex[:12])
        payload["job_id"] = job_id
        
        # Async mode: Run in background, return immediately
        if payload.get("async"):
            JOBS[job_id] = {"status": "PENDING", "started": datetime.now(timezone.utc).isoformat()}
            
            def run_async():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                executor = JobExecutor()
                result = loop.run_until_complete(executor.execute(payload))
                JOBS[job_id] = result
                loop.close()
            
            thread = threading.Thread(target=run_async)
            thread.start()
            
            return jsonify({
                "status": "ACCEPTED",
                "job_id": job_id,
                "check_status": f"/status/{job_id}"
            })
        
        # Sync mode: Wait for completion
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        executor = JobExecutor()
        result = loop.run_until_complete(executor.execute(payload))
        loop.close()
        
        JOBS[job_id] = result
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"status": "FAILED", "error": str(e)}), 500


@app.route("/status/<job_id>", methods=["GET"])
def job_status(job_id):
    """Check status of a job."""
    if job_id in JOBS:
        return jsonify(JOBS[job_id])
    return jsonify({"status": "NOT_FOUND", "job_id": job_id}), 404


@app.route("/webhook", methods=["POST"])
@require_auth
def webhook():
    """Generic webhook receiver for n8n."""
    
    payload = request.get_json() or {}
    
    # Log webhook
    log_file = LOGS_DIR / f"webhooks_{datetime.now().strftime('%Y%m%d')}.log"
    with open(log_file, "a") as f:
        f.write(f"[{datetime.now().isoformat()}] {json.dumps(payload)}\n")
    
    # Determine action based on payload
    action = payload.get("action", "run-job")
    
    if action == "run-job":
        return run_job()
    elif action == "health":
        return health()
    else:
        return jsonify({"received": True, "action": action, "payload": payload})


@app.route("/shorts", methods=["POST"])
@require_auth
def shorts():
    """Shortcut endpoint for shorts mode."""
    payload = request.get_json() or {}
    payload["mode"] = "shorts"
    request._cached_json = (payload, True)
    return run_job()


@app.route("/longform", methods=["POST"])
@require_auth
def longform():
    """Shortcut endpoint for longform mode."""
    payload = request.get_json() or {}
    payload["mode"] = "longform"
    request._cached_json = (payload, True)
    return run_job()


@app.route("/analytics", methods=["GET"])
def analytics():
    """Get AAVE analytics."""
    executor = JobExecutor()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(executor.execute({"mode": "analytics"}))
    loop.close()
    return jsonify(result)


@app.route("/topics", methods=["GET"])
def topics():
    """Get current topic pool with weights."""
    try:
        from engines.aave_engine import AAVEEngine
        aave = AAVEEngine()
        return jsonify({
            "topics": aave.get_topic_weights(),
            "count": len(aave.get_topic_weights())
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def index():
    """Root endpoint with API documentation."""
    return jsonify({
        "name": "Money Machine AI - Webhook Bridge",
        "version": "1.0.0",
        "endpoints": {
            "POST /run-job": "Execute a job (shorts, longform, replicate, analytics, health)",
            "GET /health": "System health check",
            "GET /status/<job_id>": "Check job status",
            "POST /webhook": "Generic webhook receiver",
            "POST /shorts": "Shortcut for shorts mode",
            "POST /longform": "Shortcut for longform mode",
            "GET /analytics": "Get AAVE analytics",
            "GET /topics": "Get topic pool with weights"
        },
        "status": "RUNNING"
    })


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Money Machine Webhook Bridge")
    parser.add_argument("--port", type=int, default=5000, help="Port to run on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()
    
    print(f"""
============================================================
MONEY MACHINE AI - WEBHOOK BRIDGE
============================================================
Server running at: http://{args.host}:{args.port}
Health check: http://localhost:{args.port}/health
Run job: POST http://localhost:{args.port}/run-job
============================================================
""")
    
    app.run(host=args.host, port=args.port, debug=args.debug)
