<?php
/* This file is part of Jeedom-Refoss plugin. */

require_once dirname(__FILE__) . '/../../../core/php/core.inc.php';
include_file('core', 'authentification', 'php');
if (!isConnect()) {
  include_file('desktop', '404', 'php');
  die();
}
?>

<form class="form-horizontal">
  <fieldset>
    <div class="form-group">
      <label class="col-md-4 control-label">{{Cycle d'actualisation}}
        <sup><i class="fas fa-question-circle tooltips" title="{{en secondes - par défaut 5s}}"></i></sup>
      </label>
      <div class="col-md-4">
        <input class="configKey form-control" data-l1key="refoss::cycle" />
      </div>
    </div>
    <div class="form-group">
      <label class="col-md-4 control-label">{{Port du socket interne (pour éviter un conflit avec un autre plugin)}}
        <sup><i class="fas fa-question-circle tooltips" title="{{55182 par défaut si non précisé}}"></i></sup>
      </label>
      <div class="col-md-4">
        <input class="configKey form-control" data-l1key="refoss::socketport" />
      </div>
    </div>
  </fieldset>
</form>