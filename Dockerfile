FROM registry.access.redhat.com/ubi9/python-311:latest

USER root

RUN pip install websockify && \
    curl -fsSL https://github.com/novnc/noVNC/archive/refs/tags/v1.4.0.tar.gz | \
    tar xz -C /usr/share && \
    mv /usr/share/noVNC-1.4.0 /usr/share/novnc && \
    ln -s /usr/share/novnc/vnc.html /usr/share/novnc/index.html

EXPOSE 8080

# websockify serves noVNC UI and proxies WebSocket to localhost:5900
# (oc port-forward in sidecar container exposes VMI VNC there)
CMD ["websockify", "--web=/usr/share/novnc", "--heartbeat=30", "0.0.0.0:8080", "localhost:5900"]
