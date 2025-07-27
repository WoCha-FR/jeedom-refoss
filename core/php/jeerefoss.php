<?php
/* This file is part of Jeedom-Refoss plugin. */

try {
  require_once dirname(__FILE__) . "/../../../../core/php/core.inc.php";

  if (!jeedom::apiAccess(init('apikey'), 'refoss')) {
    echo __('Vous n\'etes pas autorisé à effectuer cette action', __FILE__);
    die();
  }

  if (init('test') != '') {
    echo 'OK';
    log::add('refoss', 'debug', 'test from daemon');
    die();
  }

  $result = json_decode(file_get_contents("php://input"), true);
  if (!is_array($result)) {
    die();
  } elseif (isset($result['discover'])) {
    if ($result['discover']) {
      $message = __('Découverte réussie', __FILE__);
      log::add('refoss', 'info', $message);
      event::add('jeedom::alert', array(
        'level' => 'success',
        'page' => 'refoss',
        'message' => $message,
      ));
      refoss::checkAndUpdateDevice();
    } else {
      $message = __('Echec de la découverte, veuillez consulter le log du démon', __FILE__);
      log::add('refoss', 'warning', $message);
      event::add('jeedom::alert', array(
        'level' => 'warning',
        'page' => 'refoss',
        'message' => $message,
      ));
    }
  } elseif (isset($result['msg'])) {
    if ($result['msg'] == 'NO_DEVICES') {
      message::add('refoss', __('Aucun device configuré, veuillez lancer une découverte depuis la page de gestion des équipements du plugin', __FILE__), '', 'refoss_no_devices');
    }
  }
  echo 'OK';
} catch (Exception $e) {
  log::add('refoss', 'error', displayException($e));
}
