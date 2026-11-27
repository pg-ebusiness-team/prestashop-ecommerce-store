/*
 * Baner zgody na cookies (templates/_partials/cookie-banner.tpl, ADR 0002), a po nim okno 18+ (age-gate.tpl).
 * Wybór zapisujemy w localStorage jako {analytics, marketing}; brak wpisu = pierwsza wizyta = pokaż baner.
 * shortcut: zgoda tylko zapisywana, nic jej jeszcze nie odczytuje; przy GA4 (etap 2) dopiąć gtag('consent', ...).
 * PrestaShop sam ładuje assets/js/custom.js motywu na końcu strony, więc HTML banera już istnieje.
 */
(function () { // funkcja wywoływana od razu - zmienne nie trafiają do globalnego window
  var KEY = 'cookie-consent'; // klucz w localStorage (DevTools > Application > Local Storage)
  var dialog = document.getElementById('cookie-banner');
  var ageGate = document.getElementById('age-gate');
  // Brak okien na stronie (np. proces zamówienia) albo bardzo stara przeglądarka bez <dialog> - nic nie robimy
  if (!dialog || !ageGate || typeof dialog.showModal !== 'function') return;

  var form = dialog.querySelector('form');
  var settings = dialog.querySelector('.cookie-banner-settings'); // checkboxy kategorii, domyślnie ukryte
  var settingsBtn = dialog.querySelector('.cookie-btn-settings');
  var saveBtn = dialog.querySelector('.cookie-btn-save');

  // Zapisany wybór albo null (brak wpisu lub uszkodzony JSON - wtedy traktujemy jak pierwszą wizytę)
  function read() {
    try { return JSON.parse(localStorage.getItem(KEY)); } catch (e) { return null; }
  }

  // Przy otwartych ustawieniach „Ustawienia” znika, a „Zapisz wybrane” się pojawia - 3 przyciski mieszczą się w rzędzie
  function showSettings(show) {
    settings.hidden = !show;
    saveBtn.hidden = !show;
    settingsBtn.hidden = show;
  }

  // Otwiera baner; withSettings = true przy wejściu ze stopki (od razu widać checkboxy)
  function open(withSettings) {
    var consent = read() || {};
    // Checkboxy pokazują poprzedni wybór; form.analytics = pole o name="analytics"
    form.analytics.checked = !!consent.analytics;
    form.marketing.checked = !!consent.marketing;
    showSettings(withSettings);
    dialog.returnValue = ''; // czyścimy wynik poprzedniego zamknięcia, inaczej Esc zapisałby stary wybór
    dialog.showModal(); // modal: przyciemnione tło, fokus zamknięty w oknie
  }

  settingsBtn.addEventListener('click', function () {
    showSettings(true);
    form.analytics.focus(); // kliknięty przycisk zniknął, fokus nie może przepaść
  });

  // Przyciski submit w <form method="dialog"> zamykają okno, a ich value trafia do dialog.returnValue
  // ('necessary' / 'all' / 'save'). Esc zamyka bez value - nic nie zapisujemy, baner wróci na następnej stronie.
  dialog.addEventListener('close', function () {
    var choice = dialog.returnValue;
    if (choice) {
      var all = choice === 'all';
      var custom = choice === 'save'; // przy 'necessary' oba pola wychodzą false
      localStorage.setItem(KEY, JSON.stringify({
        analytics: all || (custom && form.analytics.checked),
        marketing: all || (custom && form.marketing.checked)
      }));
    }
    openAgeGate(); // kolejność przy pierwszej wizycie: najpierw cookies, potem 18+
  });

  // „Ustawienia cookies” w stopce (i każdy element z data-cookie-settings) otwiera baner ponownie
  document.addEventListener('click', function (e) {
    if (e.target.closest('[data-cookie-settings]')) open(true);
  });

  // --- Okno 18+ ---
  var AGE_KEY = 'age-confirmed'; // '1' w localStorage = wiek potwierdzony, okno więcej się nie pokaże
  var denied = ageGate.querySelector('.age-gate-denied');

  // Pokazuje okno 18+, jeśli wiek nie był potwierdzony (i okno nie jest już otwarte)
  function openAgeGate() {
    if (localStorage.getItem(AGE_KEY) || ageGate.open) return;
    ageGate.returnValue = '';
    ageGate.showModal();
  }

  // „Nie” nie zamyka okna - pokazuje komunikat; osoba, która kliknęła przez pomyłkę, może jeszcze wybrać „Tak”
  ageGate.querySelector('.age-gate-no').addEventListener('click', function () {
    denied.hidden = false;
  });

  // Esc nie zamyka okna: bez potwierdzenia wieku sklep ma zostać zasłonięty
  ageGate.addEventListener('cancel', function (e) {
    e.preventDefault();
  });

  // Jedyne właściwe zamknięcie to „Tak” (value="adult"). Chrome mimo preventDefault zamyka modal drugim Esc
  // z rzędu - wtedy otwieramy okno ponownie.
  ageGate.addEventListener('close', function () {
    if (ageGate.returnValue === 'adult') localStorage.setItem(AGE_KEY, '1');
    else ageGate.showModal();
  });

  // Start: pierwsza wizyta (brak wyboru cookies) - baner cookies, okno 18+ otworzy się po nim;
  // wybór cookies zapisany - od razu okno 18+ (jeśli wiek niepotwierdzony)
  if (!read()) open(false);
  else openAgeGate();
})();

