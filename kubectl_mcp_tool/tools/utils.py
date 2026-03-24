"""Shared utilities for kubectl-mcp-server tools."""

import logging
import subprocess
import json
from typing import Any, Dict, List

from ..k8s_config import _get_kubectl_context_args

logger = logging.getLogger("mcp-server")

def run_kubectl(args: List[str], context: str = "", timeout: int = 60) -> Dict[str, Any]:
    """Run kubectl command and return result.

    If a bearer token is available in the current request context,
    it is passed via the --token flag for per-user authentication.
    """
    from ..bearer_token import get_bearer_token

    token_args: List[str] = []
    bearer_token = get_bearer_token()
    if bearer_token:
        token_args = ["--token", bearer_token]
        logger.info("run_kubectl: injecting --token flag (token length=%d)", len(bearer_token))

    cmd = ["kubectl"] + _get_kubectl_context_args(context) + token_args + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return {"success": True, "output": result.stdout}
        return {"success": False, "error": result.stderr}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_resources(kind: str, namespace: str = "", context: str = "", label_selector: str = "") -> List[Dict]:
    """Get Kubernetes resources of a specific kind."""
    args = ["get", kind, "-o", "json"]
    if namespace:
        args.extend(["-n", namespace])
    else:
        args.append("-A")
    if label_selector:
        args.extend(["-l", label_selector])

    result = run_kubectl(args, context)
    if result["success"]:
        try:
            data = json.loads(result["output"])
            return data.get("items", [])
        except json.JSONDecodeError:
            return []
    return []
