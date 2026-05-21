const API_BASE = 'http://localhost:8123';

export async function api(path: string): Promise<any> {
	const res = await fetch(`${API_BASE}${path}`);
	if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
	return res.json();
}

export function tierColor(tier: string | null | undefined): string {
	const map: Record<string, string> = {
		S: 'text-orange-500 font-bold',
		A: 'text-green-500 font-semibold',
		B: 'text-cyan-400',
		C: 'text-gray-400',
		'—': 'text-gray-600',
	};
	return map[tier || ''] || 'text-gray-400';
}

export function fmtTps(tps: number | null | undefined): string {
	return tps ? `${tps.toFixed(0)} t/s` : '—';
}

export function fmtLat(lat: number | null | undefined): string {
	return lat != null ? `${lat.toFixed(2)}s` : '—';
}

export function fmtPrice(p: number | null | undefined): string {
	if (p == null) return '—';
	if (p === 0) return 'FREE';
	return `$${p.toFixed(2)}`;
}
