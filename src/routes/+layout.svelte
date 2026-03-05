<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import { onMount } from 'svelte';
	import { WebsocketTuioReceiver } from '$lib/modules/WebsocketTuioReceiver';
	import { Tuio20Client } from 'tuio-client';
	import TuioClientProvider from '$lib/providers/TUIO/TUIOClientProvider.svelte';
	import TUIODebugger from '$lib/components/TUIODebugger.svelte';
	import SocketStatus from '$lib/components/SocketStatus.svelte';
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

<SocketStatus {tableSocket} {tuioConnected} {tuioError} />


{#if tuioClient}
	<TuioClientProvider client={tuioClient}>
		<SmartphonesProvider {registry}>
			<TUIODebugger />
			{@render children?.()}
		</SmartphonesProvider>
	</TuioClientProvider>
{/if}

