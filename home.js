// The home page's window: a section stays unread in the sidebar until its answer is in view, and the composer at the
// window's foot holds the next question. Without this file every section reads as seen and the composer is not shown.
const answers = [...document.querySelectorAll('.turn')];
const rowsById = new Map([...document.querySelectorAll('.tasks a.task[href^="#"]')].map((a) => [a.hash.slice(1), a]));
const dock = document.querySelector('.dock');
const composer = dock && dock.querySelector('.composer');
const draft = dock && dock.querySelector('.draft');
const question = (turn) => [...turn.querySelector('.ask').childNodes].filter((n) => n.nodeType === Node.TEXT_NODE).map((n) => n.textContent).join('').trim();
const download = document.querySelector('.bar-get');

for (const row of rowsById.values()) row.classList.add('unread');

let next;
function follow() {
  const line = innerHeight / 3;
  let current = 0;
  answers.forEach((turn, index) => { if (turn.getBoundingClientRect().top <= line) current = index; });
  for (const turn of answers.slice(0, current + 1)) rowsById.get(turn.id)?.classList.remove('unread');
  if (!dock) return;
  // A question leaves the composer as its bubble comes out above it.
  const edge = composer.getBoundingClientRect().top;
  const waiting = answers.find((turn) => turn.querySelector('.ask').getBoundingClientRect().top > edge);
  if (waiting === next) return;
  next = waiting;
  const words = next ? question(next) : 'Download Yardlet for Mac';
  draft.textContent = words;
  composer.href = next ? `#${next.id}` : download.href;
  composer.setAttribute('aria-label', next ? `Next question: ${words}` : words);
}

let queued = false;
addEventListener('scroll', () => {
  if (queued) return;
  queued = true;
  requestAnimationFrame(() => { queued = false; follow(); });
}, { passive: true });
addEventListener('resize', follow);

if (dock) {
  next = null;
  dock.hidden = false;
  // Sending: the question arrives as the person's bubble and the answer after it, once the page is there.
  composer.addEventListener('click', () => {
    if (!next) return;
    const turn = next;
    turn.classList.remove('sent');
    requestAnimationFrame(() => turn.classList.add('sent'));
  });
}
follow();
