// Fills every .dotfill with an exactly-fitting, centred dot grid.
// Dots are zero-length round-capped segments in ONE path: crisp vector, tiny in the PDF.
(function () {
  // Drop writing rows that would be cut off at the bottom of a fill area.
  document.querySelectorAll('.lines.fill, .checks.fill').forEach(box => {
    const limit = box.getBoundingClientRect().bottom + 0.5;
    [...box.children].forEach(row => { if (row.getBoundingClientRect().bottom > limit) row.remove(); });
  });
  const NS = 'http://www.w3.org/2000/svg';
  document.querySelectorAll('.dotfill').forEach(el => {
    const w = el.clientWidth, h = el.clientHeight;
    const step = +el.dataset.step, r = +el.dataset.r, pad = +el.dataset.pad;
    const cols = Math.floor((w - 2 * pad) / step) + 1;
    const rows = Math.floor((h - 2 * pad) / step) + 1;
    const ox = (w - (cols - 1) * step) / 2, oy = (h - (rows - 1) * step) / 2;
    let d = '';
    for (let y = 0; y < rows; y++) for (let x = 0; x < cols; x++)
      d += `M${(ox + x * step).toFixed(1)} ${(oy + y * step).toFixed(1)}h0.01`;
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', w); svg.setAttribute('height', h);
    svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
    const p = document.createElementNS(NS, 'path');
    p.setAttribute('d', d);
    p.setAttribute('stroke', '#C9BBA6');
    p.setAttribute('stroke-width', (2 * r).toFixed(2));
    p.setAttribute('stroke-linecap', 'round');
    svg.appendChild(p);
    el.appendChild(svg);
  });
})();
