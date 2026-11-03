{* Podkategorie jak w źródle: same nazwy w prostokątnych ramkach, bez zdjęć *}
{if !empty($subcategories) && (!isset($display_subcategories) || $display_subcategories eq 1)}
  <section id="subcategories">
    <h2 class="subcategory-heading">{l s='Subcategories' d='Shop.Theme.Category'}</h2>
    <ul class="subcategories-list">
      {foreach from=$subcategories item=subcategory}
        <li><a class="subcategory-name" href="{$subcategory.url}">{$subcategory.name|escape:'html':'UTF-8'}</a></li>
      {/foreach}
    </ul>
  </section>
{/if}
