import json

webserverDAT = parent().op('webserver1')
msg = json.dumps({"address": "/debug/ping", "args": ["test from TD", str(absTime.frame)]})
for client in webserverDAT.webSocketConnections:
	webserverDAT.webSocketSendText(msg, client)
debug(f"[sendTest] sent to {len(webserverDAT.webSocketConnections)} clients: {msg}")
