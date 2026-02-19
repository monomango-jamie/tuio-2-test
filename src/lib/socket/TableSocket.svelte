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
			const socket = new WebSocket(this.#url);

			socket.onopen = () => {
				console.log(`[TableSocket] Connected as table (${this.#clientId})`);
				this.connected = true;
			};

			socket.onmessage = async (e) => {
				let data: WireMessage;
				try {
					data = JSON.parse(typeof e.data === 'string' ? e.data : await e.data.text());
				} catch {
					console.warn('[TableSocket] Failed to parse message:', e.data);
					return;
				}

				// Ignore own messages
				if (data.senderId === this.#clientId) return;

				// Ignore messages targeted at someone else
				if (data.targetId && data.targetId !== this.#clientId) return;

				console.log(`[TableSocket] Received: type=${data.type}`, data);

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

			socket.onclose = () => {
				console.log(`[TableSocket] Disconnected`);
				this.connected = false;
			};

			socket.onerror = (e) => {
				console.error('[TableSocket] Error:', e);
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
