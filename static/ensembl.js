function selectServerSource() {
  var server_source = document.getElementById('server-source').value;

  if (server_source == 'database') {
    databaseDisplay('block');
    speciesDisplay('none');
    divisionDisplay('none');
    releaseDisplay('none');

  } else if (server_source == 'species') {
    databaseDisplay('none');
    speciesDisplay('block');
    divisionDisplay('none');
    releaseDisplay('block');

  } else if (server_source == 'division') {
    databaseDisplay('none');
    speciesDisplay('none');
    divisionDisplay('block');
    releaseDisplay('block');

  }
}

function selectDivision() {
  var division = document.getElementById('server-division').value;

  document.getElementById('configuration-config_profile').value = division;
}

function databaseDisplay(display_value) {
  document.getElementById('server-database').style.display = display_value;
}

function speciesDisplay(display_value) {
  document.getElementById('server-species').style.display = display_value;
}

function divisionDisplay(display_value) {
  document.getElementById('server-division').style.display = display_value;
}

function releaseDisplay(display_value) {
  document.getElementById('server-database_type').style.display = display_value;
  document.getElementById('server-database_type-label').style.display = display_value;
  document.getElementById('server-release').style.display = display_value;
  document.getElementById('server-release-label').style.display = display_value;
}
