// Yardlet site: the sidebar and the title bar follow the answer in view, recordings play only while they are
// on screen, and the button on the first one pauses them all. Without this file the page is plain links and
// recordings that autoplay.
const turns = [...document.querySelectorAll('.turn')];
const links = new Map([...document.querySelectorAll('.tasks a.task[href^="#"]')].map((a) => [a.hash.slice(1), a]));
const titles = [...document.querySelectorAll('.jump-title')];
const jump = document.querySelector('.jump');

function select(turn) {
  for (const [id, link] of links) {
    if (id === turn.id) link.setAttribute('aria-current', 'location');
    else link.removeAttribute('aria-current');
  }
  const link = links.get(turn.id);
  if (link) for (const title of titles) title.textContent = link.textContent.trim();
}

if (turns.length) {
  // The current answer is the last one whose question has passed the upper third of the screen.
  let queued = false;
  const update = () => {
    queued = false;
    const line = innerHeight / 3;
    let current = turns[0];
    for (const turn of turns) if (turn.getBoundingClientRect().top <= line) current = turn;
    select(current);
  };
  addEventListener('scroll', () => { if (!queued) { queued = true; requestAnimationFrame(update); } }, { passive: true });
  addEventListener('resize', update);
  update();
}

if (jump) jump.addEventListener('click', (event) => { if (event.target.closest('a')) jump.open = false; });

const videos = [...document.querySelectorAll('.shot video')];
const button = document.querySelector('.pause');
const onScreen = new Map();
let paused = false;

function sync() {
  for (const video of videos) {
    if (!video.currentSrc) continue;
    if (paused || onScreen.get(video) === false) video.pause();
    else video.play().catch(() => {});
  }
}

if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) onScreen.set(entry.target, entry.isIntersecting);
    sync();
  });
  videos.forEach((video) => observer.observe(video));
}

if (button && videos.length && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
  button.hidden = false;
  button.addEventListener('click', () => {
    paused = !paused;
    button.setAttribute('aria-pressed', String(paused));
    button.querySelector('.sr-only').textContent = paused ? 'Play the recording' : 'Pause the recording';
    sync();
  });
}
