# me - this DAT.
# webServerDAT - the connected Web Server DAT
# request - A dictionary of the request fields
# response - A dictionary defining the response

import json
import tdu
from pathlib import Path

# Return the response dictionary.
# Serve the index.html/js file and any other files in the webroot.
def onHTTPRequest(webServerDAT, request, response):
	webroot = parent().par.Webroot.eval()
	uri = f"{webroot}{request['uri']}"
	
	if request['uri'] == '/':
		file_path = Path(f"{uri}index.html")
		response['statusCode'] = 200
		response['statusReason'] = 'OK'
		response['data'] = file_path.read_text(encoding='UTF-8')
	
	else:
		file_path = Path(uri)
		if file_path.is_file():
			response['statusCode'] = 200
			response['statusReason'] = 'OK'
			suffix = file_path.suffix
			if suffix in ['.jpg', '.jpeg', '.png', '.svg', '.gif', '.mp4']:
				response['data'] = file_path.read_bytes()
				if suffix in ['.jpg', '.jpeg']:
					response['Content-Type'] = 'image/jpg'
				elif suffix == '.png':
					response['Content-Type'] = 'image/png'
				elif suffix == '.svg':
					response['Content-Type'] = 'image/svg+xml'
				elif suffix == '.gif':
					response['Content-Type'] = 'image/gif'
			elif suffix in ['.woff', '.woff2', '.ttf', '.otf', '.eot']:
				response['data'] = file_path.read_bytes()
				if suffix == '.woff':
					response['Content-Type'] = 'font/woff'
				elif suffix == '.woff2':
					response['Content-Type'] = 'font/woff2'
				elif suffix == '.ttf':
					response['Content-Type'] = 'font/ttf'
				elif suffix == '.otf':
					response['Content-Type'] = 'font/otf'
				elif suffix == '.eot':
					response['Content-Type'] = 'application/vnd.ms-fontobject'
			else:
				response['data'] = file_path.read_text(encoding='UTF-8')
				if suffix == '.js':
					response['Content-Type'] = 'text/javascript'
		else:
			response['statusCode'] = 404
			response['statusReason'] = 'Not Found'

	return response

def broadcast(webServerDAT, msgJson):
	"""Send a message to all connected WebSocket clients."""
	connections = webServerDAT.webSocketConnections
	debug(f"[broadcast] {len(connections)} clients connected: {list(connections)}")
	for client in connections:
		debug(f"[broadcast] Sending to client {client}: {msgJson[:200]}")
		webServerDAT.webSocketSendText(msgJson, client)
	debug(f"[broadcast] Done sending to {len(connections)} clients")

def onWebSocketOpen(webServerDAT, client):
	all_clients = list(webServerDAT.webSocketConnections)
	debug(f"[WS] client connected: {client}")
	debug(f"[WS] Total clients now: {len(all_clients)} -> {all_clients}")
	op('table_clients').appendRow([client, 10])
	return

def onWebSocketClose(webServerDAT, client):
	debug(f"[WS] client disconnected: {client}")
	tbl = op('table_clients')
	if tbl.row(client):
		tbl.deleteRow(client)
	remaining = list(webServerDAT.webSocketConnections)
	debug(f"[WS] Remaining clients: {len(remaining)} -> {remaining}")
	return

def onWebSocketReceiveText(webServerDAT, client, data):
	debug(f"[WS] received TEXT from {client}: {data[:200]}")
	# Echo back for testing (uncomment to enable)
	# webServerDAT.webSocketSendText(data, client)
	return

def sendToClient(webServerDAT, client, msgJson):
	"""Send a message to a specific client with debug logging."""
	debug(f"[sendToClient] Sending to {client}: {msgJson[:200]}")
	webServerDAT.webSocketSendText(msgJson, client)
	debug(f"[sendToClient] Sent successfully to {client}")


def onWebSocketReceiveBinary(webServerDAT, client, data):
	return

def onServerStart(webServerDAT):
	debug("[WS] Server started")
	op('table_clients').clear(keepFirstRow=True)
	return

def onServerStop(webServerDAT):
	debug("[WS] Server stopped")
	op('table_clients').clear(keepFirstRow=True)
	return

def listClients(webServerDAT):
	"""Call this to see all connected clients. Usage: op('callbacks').module.listClients(op('webserver1'))"""
	clients = list(webServerDAT.webSocketConnections)
	debug(f"[listClients] {len(clients)} connected: {clients}")
	return clients

def testBroadcast(webServerDAT, message="Hello from TD"):
	"""Test broadcast to all clients. Usage: op('callbacks').module.testBroadcast(op('webserver1'), 'test')"""
	msgJson = json.dumps({"address": "/debug/test", "args": [message, str(absTime.frame)]})
	debug(f"[testBroadcast] Broadcasting: {msgJson}")
	broadcast(webServerDAT, msgJson)