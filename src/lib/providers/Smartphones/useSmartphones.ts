import { getSmartphoneRegistry } from './context';

/**
 * Hook for accessing the SmartphoneRegistry from context.
 * Use in child components wrapped by SmartphonesProvider.
 *
 * @example
 * ```svelte
 * <script>
 *   import useSmartphones from '$lib/providers/Smartphones/useSmartphones';
 *   const registry = useSmartphones();
 *   // registry.phones, registry.pairings, registry.tryPair(...)
 * </script>
 * ```
 */
export default function useSmartphones() {
	return getSmartphoneRegistry();
}
