<script lang="ts">
	import type { TableSocket } from '$lib/socket/TableSocket.svelte';

	let {
		tableSocket,
		tuioConnected = false,
		tuioError = null
	}: {
		tableSocket: TableSocket;
		tuioConnected?: boolean;
		tuioError?: string | null;
	} = $props();
</script>

<div class="socket-status">
	<div class="panel" class:connected={tableSocket.connected}>
		<div class="header">
			{tableSocket.connected ? '● Relay connected' : '○ Relay disconnected'}
		</div>
		<div class="details">
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

	<div class="panel" class:connected={tuioConnected} class:error={!!tuioError}>
		{tuioError ? `⚠ TUIO error: ${tuioError}` : tuioConnected ? '● TUIO connected' : '○ TUIO disconnected'}
	</div>
</div>

<style>
	.socket-status {
		position: fixed;
		top: 8px;
		right: 8px;
		z-index: 10;
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	.panel {
		padding: 6px 10px;
		border-radius: 4px;
		font-size: 11px;
		font-family: monospace;
		background: rgba(0, 0, 0, 0.85);
		color: #f66;
		min-width: 280px;
		border: 1px solid rgba(255, 255, 255, 0.1);
	}

	.panel.connected {
		color: #6f6;
	}

	.panel.error {
		color: #fa0;
	}

	.header {
		font-weight: bold;
		margin-bottom: 4px;
		padding-bottom: 4px;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}

	.details {
		color: #999;
		font-size: 10px;
		line-height: 1.5;
	}

	.details .error {
		color: #f66;
	}
</style>
