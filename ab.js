// Yardlet site: the home page shows one of two headlines, chosen at random on a visitor's first visit and kept
// in this browser's local storage so later visits show the same one. For the second, its download buttons
// fetch the same disk image under the name GitHub's releases list as -arm64, so the download count of each file
// says which headline brings more downloads. Nothing is sent anywhere. Without this file, or without storage,
// the page still shows one headline per visit.
let headline = null;
try { headline = localStorage.getItem('yardlet-headline'); } catch {}
if (headline !== 'a' && headline !== 'b') {
  headline = Math.random() < 0.5 ? 'a' : 'b';
  try { localStorage.setItem('yardlet-headline', headline); } catch {}
}
if (headline === 'b') {
  document.documentElement.dataset.headline = 'b';
  addEventListener('DOMContentLoaded', () => {
    for (const a of document.querySelectorAll('a[href*="/releases/download/"]')) {
      a.href = a.href.replace(/\/(Yardlet-[\d.]+)\.dmg$/, '/$1-arm64.dmg');
    }
  });
}