/*
 * Menu przyklejone do góry ekranu na desktopie, jak w źródle: po przewinięciu za baner (slider na stronie głównej,
 * na innych stronach za pasek z logo) wsuwa się z góry. Samo position: sticky nie działa, bo menu leży w #header,
 * a sticky trzyma się tylko w obrębie rodzica. Dajemy mu position: fixed (.is-stuck w custom.css), a pasek nad nim
 * dostaje margines = wysokość menu, żeby treść nie skoczyła.
 */
(function () {
  var menu = document.querySelector('#header .header-menu');
  var above = document.querySelector('#header .header-top');
  if (!menu || !above) return;
  var trigger = document.getElementById('carousel') || above;
  var desktop = window.matchMedia('(min-width: 768px)'); // na telefonie menu jest w wysuwanym panelu Classic

  function update() {
    var stuck = desktop.matches && trigger.getBoundingClientRect().bottom <= 0;
    if (stuck === menu.classList.contains('is-stuck')) return;
    above.style.marginBottom = stuck ? menu.offsetHeight + 'px' : '';
    menu.classList.toggle('is-stuck', stuck);
  }

  window.addEventListener('scroll', update, { passive: true });
  window.addEventListener('resize', update);
  update();
})();

/*
 * Kontrolki tworzone przez JS Classic i modułów bez nazw dla czytników ekranu: przyciski +/- przy ilości (same ikony),
 * pole z nazwą pliku w formularzu kontaktu i suwaki ceny w filtrach. Powstają w różnych momentach i od nowa po AJAX
 * (wariant, koszyk, filtry), więc nadajemy nazwy przy każdej zmianie DOM.
 */
(function () {
  var LABELS = [
    ['.bootstrap-touchspin-up', 'Zwiększ ilość'],
    ['.bootstrap-touchspin-down', 'Zmniejsz ilość'],
    ['.bootstrap-filestyle input[type="text"]', 'Wybrany plik'],
    ['.ui-slider-handle:first-of-type', 'Cena od'],
    ['.ui-slider-handle:last-of-type', 'Cena do']
  ];
  function label() {
    LABELS.forEach(function (l) {
      document.querySelectorAll(l[0] + ':not([aria-label])').forEach(function (el) { el.setAttribute('aria-label', l[1]); });
    });
  }
  label();
  new MutationObserver(label).observe(document.body, { childList: true, subtree: true });
})();

/* Telefon: lupa w górnym pasku (#search-toggle w header.tpl) pokazuje/ukrywa wyszukiwarkę, jak w źródle. */
(function () {
  var btn = document.querySelector('#search-toggle button');
  if (!btn) return;
  btn.addEventListener('click', function () {
    var open = document.getElementById('header').classList.toggle('search-open');
    btn.setAttribute('aria-expanded', open);
    if (open) document.querySelector('#search_widget input[type="text"]').focus();
  });
})();

/*
 * Ekran dotykowy, jak w źródle: pierwsze tapnięcie w zdjęcie produktu tylko odsłania oko i „Dodaj do koszyka”
 * (.is-tapped w custom.css), dopiero następne otwiera produkt albo naciska przycisk.
 */
(function () {
  if (!window.matchMedia('(hover: none)').matches) return;
  document.addEventListener('click', function (e) {
    var card = e.target.closest('.product-miniature .thumbnail-top');
    var open = document.querySelector('.thumbnail-top.is-tapped');
    if (open && open !== card) open.classList.remove('is-tapped');
    if (!card || card === open) return;
    card.classList.add('is-tapped');
    e.preventDefault();
    e.stopPropagation(); // core.js (koszyk, szybki podgląd) słucha na body, a ukryty przycisk też łapie tapnięcie
  }, true); // capture: przed handlerami Classic
})();

/*
 * Kod rabatowy (checkout/_partials/cart-voucher.tpl): sklep nie ma bonów, więc każdy kod kończy się komunikatem
 * „Taki bon rabatowy nie istnieje.” bez wysyłki do serwera.
 * shortcut: odpowiedź na sztywno; po dodaniu reguł koszyka w panelu usunąć ten blok i przywrócić {if} w szablonach.
 */
(function () {
  document.addEventListener('submit', function (e) {
    var form = e.target.closest('[data-link-action="add-voucher"]');
    if (!form) return;
    e.preventDefault();
    e.stopPropagation(); // capture: core.js nie wyśle AJAX-a (przy wyłączonych bonach i tak nic by nie odpowiedział)
    var error = form.parentNode.querySelector('.js-error');
    error.querySelector('.js-error-text').textContent = 'Taki bon rabatowy nie istnieje.';
    error.style.display = 'block'; // Classic chowa .alert w .promo-code przez display: none
  }, true);
})();

/*
 * Podgląd koszyka w nagłówku (modules/ps_shoppingcart/ps_shoppingcart.tpl): klik w koszyk rozwija/zwija listę,
 * klik poza nią lub Esc zamyka. Nasłuch na document, bo ps_shoppingcart.js po zmianie koszyka podmienia .blockcart.
 */
(function () {
  function toggle(btn, open) {
    btn.setAttribute('aria-expanded', open);
    document.getElementById('cart-dropdown').hidden = !open;
  }
  document.addEventListener('click', function (e) {
    var btn = document.querySelector('.blockcart .cart-toggle');
    if (!btn) return;
    if (e.target.closest('.cart-toggle')) toggle(btn, btn.getAttribute('aria-expanded') !== 'true');
    else if (!e.target.closest('#cart-dropdown')) toggle(btn, false);
  });
  document.addEventListener('keydown', function (e) {
    var btn = document.querySelector('.blockcart .cart-toggle[aria-expanded="true"]');
    if (e.key !== 'Escape' || !btn) return;
    toggle(btn, false);
    btn.focus();
  });
})();
