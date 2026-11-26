/* A Help button on every staff screen. It opens three or four numbered steps
   for that screen, in plain words, so a new member of staff can start without
   being shown. The steps are short on purpose: one action each. */
(() => {
  const STEPS = {
    '/nurse': ['The nurse\'s queue', [
      'The most urgent patient is at the top. A red mark means see them now.',
      'Press a patient to read what they said and what to check first.',
      'Change the level if you judge it differently. Only you can lower it.',
      'Press "Mark as seen" to send the patient on. The board in the waiting room calls their number to the doctor.']],
    '/vitals': ['Vitals', [
      'Press the patient\'s ticket number.',
      'Choose Weight, Height or BP, type the reading, and press Save.',
      'Choose the area the patient lives in, and their sex.',
      'If the patient agrees, press "Take a photo". It is deleted with the visit.']],
    '/doctor': ['Doctor', [
      'Patients the nurse has seen are under "Waiting for you". Press one.',
      'Read the helper\'s note and the measurements at the top.',
      'Press "Ask CAIMEx what to consider" for ideas. Type your diagnosis, or press "Say it" and speak.',
      'Add each medicine with how many, then press "Send the prescription to the pharmacy".']],
    '/pharmacy': ['Pharmacy', [
      'Press the ticket. A blue dot means a prescription is waiting.',
      'Check the photo is the person in front of you.',
      'Press "Dispense" beside each medicine the doctor prescribed. The tablet then tells the patient how to take it.',
      'Anything not prescribed, a fee waiver, or a change to a stock count needs the supervisor\'s PIN.']],
    '/outbreaks': ['the Forecast', [
      'The top row is what to expect today, before anyone arrives. Press "Hear the briefing" to have it read out.',
      'On the map, red is confirmed by the doctor and stripes are an unusual rise. Press a ward.',
      'Each card shows the last four weeks, the usual, and the likely range for the next seven days.',
      'Slide "Go back in time" to see what the page would have shown on earlier days.',
      'Press "Why?" or "Draft the alert" to have CAIMEx explain or write it from the numbers.']],
    '/national': ['the Zimbabwe map', [
      'Choose an illness, then what the map shows: the risk, the rain, the water reports or past cases.',
      'Press a province to see its warnings and what each point of the score came from.',
      'Green labels are real weather. Grey labels are made up for the demonstration.',
      'The blue ring is this clinic\'s province. Its warnings also appear on the Forecast page.']],
  };
  const page = STEPS[location.pathname.replace(/\/$/, '') || '/'];
  // The Help button sits with the page's own tools in its title band.
  const nav = document.querySelector('.page-tools') || document.querySelector('.band-in');
  if (!page || !nav) return;
  const style = document.createElement('style');
  style.textContent = `.help-steps{display:grid;gap:12px;padding:0;margin:0}.help-steps li{list-style:none;display:grid;grid-template-columns:36px 1fr;gap:12px;align-items:start;font-size:1.0625rem}
    .help-steps b{width:36px;height:36px;border-radius:50%;display:grid;place-items:center;background:var(--selected);color:var(--blue-ink);font-weight:700}
    .help-btn{display:inline-flex;align-items:center;gap:6px;min-height:44px;padding:0 14px;border-radius:999px;border:1px solid var(--ghost-edge);background:var(--ghost-fill);color:var(--ink);font-weight:600;font-size:.9375rem;cursor:pointer}
    .help-btn svg{width:18px;height:18px}.embed .help-btn{display:none}`;
  document.head.appendChild(style);
  const btn = document.createElement('button');
  btn.className = 'help-btn noprint';
  btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M9.500 9.500a2.500 2.500 0 1 1 3.500 2.300c-.700.400-1 1-1 1.700M12 17v.300"/></svg>Help';
  nav.appendChild(btn);
  const back = document.createElement('div');
  back.className = 'sheet-back'; back.hidden = true;
  back.innerHTML = `<div class="sheet stack" role="dialog" aria-modal="true" aria-labelledby="helpT"><h2 class="title" id="helpT">How to use ${page[0]}</h2>
    <ol class="help-steps">${page[1].map((s, i) => `<li><b>${i + 1}</b><span>${s}</span></li>`).join('')}</ol>
    <button class="btn primary block" id="helpOk">Got it</button></div>`;
  document.body.appendChild(back);
  const close = () => { back.hidden = true; btn.focus(); };
  btn.onclick = () => { back.hidden = false; back.querySelector('#helpOk').focus(); };
  back.onclick = e => { if (e.target === back || e.target.id === 'helpOk') close(); };
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !back.hidden) close(); });
})();
