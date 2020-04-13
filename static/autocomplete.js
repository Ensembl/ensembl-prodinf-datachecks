$(document).ready(function(){
    /* Something like this, somewhere, to enable matches other than at start
    function(d){
        var tokens = [];
        //the available string is 'name' in your datum
        var stringSize = d.name.length;
        //multiple combinations for every available size
        //(eg. dog = d, o, g, do, og, dog)
        for (var size = 1; size <= stringSize; size++){
          for (var i = 0; i+size<= stringSize; i++){
              tokens.push(d.name.substr(i, size));
          }
        }

        return tokens;
    }
    */

    var datacheck_name_list = new Bloodhound({
        datumTokenizer: Bloodhound.tokenizers.whitespace,
        queryTokenizer: Bloodhound.tokenizers.whitespace,
        prefetch: 'names/list'
    });

    $('#datacheck-datacheck_name').tagsinput({
        typeaheadjs: {
            highlight: true,
            name: 'datacheck_name_list',
            source: datacheck_name_list
        }
    });

    var datacheck_group_list = new Bloodhound({
        datumTokenizer: Bloodhound.tokenizers.whitespace,
        queryTokenizer: Bloodhound.tokenizers.whitespace,
        prefetch: 'groups/list'
    });

    $('#datacheck-datacheck_group').tagsinput({
        typeaheadjs: {
            highlight: true,
            name: 'datacheck_group_list',
            source: datacheck_group_list
        }
    });

    var datacheck_database_list = new Bloodhound({
        datumTokenizer: Bloodhound.tokenizers.whitespace,
        queryTokenizer: Bloodhound.tokenizers.whitespace
    });

    /* Not working...
    $('#server-database').tagsinput({
        typeaheadjs: {
            remote: {
                url: '/databases/list?db_uri=',
                prepare: function (query, settings) {
                    settings.url += encodeURIComponent($('#server-server_url').val());

                    return settings;
                }
            },
            highlight: true,
            name: 'datacheck_database_list',
            source: datacheck_database_list
        }
    });
    */
});
