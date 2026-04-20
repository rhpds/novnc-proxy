FROM registry.access.redhat.com/ubi9/python-311:latest

USER root

# Install Python deps + noVNC
RUN pip install websockify aiohttp aiohttp-jinja2 && \
    curl -fsSL https://github.com/novnc/noVNC/archive/refs/tags/v1.4.0.tar.gz | \
    tar xz -C /usr/share && \
    mv /usr/share/noVNC-1.4.0 /usr/share/novnc && \
    ln -s /usr/share/novnc/vnc.html /usr/share/novnc/index.html

# Install kubectl
RUN curl -fsSL "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    -o /usr/local/bin/kubectl && chmod +x /usr/local/bin/kubectl

COPY proxy.py /usr/local/bin/proxy.py

EXPOSE 8080

# Start kubectl proxy in background, then run the VNC WebSocket proxy
CMD ["/bin/sh", "-c", "kubectl proxy --port=8001 --address=127.0.0.1 & sleep 3 && python3 /usr/local/bin/proxy.py"]
