"""Start all three OzAgriMate backend services in one terminal for the demonstration.

    python run_all.py        (Windows: py -3 run_all.py)

Each service keeps its own composition root, port and in-memory state, exactly as
when started individually; this launcher only runs them side by side. It does not
add an API gateway, broker or shared database (none is required by A4).
"""
import argparse
import threading
from services.farm_management.app import create_server as farm_server
from services.telemetry.app import create_server as telemetry_server
from services.irrigation_alerts.app import create_server as irrigation_alerts_server

SERVICES = [  # (container name, factory, default port, endpoints served)
    ("Farm Management", farm_server, 8001,
     ["POST /farms", "GET /farms/{farmId}"]),
    ("Telemetry", telemetry_server, 8002,
     ["POST /farms/{farmId}/telemetry", "GET /farms/{farmId}/telemetry"]),
    ("Irrigation and Alerts", irrigation_alerts_server, 8003,
     ["POST /farms/{farmId}/irrigation-requests", "PUT /farms/{farmId}/irrigation-requests/{requestId}",
      "POST /farms/{farmId}/alert-rules", "DELETE /farms/{farmId}/alert-rules/{ruleId}"]),
]


def start_all(host="127.0.0.1", ports=None):
    """Start every service on a daemon thread. Returns [(name, server, endpoints)]."""
    started = []
    for i, (name, factory, default_port, endpoints) in enumerate(SERVICES):
        port = default_port if ports is None else ports[i]
        server = factory(host=host, port=port)
        threading.Thread(target=server.serve_forever, name=name, daemon=True).start()
        started.append((name, server, endpoints))
    return started


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.parse_args()
    running = start_all()
    print("OzAgriMate local demonstration - in-memory data resets on restart. Ctrl+C to stop.\n", flush=True)
    for name, server, endpoints in running:
        print(f"{name:<22} http://127.0.0.1:{server.server_address[1]}", flush=True)
        for endpoint in endpoints:
            print(f"    {endpoint}", flush=True)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        for _, server, _ in running:
            server.shutdown()
            server.server_close()
