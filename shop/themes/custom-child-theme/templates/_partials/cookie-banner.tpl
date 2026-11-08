{**
 * Baner zgody na cookies wzorowany na luksusowealkohole.pl (docs/cookies.png), FRONT-4, ADR 0002.
 * Natywny <dialog>: showModal() daje przyciemnienie tła, pułapkę fokusu i obsługę klawiatury bez bibliotek.
 * Logika (zapis wyboru, ponowne otwarcie ze stopki) w assets/js/custom.js.
 *}
<dialog id="cookie-banner" class="cookie-banner" aria-labelledby="cookie-banner-title" aria-describedby="cookie-banner-text">
  <form method="dialog">
    <h2 id="cookie-banner-title" class="cookie-banner-title" tabindex="-1" autofocus>Drogi użytkowniku</h2>
    <p id="cookie-banner-text" class="cookie-banner-text">
      Witamy! Stosujemy pliki cookie w celu zapewnienia prawidłowego funkcjonowania serwisu. Za Twoją zgodą możemy
      również wykorzystywać pliki cookie w celach analitycznych (badanie ruchu w sklepie) i marketingowych
      (dopasowanie reklam do Twoich preferencji). Zgodę wyrazisz, klikając „Zaakceptuj wszystkie”, a dostosujesz ją
      w „Ustawieniach”. Wyrażoną zgodę możesz wycofać w każdym momencie w „Ustawieniach cookies” w stopce strony.
      Administratorem Twoich danych osobowych jest {$shop.name}. Więcej informacji znajdziesz w naszej
      <a href="{$link->getCMSLink(2)}">Polityce prywatności</a>.
    </p>

    <fieldset class="cookie-banner-settings" hidden>
      <legend class="cookie-banner-legend">Ustawienia plików cookie</legend>
      <label><input type="checkbox" checked disabled> Niezbędne - koszyk, logowanie, zapamiętanie tego wyboru (zawsze aktywne)</label>
      <label><input type="checkbox" name="analytics"> Analityczne - anonimowe statystyki odwiedzin</label>
      <label><input type="checkbox" name="marketing"> Marketingowe - reklamy dopasowane do Twoich zainteresowań</label>
    </fieldset>

    <div class="cookie-banner-buttons">
      <button type="button" class="cookie-btn cookie-btn-settings">Ustawienia</button>
      <button type="submit" class="cookie-btn cookie-btn-save" value="save" hidden>Zapisz wybrane</button>
      <button type="submit" class="cookie-btn cookie-btn-necessary" value="necessary">Zatwierdź tylko wymagane</button>
      <button type="submit" class="cookie-btn cookie-btn-all" value="all">Zaakceptuj wszystkie</button>
    </div>
  </form>
</dialog>
