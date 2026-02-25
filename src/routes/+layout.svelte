<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import { onMount } from 'svelte';
	import { WebsocketTuioReceiver } from '$lib/modules/WebsocketTuioReceiver.svelte';
	import { Tuio20Client } from 'tuio-client';
	import TuioClientProvider from '$lib/providers/TUIO/TUIOClientProvider.svelte';
	import TUIODebugger from '$lib/components/TUIODebugger.svelte';
	import SmartphonesProvider from '$lib/providers/Smartphones/SmartphonesProvider.svelte';
	import { SmartphoneRegistry } from '$lib/providers/Smartphones/SmartphoneRegistry.svelte';
	import { TableSocket } from '$lib/socket/TableSocket.svelte';

	let tuioClient = $state<Tuio20Client | null>(null);
	let tuioReceiver = $state<WebsocketTuioReceiver | null>(null);
	let tuioConnected = $state(false);

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
		const receiver = new WebsocketTuioReceiver('10.10.110.21', 9981);
		receiver.onConnected = () => { tuioConnected = true; };
		receiver.onDisconnected = () => { tuioConnected = false; };
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
	<div class="relay-header">
		{tableSocket.connected ? '● Relay connected' : '○ Relay disconnected'}
	</div>
	<div class="relay-details">
		<div>URL: {tableSocket.url}</div>
		<div>State: {tableSocket.readyStateLabel}</div>
		<div>Messages: {tableSocket.messageCount}</div>
		{#if tableSocket.lastMessageTime}
			<div>Last msg: {tableSocket.lastMessageTime.toLocaleTimeString()} ({tableSocket.lastMessageType})</div>
		{/if}
		{#if tableSocket.lastError}
			<div class="error">Error: {tableSocket.lastError}</div>
		{/if}
		{#if tableSocket.connectTime}
			<div>Connected at: {tableSocket.connectTime.toLocaleTimeString()}</div>
		{/if}
	</div>
</div>
<div class="tuio-status" class:connected={tuioConnected}>
	<div class="tuio-header">
		{tuioConnected ? '● TUIO connected' : '○ TUIO disconnected'}
	</div>
	{#if tuioReceiver}
		<div class="tuio-details">
			<div>URL: {tuioReceiver.url}</div>
			<div>State: {tuioReceiver.readyStateLabel}</div>
			<div>Messages: {tuioReceiver.messageCount}</div>
			{#if tuioReceiver.lastMessageTime}
				<div>Last msg: {tuioReceiver.lastMessageTime.toLocaleTimeString()}</div>
			{/if}
			{#if tuioReceiver.lastError}
				<div class="error">Error: {tuioReceiver.lastError}</div>
			{/if}
			{#if tuioReceiver.connectTime}
				<div>Connected at: {tuioReceiver.connectTime.toLocaleTimeString()}</div>
			{/if}
		</div>
	{:else}
		<div class="tuio-details">Initializing...</div>
	{/if}
	<button class="debug-btn" onclick={() => {
		const msg = JSON.stringify({ address: '/debug/ping', args: ['hello from browser', Date.now()] });
		console.log('[DEBUG] Sending test message to TD:', msg);
		tuioReceiver?.sendTest(msg);
	}}>
		⚡ Send test to TD
	</button>
	<button class="debug-btn" onclick={() => {
		console.log('[DEBUG] TUIO Socket:', tuioReceiver);
	}}>
		📋 Log socket
	</button>
</div>

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
		padding: 6px 10px;
		border-radius: 4px;
		font-size: 11px;
		font-family: monospace;
		background: rgba(0, 0, 0, 0.85);
		color: #f66;
		min-width: 280px;
		border: 1px solid rgba(255, 255, 255, 0.1);
	}

	.relay-status.connected {
		color: #6f6;
	}

	.relay-header {
		font-weight: bold;
		margin-bottom: 4px;
		padding-bottom: 4px;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}

	.relay-details {
		color: #999;
		font-size: 10px;
		line-height: 1.5;
	}

	.relay-details .error {
		color: #f66;
	}

	.tuio-status {
		position: fixed;
		top: 150px;
		right: 8px;
		z-index: 10;
		padding: 6px 10px;
		border-radius: 4px;
		font-size: 11px;
		font-family: monospace;
		background: rgba(0, 0, 0, 0.85);
		color: #f66;
		min-width: 280px;
		border: 1px solid rgba(255, 255, 255, 0.1);
	}

	.tuio-status.connected {
		color: #6f6;
	}

	.tuio-header {
		font-weight: bold;
		margin-bottom: 4px;
		padding-bottom: 4px;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}

	.tuio-details {
		color: #999;
		font-size: 10px;
		line-height: 1.5;
	}

	.tuio-details .error {
		color: #f66;
	}

	.debug-btn {
		margin-top: 6px;
		padding: 4px 10px;
		border-radius: 4px;
		font-size: 10px;
		font-family: monospace;
		background: rgba(255, 200, 0, 0.2);
		border: 1px solid rgba(255, 200, 0, 0.5);
		color: #fc0;
		cursor: pointer;
	}
</style>
