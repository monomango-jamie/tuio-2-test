<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import { SocketProvider, SvelteSocket } from '@hardingjam/svelte-socket';
	import { onMount } from 'svelte';

	let svelteSocket = $state<SvelteSocket>();

	onMount(() => {
		svelteSocket = new SvelteSocket({
			url: 'ws://10.29.24.190:9980/',
			reconnectOptions: {
				enabled: true,
				delay: 1000,
				maxAttempts: 10
			}
		});
	});

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

{#if svelteSocket}
	<SocketProvider {svelteSocket}>
		{@render children?.()}
	</SocketProvider>
{/if}
