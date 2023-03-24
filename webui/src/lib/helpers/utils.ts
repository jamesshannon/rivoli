export function dateTime(timestamp: number | undefined): string {
	return new Date(timestamp * 1000).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' });
}
