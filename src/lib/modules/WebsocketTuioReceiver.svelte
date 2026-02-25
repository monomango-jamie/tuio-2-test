<script lang="ts" module>
	import { TuioReceiver } from 'tuio-client';

	export class WebsocketTuioReceiver extends TuioReceiver {
		private readonly _url: string;
		private _ws: WebSocket | null = null;

		public onConnected: (() => void) | null = null;
		public onDisconnected: (() => void) | null = null;

		// Debug state
		public messageCount = $state(0);
		public lastMessageTime: Date | null = $state(null);
		public lastError: string | null = $state(null);
		public connectTime: Date | null = $state(null);
		private _readyState: number = $state(WebSocket.CLOSED);

		get url() {
			return this._url;
		}

		get readyState(): number {
			return this._readyState;
		}

		get readyStateLabel(): string {
			switch (this._readyState) {
				case WebSocket.CONNECTING:
					return 'CONNECTING';
				case WebSocket.OPEN:
					return 'OPEN';
				case WebSocket.CLOSING:
					return 'CLOSING';
				case WebSocket.CLOSED:
					return 'CLOSED';
				default:
					return 'UNKNOWN';
			}
		}

		constructor(host: string, port: number) {
			super();
			this._url = `ws://${host}:${port}`;
		}

		/** Send a raw string to TD — for debugging only */
		public sendTest(msg: string) {
			if (!this._ws || this._ws.readyState !== WebSocket.OPEN) {
				console.warn('[TuioReceiver] sendTest: socket not open');
				return;
			}
			console.log('[TuioReceiver] sendTest →', msg);
			this._ws.send(msg);
		}

		public connect() {
			console.log(`[TuioReceiver] Connecting to ${this._url}...`);
			this.lastError = null;
			this._readyState = WebSocket.CONNECTING;
			this._ws = new WebSocket(this._url);

			this._ws.onopen = () => {
				this._readyState = WebSocket.OPEN;
				this.connectTime = new Date();
				console.log(`[TuioReceiver] Connected to ${this._url}`);
				this.isConnected = true;
				this.onConnected?.();
			};

			this._ws.onclose = (e) => {
				this._readyState = WebSocket.CLOSED;
				console.warn(`[TuioReceiver] Disconnected (code=${e.code}, reason=${e.reason || 'none'})`);
				this.isConnected = false;
				if (e.code !== 1000) {
					this.lastError = `Closed with code ${e.code}: ${e.reason || 'no reason'}`;
				}
				this.onDisconnected?.();
			};

			this._ws.onerror = (e) => {
				const errMsg = `WebSocket error (check if server is running at ${this._url})`;
				console.error(`[TuioReceiver] ${errMsg}`, e);
				this.lastError = errMsg;
			};

			this._ws.onmessage = (event) => {
				this.messageCount++;
				this.lastMessageTime = new Date();
				console.log(`[TuioReceiver] Raw message #${this.messageCount}:`, event.data);
				try {
					const msg = JSON.parse(event.data);
					this.onOscMessage(msg);
				} catch (e) {
					const errMsg = `Failed to parse message: ${event.data}`;
					console.warn(`[TuioReceiver] ${errMsg}`, e);
					this.lastError = errMsg;
				}
			};
		}

		public disconnect() {
			this._readyState = WebSocket.CLOSING;
			this._ws?.close();
			this._ws = null;
			this._readyState = WebSocket.CLOSED;
			this.isConnected = false;
		}
	}
</script>
