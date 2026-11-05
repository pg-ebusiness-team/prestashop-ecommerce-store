{* Kolumna „Subskrybuj newsletter” w stopce; pola formularza i hooki zgód jak w Classic *}
<div class="block_newsletter footer-newsletter" id="blockEmailSubscription_{$hookName}">
  <p class="h3">Subskrybuj newsletter</p>
  <p id="block-newsletter-label">Subskrybuj nasz newsletter by otrzymywać nowinki ze świata alkoholi.</p>
  <form action="{$urls.current_url}#blockEmailSubscription_{$hookName}" method="post">
    <div class="footer-newsletter-field">
      <input name="email" type="email" value="{$value}" placeholder="{l s='Your email address' d='Shop.Forms.Labels'}" aria-labelledby="block-newsletter-label" required>
      <button type="submit" name="submitNewsletter" value="1" aria-label="{l s='Subscribe' d='Shop.Theme.Actions'}">
        <i class="material-icons" aria-hidden="true">mail_outline</i>
      </button>
    </div>
    <input type="hidden" name="blockHookName" value="{$hookName}">
    <input type="hidden" name="action" value="0">
    {if $conditions}
      <p class="footer-newsletter-conditions">{$conditions}</p>
    {/if}
    {if $msg}
      <p class="alert {if $nw_error}alert-danger{else}alert-success{/if}">{$msg}</p>
    {/if}
    {hook h='displayNewsletterRegistration'}
    {if isset($id_module)}
      {hook h='displayGDPRConsent' id_module=$id_module}
    {/if}
  </form>
</div>
