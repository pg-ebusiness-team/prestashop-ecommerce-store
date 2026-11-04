{**
 * Kategoria jak w źródle (FRONT-2): tytuł, opis i podkategorie na całą szerokość nad lewą kolumną z filtrami.
 * Blok breadcrumb leży w layoucie przed wierszem kolumn, więc dokładamy tam nagłówek; w prawej kolumnie go usuwamy.
 * id="js-product-list-header" zostaje - ps_facetedsearch podmienia ten element po filtrowaniu (AJAX).
 *}
{extends file='parent:catalog/listing/category.tpl'}

{block name='breadcrumb'}
  {$smarty.block.parent}
  {include file='catalog/_partials/category-header.tpl' listing=$listing category=$category}
  {if isset($subcategories) && $subcategories|@count > 0}
    {include file='catalog/_partials/subcategories.tpl' subcategories=$subcategories}
  {/if}
{/block}

{block name='product_list_header'}{/block}
{block name='subcategory_list'}{/block}
