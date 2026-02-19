<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import { onMount } from 'svelte';
	import { WebsocketTuioReceiver } from '$lib/modules/WebsocketTuioReceiver';
	import { Tuio20Client } from 'tuio-client';
	import TuioClientProvider from '$lib/providers/TUIO/TUIOClientProvider.svelte';
	import TUIODebugger from '$lib/components/TUIODebugger.svelte';
	import SmartphonesProvider from '$lib/providers/Smartphones/SmartphonesProvider.svelte';
	import { SmartphoneRegistry } from '$lib/providers/Smartphones/SmartphoneRegistry.svelte';
	import { TableSocket } from '$lib/socket/TableSocket.svelte';

	let tuioClient = $state<Tuio20Client | null>(null);
	let tuioReceiver = $state<WebsocketTuioReceiver | null>(null);

	const registry = new SmartphoneRegistry();
	
	const tableSocket = new TableSocket({
		url: 'wss://tuio-ws-production.up.railway.app?room=test&role=table'
	});

	// Route incoming messages to the registry
	tableSocket.onJoin = (msg) => {
		registry.addPhone(msg.senderId);
	};

	tableSocket.onContactInfo = (msg) => {
		registry.updateContactInfo(msg.senderId, {
			firstName: msg.firstName,
			lastName: msg.lastName,
			email: msg.email,
			company: msg.company
		});
	};

	tableSocket.onPlaced = (msg) => {
		registry.addPlacedSignal(msg.senderId);
	};

	onMount(() => {
		const receiver = new WebsocketTuioReceiver('10.10.110.21', 9980);
		const client = new Tuio20Client(receiver);
		receiver.connect();
		client.connect();
		tuioClient = client;
		tuioReceiver = receiver;

		tableSocket.connect();

		// Listen for TUIO bounds+symbol → attempt pairing → send tuio-pair
		client.addTuioListener({
			tuioAdd(obj) {
				if (obj.containsNewTuioBounds() && obj.symbol) {
					const deviceId = obj.symbol.data;
					if (!deviceId) return;

					const pairedSenderId = registry.tryPair(deviceId);
					if (pairedSenderId) {
						tableSocket.sendTuioPair(pairedSenderId, deviceId);
					}
				}
			},
			tuioUpdate() {},
			tuioRemove() {},
			tuioRefresh() {}
		});

		return () => {
			client.disconnect();
			receiver.disconnect();
			tableSocket.disconnect();
		};
	});

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="relay-status" class:connected={tableSocket.connected}>
	{tableSocket.connected ? '● Relay connected' : '○ Relay disconnected'}
</div>

<button class="debug-btn" onclick={() => {
	const msg = JSON.stringify({ address: '/debug/ping', args: ['hello from browser', Date.now()] });
	console.log('[DEBUG] Sending test message to TD:', msg);
	tuioReceiver?.sendTest(msg);
}}>
	⚡ Send test to TD
</button>

{#if tuioClient}
	<TuioClientProvider client={tuioClient}>
		<SmartphonesProvider {registry}>
			<TUIODebugger />
			{@render children?.()}
		</SmartphonesProvider>
	</TuioClientProvider>
{/if}

<style>
	.relay-status {
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

	.relay-status.connected {
		color: #6f6;
	}

	.debug-btn {
		position: fixed;
		top: 36px;
		right: 8px;
		z-index: 10;
		padding: 4px 10px;
		border-radius: 4px;
		font-size: 12px;
		font-family: monospace;
		background: rgba(255, 200, 0, 0.2);
		border: 1px solid rgba(255, 200, 0, 0.5);
		color: #fc0;
		cursor: pointer;
	}
</style>
