<script lang="ts">
	import useTuioClient from '$lib/providers/TUIO/useTuioClient';
	import { Tuio20Canvas } from '$lib/modules/TUIO20Canvas';
	import { onMount, getContext } from 'svelte';

	const client = useTuioClient();
	const debugger_ = getContext<{ addRelay: (data: Record<string, unknown>) => void }>('tuio-debugger');

	let canvasEl: HTMLCanvasElement;
	let wsConnected = $state(false);
	let wsError = $state('');

	const clientId = crypto.randomUUID();

	const PAIR_WINDOW_MS = 5000;

	// Queue of { senderId, timestamp } from received 'placed' messages
	let placedQueue: { senderId: string; timestamp: number }[] = [];

	onMount(() => {
		const tuioCanvas = new Tuio20Canvas(client, true);
		tuioCanvas.init(canvasEl);
		tuioCanvas.start();

		// WebSocket relay connection
		const socket = new WebSocket('wss://tuio-ws-production.up.railway.app?room=test');

		socket.addEventListener('open', () => {
			wsConnected = true;
			wsError = '';
			console.log('[WS Relay] Connected');
		});

		socket.addEventListener('close', () => {
			wsConnected = false;
			console.log('[WS Relay] Disconnected');
		});

		socket.addEventListener('error', (e) => {
			wsError = 'WebSocket connection error';
			console.error('[WS Relay] Error', e);
		});

		socket.addEventListener('message', async (event) => {
			const raw = event.data instanceof Blob ? await event.data.text() : event.data;
			console.log('[WS Relay] Received:', raw);
			try {
				const msg = JSON.parse(raw);
				if (msg.type === 'placed') {
					placedQueue.push({ senderId: msg.senderId, timestamp: Date.now() });
					debugger_?.addRelay({ type: 'placed', senderId: msg.senderId ?? '?', sender: msg.sender ?? '?' });
				}
			} catch {
				// ignore non-JSON
			}
		});

		function sendPair(targetId: string, tuioDeviceId: string) {
			if (socket.readyState !== WebSocket.OPEN) return;
			socket.send(JSON.stringify({
				type: 'tuio-pair',
				tuioDeviceId,
				targetId,
				senderId: clientId,
				sender: 'table',
				role: 'table'
			}));
		}

		client.addTuioListener({
			tuioAdd(obj) {
				if (obj.containsNewTuioBounds() && obj.symbol?.data) {
					const tuioDeviceId = obj.symbol.data;
					const now = Date.now();

					// Prune stale signals
					placedQueue = placedQueue.filter(p => now - p.timestamp < PAIR_WINDOW_MS);

					if (placedQueue.length === 1) {
						const { senderId } = placedQueue.shift()!;
						sendPair(senderId, tuioDeviceId);
						debugger_?.addRelay({ type: 'tuio-pair', tuioDeviceId, targetId: senderId });
						console.log(`[Pair] ${tuioDeviceId} → ${senderId}`);
					} else if (placedQueue.length > 1) {
						console.warn('[Pair] Ambiguous: multiple placed signals, skipping');
						debugger_?.addRelay({ type: 'pair-ambiguous', tuioDeviceId, count: placedQueue.length });
					}
				}
			},
			tuioUpdate(_obj) {},
			tuioRemove(_obj) {},
			tuioRefresh() {}
		});

		return () => {
			tuioCanvas.destroy();
			socket.close();
		};
	});
</script>

<div class="status" class:connected={wsConnected}>
	{wsConnected ? '● Relay connected' : '○ Relay disconnected'}
	{#if wsError}<span class="error">{wsError}</span>{/if}
</div>

<canvas bind:this={canvasEl}></canvas>

<style>
	canvas {
		position: fixed;
		inset: 0;
		display: block;
	}

	.status {
		position: fixed;
		top: 8px;
		right: 8px;
		z-index: 10;
		padding: 4px 10px;
		border-radius: 4px;
		font-size: 12px;
		font-family: monospace;
		background: rgba(0, 0, 0, 0.7);
		color: #f66;
	}

	.status.connected {
		color: #6f6;
	}

	.error {
		color: #f66;
		margin-left: 8px;
	}
</style>