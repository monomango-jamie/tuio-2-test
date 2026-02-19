<script lang="ts">
	import useTuioClient from '$lib/providers/TUIO/useTuioClient';
	import type {
		Tuio20Object,
		Tuio20Token,
		Tuio20Pointer,
		Tuio20Bounds,
		Tuio20Symbol,
		TuioTime
	} from 'tuio-client';
	import { onMount, setContext } from 'svelte';

	const client = useTuioClient();

	interface LogEntry {
		id: number;
		time: string;
		event: 'add' | 'update' | 'remove' | 'refresh' | 'relay';
		data: Record<string, unknown>;
	}

	let logs: LogEntry[] = $state([]);
	let logId = 0;
	let showUpdates = $state(false);
	let maxLogs = 200;
	let minimized = $state(false);

	// Expose addRelay so sibling/parent components can push relay messages in
	export function addRelay(data: Record<string, unknown>) {
		logs = [{ id: logId++, time: timestamp(), event: 'relay', data }, ...logs].slice(0, maxLogs);
	}
	setContext('tuio-debugger', { addRelay: (data: Record<string, unknown>) => addRelay(data) });

	function timestamp() {
		return new Date().toISOString().slice(11, 23);
	}

	function serializeToken(token: Tuio20Token) {
		return {
			type: 'token',
			sessionId: token.sessionId,
			tuId: token.tuId,
			cId: token.cId,
			position: { x: token.position.x.toFixed(4), y: token.position.y.toFixed(4) },
			angle: token.angle.toFixed(3)
		};
	}

	function serializePointer(pointer: Tuio20Pointer) {
		return {
			type: 'pointer',
			sessionId: pointer.sessionId,
			tuId: pointer.tuId,
			cId: pointer.cId,
			position: { x: pointer.position.x.toFixed(4), y: pointer.position.y.toFixed(4) },
			angle: pointer.angle.toFixed(3),
			shear: pointer.shear.toFixed(3),
			radius: pointer.radius.toFixed(3),
			press: pointer.press.toFixed(3)
		};
	}

	function serializeBounds(bounds: Tuio20Bounds, symbol: Tuio20Symbol | null) {
		const data: Record<string, unknown> = {
			type: 'bounds',
			sessionId: bounds.sessionId,
			position: { x: bounds.position.x.toFixed(4), y: bounds.position.y.toFixed(4) },
			angle: bounds.angle.toFixed(3),
			size: { x: bounds.size.x.toFixed(4), y: bounds.size.y.toFixed(4) },
			area: bounds.area.toFixed(4)
		};
		if (symbol) {
			data.symbol = {
				tuId: symbol.tuId,
				cId: symbol.cId,
				group: symbol.group,
				data: symbol.data
			};
		}
		return data;
	}

	function addLog(event: LogEntry['event'], data: Record<string, unknown>) {
		logs = [{ id: logId++, time: timestamp(), event, data }, ...logs].slice(0, maxLogs);
	}

	function serializeObject(obj: Tuio20Object, event: LogEntry['event']) {
		if (event === 'add') {
			if (obj.containsNewTuioToken() && obj.token) {
				addLog(event, serializeToken(obj.token));
			}
			if (obj.containsNewTuioPointer() && obj.pointer) {
				addLog(event, serializePointer(obj.pointer));
			}
			if (obj.containsNewTuioBounds() && obj.bounds) {
				addLog(event, serializeBounds(obj.bounds, obj.symbol));
			}
		} else {
			if (obj.containsTuioToken() && obj.token) {
				addLog(event, serializeToken(obj.token));
			}
			if (obj.containsTuioPointer() && obj.pointer) {
				addLog(event, serializePointer(obj.pointer));
			}
			if (obj.containsTuioBounds() && obj.bounds) {
				addLog(event, serializeBounds(obj.bounds, obj.symbol));
			}
		}
	}

	onMount(() => {
		client.addTuioListener({
			tuioAdd(obj: Tuio20Object) {
				serializeObject(obj, 'add');
			},
			tuioUpdate(obj: Tuio20Object) {
				if (showUpdates) {
					serializeObject(obj, 'update');
				}
			},
			tuioRemove(obj: Tuio20Object) {
				serializeObject(obj, 'remove');
			},
			tuioRefresh(_time: TuioTime) {}
		});
	});

	const eventColors: Record<LogEntry['event'], string> = {
		add: '#6f6',
		update: '#ff6',
		remove: '#f66',
		refresh: '#66f',
		relay: '#f9a'
	};
</script>

<div class="debugger" class:minimized>
	<div class="header">
		<span class="title">TUIO Debug</span>
		<div class="controls">
			<label class="toggle">
				<input type="checkbox" bind:checked={showUpdates} />
				updates
			</label>
			<button onclick={() => (logs = [])}>clear</button>
			<button onclick={() => (minimized = !minimized)}>
				{minimized ? '▲' : '▼'}
			</button>
		</div>
	</div>
	{#if !minimized}
		<div class="log-list">
			{#each logs as entry (entry.id)}
				<div class="log-entry">
					<span class="time">{entry.time}</span>
					<span class="event" style="color: {eventColors[entry.event]}">{entry.event}</span>
					<pre class="data">{JSON.stringify(entry.data, null, 2)}</pre>
				</div>
			{/each}
			{#if logs.length === 0}
				<div class="empty">Waiting for TUIO events...</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.debugger {
		position: fixed;
		top: 8px;
		left: 8px;
		z-index: 100;
		width: 420px;
		max-height: 80vh;
		background: rgba(0, 0, 0, 0.85);
		border: 1px solid rgba(255, 255, 255, 0.15);
		border-radius: 6px;
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 11px;
		color: #ccc;
		display: flex;
		flex-direction: column;
	}

	.debugger.minimized {
		max-height: none;
	}

	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 6px 10px;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
		flex-shrink: 0;
	}

	.title {
		font-weight: bold;
		color: #fff;
	}

	.controls {
		display: flex;
		gap: 8px;
		align-items: center;
	}

	.toggle {
		display: flex;
		align-items: center;
		gap: 4px;
		cursor: pointer;
		color: #999;
	}

	.toggle input {
		margin: 0;
	}

	button {
		background: rgba(255, 255, 255, 0.1);
		border: none;
		color: #ccc;
		padding: 2px 8px;
		border-radius: 3px;
		cursor: pointer;
		font-size: 11px;
		font-family: inherit;
	}

	button:hover {
		background: rgba(255, 255, 255, 0.2);
	}

	.log-list {
		overflow-y: auto;
		padding: 4px 0;
		flex: 1;
	}

	.log-entry {
		padding: 3px 10px;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}

	.log-entry:hover {
		background: rgba(255, 255, 255, 0.05);
	}

	.time {
		color: #777;
		margin-right: 6px;
	}

	.event {
		font-weight: bold;
		text-transform: uppercase;
		margin-right: 6px;
		font-size: 10px;
	}

	.data {
		margin: 2px 0 0 0;
		padding: 0;
		white-space: pre-wrap;
		word-break: break-all;
		color: #aaa;
		line-height: 1.4;
	}

	.empty {
		padding: 12px 10px;
		color: #666;
		text-align: center;
	}
</style>
