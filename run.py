"""Launch Minerva in a native window (pywebview) or, failing that, your default browser."""
import sys
import threading
import time
import webbrowser

import server


def selftest():
    """Boot the server, hit the API and exit. Used by the build to prove the bundle works."""
    import json
    import urllib.request
    httpd = server.make_server(0)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{httpd.server_address[1]}"
    state = json.load(urllib.request.urlopen(base + "/api/state"))
    page = urllib.request.urlopen(base + "/").read()
    ok = len(state["sites"]) > 0 and b"Minerva" in page
    print("selftest", "ok" if ok else "FAILED", f"({len(state['sites'])} sites)")
    sys.exit(0 if ok else 1)


def main():
    if "--selftest" in sys.argv:
        selftest()
    httpd = server.make_server(0)
    port = httpd.server_address[1]
    url = f"http://127.0.0.1:{port}/"
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        import webview
    except Exception:
        webview = None
    if webview and "--browser" not in sys.argv:
        webview.create_window("Minerva", url, width=1480, height=940, min_size=(1120, 720),
                              background_color="#0B0F14", text_select=True)
        webview.start()
    else:
        print(f"Minerva running at {url}  (Ctrl+C to quit)")
        webbrowser.open(url)
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
