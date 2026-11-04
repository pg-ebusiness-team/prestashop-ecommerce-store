{**
 * Stopka jak w luksusowealkohole.pl (FRONT-2): 4 kolumny (logo, opis i dane kontaktowe / Produkty / Nasza firma /
 * newsletter) i dolny pasek (social media, copyright). Moduły wywołujemy po nazwie (mod=...), żeby trafiły
 * do właściwych kolumn; dane kontaktowe pochodzą z konfiguracji sklepu (Parametry sklepu > Kontakt).
 *}
<div class="footer-container">
  <div class="container">
    <div class="footer-main">
      <div class="footer-about">
        {* Przezroczysta wersja logo ze źródła (logo w nagłówku ma białe tło), pobiera ją `make theme` *}
        <a class="footer-logo" href="{$urls.pages.index}">
          <img src="{$urls.img_ps_url}cms/home/footer-logo.png" alt="{$shop.name}" width="666" height="276" loading="lazy">
        </a>
        <p class="footer-description">Odkryj świat wyrafinowanych smaków i aromatów w naszym sklepie internetowym, gdzie każdy alkohol opowiada własną, fascynującą historię.</p>
        <ul class="footer-contact">
          {if $shop.address.formatted}
            <li><i class="material-icons" aria-hidden="true">place</i><span>{$shop.address.formatted nofilter}</span></li>
          {/if}
          {if $shop.phone}
            <li><i class="material-icons" aria-hidden="true">phone</i><a href="tel:{$shop.phone|replace:' ':''}">{$shop.phone}</a></li>
          {/if}
          {if $shop.fax}
            <li><i class="material-icons" aria-hidden="true">print</i><span>{$shop.fax}</span></li>
          {/if}
          {if $shop.email}
            <li><i class="material-icons" aria-hidden="true">mail_outline</i><a href="mailto:{$shop.email}">{$shop.email}</a></li>
          {/if}
        </ul>
      </div>
      {hook h='displayFooter' mod='ps_linklist'}
      {hook h='displayFooterBefore' mod='ps_emailsubscription'}
    </div>
  </div>
  <div class="footer-bottom">
    <div class="container">
      {hook h='displayFooterBefore' mod='ps_socialfollow'}
      <p class="footer-copyright">&copy; {'Y'|date} {$shop.name}</p>
    </div>
  </div>
  {* Pozostałe moduły stopki (np. okna listy życzeń) - bez własnego miejsca w układzie *}
  {hook h='displayFooter' mod='blockwishlist'}
  {hook h='displayFooterAfter'}
</div>
