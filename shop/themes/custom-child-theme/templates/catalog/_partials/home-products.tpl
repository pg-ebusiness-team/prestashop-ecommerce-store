{**
 * Siatka produktów z przyciskiem pod spodem (FRONT-2) - wspólna dla modułów na stronie głównej
 * (szablony w modules/*). Parametry: products, link, linkLabel.
 *}
{include file="catalog/_partials/productlist.tpl" products=$products cssClass="row" productClass="col-xs-12 col-sm-6 col-lg-3"}
<div class="home-products-more">
  <a class="btn btn-outline-primary" href="{$link}">{$linkLabel}</a>
</div>
