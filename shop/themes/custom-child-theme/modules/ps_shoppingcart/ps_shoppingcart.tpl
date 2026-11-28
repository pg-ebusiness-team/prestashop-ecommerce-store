{**
 * Kliknięcie w koszyk w nagłówku rozwija podgląd (produkty, suma, przejście do koszyka) zamiast od razu
 * otwierać stronę koszyka - na desktopie i telefonie (Classic przenosi cały .blockcart do #_mobile_cart).
 * Otwieranie/zamykanie: assets/js/custom.js. ps_shoppingcart.js po każdej zmianie koszyka podmienia cały
 * .blockcart na świeżo wyrenderowany szablon, więc podgląd sam pokazuje aktualną zawartość.
 * Przycisk zawsze aktywny, także przy pustym koszyku (Classic renderuje link tylko przy products_count > 0).
 *}
<div id="_desktop_cart">
  <div class="blockcart cart-preview {if $cart.products_count > 0}active{else}inactive{/if}" data-refresh-url="{$refresh_url}">
    <div class="header">
      <button type="button" class="btn-unstyle cart-toggle" aria-expanded="false" aria-controls="cart-dropdown" aria-label="{l s='Shopping cart link containing %nbProducts% product(s)' sprintf=['%nbProducts%' => $cart.products_count] d='Shop.Theme.Checkout'}">
        <i class="material-icons shopping-cart" aria-hidden="true">shopping_cart</i>
        <span class="hidden-sm-down">{l s='Cart' d='Shop.Theme.Checkout'}</span>
        <span class="cart-products-count">({$cart.products_count})</span>
      </button>
    </div>
    <div class="cart-dropdown" id="cart-dropdown" hidden>
      {if $cart.products_count > 0}
        <ul class="cart-dropdown-products">
          {foreach from=$cart.products item=product}
            <li class="cart-dropdown-product">
              <a href="{$product.url}" tabindex="-1" aria-hidden="true">
                <img src="{if $product.default_image}{$product.default_image.small.url}{else}{$urls.no_picture_image.bySize.small_default.url}{/if}" alt="" width="64" height="64" loading="lazy">
              </a>
              <div>
                <a class="cart-dropdown-name" href="{$product.url}">{$product.name}</a>
                {foreach from=$product.attributes key=property item=value}
                  <span class="cart-dropdown-attr">{$property}: {$value}</span>
                {/foreach}
                <span class="cart-dropdown-qty">{$product.quantity} × {$product.price}</span>
              </div>
            </li>
          {/foreach}
        </ul>
        <p class="cart-dropdown-total">
          <span>{$cart.totals.total.label}</span>
          <strong>{$cart.totals.total.value}</strong>
        </p>
        <a class="btn btn-primary btn-block" href="{$cart_url}" rel="nofollow">Przejdź do koszyka</a>
      {else}
        <p class="cart-dropdown-empty">Twój koszyk jest pusty.</p>
      {/if}
    </div>
  </div>
</div>
