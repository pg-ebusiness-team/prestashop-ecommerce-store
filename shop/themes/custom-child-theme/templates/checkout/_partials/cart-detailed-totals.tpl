{**
 * Sumy koszyka (Classic) bez kodu rabatowego - ten jest w osobnym boksie (checkout/cart.tpl).
 * Dochodzi wiersz „Do darmowej dostawy brakuje” z progu PS_SHIPPING_FREE_PRICE (Sklep > Wysyłka > Preferencje).
 *}
{block name='cart_detailed_totals'}
<div class="cart-detailed-totals js-cart-detailed-totals">

  <div class="card-block cart-detailed-subtotals js-cart-detailed-subtotals">
    {foreach from=$cart.subtotals item="subtotal"}
      {if $subtotal && $subtotal.value|count_characters > 0 && $subtotal.type !== 'tax'}
        <div class="cart-summary-line" id="cart-subtotal-{$subtotal.type}">
          <span class="label{if 'products' === $subtotal.type} js-subtotal{/if}">
            {if 'products' == $subtotal.type}
              {$cart.summary_string}
            {else}
              {$subtotal.label}
            {/if}
          </span>
          <span class="value">
            {if 'discount' == $subtotal.type}-&nbsp;{/if}{$subtotal.value}
          </span>
          {if $subtotal.type === 'shipping'}
              <div><small class="value">{hook h='displayCheckoutSubtotalDetails' subtotal=$subtotal}</small></div>
          {/if}
        </div>
      {/if}
    {/foreach}
  </div>

  {* shortcut: porównuje z sumą produktów po rabatach na produkty, bez kodów rabatowych - jeśli próg ma liczyć się po kodach, użyć Cart::getOrderTotal w module *}
  {$free_shipping_from = Tools::convertPrice((float) Configuration::get('PS_SHIPPING_FREE_PRICE'))}
  {if $free_shipping_from > 0 && !empty($cart.products) && $cart.subtotals.products.amount < $free_shipping_from}
    <div class="card-block cart-free-shipping">
      <div class="cart-summary-line">
        <span class="label">Do darmowej dostawy brakuje:</span>
        <span class="value">{Context::getContext()->getCurrentLocale()->formatPrice($free_shipping_from - $cart.subtotals.products.amount, $currency.iso_code)}</span>
      </div>
    </div>
  {/if}

  {include file='checkout/_partials/cart-summary-totals.tpl' cart=$cart}
</div>
{/block}
