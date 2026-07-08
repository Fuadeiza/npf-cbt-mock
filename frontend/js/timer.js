// A simple countdown timer. Ticks once per second, reports remaining seconds,
// and fires onExpire exactly once when it reaches zero.

export class CountdownTimer {
  constructor(durationSeconds, { onTick, onExpire }) {
    this._remaining = durationSeconds;
    this._onTick = onTick;
    this._onExpire = onExpire;
    this._handle = null;
  }

  start() {
    this._onTick(this._remaining);
    this._handle = setInterval(() => this._step(), 1000);
  }

  _step() {
    this._remaining -= 1;
    if (this._remaining <= 0) {
      this._remaining = 0;
      this._onTick(0);
      this.stop();
      this._onExpire();
      return;
    }
    this._onTick(this._remaining);
  }

  stop() {
    if (this._handle !== null) {
      clearInterval(this._handle);
      this._handle = null;
    }
  }
}

export function formatClock(totalSeconds) {
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}
