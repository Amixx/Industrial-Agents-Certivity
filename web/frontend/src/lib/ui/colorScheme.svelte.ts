export type Scheme = 'light' | 'dark';

const KEY = 'sudo-color-scheme';

class ColorScheme {
	current: Scheme = $state(
		typeof document !== 'undefined' && document.documentElement.dataset.theme === 'dark'
			? 'dark'
			: 'light',
	);

	toggle() {
		this.current = this.current === 'dark' ? 'light' : 'dark';
		document.documentElement.dataset.theme = this.current;
		try {
			localStorage.setItem(KEY, this.current);
		} catch {}
	}
}

export const colorScheme = new ColorScheme();
