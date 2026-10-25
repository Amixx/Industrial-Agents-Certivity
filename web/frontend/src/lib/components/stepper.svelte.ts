// Shared state of the about page's step-through diagrams: the current step, play and pause,
// arrow keys, and playing from the first time the diagram is mostly on screen. A looping
// diagram starts over after its last step and counts the rounds.

export type Row = {
	label: string;
	body?: string | string[];
	mono?: boolean;
	// Before and after, shown as a word diff.
	diff?: [string, string];
};

export type Detail = { name: string; who: string; file: string; desc: string; trace: Row[] };

export class Stepper {
	readonly last: number;
	readonly loop: boolean;
	readonly still = matchMedia('(prefers-reduced-motion: reduce)').matches;
	step = $state(0);
	playing = $state(false);
	round = $state(0);
	#started = false;

	constructor(count: number, { pace = 2600, loop = false } = {}) {
		this.last = count - 1;
		this.loop = loop;
		if (this.still) this.step = this.last;
		$effect(() => {
			if (!this.playing) return;
			const t = setInterval(() => {
				if (this.step < this.last || this.loop) this.#advance();
				else this.playing = false;
			}, pace);
			return () => clearInterval(t);
		});
	}

	#advance() {
		if (this.step < this.last) this.step += 1;
		else if (this.loop) {
			this.step = 0;
			this.round += 1;
		}
	}

	next = () => {
		this.playing = false;
		this.#advance();
	};

	pick = (i: number) => {
		this.playing = false;
		this.step = Math.max(0, Math.min(this.last, i));
	};

	toggle = () => {
		if (!this.playing && !this.loop && this.step === this.last) this.step = 0;
		this.playing = !this.playing;
	};

	key = (e: KeyboardEvent) => {
		if (e.key === 'ArrowRight') this.next();
		else if (e.key === 'ArrowLeft') this.pick(this.step - 1);
		else return;
		e.preventDefault();
	};

	autoplay = (node: HTMLElement) => {
		if (this.still) return;
		const io = new IntersectionObserver(
			([e]) => {
				if (!e.isIntersecting || this.#started) return;
				this.#started = true;
				this.playing = true;
				io.disconnect();
			},
			{ threshold: 0.5 },
		);
		io.observe(node);
		return { destroy: () => io.disconnect() };
	};
}

export const pad = (n: number) => String(n).padStart(2, '0');
