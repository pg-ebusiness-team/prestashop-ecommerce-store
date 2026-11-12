{**
 * Potwierdzenie pełnoletności (18+), pokazywane po banerze cookies przy pierwszej wizycie (FRONT-4).
 * Wygląd jak baner cookies (klasy cookie-banner / cookie-btn), logika w assets/js/custom.js.
 *}
<dialog id="age-gate" class="cookie-banner age-gate" aria-labelledby="age-gate-title" aria-describedby="age-gate-text">
  <form method="dialog">
    <h2 id="age-gate-title" class="cookie-banner-title" tabindex="-1" autofocus>Czy masz ukończone 18 lat?</h2>
    <p id="age-gate-text" class="cookie-banner-text">
      W naszym sklepie znajdziesz napoje alkoholowe. Zgodnie z ustawą o wychowaniu w trzeźwości i przeciwdziałaniu
      alkoholizmowi nie sprzedajemy alkoholu osobom niepełnoletnim. Aby wejść do sklepu, potwierdź, że masz
      ukończone 18 lat.
    </p>
    {* Komunikat po kliknięciu „Nie”; role="alert" - czytnik ekranu odczyta go od razu *}
    <p class="age-gate-denied" role="alert" hidden>
      Przykro nam, zawartość sklepu jest dostępna wyłącznie dla osób pełnoletnich.
    </p>
    <div class="cookie-banner-buttons">
      <button type="button" class="cookie-btn cookie-btn-necessary age-gate-no">Nie, mam mniej niż 18 lat</button>
      <button type="submit" class="cookie-btn cookie-btn-all" value="adult">Tak, mam ukończone 18 lat</button>
    </div>
  </form>
</dialog>
