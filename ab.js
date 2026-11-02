// Yardlet site: the home page shows one of two headlines, chosen at random on a visitor's first visit and kept
// in this browser's local storage so later visits show the same one. Each headline's download buttons fetch the
// same disk image under a name of its own in GitHub's releases (-apple-silicon for the first, -arm64 for the
// second), so the download count of each file says which headline brings more downloads; the plain name stays
// for updates, Homebrew and visitors without this file. Nothing is sent anywhere. Without this file, or without
// storage, the page still shows one headline per visit.
let headline = null;
try { headline = localStorage.getItem('yardlet-headline'); } catch {}
if (headline !== 'a' && headline !== 'b') {
  headline = Math.random() < 0.5 ? 'a' : 'b';
  try { localStorage.setItem('yardlet-headline', headline); } catch {}
}
if (headline === 'b') document.documentElement.dataset.headline = 'b';
addEventListener('DOMContentLoaded', () => {
  const suffix = headline === 'b' ? '-arm64' : '-apple-silicon';
  for (const a of document.querySelectorAll('a[href*="/releases/download/"]')) {
    a.href = a.href.replace(/\/(Yardlet-[\d.]+)\.dmg$/, `/$1${suffix}.dmg`);
  }
});
