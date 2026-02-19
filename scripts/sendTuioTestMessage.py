import json
import time

webserverDAT = op.WebServer.op('webserver1')

# Mock frame metadata
ts = time.time()
frameId = int(ts * 1000) & 0xFFFFFFFF
oscTime = str(int(ts * (2**32)))
dim = (1080 << 16) | 1920  # 1920x1080 sensor
source = "sendTuioTestMessage"

# Mock touch IDs
ptrId = 1
symId = 2

messages = [
	{"address": "/tuio2/frm", "args": [frameId, oscTime, dim, source]},
	{"address": "/tuio2/ptr", "args": [ptrId, 0, 0, 0.5, 0.5, 0.0, 0.0, 0.01, 0.0]},
	{"address": "/tuio2/sym", "args": [symId, 0, 0, "sxm", "test-device-uuid"]},
	{"address": "/tuio2/alv", "args": [ptrId, symId]},
]

for msg in messages:
	msgJson = json.dumps(msg)
	for client in webserverDAT.webSocketConnections:
		webserverDAT.webSocketSendText(msgJson, client)

debug(f"[sendTuioTest] sent {len(messages)} messages to {len(webserverDAT.webSocketConnections)} clients")
