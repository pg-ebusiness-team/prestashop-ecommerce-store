{* Nagłówek kategorii jak w źródle: duży tytuł i opis, bez karty i zdjęcia kategorii z Classic *}
<div id="js-product-list-header" class="category-header">
  <h1 class="h1">{$category.name}</h1>
  {if $listing.pagination.items_shown_from == 1 && $category.description}
    <div id="category-description">{$category.description nofilter}</div>
  {/if}
</div>
