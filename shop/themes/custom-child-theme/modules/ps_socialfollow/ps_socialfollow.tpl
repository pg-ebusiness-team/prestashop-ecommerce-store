{* Ikony social media w dolnym pasku stopki (ikony SVG z Classic, szare warianty .icon-gray) *}
{block name='block_social'}
  {if $social_links}
    <div class="block-social">
      <ul>
        {foreach from=$social_links item='social_link'}
          <li class="{$social_link.class} icon-gray"><a href="{$social_link.url}" target="_blank" rel="noopener noreferrer">{$social_link.label}</a></li>
        {/foreach}
      </ul>
    </div>
  {/if}
{/block}
