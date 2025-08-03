<?php
/* This file is part of Jeedom-Refoss plugin. */

/* * ***************************Includes********************************* */
require_once __DIR__  . '/../../../../core/php/core.inc.php';

class refoss extends eqLogic
{
  private static $_restart_daemon = false;

  /** Static Functions */
  public static function discoverModule($address = '255.255.255.255')
  {
    $deamon_info = self::deamon_info();
    if ($deamon_info['state'] != 'ok') {
      throw new RuntimeException(__('Le démon n\'est pas démarré', __FILE__));
    }
    if ($address == '') $address = '255.255.255.255';
    if ($address == '255.255.255.255') {
      log::add(__CLASS__, 'info', __('Découverte des modules sur tout le réseau...', __FILE__));
    } else {
      log::add(__CLASS__, 'info', sprintf(__("Découverte du module avec l'ip %s", __FILE__), $address));
    }
    self::sendToDaemon(array(
      'action' => 'discover',
      'address' => $address
    ));
  }

  public static function sendToDaemon($params)
  {
    log::add(__CLASS__, 'debug', 'params to send to daemon:' . json_encode($params));
    $params['apikey'] = jeedom::getApiKey(__CLASS__);
    $payLoad = json_encode($params);
    $socket = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
    socket_connect($socket, '127.0.0.1', self::getSocketPort());
    socket_write($socket, $payLoad, strlen($payLoad));
    socket_close($socket);
  }

  protected static function getSocketPort()
  {
    return config::byKey('refoss::socketport', __CLASS__, 55182);
  }

  public static function checkAndUpdateDevice()
  {
    // JSON File
    $file = __DIR__ . '/../../data/config.json';
    if (!file_exists($file)) {
      log::add(__CLASS__, 'debug', '[' . __FUNCTION__ . '] ' . __('Fichier de configuration absent.', __FILE__));
      return;
    }
    // File Content
    $content = is_json(file_get_contents($file), false);
    if ($content === false) {
      log::add(__CLASS__, 'debug', '[' . __FUNCTION__ . '] ' . __('Fichier de configuration incorrect.', __FILE__));
      return;
    }
    // JSON Object
    foreach ($content as $uuid => $data) {
      $eqLogic = self::byLogicalId($uuid, __CLASS__);
      if (!is_object($eqLogic)) {
        // Paramètres fixes
        $eqLogic = new refoss();
        $eqLogic->setEqType_name(__CLASS__);
        $eqLogic->setLogicalId($uuid);
        $eqLogic->setName($data['devName'].'-'. $data['uuid']);
        $eqLogic->setConfiguration('hardware', $data['devHardWare']);
        $eqLogic->setConfiguration('mac', $data['mac']);
        $eqLogic->setConfiguration('uuid', $data['uuid']);
        $eqLogic->setConfiguration('device', $data['deviceType']);
        $eqLogic->setConfiguration('subtype', $data['subType']);
        $eqLogic->setIsVisible(1);
        $eqLogic->setIsEnable(1);
        event::add('refoss::newDevice');
      }
      // Paramètres evolutifs
      $eqLogic->setConfiguration('ip', $data['ip']);
      $eqLogic->setConfiguration('software', $data['devSoftWare']);
      $eqLogic->save();
    }
  }

  public function preUpdate()
  {
    if ($this->getIsEnable() != eqLogic::byId($this->getId())->getIsEnable()) {
      self::$_restart_daemon = true;
    }
  }

  public function postUpdate()
  {
    if (self::$_restart_daemon) {
      log::add(__CLASS__, 'debug', '[' . __FUNCTION__ . '] ' . __('Equipements actifs modifiés, redémarrage du démon. ', __FILE__));
      self::executeAsync('deamon_start');
    }
  }

  public function postSave()
  {
    if ($this->getConfiguration('applyDevice') != $this->getConfiguration('device')) {
      $this->setConfiguration('applyDevice', $this->getConfiguration('device'));
      $this->save();
      if ($this->getConfiguration('device') == '') {
        return true;
      }
      $device = self::devicesParameters($this->getConfiguration('device'));
      if (!is_array($device)) {
        return true;
      }
      $this->import($device, true);
      log::add(__CLASS__, 'info', '[' . __FUNCTION__ . '] ' . __('Création des commandes pour un device de type ', __FILE__) . $this->getConfiguration('device'));
    }
  }

