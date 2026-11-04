{**
 * Ścieżka jak w Classic, ale bez wewnętrznego {block name='breadcrumb'}: ma tę samą nazwę co blok layoutu,
 * więc catalog/listing/category.tpl, nadpisując blok layoutu, nadpisywałby też ten (podwójny nagłówek kategorii).
 *}
<nav data-depth="{$breadcrumb.count}" class="breadcrumb">
  <ol>
    {foreach from=$breadcrumb.links item=path name=breadcrumb}
      {block name='breadcrumb_item'}
        <li>
          {if not $smarty.foreach.breadcrumb.last}
            <a href="{$path.url}"><span>{$path.title}</span></a>
          {else}
            <span>{$path.title}</span>
          {/if}
        </li>
      {/block}
    {/foreach}
  </ol>
</nav>
