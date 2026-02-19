import { TuioReceiver } from 'tuio-client';

export class WebsocketTuioReceiver extends TuioReceiver {
	private readonly _url: string;
	private _ws: WebSocket | null = null;

	public onConnected: (() => void) | null = null;
	public onDisconnected: (() => void) | null = null;

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
		console.log(`[TuioReceiver] Connecting to ${this._url}`);
		this._ws = new WebSocket(this._url);

		this._ws.onopen = () => {
			console.log(`[TuioReceiver] Connected to ${this._url}`);
			this.isConnected = true;
			this.onConnected?.();
		};

		this._ws.onclose = (e) => {
			console.warn(`[TuioReceiver] Disconnected (code=${e.code})`);
			this.isConnected = false;
			this.onDisconnected?.();
		};

		this._ws.onerror = (e) => {
			console.error(`[TuioReceiver] WebSocket error`, e);
		};

		this._ws.onmessage = (event) => {
			console.log('[TuioReceiver] Raw message:', event.data);
			try {
				const msg = JSON.parse(event.data);
				this.onOscMessage(msg);
			} catch (e) {
				console.warn('[TuioReceiver] Failed to parse message:', event.data, e);
			}
		};
	}

	public disconnect() {
		this._ws?.close();
		this._ws = null;
		this.isConnected = false;
	}
}
