/* .. See the NOTICE file distributed with this work for additional information
    regarding copyright ownership.
    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at
        http://www.apache.org/licenses/LICENSE-2.0
    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.*/

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
