// ── Client Roles ───────────────────────────────────────────

export type ClientRole = 'phone' | 'table';

export const TABLE_CLIENT_ID = 'table-main';

// ── Wire Message Types (sent/received over WebSocket) ──────

/** Base fields present on every wire message */
interface BaseWireMessage {
	senderId: string;
	sender: string;
	role: ClientRole;
	/** When set, only the client with this ID should process the message */
	targetId?: string;
}

/** Phone announces itself to the table */
export interface JoinWireMessage extends BaseWireMessage {
	type: 'join';
}

/** Phone sends contact info after form submission */
export interface ContactInfoWireMessage extends BaseWireMessage {
	type: 'contact-info';
	firstName: string;
	lastName: string;
	email: string;
	company: string;
	phone?: string;
}

/** Phone signals it has been placed flat (accelerometer) */
export interface PlacedWireMessage extends BaseWireMessage {
	type: 'placed';
}

/** Table tells a phone which TUIO device UUID it is paired with */
export interface TuioPairWireMessage extends BaseWireMessage {
	type: 'tuio-pair';
	tuioDeviceId: string;
}

/** Union of all wire message shapes */
export type WireMessage =
	| JoinWireMessage
	| ContactInfoWireMessage
	| PlacedWireMessage
	| TuioPairWireMessage;
