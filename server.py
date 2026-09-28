"""
MCP server: restart a specific pod by name in the 'web' namespace.

Uses the local kubeconfig (Docker Desktop's 'docker-desktop' context by default)
via the official `kubernetes` Python client.

Run:
    pip install "mcp[cli]" kubernetes
    python server.py
"""

import logging
from typing import Any

from kubernetes import client, config
from kubernetes.client.rest import ApiException
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("k8s-restart-mcp")

# Fixed scope: only this namespace is ever touched.
NAMESPACE = "web"

mcp = FastMCP("k8s-pod-restart")


def _load_k8s_client() -> client.CoreV1Api:
    """Load kubeconfig, preferring the docker-desktop context if present."""
    try:
        config.load_kube_config(context="docker-desktop")
        logger.info("Loaded kubeconfig context 'docker-desktop'")
    except Exception:
        # Fall back to whatever the current context is.
        config.load_kube_config()
        logger.info("Loaded default kubeconfig context")
    return client.CoreV1Api()


@mcp.tool()
def list_pods() -> str:
    """List all pod names currently running in the 'web' namespace.

    Use this first to find the exact pod name before calling restart_pod.
    """
    v1 = _load_k8s_client()
    try:
        pods = v1.list_namespaced_pod(namespace=NAMESPACE)
    except ApiException as e:
        return f"Error listing pods in namespace '{NAMESPACE}': {e.reason}"

    if not pods.items:
        return f"No pods found in namespace '{NAMESPACE}'."

    lines = [f"Pods in namespace '{NAMESPACE}':"]
    for pod in pods.items:
        status = pod.status.phase
        lines.append(f"- {pod.metadata.name} ({status})")
    return "\n".join(lines)


@mcp.tool()
def restart_pod(pod_name: str) -> str:
    """Restart a specific pod by name in the 'web' namespace.

    This deletes the named pod. If it is managed by a Deployment,
    ReplicaSet, or StatefulSet, Kubernetes will automatically recreate
    it. If the pod is standalone (not managed by a controller), it will
    NOT come back on its own.

    Args:
        pod_name: The exact name of the pod to restart, e.g. 'web-abc123-xyz'.
    """
    v1 = _load_k8s_client()

    # Confirm the pod exists in the allowed namespace before deleting.
    try:
        v1.read_namespaced_pod(name=pod_name, namespace=NAMESPACE)
    except ApiException as e:
        if e.status == 404:
            return (
                f"Pod '{pod_name}' not found in namespace '{NAMESPACE}'. "
                f"Call list_pods to see available pod names."
            )
        return f"Error checking pod '{pod_name}': {e.reason}"

    try:
        v1.delete_namespaced_pod(name=pod_name, namespace=NAMESPACE)
    except ApiException as e:
        return f"Error restarting pod '{pod_name}': {e.reason}"

    return (
        f"Pod '{pod_name}' in namespace '{NAMESPACE}' has been deleted. "
        f"If it's managed by a Deployment/ReplicaSet/StatefulSet, a new "
        f"pod will be created automatically. Call list_pods shortly to verify."
    )


if __name__ == "__main__":
    mcp.run()
