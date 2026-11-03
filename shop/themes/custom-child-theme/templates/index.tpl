{**
 * Strona główna (FRONT-2): po displayHome (slider, kafelki, banery) sekcja „W naszej ofercie”
 * z zakładkami Wszystkie / Bestsellery / Nowości (zakładki Bootstrapa z Classic, bez własnego JS) i „Kup taniej”.
 * Moduły produktów są podpięte pod własny hook displayHomeProducts (config/theme.yml).
 *}
{extends file='parent:index.tpl'}

{block name='page_content'}
  {block name='hook_home'}
    {$HOOK_HOME nofilter}
  {/block}

  {capture name='offer_all'}{hook h='displayHomeProducts' mod='ps_featuredproducts'}{/capture}
  {capture name='offer_best'}{hook h='displayHomeProducts' mod='ps_bestsellers'}{/capture}
  {capture name='offer_new'}{hook h='displayHomeProducts' mod='ps_newproducts'}{/capture}
  {* Moduł bez produktów (np. bestsellery bez zamówień) nie zwraca nic - wtedy pomijamy jego zakładkę *}
  {$offer_tabs = [
    ['id' => 'offer-all', 'label' => 'Wszystkie', 'html' => $smarty.capture.offer_all|trim],
    ['id' => 'offer-best', 'label' => 'Bestsellery', 'html' => $smarty.capture.offer_best|trim],
    ['id' => 'offer-new', 'label' => 'Nowości', 'html' => $smarty.capture.offer_new|trim]
  ]}
  {$offer_active = null}

  <section class="featured-products home-products home-products--grey home-offer">
    <h2 class="h2 products-section-title">W naszej ofercie</h2>
    <ul class="nav nav-tabs home-tabs" role="tablist">
      {foreach $offer_tabs as $tab}
        {if $tab.html}
          <li class="nav-item">
            <a class="nav-link{if !$offer_active} active{/if}" data-toggle="tab" href="#{$tab.id}" id="{$tab.id}-tab" role="tab" aria-controls="{$tab.id}" aria-selected="{if !$offer_active}true{else}false{/if}">{$tab.label}</a>
          </li>
          {if !$offer_active}{$offer_active = $tab.id}{/if}
        {/if}
      {/foreach}
    </ul>
    <div class="tab-content">
      {foreach $offer_tabs as $tab}
        {if $tab.html}
          <div class="tab-pane fade{if $tab.id == $offer_active} in active{/if}" id="{$tab.id}" role="tabpanel" aria-labelledby="{$tab.id}-tab">
            {$tab.html nofilter}
          </div>
        {/if}
      {/foreach}
    </div>
  </section>

  {hook h='displayHomeProducts' mod='ps_specials'}
{/block}
