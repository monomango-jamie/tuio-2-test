import { TuioReceiver } from 'tuio-client';

export class WebsocketTuioReceiver extends TuioReceiver {
	private readonly _url: string;
	private _ws: WebSocket | null = null;

	constructor(host: string, port: number) {
		super();
		this._url = `ws://${host}:${port}`;
	}

	public connect() {
		console.log(`[TuioReceiver] Connecting to ${this._url}`);
		this._ws = new WebSocket(this._url);

		this._ws.onopen = () => {
			console.log(`[TuioReceiver] Connected to ${this._url}`);
			this.isConnected = true;
		};

		this._ws.onclose = (e) => {
			console.warn(`[TuioReceiver] Disconnected (code=${e.code})`);
			this.isConnected = false;
		};

		this._ws.onerror = (e) => {
			console.error(`[TuioReceiver] WebSocket error`, e);
		};

		this._ws.onmessage = (event) => {
			try {
				const msg = JSON.parse(event.data);
				console.log('[TuioReceiver] Received:', msg);
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
