"""Servidor HTTP auxiliar de saúde (opcional).

Não substitui o bot: serve apenas para plataformas de hospedagem que exigem
um serviço web respondendo em uma porta (ex.: plano gratuito do Render).
Desative com HEALTH_ENABLED=false.
"""

from __future__ import annotations

import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

logger = logging.getLogger(__name__)


class _Handler(BaseHTTPRequestHandler):
    server_version = "LinguaBotHealth/2.0"

    def do_GET(self) -> None:  # noqa: N802 - nome exigido pela stdlib
        if self.path in {"/", "/health", "/healthz"}:
            payload = json.dumps({"status": "ok", "service": "linguabot"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args) -> None:  # silencia o log padrão
        logger.debug("health: %s", args)


def start_health_server(port: int, host: str = "0.0.0.0") -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), _Handler)
    thread = threading.Thread(target=server.serve_forever, name="health-server", daemon=True)
    thread.start()
    logger.info("Servidor de saúde ouvindo em http://%s:%s", host, port)
    return server
