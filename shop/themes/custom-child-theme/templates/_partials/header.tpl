{**
 * Nagłówek wzorowany na luksusowealkohole.pl (docs/wyglad_strony.md):
 * górny pasek, logo na środku, wyszukiwarka/konto/koszyk po prawej, menu w osobnym pasku.
 * Identyfikatory _desktop_* / _mobile_* zostają z Classic - używa ich JS Classic w widoku mobilnym.
 *}
{block name='header_banner'}
  <div class="header-banner">
    {hook h='displayBanner'}
  </div>
{/block}

{block name='header_nav'}
  <nav class="header-nav">
    <div class="container">
      <div class="row">
        <div class="hidden-sm-down">
          <div class="col-md-6 col-xs-12">
            <a class="header-b2b" href="{$urls.pages.contact}">Poznaj specjalną ofertę dla firm i restauracji »</a>
          </div>
          <div class="col-md-6 header-contact">
            {if $shop.phone}
              <a href="tel:{$shop.phone|replace:' ':''}"><i class="material-icons" aria-hidden="true">&#xE0CD;</i>{$shop.phone}</a>
            {/if}
            {if $shop.email}
              <a href="mailto:{$shop.email}"><i class="material-icons" aria-hidden="true">&#xE0BE;</i>{$shop.email}</a>
            {/if}
          </div>
        </div>
        <div class="hidden-md-up text-sm-center mobile">
          <div class="float-xs-left" id="menu-icon">
            <i class="material-icons d-inline">&#xE5D2;</i>
          </div>
          <div class="float-xs-right" id="_mobile_cart"></div>
          <div class="float-xs-right" id="_mobile_user_info"></div>
          <div class="top-logo" id="_mobile_logo"></div>
          <div class="clearfix"></div>
        </div>
      </div>
    </div>
  </nav>
{/block}

{block name='header_top'}
  <div class="header-top">
    <div class="container">
      <div class="row">
        <div class="col-md-4 hidden-sm-down"></div>
        <div class="col-md-4 hidden-sm-down" id="_desktop_logo">
          {if $shop.logo_details}
            {if $page.page_name == 'index'}
              <h1>
                {renderLogo}
              </h1>
            {else}
              {renderLogo}
            {/if}
          {/if}
        </div>
        <div class="header-top-right col-md-4 col-sm-12">
          {hook h='displaySearch'}
          {* widgety zamiast displayNav2: hook ma też przełączniki języka i waluty, których theme.yml nie potrafi odpiąć *}
          <div class="header-actions">
            {widget name='ps_customersignin'}
            {widget name='ps_shoppingcart'}
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="header-menu">
    <div class="container">
      {hook h='displayTop'}
      <div id="mobile_top_menu_wrapper" class="row hidden-md-up" style="display:none;">
        <div class="js-top-menu mobile" id="_mobile_top_menu"></div>
        <div class="js-top-menu-bottom">
          <div id="_mobile_currency_selector"></div>
          <div id="_mobile_language_selector"></div>
          <div id="_mobile_contact_link"></div>
        </div>
      </div>
    </div>
  </div>
  {if $page.page_name == 'index'}
    <ul class="header-benefits">
      <li><i class="material-icons" aria-hidden="true">&#xE558;</i>Wysyłka gratis od 450 zł*</li>
      <li><i class="material-icons" aria-hidden="true">&#xE8F6;</i>Karty podarunkowe</li>
      <li><a href="{$urls.pages.prices_drop}"><i class="material-icons" aria-hidden="true">&#xE263;</i>Wyjątkowe promocje</a></li>
    </ul>
  {/if}
  {hook h='displayNavFullWidth'}
{/block}
