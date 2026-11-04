{* Każdy blok linków to osobna kolumna stopki (templates/_partials/footer.tpl), bez zwijania z Classic *}
{foreach $linkBlocks as $linkBlock}
  <nav class="footer-links" aria-labelledby="footer-links-{$linkBlock.id}">
    <p class="h3" id="footer-links-{$linkBlock.id}">{$linkBlock.title}</p>
    <ul>
      {foreach $linkBlock.links as $link}
        <li>
          <a id="{$link.id}-{$linkBlock.id}" class="{$link.class}" href="{$link.url}" title="{$link.description}"{if !empty($link.target)} target="{$link.target}"{/if}>{$link.title}</a>
        </li>
      {/foreach}
    </ul>
  </nav>
{/foreach}
