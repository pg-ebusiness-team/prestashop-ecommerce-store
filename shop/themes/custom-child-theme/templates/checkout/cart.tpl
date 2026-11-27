{**
 * Koszyk jak w luksusowealkohole.pl (FRONT-2): tytuł nad listą, „Kontynuuj zakupy” nad produktami,
 * po prawej dwa boksy - „Podsumowanie” (sumy + przycisk do kasy) i „Kod rabatowy”.
 * Sumy i kod rabatowy odświeża AJAX z core.js (.js-cart-detailed-totals, .js-cart-voucher) - klasy zostają z Classic.
 *}
{extends file='parent:checkout/cart.tpl'}

{block name='content'}
  <section id="main">
    <h1 class="h1 cart-title">{l s='Shopping Cart' d='Shop.Theme.Checkout'}</h1>
    <div class="cart-grid row">
      <div class="cart-grid-body col-lg-8">
        <a class="cart-continue" href="{$urls.pages.index}">
          <i class="material-icons" aria-hidden="true">chevron_left</i>{l s='Continue shopping' d='Shop.Theme.Actions'}
        </a>

        <div class="cart-container">
          {include file='checkout/_partials/cart-detailed.tpl' cart=$cart}
        </div>

        {hook h='displayShoppingCartFooter'}
      </div>

      <div class="cart-grid-right col-lg-4">
        <div class="card cart-summary cart-box">
          <h2 class="cart-box-title">Podsumowanie</h2>
          {hook h='displayShoppingCart'}
          {include file='checkout/_partials/cart-detailed-totals.tpl' cart=$cart}
          {include file='checkout/_partials/cart-detailed-actions.tpl' cart=$cart}
        </div>

        <div class="card cart-box cart-voucher-box">
          <h2 class="cart-box-title">Kod rabatowy</h2>
          {include file='checkout/_partials/cart-voucher.tpl'}
        </div>

        {hook h='displayReassurance'}
      </div>
    </div>

    {hook h='displayCrossSellingShoppingCart'}
  </section>
{/block}
