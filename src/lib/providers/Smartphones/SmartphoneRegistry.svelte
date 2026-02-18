<script lang="ts" module>
	const PAIR_WINDOW_MS = 2000;

	export interface PhoneInfo {
		senderId: string;
		firstName?: string;
		lastName?: string;
		email?: string;
		company?: string;
		tuioDeviceId?: string;
		joinedAt: number;
	}

	interface PlacedSignal {
		senderId: string;
		timestamp: number;
	}

	/**
	 * Reactive registry that tracks connected phones and TUIO device pairings.
	 *
	 * Two maps:
	 * - `phones`   — senderId → phone info (populated on `join` / `contact-info`)
	 * - `pairings` — tuioDeviceId (symbol.data UUID) → senderId
	 *
	 * Pairing strategy:
	 * - Phone sends `placed` when accelerometer detects flat orientation
	 * - Table queues it with a timestamp
	 * - When a new TUIO bounds+symbol appears within PAIR_WINDOW_MS, pair them
	 * - If ambiguous (multiple placed signals), skip auto-pair
	 */
	export class SmartphoneRegistry {
		/** Connected phones keyed by senderId */
		phones: Map<string, PhoneInfo> = $state(new Map());

		/** TUIO device UUID (symbol.data) → senderId */
		pairings: Map<string, string> = $state(new Map());

		/** Recent `placed` signals waiting to be matched with TUIO events */
		#placedQueue: PlacedSignal[] = [];

		/** Register a phone on `join` */
		addPhone(senderId: string) {
			if (this.phones.has(senderId)) return;
			this.phones.set(senderId, { senderId, joinedAt: Date.now() });
			this.phones = new Map(this.phones);
			console.log(`[Registry] Phone joined: ${senderId} (${this.phones.size} total)`);
		}

		/** Update phone info on `contact-info` */
		updateContactInfo(
			senderId: string,
			info: { firstName: string; lastName: string; email: string; company: string }
		) {
			const phone = this.phones.get(senderId);
			if (!phone) {
				console.warn(`[Registry] contact-info for unknown phone: ${senderId}`);
				return;
			}
			Object.assign(phone, info);
			this.phones = new Map(this.phones);
			console.log(`[Registry] Contact info updated for ${senderId}:`, info);
		}

		/** Record a `placed` signal from a phone */
		addPlacedSignal(senderId: string) {
			this.#placedQueue.push({ senderId, timestamp: Date.now() });
			console.log(
				`[Registry] Placed signal from ${senderId} (${this.#placedQueue.length} in queue)`
			);
		}

		/**
		 * Attempt to pair a newly detected TUIO device with a phone.
		 * Called when `tuioAdd` fires with bounds+symbol.
		 *
		 * @param tuioDeviceId — `symbol.data` UUID from the TUIO event
		 * @returns The senderId of the paired phone, or null if no match / ambiguous
		 */
		tryPair(tuioDeviceId: string): string | null {
			// Already paired — return existing match
			const existing = this.pairings.get(tuioDeviceId);
			if (existing) {
				console.log(`[Registry] Known device ${tuioDeviceId} → paired with ${existing}`);
				return existing;
			}

			// Prune stale signals
			const now = Date.now();
			this.#placedQueue = this.#placedQueue.filter((s) => now - s.timestamp < PAIR_WINDOW_MS);

			if (this.#placedQueue.length === 0) {
				console.log(`[Registry] New device ${tuioDeviceId} but no placed signals in window`);
				return null;
			}

			if (this.#placedQueue.length > 1) {
				console.warn(
					`[Registry] Ambiguous: ${this.#placedQueue.length} placed signals for device ${tuioDeviceId}. Skipping.`
				);
				return null;
			}

			// Exactly one — pair it
			const signal = this.#placedQueue.pop()!;
			this.#setPairing(tuioDeviceId, signal.senderId);
			return signal.senderId;
		}

		/** Look up which phone a known TUIO device belongs to */
		getPhoneForDevice(tuioDeviceId: string): PhoneInfo | null {
			const senderId = this.pairings.get(tuioDeviceId);
			if (!senderId) return null;
			return this.phones.get(senderId) ?? null;
		}

		#setPairing(tuioDeviceId: string, senderId: string) {
			this.pairings.set(tuioDeviceId, senderId);
			this.pairings = new Map(this.pairings);

			const phone = this.phones.get(senderId);
			if (phone) {
				phone.tuioDeviceId = tuioDeviceId;
				this.phones = new Map(this.phones);
			}

			console.log(`[Registry] Paired: device ${tuioDeviceId} ↔ phone ${senderId}`);
		}
	}
</script>
