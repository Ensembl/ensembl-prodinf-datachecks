function selectServerSource() {
  const server_source = document.getElementById('server-source').value;

  if (server_source === 'dbname') {
    dbnameDisplay('block');
    speciesDisplay('none');
    divisionDisplay('none');
    db_typeDisplay('none');

  } else if (server_source === 'species') {
    dbnameDisplay('none');
    speciesDisplay('block');
    divisionDisplay('none');
    db_typeDisplay('block');

  } else if (server_source === 'division') {
    dbnameDisplay('none');
    speciesDisplay('none');
    divisionDisplay('block');
    db_typeDisplay('block');

  }
}

function dbnameDisplay(display_value) {
  document.getElementById('server-dbname').style.display = display_value;

}

function speciesDisplay(display_value) {
  document.getElementById('server-species').style.display = display_value;

}

function divisionDisplay(display_value) {
  document.getElementById('server-division').style.display = display_value;

}

function db_typeDisplay(display_value) {
  document.getElementById('server-db_type').style.display = display_value;
  document.getElementById('server-db_type-label').style.display = display_value;
}
