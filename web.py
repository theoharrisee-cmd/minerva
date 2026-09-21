"""Run Minerva as a hosted web app (Render, Fly, Railway, any Docker host).

Required environment:  MINERVA_PASSWORD   the password protecting everything
Optional:              PORT (default 8080), MINERVA_HOME (data folder, put it on a persistent disk),
                       ANTHROPIC_API_KEY, MINERVA_SECRET (cookie signing key; defaults to a hash of the password)"""
import os
import sys

if not os.environ.get("MINERVA_PASSWORD"):
    sys.exit("Refusing to start: set MINERVA_PASSWORD so the app is not open to the internet.")
os.environ.setdefault("MINERVA_HOSTED", "1")

import server  # noqa: E402

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    httpd = server.make_server(port, "0.0.0.0")
    print(f"Minerva listening on 0.0.0.0:{port}", flush=True)
    httpd.serve_forever()
