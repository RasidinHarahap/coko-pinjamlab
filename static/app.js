/* PinjamLab v5.0 · progressive, local, dependency-free enhancements.
 * Core CRUD and navigation work without JavaScript.
 */
(() => {
  'use strict';
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const command = document.getElementById('command-dialog');
  const input = document.getElementById('command-input');
  const options = command ? [...command.querySelectorAll('[data-command-item]')] : [];

  if (command && typeof command.showModal === 'function') {
    const open = () => {
      if (command.open) return;
      command.showModal();
      if (input) { input.value = ''; filterCommand(''); input.focus(); }
    };
    const close = () => { if (command.open) command.close(); };
    const filterCommand = (value) => {
      const query = value.toLocaleLowerCase('id-ID').trim();
      options.forEach(item => { item.hidden = !`${item.textContent} ${item.dataset.keywords || ''}`.toLocaleLowerCase('id-ID').includes(query); });
    };
    document.querySelectorAll('[data-command-open]').forEach(button => button.addEventListener('click', open));
    document.querySelectorAll('[data-command-close]').forEach(button => button.addEventListener('click', close));
    input?.addEventListener('input', () => filterCommand(input.value));
    input?.addEventListener('keydown', event => {
      if (event.key === 'Enter') {
        const first = options.find(option => !option.hidden);
        if (first) { event.preventDefault(); first.click(); }
      }
    });
    command.addEventListener('click', event => { if (event.target === command) close(); });
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && command.open) {
        event.preventDefault(); close(); return;
      }
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault(); command.open ? close() : open();
      }
    });
  }

  // Confirmation happens before submit and never changes form fields.
  document.querySelectorAll('form[data-confirm]').forEach(form => {
    form.addEventListener('submit', event => {
      if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    });
  });
  document.querySelectorAll('[data-print-receipt]').forEach(button => {
    button.addEventListener('click', () => window.print());
  });

  // Enhance HTML date inputs. Keep server-side validation authoritative.
  const loanForm = document.querySelector('[data-loan-form]');
  if (loanForm) {
    const start = loanForm.querySelector('[name="borrowed_on"]');
    const due = loanForm.querySelector('[name="due_on"]');
    const updateRange = () => {
      if (!start?.value || !due) return;
      const day = new Date(`${start.value}T12:00:00Z`);
      if (Number.isNaN(day.getTime())) return;
      const maxDays = Number(loanForm.dataset.maxDays) || 7;
      const max = new Date(day.getTime() + maxDays * 86400000).toISOString().slice(0,10);
      due.min = start.value;
      due.max = max;
      if (due.value && due.value < due.min) due.setCustomValidity('Batas kembali tidak boleh sebelum tanggal pinjam.');
      else if (due.value && due.value > due.max) due.setCustomValidity(`Durasi maksimal ${maxDays} hari.`);
      else due.setCustomValidity('');
    };
    start?.addEventListener('change', updateRange);
    due?.addEventListener('change', updateRange);
    updateRange();
  }

  const returnForm = document.querySelector('[data-return-form]');
  if (returnForm) {
    const condition = returnForm.querySelector('[name="return_condition"]');
    const notes = returnForm.querySelector('[name="return_notes"]');
    const syncRequired = () => {
      if (condition && notes) notes.required = condition.value !== 'Baik';
    };
    condition?.addEventListener('change', syncRequired);
    syncRequired();
  }

  // Respect reduced motion and do not animate counts in inaccessible contexts.
  if (!reduced.matches && 'IntersectionObserver' in window) {
    const targets = [...document.querySelectorAll('[data-count]')];
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        observer.unobserve(entry.target);
        const element = entry.target;
        const target = Number(element.dataset.count);
        if (!Number.isSafeInteger(target) || target < 0 || target > 100000) return;
        const started = performance.now();
        const duration = 850;
        const tick = now => {
          const progress = Math.min((now - started) / duration, 1);
          const easing = 1 - (1 - progress) ** 3;
          element.textContent = String(Math.round(target * easing));
          if (progress < 1) requestAnimationFrame(tick);
          else element.textContent = element.dataset.count;
        };
        requestAnimationFrame(tick);
      });
    }, {threshold: .25});
    targets.forEach(element => observer.observe(element));
  }


  // Animasi berjalan otomatis; preferensi Kurangi Gerakan sistem tetap dihormati.

  // Tindakan nyata di dashboard: memuat ulang data dan menyalin angka terbaru.
  // Tidak menggunakan angka tiruan, tidak menulis atau mengubah data database.
  const summaryButton = document.querySelector('[data-copy-summary]');
  const summaryFeedback = document.querySelector('[data-summary-feedback]');
  summaryButton?.addEventListener('click', async () => {
    const data = summaryButton.dataset;
    const summary = [
      'PINJAMLAB — RINGKASAN OPERASIONAL',
      `Tanggal: ${data.date || '-'} WIB`,
      `Alat terdaftar: ${data.equipment || '0'}`,
      `Siap dipinjam: ${data.available || '0'}`,
      `Sedang dipinjam: ${data.active || '0'}`,
      `Terlambat: ${data.late || '0'}`,
      `Selesai: ${data.returned || '0'}`,
      `Perlu perhatian: ${data.maintenance || '0'}`,
      'Sumber: Dashboard PinjamLab (data saat halaman dimuat).'
    ].join('\n');
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard tidak tersedia');
      await navigator.clipboard.writeText(summary);
      if (summaryFeedback) summaryFeedback.textContent = 'Ringkasan berhasil disalin.';
    } catch (_) {
      if (summaryFeedback) summaryFeedback.textContent = 'Izin clipboard tidak tersedia. Gunakan HTTPS atau localhost.';
    }
  });

  // Sorting only reorders the rows already displayed, never mutates the database.
  const collator = new Intl.Collator('id', { numeric: true, sensitivity: 'base' });
  document.querySelectorAll('[data-sort-table]').forEach(table => {
    const tbody = table.tBodies[0];
    if (!tbody) return;
    const buttons = [...table.querySelectorAll('[data-sort-index]')];
    let activeIndex = -1;
    let asc = true;
    buttons.forEach(button => button.addEventListener('click', () => {
      const index = Number(button.dataset.sortIndex);
      if (!Number.isInteger(index) || index < 0) return;
      asc = activeIndex === index ? !asc : true;
      activeIndex = index;
      const dateSort = button.dataset.sortKind === 'date';
      const rows = [...tbody.rows];
      rows.sort((a, b) => {
        const aText = dateSort ? a.dataset.loanDate : a.cells[index]?.textContent.trim();
        const bText = dateSort ? b.dataset.loanDate : b.cells[index]?.textContent.trim();
        return (asc ? 1 : -1) * collator.compare(aText || '', bText || '');
      });
      rows.forEach(row => tbody.appendChild(row));
      buttons.forEach(item => {
        const selected = item === button;
        item.dataset.sortActive = String(selected);
        item.parentElement?.setAttribute('aria-sort', selected ? (asc ? 'ascending' : 'descending') : 'none');
        const arrow = item.querySelector('span');
        if (arrow) arrow.textContent = selected ? (asc ? '↑' : '↓') : '↕';
      });
    }));
  });

  // Form readiness is visual assistance only. The Flask validation is final.
  document.querySelectorAll('.form-panel form').forEach(form => {
    const feedback = form.parentElement?.querySelector('[data-form-feedback]');
    if (!feedback) return;
    const target = feedback.closest('.form-feedback');
    const refresh = () => {
      const missing = [...form.querySelectorAll('input[required],select[required],textarea[required]')]
        .filter(field => !field.disabled && !field.checkValidity());
      let text = 'Data lengkap. Periksa kembali, kemudian pilih Simpan.';
      if (missing.length) {
        const field = missing[0];
        const label = field.closest('label');
        const labelText = label?.childNodes[0]?.textContent.trim() || field.getAttribute('aria-label') || 'isian';
        text = 'Periksa ' + labelText.toLowerCase() + ' sebelum menyimpan.';
      }
      const start = form.querySelector('[name="borrowed_on"]');
      const due = form.querySelector('[name="due_on"]');
      if (!missing.length && start?.value && due?.value) {
        const days = Math.round((Date.parse(due.value + 'T12:00:00Z') - Date.parse(start.value + 'T12:00:00Z')) / 86400000);
        if (Number.isInteger(days) && days >= 0) text = 'Data lengkap · masa pinjam ' + days + ' hari. Siap disimpan.';
      }
      feedback.textContent = text;
      target?.classList.toggle('is-ready', missing.length === 0);
    };
    form.addEventListener('input', refresh);
    form.addEventListener('change', refresh);
    refresh();
  });

  // Reading indicator and the back-to-top control use a single scroll listener.
  const progress = document.querySelector('.page-reading-track > div');
  const toTop = document.querySelector('[data-back-to-top]');
  if (progress) { progress.style.width = '100%'; progress.style.transform = 'scaleX(0)'; }
  let scrollQueued = false;
  const refreshScroll = () => {
    const maxScroll = Math.max(0, document.documentElement.scrollHeight - innerHeight);
    const fraction = maxScroll ? Math.min(1, Math.max(0, scrollY / maxScroll)) : 0;
    if (progress) progress.style.transform = `scaleX(${fraction})`;
    if (toTop) toTop.classList.toggle('is-visible', scrollY > 320);
    scrollQueued = false;
  };
  window.addEventListener('scroll', () => {
    if (!scrollQueued) { scrollQueued = true; requestAnimationFrame(refreshScroll); }
  }, { passive: true });
  window.addEventListener('resize', refreshScroll, { passive: true });
  toTop?.addEventListener('click', () => window.scrollTo({ top: 0, behavior: reduced.matches ? 'auto' : 'smooth' }));
  refreshScroll();

  // Sections appear as the reader reaches them, with graceful no-JS fallback.
  if (!reduced.matches && 'IntersectionObserver' in window) {
    document.body.classList.add('js-enhanced');
    const reveal = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('in-view');
        reveal.unobserve(entry.target);
      });
    }, { threshold: 0.05, rootMargin: '0px 0px 28px 0px' });
    document.querySelectorAll('.lab-diagnostics, .dashboard-columns, .page-heading, .form-layout, .stats-heading, .recent-panel, .workflow-card')
      .forEach(element => { element.classList.add('reveal-ready'); reveal.observe(element); });
  }
})();
