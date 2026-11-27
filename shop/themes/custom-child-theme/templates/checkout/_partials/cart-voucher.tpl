{**
 * Kod rabatowy (Classic) jak w źródle: pole zawsze widoczne, bez zwijanego „Masz kod promocyjny?”.
 * Nagłówek boksu jest w checkout/cart.tpl, bo ten plik odświeża AJAX (.js-cart-voucher).
 * W podsumowaniu zamówienia (checkout) Classic też go używa - tam pole też jest od razu widoczne.
 * Bez {if $cart.vouchers.allowed}: sklep nie ma reguł koszyka, a pole ma być zawsze (odpowiedź daje custom.js).
 *}
  {block name='cart_voucher'}
    <div class="block-promo">
      <div class="cart-voucher js-cart-voucher">
        {if $cart.vouchers.added}
          <ul class="promo-name card-block">
            {foreach from=$cart.vouchers.added item=voucher}
              <li class="cart-summary-line">
                <span class="label">{$voucher.name}</span>
                <div class="float-xs-right">
                  <span>{$voucher.reduction_formatted}</span>
                  {if isset($voucher.code) && $voucher.code !== ''}
                    <a href="{$voucher.delete_url}" data-link-action="remove-voucher" aria-label="{l s='Remove' d='Shop.Theme.Actions'}"><i class="material-icons" aria-hidden="true">&#xE872;</i></a>
                  {/if}
                </div>
              </li>
            {/foreach}
          </ul>
        {/if}

        <div id="promo-code" class="promo-code">
          <form action="{$urls.pages.cart}" data-link-action="add-voucher" method="post">
            <input type="hidden" name="token" value="{$static_token}">
            <input type="hidden" name="addDiscount" value="1">
            <input class="promo-input" type="text" name="discount_name" placeholder="Wpisz kod rabatowy" aria-label="{l s='Promo code' d='Shop.Theme.Checkout'}">
            <button type="submit" class="btn btn-primary"><span>Zastosuj</span></button>
          </form>
          <div class="alert alert-danger js-error" role="alert">
            <i class="material-icons" aria-hidden="true">&#xE001;</i><span class="ml-1 js-error-text"></span>
          </div>
        </div>

        {if $cart.discounts|count > 0}
          <p class="block-promo promo-highlighted">
            {l s='Take advantage of our exclusive offers:' d='Shop.Theme.Actions'}
          </p>
          <ul class="js-discount card-block promo-discounts">
            {foreach from=$cart.discounts item=discount}
              <li class="cart-summary-line">
                <span class="label"><span class="code">{$discount.code}</span> - {$discount.name}</span>
              </li>
            {/foreach}
          </ul>
        {/if}
      </div>
    </div>
  {/block}
