import { getContext, setContext } from 'svelte';
import type { SmartphoneRegistry } from './SmartphoneRegistry.svelte';

const KEY = 'smartphoneRegistry';

export function setSmartphoneRegistry(registry: SmartphoneRegistry) {
	setContext(KEY, registry);
}

export function getSmartphoneRegistry(): SmartphoneRegistry {
	return getContext<SmartphoneRegistry>(KEY);
}
