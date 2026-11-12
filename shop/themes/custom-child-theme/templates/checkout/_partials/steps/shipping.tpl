{**
 * Krok „Dostawa” w zamówieniu (Classic 2.2.0) - zmieniony tylko komunikat przy braku przewoźników.
 * Classic pisze „brak przewoźników dla Twojego adresu”, co przy naszej konfiguracji myli klienta: aktywna jest tylko
 * Polska, a obaj przewoźnicy ją obsługują, więc jedyną przyczyną braku przewoźnika jest przekroczony limit wagi
 * zamówienia (max_weight z shop/scripts/configure-sales.php, zmienna MAX_ORDER_WEIGHT_KG w deploy/compose.yaml).
 * Limitu nie wpisujemy w tekst, żeby nie rozjechał się z konfiguracją - link prowadzi do strony CMS „Dostawa” (id 1).
 * Komunikat nie jest w osobnym bloku Classic, dlatego nadpisujemy cały blok step_content (reszta bez zmian).
 *}
{extends file='parent:checkout/_partials/steps/shipping.tpl'}

{block name='step_content'}
  <div id="hook-display-before-carrier">
    {$hookDisplayBeforeCarrier nofilter}
  </div>

  <div class="delivery-options-list">
    {if $delivery_options|count}
      <form
        class="clearfix"
        id="js-delivery"
        data-url-update="{url entity='order' params=['ajax' => 1, 'action' => 'selectDeliveryOption']}"
        method="post"
      >
        <div class="form-fields">
          {block name='delivery_options'}
            <div class="delivery-options">
              {foreach from=$delivery_options item=carrier key=carrier_id}
                  <div class="delivery-option js-delivery-option">
                    <div class="col-sm-1">
                      <span class="custom-radio float-xs-left">
                        <input type="radio" name="delivery_option[{$id_address}]" id="delivery_option_{$carrier.id}" value="{$carrier_id}"{if $delivery_option == $carrier_id} checked{/if}>
                        <span></span>
                      </span>
                    </div>
                    <label for="delivery_option_{$carrier.id}" class="col-xs-9 col-sm-11 delivery-option-2">
                      <div class="row">
                        <div class="col-sm-5 col-xs-12">
                          <div class="row carrier{if $carrier.logo} carrier-hasLogo{/if}">
                            {if $carrier.logo}
                            <div class="col-xs-12 col-md-4 carrier-logo">
                                <img src="{$carrier.logo}" alt="{$carrier.name}" loading="lazy" />
                            </div>
                            {/if}
                            <div class="col-xs-12 carriere-name-container{if $carrier.logo} col-md-8{/if}">
                              <span class="h6 carrier-name">{$carrier.name}</span>
                            </div>
                          </div>
                        </div>
                        <div class="col-sm-4 col-xs-12">
                          <span class="carrier-delay">{$carrier.delay}</span>
                        </div>
                        <div class="col-sm-3 col-xs-12">
                          <span class="carrier-price">{$carrier.price}</span>
                        </div>
                      </div>
                    </label>
                  </div>
                  <div class="carrier-extra-content js-carrier-extra-content"{if ($delivery_option != $carrier_id) || ($delivery_option == $carrier_id && empty($carrier.extraContent))} style="display:none;"{/if}>
                    {$carrier.extraContent nofilter}
                  </div>
                  <div class="clearfix"></div>
              {/foreach}
            </div>
          {/block}
          <div class="order-options">
            <div id="delivery">
              <label for="delivery_message">{l s='If you would like to add a comment about your order, please write it in the field below.' d='Shop.Theme.Checkout'}</label>
              <textarea rows="2" cols="120" id="delivery_message" name="delivery_message">{$delivery_message}</textarea>
            </div>

            {if $recyclablePackAllowed}
              <span class="custom-checkbox">
                <input type="checkbox" id="input_recyclable" name="recyclable" value="1" {if $recyclable} checked {/if}>
                <span><i class="material-icons rtl-no-flip checkbox-checked">&#xE5CA;</i></span>
                <label for="input_recyclable">{l s='I would like to receive my order in recycled packaging.' d='Shop.Theme.Checkout'}</label>
              </span>
            {/if}

            {if $gift.allowed}
              <span class="custom-checkbox">
                <input class="js-gift-checkbox" id="input_gift" name="gift" type="checkbox" value="1" {if $gift.isGift}checked="checked"{/if}>
                <span><i class="material-icons rtl-no-flip checkbox-checked">&#xE5CA;</i></span>
                <label for="input_gift">{$gift.label}</label >
              </span>

              <div id="gift" class="collapse{if $gift.isGift} in{/if}">
                <label for="gift_message">{l s='If you\'d like, you can add a note to the gift:' d='Shop.Theme.Checkout'}</label>
                <textarea rows="2" cols="120" id="gift_message" name="gift_message">{$gift.message}</textarea>
              </div>
            {/if}

          </div>
        </div>
        <button type="submit" class="continue btn btn-primary float-xs-right" name="confirmDeliveryOption" value="1">
          {l s='Continue' d='Shop.Theme.Actions'}
        </button>
      </form>
    {else}
      <p class="alert alert-danger">
        Zamówienie przekracza maksymalną wagę przesyłki, dlatego nie możemy go wysłać.
        Zmniejsz liczbę produktów w koszyku. Większe zamówienia realizujemy indywidualnie - szczegóły na stronie
        <a href="{url entity='cms' id=1}">Dostawa</a>.
      </p>
    {/if}
  </div>

  <div id="hook-display-after-carrier">
    {$hookDisplayAfterCarrier nofilter}
  </div>

  <div id="extra_carrier"></div>
{/block}
