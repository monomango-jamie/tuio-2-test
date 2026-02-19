import json

webserverDAT = parent().op('webserver1')
msg = json.dumps({"address": "/debug/ping", "args": ["test from TD", str(absTime.frame)]})
clients = webserverDAT.webSocketConnections
debug(f"[sendTest] {len(clients)} clients: {[repr(c) for c in clients]}")
for client in clients:
	try:
		webserverDAT.webSocketSendText(msg, client)
		debug(f"[sendTest] sent to {repr(client)}")
	except Exception as e:
		debug(f"[sendTest] ERROR sending to {repr(client)}: {e}")
