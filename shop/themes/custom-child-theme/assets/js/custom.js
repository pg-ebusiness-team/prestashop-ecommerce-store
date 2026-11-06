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
