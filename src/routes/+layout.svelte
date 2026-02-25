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

	let tuioError = $state<string | null>(null);

	onMount(() => {
		let receiver: WebsocketTuioReceiver | null = null;
		let client: Tuio20Client | null = null;

		try {
			receiver = new WebsocketTuioReceiver('127.0.0.1', 3333);
			receiver.onConnected = () => {
				tuioConnected = true;
				tuioError = null;
			};
			receiver.onDisconnected = () => {
				tuioConnected = false;
			};
			receiver.onError = (e) => {
				tuioError = e instanceof Error ? e.message : String(e);
				console.error('[Layout] TUIO receiver error:', e);
			};

			client = new Tuio20Client(receiver);
			receiver.connect();
			client.connect();
			tuioClient = client;
		} catch (e) {
			tuioError = e instanceof Error ? e.message : String(e);
			console.error('[Layout] Failed to initialize TUIO:', e);
		}

		try {
			tableSocket.connect();
		} catch (e) {
			console.error('[Layout] Failed to connect table socket:', e);
		}

		return () => {
			try { client?.disconnect(); } catch (e) { console.error('[Layout] TUIO client cleanup error:', e); }
			try { receiver?.disconnect(); } catch (e) { console.error('[Layout] TUIO receiver cleanup error:', e); }
			try { tableSocket.disconnect(); } catch (e) { console.error('[Layout] Table socket cleanup error:', e); }
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
<div class="tuio-status" class:connected={tuioConnected} class:error={tuioError}>
	{tuioError ? `⚠ TUIO error: ${tuioError}` : tuioConnected ? '● TUIO connected' : '○ TUIO disconnected'}
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

	.tuio-status.error {
		color: #fa0;
	}
</style>