  private static function devicesParameters($_device = '')
  {
    $return = array();
    $files = ls(__DIR__ . '/../config/devices', '*.json', false, array('files', 'quiet'));
    foreach ($files as $file) {
      try {
        $return[str_replace('.json', '', $file)] = is_json(file_get_contents(__DIR__ . '/../config/devices/' . $file), false);
      } catch (Exception $e) {
      }
    }
    if (isset($_device) && $_device != '') {
      if (isset($return[$_device])) {
        return $return[$_device];
      }
      return array();
    }
    return $return;
  }

  public function getImage()
  {
    if (file_exists(__DIR__ . '/../config/devices/' .  $this->getConfiguration('device') . '.png')) {
      return 'plugins/refoss/core/config/devices/' .  $this->getConfiguration('device') . '.png';
    }
    return false;
  }

  private static function executeAsync(string $_method, $_date = 'now')
  {
    if (!method_exists(__CLASS__, $_method)) {
      throw new InvalidArgumentException("Method provided for executeAsync does not exist: {$_method}");
    }

    $cron = new cron();
    $cron->setClass(__CLASS__);
    $cron->setFunction($_method);
    $cron->setOnce(1);
    $scheduleTime = strtotime($_date);
    $cron->setSchedule(cron::convertDateToCron($scheduleTime));
    $cron->save();
    $cron->run();
  }

  /** DEAMON */
  public static function deamon_info()
  {
    $return = array();
    $return['log'] = __CLASS__;
    $return['launchable'] = 'ok';
    $return['state'] = 'nok';
    $pid_file = jeedom::getTmpFolder(__CLASS__) . '/daemon.pid';
    if (file_exists($pid_file)) {
      if (@posix_getsid(trim(file_get_contents($pid_file)))) {
        $return['state'] = 'ok';
      } else {
        shell_exec(system::getCmdSudo() . 'rm -rf ' . $pid_file . ' 2>&1 > /dev/null');
      }
    }
    return $return;
  }

  public static function deamon_stop()
  {
    $pid_file = jeedom::getTmpFolder(__CLASS__) . '/daemon.pid';
    if (file_exists($pid_file)) {
      $pid = intval(trim(file_get_contents($pid_file)));
      system::kill($pid);
    }
    sleep(1);
    system::kill('refossd.py');
    sleep(1);
  }

  public static function deamon_start()
  {
    self::deamon_stop();
    $deamon_info = self::deamon_info();
    if ($deamon_info['launchable'] != 'ok') {
      throw new Exception(__('Veuillez vérifier la configuration', __FILE__));
    }
    message::removeAll(__CLASS__, 'refoss_no_devices');

    $excluded_uuid = '';
    foreach (eqLogic::byType(__CLASS__) as $eqlogic) {
      if ($eqlogic->getIsEnable() == 0) {
        $excluded_uuid .= $eqlogic->getLogicalId() . ',';
      }
    }

    $path = realpath(dirname(__FILE__) . '/../../resources/refossd');
    $cmd = self::getPython3() . "{$path}/refossd.py";
    $cmd .= ' --loglevel ' . log::convertLogLevel(log::getLogLevel(__CLASS__));
    $cmd .= ' --socketport ' . self::getSocketPort();
    $cmd .= ' --actu ' . config::byKey('refoss::cycle', __CLASS__, 5);
    $cmd .= " --excluded_uuid '{$excluded_uuid}'";
    $cmd .= ' --callback ' . network::getNetworkAccess('internal', 'proto:127.0.0.1:port:comp') . '/plugins/refoss/core/php/jeerefoss.php';
    $cmd .= ' --apikey ' . jeedom::getApiKey(__CLASS__);
    $cmd .= ' --pid ' . jeedom::getTmpFolder(__CLASS__) . '/daemon.pid';
    log::add(__CLASS__, 'info', 'Lancement démon:' . self::getPython3() . "{$path}/refossd.py");
    $result = exec($cmd . ' >> ' . log::getPathToLog(__CLASS__ . '_daemon') . ' 2>&1 &');
    $i = 0;
    while ($i < 10) {
      $deamon_info = self::deamon_info();
      if ($deamon_info['state'] == 'ok') {
        break;
      }
      sleep(1);
      $i++;
    }
    if ($i >= 10) {
      log::add(__CLASS__, 'error', __('Impossible de lancer le démon', __FILE__), 'unableStartDeamon');
      return false;
    }
    message::removeAll(__CLASS__, 'unableStartDeamon');

    return true;
  }

  public static function backupExclude()
  {
    return [
      'resources/venv'
    ];
  }

  private static function getPython3()
  {
    if (method_exists('system', 'getCmdPython3')) {
      return system::getCmdPython3(__CLASS__);
    }
    return 'python3 ';
  }
}

class refossCmd extends cmd {}
