import OSC from 'osc-js';
import { TuioReceiver } from 'tuio-client';

export class WebsocketTuioReceiver extends TuioReceiver {
	private readonly _host: string;
	private readonly _port: number;
	private _osc: OSC | null = null;

	public onConnected: (() => void) | null = null;
	public onDisconnected: (() => void) | null = null;
	public onError: ((e: unknown) => void) | null = null;

	constructor(host: string, port: number) {
		super();
		this._host = host;
		this._port = port;
		const plugin = new OSC.WebsocketClientPlugin({ host: this._host, port: this._port });
		this._osc = new OSC({ plugin });
		this._osc.on('open', () => { this.isConnected = true; this.onConnected?.(); });
		this._osc.on('close', () => { this.isConnected = false; this.onDisconnected?.(); });
		this._osc.on('error', (e: unknown) => { this.onError?.(e); });
		this._osc.on('*', (message: OSC.Message) => this.onOscMessage(message));
	}

	public connect() {
		this._osc?.open();
	}

	public disconnect() {
		this._osc?.close();
		this._osc = null;
		this.isConnected = false;
	}
}
