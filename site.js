// Yardlet site: a control that pauses the page's motion, video that plays only while it is on screen,
// and the explorer's list marking the chapter whose picture is on screen. The page works without this
// file: the video autoplays, the control stays hidden and the list is a list of links.
const root = document.documentElement;
const videos = [...document.querySelectorAll('video')];
const toggle = document.querySelector('.motion-toggle');
const onScreen = new Map();
let paused = false;

function sync() {
  for (const video of videos) {
    if (!video.querySelector('source') || !video.currentSrc) continue;
    if (paused || onScreen.get(video) === false) video.pause();
    else video.play().catch(() => {});
  }
}

if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) onScreen.set(entry.target, entry.isIntersecting);
    sync();
  });
  for (const video of videos) observer.observe(video);
}

const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;

if (toggle && !reducedMotion && videos.some((video) => video.querySelector('source'))) {
  toggle.hidden = false;
  toggle.addEventListener('click', () => {
    paused = !paused;
    root.classList.toggle('motion-paused', paused);
    toggle.setAttribute('aria-pressed', String(paused));
    toggle.querySelector('.sr-only').textContent = paused ? 'Play motion' : 'Pause motion';
    sync();
  });
}

// The explorer: the chapter whose picture shows the most below the header is the current one; before the
// first picture comes up it is the first, and once the last has gone by it stays the last.
const chapters = [...document.querySelectorAll('.chapter')];
const chapterLinks = chapters.map((chapter) => document.querySelector(`.explorer-nav a[href="#${chapter.id}"]`));
if (chapters.length && chapterLinks.every(Boolean)) {
  const header = document.querySelector('.site-header');
  let current = -1;
  let queued = false;

  const update = () => {
    queued = false;
    const top = header ? header.getBoundingClientRect().bottom : 0;
    const bottom = window.innerHeight;
    let best = -1;
    let bestShown = 0;
    chapters.forEach((chapter, index) => {
      const box = (chapter.querySelector('.chapter-stage') || chapter).getBoundingClientRect();
      const shown = Math.min(bottom, box.bottom) - Math.max(top, box.top);
      if (shown > bestShown) { best = index; bestShown = shown; }
    });
    if (best < 0) {
      const first = (chapters[0].querySelector('.chapter-stage') || chapters[0]).getBoundingClientRect();
      best = first.top >= top ? 0 : chapters.length - 1;
    }
    if (best === current) return;
    current = best;
    chapterLinks.forEach((link, index) => {
      if (index === best) link.setAttribute('aria-current', 'true');
      else link.removeAttribute('aria-current');
    });
  };
  const queue = () => { if (!queued) { queued = true; requestAnimationFrame(update); } };
  window.addEventListener('scroll', queue, { passive: true });
  window.addEventListener('resize', queue);
  update();
}
