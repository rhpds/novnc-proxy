#!/usr/bin/env python3
"""
noVNC WebSocket proxy for KubeVirt VMs.
Serves noVNC UI and proxies VNC WebSocket connections via kubectl proxy.
"""
import asyncio
import os
import pathlib
from aiohttp import web, ClientSession, WSMsgType

NOVNC_PATH = pathlib.Path('/usr/share/novnc')
NAMESPACE = os.environ.get('NAMESPACE', '')
VM_NAME = os.environ.get('VM_NAME', 'rhel-podman')


async def vnc_ws(request):
    """Bridge noVNC WebSocket client to KubeVirt VNC API via kubectl proxy."""
    ns = NAMESPACE or request.match_info.get('namespace', '')
    vm = VM_NAME

    api_url = (
        f'ws://127.0.0.1:8001/apis/subresources.kubevirt.io/v1'
        f'/namespaces/{ns}/virtualmachineinstances/{vm}/vnc'
    )

    client_ws = web.WebSocketResponse()
    await client_ws.prepare(request)

    try:
        async with ClientSession() as session:
            async with session.ws_connect(api_url, protocols=['binary']) as server_ws:

                async def c2s():
                    async for msg in client_ws:
                        if msg.type == WSMsgType.BINARY:
                            await server_ws.send_bytes(msg.data)
                        elif msg.type == WSMsgType.TEXT:
                            await server_ws.send_str(msg.data)
                        elif msg.type in (WSMsgType.CLOSE, WSMsgType.ERROR):
                            break

                async def s2c():
                    async for msg in server_ws:
                        if msg.type == WSMsgType.BINARY:
                            await client_ws.send_bytes(msg.data)
                        elif msg.type == WSMsgType.TEXT:
                            await client_ws.send_str(msg.data)
                        elif msg.type in (WSMsgType.CLOSE, WSMsgType.ERROR):
                            break

                done, pending = await asyncio.wait(
                    [asyncio.ensure_future(c2s()), asyncio.ensure_future(s2c())],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()
    except Exception as e:
        print(f'VNC proxy error: {e}')

    return client_ws


app = web.Application()
app.router.add_get('/websockify', vnc_ws)
app.router.add_static('/', NOVNC_PATH)

if __name__ == '__main__':
    print('noVNC KubeVirt proxy starting on :8080')
    web.run_app(app, host='0.0.0.0', port=8080)
