{* Paginacja jak w źródle: „Wyświetlanie x-y z z” po lewej, numery stron w kwadratach po prawej, strzałki bez tekstu *}
<nav class="pagination" aria-label="{l s='Pagination' d='Shop.Theme.Global'}">
  <div class="pagination-summary">
    {block name='pagination_summary'}
      {l s='Showing %from%-%to% of %total% item(s)' d='Shop.Theme.Catalog' sprintf=['%from%' => $pagination.items_shown_from ,'%to%' => $pagination.items_shown_to, '%total%' => $pagination.total_items]}
    {/block}
  </div>

  {block name='pagination_page_list'}
    {if $pagination.should_be_displayed}
      <ul class="page-list">
        {foreach from=$pagination.pages item="page"}
          <li{if $page.current} class="current"{/if}>
            {if $page.type === 'spacer'}
              <span class="spacer">&hellip;</span>
            {else}
              <a
                rel="{if $page.type === 'previous'}prev{elseif $page.type === 'next'}next{else}nofollow{/if}"
                href="{$page.url}"
                class="{if $page.type === 'previous'}previous {elseif $page.type === 'next'}next {/if}{['disabled' => !$page.clickable, 'js-search-link' => true]|classnames}"
                {if $page.current}aria-current="page"{/if}
              >
                {if $page.type === 'previous'}
                  <i class="material-icons" aria-hidden="true">arrow_back</i><span class="sr-only">{l s='Previous' d='Shop.Theme.Actions'}</span>
                {elseif $page.type === 'next'}
                  <i class="material-icons" aria-hidden="true">arrow_forward</i><span class="sr-only">{l s='Next' d='Shop.Theme.Actions'}</span>
                {else}
                  {$page.page}
                {/if}
              </a>
            {/if}
          </li>
        {/foreach}
      </ul>
    {/if}
  {/block}
</nav>
