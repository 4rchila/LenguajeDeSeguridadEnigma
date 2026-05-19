/* =====================================================================
   ENIGMA — Lógica de la presentación ejecutiva
   ===================================================================== */

(() => {
  'use strict';

  const slides = Array.from(document.querySelectorAll('.slide'));
  const total = slides.length;

  const $title    = document.getElementById('slide-title');
  const $current  = document.getElementById('slide-current');
  const $totalEl  = document.getElementById('slide-total');
  const $progress = document.getElementById('progress-bar');
  const $btnPrev  = document.getElementById('btn-prev');
  const $btnNext  = document.getElementById('btn-next');
  const $btnOvr   = document.getElementById('btn-overview');
  const $overview = document.getElementById('overview');
  const $thumbs   = document.getElementById('thumbs');
  const $lightbox = document.getElementById('lightbox');
  const $lbImg    = document.getElementById('lightbox-img');
  const $lbClose  = document.getElementById('lightbox-close');
  const $help     = document.getElementById('help');
  const $timer    = document.getElementById('timer');
  const $timerTxt = document.getElementById('timer-text');
  // Timer elements may not exist if removed from HTML

  let current = 0;
  const pad = (n) => String(n).padStart(2, '0');
  $totalEl.textContent = pad(total);

  /* =================================================================
     Navegación entre slides
  ================================================================= */
  function showSlide(idx, dir = 1) {
    idx = Math.max(0, Math.min(total - 1, idx));
    if (idx === current && document.querySelector('.slide.active')) return;

    slides.forEach((s, i) => {
      s.classList.remove('active', 'prev');
      if (i === idx) {
        s.classList.add('active');
        s.scrollTop = 0;
      } else if (i < idx) {
        s.classList.add('prev');
      }
    });

    current = idx;
    $title.textContent = slides[idx].dataset.title || `Slide ${idx + 1}`;
    $current.textContent = pad(idx + 1);
    $progress.style.width = (((idx + 1) / total) * 100) + '%';

    $btnPrev.disabled = idx === 0;
    $btnNext.disabled = idx === total - 1;

    history.replaceState(null, '', `#${idx + 1}`);
  }

  function next() { showSlide(current + 1, 1); }
  function prev() { showSlide(current - 1, -1); }

  $btnPrev.addEventListener('click', prev);
  $btnNext.addEventListener('click', next);

  /* =================================================================
     Teclado
  ================================================================= */
  document.addEventListener('keydown', (e) => {
    if ($lightbox.classList.contains('active')) {
      if (e.key === 'Escape') closeLightbox();
      return;
    }
    if ($overview.classList.contains('active')) {
      if (e.key === 'Escape' || e.key.toLowerCase() === 'o') toggleOverview(false);
      return;
    }
    if ($help.classList.contains('active')) {
      if (e.key === 'Escape' || e.key === '?') toggleHelp(false);
      return;
    }

    switch (e.key) {
      case 'ArrowRight':
      case 'ArrowDown':
      case 'PageDown':
      case ' ':
        e.preventDefault(); next(); break;
      case 'ArrowLeft':
      case 'ArrowUp':
      case 'PageUp':
        e.preventDefault(); prev(); break;
      case 'Home': e.preventDefault(); showSlide(0); break;
      case 'End':  e.preventDefault(); showSlide(total - 1); break;
      case 'o': case 'O': toggleOverview(true); break;
      case '?': toggleHelp(true); break;
      case 't': case 'T': toggleTimer(); break;
      case 'f': case 'F': toggleFullscreen(); break;
      default:
        if (/^[1-9]$/.test(e.key)) {
          const n = parseInt(e.key, 10) - 1;
          if (n < total) showSlide(n);
        }
    }
  });

  /* =================================================================
     Swipe (mobile / trackpad)
  ================================================================= */
  let touchStartX = 0, touchStartY = 0;
  document.addEventListener('touchstart', (e) => {
    touchStartX = e.touches[0].clientX;
    touchStartY = e.touches[0].clientY;
  }, { passive: true });

  document.addEventListener('touchend', (e) => {
    if ($lightbox.classList.contains('active') || $overview.classList.contains('active')) return;
    const dx = e.changedTouches[0].clientX - touchStartX;
    const dy = e.changedTouches[0].clientY - touchStartY;
    if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy)) {
      dx < 0 ? next() : prev();
    }
  }, { passive: true });

  /* =================================================================
     Overview (miniaturas)
  ================================================================= */
  function buildThumbs() {
    $thumbs.innerHTML = '';
    slides.forEach((s, i) => {
      const div = document.createElement('div');
      div.className = 'thumb';
      div.innerHTML = `
        <div class="n">${pad(i + 1)} · ${total}</div>
        <div class="t">${s.dataset.title || `Slide ${i + 1}`}</div>
      `;
      div.addEventListener('click', () => {
        showSlide(i);
        toggleOverview(false);
      });
      $thumbs.appendChild(div);
    });
  }

  function toggleOverview(force) {
    const willOpen = force !== undefined ? force : !$overview.classList.contains('active');
    $overview.classList.toggle('active', willOpen);
  }

  $btnOvr.addEventListener('click', () => toggleOverview());
  $overview.addEventListener('click', (e) => {
    if (e.target === $overview) toggleOverview(false);
  });

  /* =================================================================
     Lightbox para capturas
  ================================================================= */
  function openLightbox(src, alt = '') {
    $lbImg.src = src;
    $lbImg.alt = alt;
    $lightbox.classList.add('active');
  }
  function closeLightbox() {
    $lightbox.classList.remove('active');
    $lbImg.src = '';
  }

  document.addEventListener('click', (e) => {
    const shot = e.target.closest('.shot');
    if (shot && shot.dataset.src) {
      const img = shot.querySelector('img');
      openLightbox(shot.dataset.src, img ? img.alt : '');
    }
  });

  $lbClose.addEventListener('click', closeLightbox);
  $lightbox.addEventListener('click', (e) => {
    if (e.target === $lightbox) closeLightbox();
  });

  /* =================================================================
     Ayuda / atajos
  ================================================================= */
  function toggleHelp(force) {
    const willOpen = force !== undefined ? force : !$help.classList.contains('active');
    $help.classList.toggle('active', willOpen);
  }
  $help.addEventListener('click', (e) => {
    if (e.target === $help) toggleHelp(false);
  });

  /* =================================================================
     Timer de la presentación (13 minutos = 780 segundos)
  ================================================================= */
  const DURATION = 13 * 60;
  let remaining = DURATION;
  let timerInt = null;
  let running = false;

  function fmt(s) {
    const sign = s < 0 ? '-' : '';
    const abs = Math.abs(s);
    const m = String(Math.floor(abs / 60)).padStart(2, '0');
    const ss = String(abs % 60).padStart(2, '0');
    return `${sign}${m}:${ss}`;
  }

  function updateTimerUI() {
    if (!$timerTxt || !$timer) return;
    $timerTxt.textContent = fmt(remaining);
    $timer.classList.remove('running', 'warn', 'over');
    if (remaining < 0) $timer.classList.add('over');
    else if (remaining <= 120 && running) $timer.classList.add('warn');
    else if (running) $timer.classList.add('running');
  }

  function tick() {
    remaining -= 1;
    updateTimerUI();
  }

  function toggleTimer() {
    if (running) {
      clearInterval(timerInt);
      timerInt = null;
      running = false;
    } else {
      timerInt = setInterval(tick, 1000);
      running = true;
    }
    updateTimerUI();
  }

  function resetTimer() {
    clearInterval(timerInt);
    timerInt = null;
    running = false;
    remaining = DURATION;
    updateTimerUI();
  }

  if ($timer) {
    $timer.addEventListener('click', toggleTimer);
    $timer.addEventListener('dblclick', (e) => {
      e.preventDefault();
      resetTimer();
    });
  }

  /* =================================================================
     Pantalla completa
  ================================================================= */
  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen?.();
    } else {
      document.exitFullscreen?.();
    }
  }

  /* =================================================================
     Bootstrap
  ================================================================= */
  buildThumbs();
  const initial = parseInt((location.hash || '#1').slice(1), 10) || 1;
  showSlide(initial - 1);
  updateTimerUI();

  // Mensaje en consola, por si alguien abre devtools
  console.log('%cENIGMA · Presentación cargada', 'color:#f4c430; font-weight:700; font-size:14px;');
  console.log('Atajos:  ← →  navegar  ·  O resumen  ·  T timer  ·  ? ayuda  ·  F pantalla completa');
})();
