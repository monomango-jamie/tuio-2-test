<script lang="ts" module>
	import type {
		WireMessage,
		JoinWireMessage,
		ContactInfoWireMessage,
		PlacedWireMessage,
		TuioPairWireMessage
	} from './types';
	import { TABLE_CLIENT_ID } from './types';

	export interface TableSocketOptions {
		url: string;
	}

	/**
	 * Reactive WebSocket client for the table side.
	 *
	 * Connects as role=table with a fixed client ID.
	 * Routes incoming phone messages via callbacks.
	 * Sends `tuio-pair` messages targeted to specific phones.
	 */
	export class TableSocket {
		ws: WebSocket | null = $state(null);
		connected = $state(false);

		#url: string;
		#clientId = TABLE_CLIENT_ID;

		// Debug state
		messageCount = $state(0);
		lastMessageTime: Date | null = $state(null);
		lastMessageType: string | null = $state(null);
		lastError: string | null = $state(null);
		connectTime: Date | null = $state(null);

		get url() {
			return this.#url;
		}

		get readyState(): number | null {
			return this.ws?.readyState ?? null;
		}

		get readyStateLabel(): string {
			if (!this.ws) return 'NO_SOCKET';
			switch (this.ws.readyState) {
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

		get debugInfo() {
			return {
				url: this.#url,
				clientId: this.#clientId,
				connected: this.connected,
				readyState: this.readyStateLabel,
				messageCount: this.messageCount,
				lastMessageTime: this.lastMessageTime?.toISOString() ?? null,
				lastMessageType: this.lastMessageType,
				lastError: this.lastError,
				connectTime: this.connectTime?.toISOString() ?? null
			};
		}

		/** Callback for ALL incoming messages (fires before type-specific callbacks) */
		onMessage: ((msg: WireMessage) => void) | null = null;

		/** Callbacks for incoming message types */
		onJoin: ((msg: JoinWireMessage) => void) | null = null;
		onContactInfo: ((msg: ContactInfoWireMessage) => void) | null = null;
		onPlaced: ((msg: PlacedWireMessage) => void) | null = null;

		get clientId() {
			return this.#clientId;
		}

		constructor(options: TableSocketOptions) {
			this.#url = options.url;
			console.log(`[TableSocket] Created: clientId=${this.#clientId}`);
		}

		connect() {
			console.log(`[TableSocket] Connecting to ${this.#url}...`);
			this.lastError = null;
			const socket = new WebSocket(this.#url);

			socket.onopen = () => {
				this.connectTime = new Date();
				console.log(`[TableSocket] Connected as table (${this.#clientId}) to ${this.#url}`);
				this.connected = true;
			};

			socket.onmessage = async (e) => {
				let data: WireMessage;
				this.messageCount++;
				this.lastMessageTime = new Date();
				console.log(`[TableSocket] Raw message #${this.messageCount}:`, e.data);
				try {
					data = JSON.parse(typeof e.data === 'string' ? e.data : await e.data.text());
				} catch (err) {
					const errMsg = `Failed to parse message: ${e.data}`;
					console.warn(`[TableSocket] ${errMsg}`);
					this.lastError = errMsg;
					this.lastMessageType = 'PARSE_ERROR';
					return;
				}

				this.lastMessageType = data.type;

				// Fire generic message callback for ALL messages
				this.onMessage?.(data);

				// Ignore own messages
				if (data.senderId === this.#clientId) {
					console.log(`[TableSocket] Ignoring own message: type=${data.type}`);
					return;
				}

				// Ignore messages targeted at someone else
				if (data.targetId && data.targetId !== this.#clientId) {
					console.log(
						`[TableSocket] Ignoring message for other target: type=${data.type}, targetId=${data.targetId}`
					);
					return;
				}

				console.log(`[TableSocket] Processing: type=${data.type}`, data);

				switch (data.type) {
					case 'join':
						this.onJoin?.(data);
						break;
					case 'contact-info':
						this.onContactInfo?.(data);
						break;
					case 'placed':
						this.onPlaced?.(data);
						break;
					default:
						console.log(`[TableSocket] Unhandled message type: ${data.type}`);
				}
			};

			socket.onclose = (e) => {
				console.log(`[TableSocket] Disconnected: code=${e.code}, reason=${e.reason || 'none'}`);
				this.connected = false;
				if (e.code !== 1000) {
					this.lastError = `Closed with code ${e.code}: ${e.reason || 'no reason'}`;
				}
			};

			socket.onerror = (e) => {
				const errMsg = `WebSocket error (check if server is running at ${this.#url})`;
				console.error(`[TableSocket] ${errMsg}`, e);
				this.lastError = errMsg;
			};

			this.ws = socket;
		}

		/** Send a tuio-pair message targeted to a specific phone */
		sendTuioPair(targetId: string, tuioDeviceId: string) {
			if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;

			const payload: TuioPairWireMessage = {
				type: 'tuio-pair',
				senderId: this.#clientId,
				sender: 'table',
				role: 'table',
				targetId,
				tuioDeviceId
			};

			console.log(`[TableSocket] Sending tuio-pair to ${targetId}:`, payload);
			this.ws.send(JSON.stringify(payload));
		}

		disconnect() {
			this.ws?.close();
		}
	}
</script>
