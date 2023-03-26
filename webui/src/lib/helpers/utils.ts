export function dateTime(timestamp: number | undefined): string {
	return new Date(timestamp * 1000).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' });
}

export function makeObjectId() {
	return _hex(Date.now() / 1000) + ' '.repeat(16).replace(/./g, () => _hex(Math.random() * 16));
}

function _hex(value: number) {
	return Math.floor(value).toString(16);
}
