#!/usr/bin/env python3
"""Tiny local relay between PicoClaw and the Anthropic API that drops `temperature`.

PicoClaw (v0.3.1) always sends a temperature, but newer Claude models such as Sonnet 5.5
reject it ("`temperature` is deprecated for this model"). PicoClaw's api_base points here
(http://127.0.0.1:8787/v1); every request is forwarded unchanged to api.anthropic.com
except that JSON bodies lose their `temperature` field. Responses, including streamed
(SSE) ones, are relayed as they arrive. Listens on localhost only; the API key just
passes through in the request headers and is never logged.
"""

import http.client
import json
import ssl
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LISTEN = ("127.0.0.1", 8787)
UPSTREAM = "api.anthropic.com"
DROP_FIELDS = ("temperature",)
HOP_BY_HOP = {"connection", "keep-alive", "transfer-encoding", "content-length", "host",
              "proxy-connection", "te", "trailer", "upgrade", "accept-encoding"}


class Relay(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"  # close-delimited responses: simple and stream-friendly

    def _forward(self):
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        if body and "json" in (self.headers.get("Content-Type") or ""):
            try:
                data = json.loads(body)
                if isinstance(data, dict) and any(data.pop(f, None) is not None for f in DROP_FIELDS):
                    body = json.dumps(data).encode()
            except ValueError:
                pass  # not JSON after all: forward as-is
        headers = {k: v for k, v in self.headers.items() if k.lower() not in HOP_BY_HOP}
        headers["Content-Length"] = str(len(body))
        conn = http.client.HTTPSConnection(UPSTREAM, timeout=300, context=ssl.create_default_context())
        try:
            conn.request(self.command, self.path, body=body, headers=headers)
            resp = conn.getresponse()
            self.send_response(resp.status, resp.reason)
            for k, v in resp.getheaders():
                if k.lower() not in HOP_BY_HOP:
                    self.send_header(k, v)
            self.end_headers()
            while chunk := resp.read1(4096):  # relay as it arrives, so streaming stays live
                self.wfile.write(chunk)
                self.wfile.flush()
        except OSError as e:
            self.send_error(502, f"upstream error: {e.__class__.__name__}")
        finally:
            conn.close()

    do_POST = do_GET = _forward

    def log_message(self, fmt, *args):
        print(f"{self.command} {self.path} -> {args[1] if len(args) > 1 else ''}", flush=True)


if __name__ == "__main__":
    print(f"claude-param-proxy on http://{LISTEN[0]}:{LISTEN[1]} -> https://{UPSTREAM}", flush=True)
    ThreadingHTTPServer(LISTEN, Relay).serve_forever()
