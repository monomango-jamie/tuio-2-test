<script lang="ts">
	import { setSmartphoneRegistry } from './context';
	import type { SmartphoneRegistry } from './SmartphoneRegistry.svelte';
	import type { Snippet } from 'svelte';

	let { registry, children }: { registry: SmartphoneRegistry; children: Snippet } = $props();

	setSmartphoneRegistry(registry);
</script>

{@render children()}
