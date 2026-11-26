{* Nagłówek kategorii jak w źródle: duży tytuł i opis, bez karty i zdjęcia kategorii z Classic.
   Dalsza część opisu (additional_description) zwinięta pod przyciskiem „Pokaż więcej” - collapse z Bootstrapa Classic. *}
<div id="js-product-list-header" class="category-header">
  <h1 class="h1">{$category.name}</h1>
  {if $listing.pagination.items_shown_from == 1 && $category.description}
    <div id="category-description">{$category.description nofilter}</div>
    {if $category.additional_description}
      <button class="category-more" type="button" data-toggle="collapse" data-target="#category-additional-description"
              aria-expanded="false" aria-controls="category-additional-description">
        Pokaż więcej
        <i class="material-icons" aria-hidden="true">&#xE313;</i>
      </button>
      <div id="category-additional-description" class="collapse">{$category.additional_description nofilter}</div>
    {/if}
  {/if}
</div>
