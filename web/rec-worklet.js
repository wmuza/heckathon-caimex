/* Passes each block of microphone samples to the page. See rec.js. */
class MukotiTap extends AudioWorkletProcessor {
  process(inputs) {
    const ch = inputs[0] && inputs[0][0];
    if (ch && ch.length) this.port.postMessage(new Float32Array(ch));
    return true;
  }
}
registerProcessor('mukoti-tap', MukotiTap);
