{**
 * Miniatura produktu jak w luksusowealkohole.pl (FRONT-2), na bazie szablonu Classic.
 * Zmiany: wstęga „Promocja” zamiast flag Classic, w rogu zdjęcia tylko ikona oka (szybki podgląd),
 * pasek „Dodaj do koszyka” na dole zdjęcia (AJAX z core.js - data-button-action="add-to-cart"),
 * pełna nazwa (obcina CSS), cena bez procentu rabatu.
 *}
{block name='product_miniature_item'}
<div class="js-product product{if !empty($productClasses)} {$productClasses}{/if}">
  <article class="product-miniature js-product-miniature" data-id-product="{$product.id_product}" data-id-product-attribute="{$product.id_product_attribute}">
    <div class="thumbnail-container">
      <div class="thumbnail-top">
        {block name='product_thumbnail'}
          {if $product.cover}
            <a href="{$product.url}" class="thumbnail product-thumbnail">
              <picture>
                {if !empty($product.cover.bySize.home_default.sources.avif)}<source srcset="{$product.cover.bySize.home_default.sources.avif}" type="image/avif">{/if}
                {if !empty($product.cover.bySize.home_default.sources.webp)}<source srcset="{$product.cover.bySize.home_default.sources.webp}" type="image/webp">{/if}
                <img
                  src="{$product.cover.bySize.home_default.url}"
                  alt="{if !empty($product.cover.legend)}{$product.cover.legend}{else}{$product.name}{/if}"
                  loading="lazy"
                  data-full-size-image-url="{$product.cover.large.url}"
                  width="{$product.cover.bySize.home_default.width}"
                  height="{$product.cover.bySize.home_default.height}"
                />
              </picture>
            </a>
          {else}
            <a href="{$product.url}" class="thumbnail product-thumbnail">
              <picture>
                {if !empty($urls.no_picture_image.bySize.home_default.sources.avif)}<source srcset="{$urls.no_picture_image.bySize.home_default.sources.avif}" type="image/avif">{/if}
                {if !empty($urls.no_picture_image.bySize.home_default.sources.webp)}<source srcset="{$urls.no_picture_image.bySize.home_default.sources.webp}" type="image/webp">{/if}
                <img
                  src="{$urls.no_picture_image.bySize.home_default.url}"
                  alt="{$product.name}"
                  loading="lazy"
                  width="{$urls.no_picture_image.bySize.home_default.width}"
                  height="{$urls.no_picture_image.bySize.home_default.height}"
                />
              </picture>
            </a>
          {/if}
        {/block}

        {block name='quick_view'}
          <a class="quick-view js-quick-view" href="#" data-link-action="quickview" aria-label="{l s='Quick view' d='Shop.Theme.Actions'}" title="{l s='Quick view' d='Shop.Theme.Actions'}">
            <i class="material-icons" aria-hidden="true">visibility</i>
          </a>
        {/block}

        {block name='product_add_to_cart'}
          {if $product.add_to_cart_url}
            <form action="{$urls.pages.cart}" method="post" class="miniature-cart">
              <input type="hidden" name="token" value="{$static_token}">
              <input type="hidden" name="id_product" value="{$product.id_product}">
              <input type="hidden" name="id_product_attribute" value="{$product.id_product_attribute}">
              <input type="hidden" name="id_customization" value="0">
              {* minimal_quantity bywa 0 (produkty z wariantami), a |default nie zamienia zera - koszyk odrzuca qty=0 *}
              <input type="hidden" name="qty" value="{if $product.minimal_quantity > 1}{$product.minimal_quantity}{else}1{/if}">
              <button type="submit" class="miniature-cart-btn" data-button-action="add-to-cart">
                <i class="material-icons" aria-hidden="true">local_mall</i>
                {l s='Add to cart' d='Shop.Theme.Actions'}
              </button>
            </form>
          {else}
            {* Brak w magazynie albo produkt wymaga personalizacji - wybór na stronie produktu *}
            <a class="miniature-cart-btn" href="{$product.url}">Zobacz produkt</a>
          {/if}
        {/block}

        {if $product.has_discount}
          <span class="product-ribbon">Promocja</span>
        {/if}
      </div>

      <div class="product-description">
        {block name='product_name'}
          {if $page.page_name == 'index'}
            <h3 class="h3 product-title"><a href="{$product.url}" content="{$product.url}">{$product.name}</a></h3>
          {else}
            <h2 class="h3 product-title"><a href="{$product.url}" content="{$product.url}">{$product.name}</a></h2>
          {/if}
        {/block}

        {block name='product_price_and_shipping'}
          {if $product.show_price}
            <div class="product-price-and-shipping">
              {if $product.has_discount}
                {hook h='displayProductPriceBlock' product=$product type="old_price"}

                <span class="regular-price" aria-label="{l s='Regular price' d='Shop.Theme.Catalog'}">{$product.regular_price}</span>
              {/if}

              {hook h='displayProductPriceBlock' product=$product type="before_price"}

              <span class="price" aria-label="{l s='Price' d='Shop.Theme.Catalog'}">
                {capture name='custom_price'}{hook h='displayProductPriceBlock' product=$product type='custom_price' hook_origin='products_list'}{/capture}
                {if '' !== $smarty.capture.custom_price}
                  {$smarty.capture.custom_price nofilter}
                {else}
                  {$product.price}
                {/if}
              </span>

              {hook h='displayProductPriceBlock' product=$product type='after_price'}

              {hook h='displayProductPriceBlock' product=$product type='unit_price'}

              {hook h='displayProductPriceBlock' product=$product type='weight'}
            </div>
          {/if}
        {/block}

        {block name='product_reviews'}
          {hook h='displayProductListReviews' product=$product}
        {/block}
      </div>
    </div>
  </article>
</div>
{/block}
