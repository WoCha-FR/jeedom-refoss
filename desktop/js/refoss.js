/* This file is part of Jeedom-Refoss plugin. */
document.getElementById('bt_syncRefoss').addEventListener('click', function () {

  jeeDialog.prompt({
    title: "{{Découverte des équipements}}",
    message: '<b>{{IP du module (optionnelle)}}:</b> <sup><i class="fas fa-question-circle" title="{{uniquement nécessaire si le module est sur un LAN différent de Jeedom}}"></i></sup>',
    placeholder: '255.255.255.255',
  }, function(result, key) {
    if (key == 'confirm') {
      if (result === null) result = '255.255.255.255'
      // Ajax for discovery
      domUtils.ajax({
        type: 'POST',
        url: 'plugins/refoss/core/ajax/refoss.ajax.php',
        dataType: 'json',
        global: false,
        data: {
          action: 'discover',
          address: result,
        },
        error: function (request, status, error) {
          domUtils.handleAjaxError(request, status, error)
        },
        success: function(data) {
          if( data.state != 'ok') {
            jeedomUtils.showAlert({ message: data.result, level: 'danger' })
            return
          }
        },
      })
    }
  })
});

function addCmdToTable(_cmd) {
  if (document.getElementById('table_cmd') == null) return
  if (!isset(_cmd)) {
    var _cmd = { configuration: {} }
  }
  if (!isset(_cmd.configuration)) {
    _cmd.configuration = {}
  }
  var tr = '<tr>'
  tr += '<td class="hidden-xs">'
  tr += '<span class="cmdAttr" data-l1key="id"></span>'
  tr += "</td>"
  tr += "<td>"
  tr += '<div class="input-group">'
  tr += '<input class="cmdAttr form-control input-sm roundedLeft" data-l1key="name" placeholder="{{Nom de la commande}}">'
  tr += '<span class="input-group-btn"><a class="cmdAction btn btn-sm btn-default" data-l1key="chooseIcon" title="{{Choisir une icône}}"><i class="fas fa-icons"></i></a></span>'
  tr += '<span class="cmdAttr input-group-addon roundedRight" data-l1key="display" data-l2key="icon" style="font-size:19px;padding:0 5px 0 0!important;"></span>'
  tr += "</div>"
  tr += "<td>"
  tr += '<input class="cmdAttr form-control input-sm" data-l1key="type" disabled /> '
  tr += '<input class="cmdAttr form-control input-sm" data-l1key="subType" disabled /> '
  tr += "</td>"
  tr += "<td>"
  tr += '<label class="checkbox-inline"><input type="checkbox" class="cmdAttr" data-l1key="isVisible" checked/>{{Afficher}}</label> '
  tr += '<label class="checkbox-inline"><input type="checkbox" class="cmdAttr" data-l1key="isHistorized" checked/>{{Historiser}}</label> '
  tr += '<div style="margin-top:7px;">'
  tr += '<input class="tooltips cmdAttr form-control input-sm" data-l1key="configuration" data-l2key="minValue" placeholder="{{Min}}" title="{{Min}}" style="width:30%;max-width:80px;display:inline-block;margin-right:2px;">'
  tr += '<input class="tooltips cmdAttr form-control input-sm" data-l1key="configuration" data-l2key="maxValue" placeholder="{{Max}}" title="{{Max}}" style="width:30%;max-width:80px;display:inline-block;margin-right:2px;">'
  tr += '<input class="tooltips cmdAttr form-control input-sm" data-l1key="unite" placeholder="Unité" title="{{Unité}}" style="width:30%;max-width:80px;display:inline-block;margin-right:2px;">'
  tr += "</div>"
  tr += "<td>"
  tr += '<span class="cmdAttr" data-l1key="htmlstate"></span>'
  tr += "</td>"
  tr += "<td>"
  if (is_numeric(_cmd.id)) {
    tr += '<a class="btn btn-default btn-xs cmdAction" data-action="configure" title="{{Configuration avancée}}"><i class="fas fa-cogs"></i></a> '
    tr += '<a class="btn btn-default btn-xs cmdAction" data-action="test"><i class="fas fa-rss"></i> {{Tester}}</a>'
  }
  tr += "</td>"
  tr += "<td>"
  tr += '<i class="fas fa-minus-circle pull-right cmdAction cursor" data-action="remove" title="{{Supprimer la commande}}"></i>'
  tr += "</td>"
  tr += "</tr>"
  let newRow = document.createElement('tr')
  newRow.innerHTML = tr
  newRow.addClass('cmd')
  newRow.setAttribute('data-cmd_id', init(_cmd.id))
  document.getElementById('table_cmd').querySelector('tbody').appendChild(newRow)
  jeedom.eqLogic.buildSelectCmd({
    id: document.querySelector('.eqLogicAttr[data-l1key="id"]').jeeValue(),
    filter: { type: 'info' },
    error: function(error) {
      jeedomUtils.showAlert({ message: error.message, level: 'danger' })
    },
    success: function(result) {
      newRow.setJeeValues(_cmd, '.cmdAttr')
      jeedom.cmd.changeType(newRow, init(_cmd.subType))
    }
  })
}
