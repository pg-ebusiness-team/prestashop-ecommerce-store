{**
 * Strona produktu jak w źródle (FRONT-2), na bazie Classic:
 * - lewa połowa: zdjęcie w ramce, miniatury, uwaga o możliwej różnicy zdjęcia (bez flag „Nowy”/„-20%”);
 * - prawa połowa w kolejności źródła: nazwa, krótki opis, indeks, warianty, cena, ilość i „Dodaj do koszyka”;
 * - pod spodem, zamiast zakładek Classic, dwie kolumny „Opis produktu” i „Szczegóły” (cechy produktu),
 *   potem „Kup razem z” (akcesoria produktu) i „Podobne produkty” (ps_categoryproducts w displayFooterProduct).
 * Ceny zostają w .product-container - core.js podmienia je po zmianie wariantu.
 *}
{extends file='parent:catalog/product.tpl'}

{block name='page_content'}
  {block name='product_cover_thumbnails'}
    {include file='catalog/_partials/product-cover-thumbnails.tpl'}
  {/block}
  <div class="scroll-box-arrows">
    <i class="material-icons left">&#xE314;</i>
    <i class="material-icons right">&#xE315;</i>
  </div>
  <p class="product-image-note"><strong>Uwaga:</strong> Zdjęcie produktu może różnić się od rzeczywistej butelki lub opakowania w zależności od partii produkcji lub rocznika. Zachęcamy do zapoznania się z opisem produktu przed dokonaniem zakupu.</p>
{/block}

{* Cena jest niżej, między wariantami a przyciskiem (blok product_discounts) *}
{block name='product_prices'}{/block}

{block name='product_description_short'}
  <div id="product-description-short-{$product.id}" class="product-description">{$product.description_short nofilter}</div>
  {if $product.reference_to_display}
    <p class="product-reference-line"><strong>{l s='Reference' d='Shop.Theme.Catalog'}:</strong> {$product.reference_to_display}</p>
  {/if}
{/block}

{block name='product_discounts'}
  {include file='catalog/_partials/product-prices.tpl'}
  {$smarty.block.parent}
{/block}

{block name='product_tabs'}{/block}

{block name='product_accessories'}
  {if $product.description || $product.grouped_features}
    <section class="product-info-columns">
      <div class="product-info-col">
        {if $product.description}
          <h2 class="product-info-title">Opis produktu</h2>
          <div class="product-description">{$product.description nofilter}</div>
        {/if}
      </div>
      <div class="product-info-col">
        {if $product.grouped_features}
          <h2 class="product-info-title">Szczegóły</h2>
          <table class="product-features-table">
            {foreach from=$product.grouped_features item=feature}
              <tr>
                <th scope="row">{$feature.name}</th>
                <td>{$feature.value|escape:'htmlall'|nl2br nofilter}</td>
              </tr>
            {/foreach}
          </table>
        {/if}
      </div>
    </section>
  {/if}

  {if $accessories}
    <section class="featured-products home-products home-products--grey product-accessories">
      <h2 class="h2 products-section-title">Kup razem z</h2>
      {include file='catalog/_partials/productlist.tpl' products=$accessories cssClass='row' productClass='col-xs-12 col-sm-6 col-lg-3'}
    </section>
  {/if}
{/block}
