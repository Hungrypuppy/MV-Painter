// Fills every .dotfill with an SVG dot grid that fits its box exactly (vector in the PDF).
(function () {
  const NS = 'http://www.w3.org/2000/svg';
  document.querySelectorAll('.dotfill').forEach(el => {
    const w = el.clientWidth, h = el.clientHeight;
    const step = +el.dataset.step, r = +el.dataset.r, pad = +el.dataset.pad;
    const cols = Math.floor((w - 2 * pad) / step) + 1;
    const rows = Math.floor((h - 2 * pad) / step) + 1;
    const ox = (w - (cols - 1) * step) / 2, oy = (h - (rows - 1) * step) / 2;
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', w); svg.setAttribute('height', h);
    svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
    const g = document.createElementNS(NS, 'g');
    g.setAttribute('fill', '#C9BBA6');
    for (let y = 0; y < rows; y++) for (let x = 0; x < cols; x++) {
      const c = document.createElementNS(NS, 'circle');
      c.setAttribute('cx', (ox + x * step).toFixed(1));
      c.setAttribute('cy', (oy + y * step).toFixed(1));
      c.setAttribute('r', r);
      g.appendChild(c);
    }
    svg.appendChild(g);
    el.appendChild(svg);
  });
})();
