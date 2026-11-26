/* Records the microphone as 16 kHz mono WAV, the same in every browser.

   Why not the browser's own recorder: it writes WebM in Chrome, MP4 in Safari
   and Ogg in Firefox. The gateway billed a WebM clip about three times its
   real length (measured 2026-11-25), and not every browser can play another
   browser's format back to the nurse. WAV is billed by its true length and
   plays everywhere. */

class WavRecorder {
  constructor(ctx, source) {
    this.ctx = ctx; this.source = source; this.chunks = []; this.on = false; this.node = null;
  }

  async _attach() {
    if (this.node) return;
    const sink = this.ctx.createGain(); sink.gain.value = 0; sink.connect(this.ctx.destination);
    const keep = data => { if (this.on) this.chunks.push(data); };
    if (this.ctx.audioWorklet) {
      try {
        await this.ctx.audioWorklet.addModule('rec-worklet.js');
        this.node = new AudioWorkletNode(this.ctx, 'mukoti-tap', { numberOfInputs: 1, numberOfOutputs: 1, channelCount: 1 });
        this.node.port.onmessage = e => keep(e.data);
      } catch (e) { this.node = null; }
    }
    if (!this.node) {                       // older browsers
      this.node = this.ctx.createScriptProcessor(4096, 1, 1);
      this.node.onaudioprocess = e => keep(new Float32Array(e.inputBuffer.getChannelData(0)));
    }
    this.source.connect(this.node); this.node.connect(sink);
  }

  async start() { await this._attach(); this.chunks = []; this.on = true; }

  /* Stop and return the WAV. trimEnd drops that many seconds of trailing
     silence, so nobody pays to transcribe the pause that ended the turn. */
  stop(trimEnd = 0) {
    this.on = false;
    const rate = this.ctx.sampleRate;
    let n = this.chunks.reduce((s, c) => s + c.length, 0);
    const all = new Float32Array(n);
    let o = 0; for (const c of this.chunks) { all.set(c, o); o += c.length; }
    this.chunks = [];
    n = Math.max(0, n - Math.floor(trimEnd * rate));
    const pcm = WavRecorder.resample(all.subarray(0, n), rate, 16000);
    return { blob: WavRecorder.wav(pcm, 16000), seconds: pcm.length / 16000 };
  }

  static resample(input, from, to) {
    if (from === to) return input;
    const ratio = from / to, out = new Float32Array(Math.floor(input.length / ratio));
    for (let i = 0; i < out.length; i++) {          // average each window: a plain low-pass
      const a = Math.floor(i * ratio), b = Math.min(input.length, Math.floor((i + 1) * ratio));
      let s = 0; for (let j = a; j < b; j++) s += input[j];
      out[i] = b > a ? s / (b - a) : 0;
    }
    return out;
  }

  static wav(samples, rate) {
    const buf = new ArrayBuffer(44 + samples.length * 2), v = new DataView(buf);
    const str = (o, s) => { for (let i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i)); };
    str(0, 'RIFF'); v.setUint32(4, 36 + samples.length * 2, true); str(8, 'WAVE'); str(12, 'fmt ');
    v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
    v.setUint32(24, rate, true); v.setUint32(28, rate * 2, true); v.setUint16(32, 2, true); v.setUint16(34, 16, true);
    str(36, 'data'); v.setUint32(40, samples.length * 2, true);
    for (let i = 0; i < samples.length; i++) {
      const x = Math.max(-1, Math.min(1, samples[i]));
      v.setInt16(44 + i * 2, x < 0 ? x * 0x8000 : x * 0x7FFF, true);
    }
    return new Blob([buf], { type: 'audio/wav' });
  }
}
