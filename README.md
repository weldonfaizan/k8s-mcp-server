# k8s-pod-restart MCP server

Restarts a pod by name in the `web` namespace on your Docker Desktop
Kubernetes cluster. Exposes two tools:

- `list_pods()` — lists pod names + status in the `web` namespace
- `restart_pod(pod_name)` — deletes the named pod (its controller,
  e.g. a Deployment, recreates it)

## Setup

```bash
cd k8s-mcp-server
python -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Make sure Docker Desktop's Kubernetes is enabled and your kubeconfig
context is named `docker-desktop` (the default). Check with:

```bash
kubectl config get-contexts
```

## Run standalone (sanity check)

```bash
python server.py
```

This starts the server over stdio and waits for an MCP client to
connect — it won't print anything on its own, that's expected.

## Wire it into an MCP client

Add it to your client's MCP server config, e.g.:

```json
{
  "mcpServers": {
    "k8s-pod-restart": {
      "command": "/absolute/path/to/venv/bin/python",
      "args": ["/absolute/path/to/k8s-mcp-server/server.py"]
    }
  }
}
```

If your MCP client talks to LLM, it will discover
`list_pods` and `restart_pod` as callable tools and can invoke them
directly — no more manual `kubectl` needed.

## Safety notes

- Hardcoded to the `web` namespace only — the model can't restart
  pods anywhere else, even if it tries.
- `restart_pod` deletes the pod. If it's not managed by a
  Deployment/ReplicaSet/StatefulSet, it will NOT come back — verify
  with `list_pods` afterward.
- No bulk/"restart all" tool is included on purpose, to avoid an
  accidental wipe of the whole namespace from one bad prompt.
