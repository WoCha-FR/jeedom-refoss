<?php
/* This file is part of Jeedom-Refoss plugin. */

try {
  require_once __DIR__ . '/../../../../core/php/core.inc.php';
  include_file('core', 'authentification', 'php');

  if (!isConnect('admin')) {
    throw new Exception(__('401 - Accès non autorisé', __FILE__));
  }

  ajax::init();

  if (init('action') == 'discover') {
    refoss::discoverModule(init('address'));
    ajax::success();
  }

  throw new Exception(__('Aucune méthode correspondante à :', __FILE__) . ' ' . init('action'));
  /*     * *********Catch exeption*************** */
} catch (Exception $e) {
  ajax::error(displayException($e), $e->getCode());
}
