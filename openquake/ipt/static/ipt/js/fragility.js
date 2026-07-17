/*
   Copyright (c) 2015-2019, GEM Foundation.

      This program is free software: you can redistribute it and/or modify
      it under the terms of the GNU Affero General Public License as
      published by the Free Software Foundation, either version 3 of the
      License, or (at your option) any later version.

      This program is distributed in the hope that it will be useful,
      but WITHOUT ANY WARRANTY; without even the implied warranty of
      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
      GNU Affero General Public License for more details.

      You should have received a copy of the GNU Affero General Public License
      along with this program.  If not, see <https://www.gnu.org/licenses/agpl.html>.
*/

var ff_obj = {
    pfx: 'div.ff_gid ',
    o: $('div.ff_gid'),
    tbl: {},
    tbl_idx: 0,
    nrml: "",
    limitStates: [],
    is_interactive: true,

    ctx: {
        functionId: null,
        assetCategory: null,
        lossCategory: null,
        functionDescription: null,
        limitStates: null,
        tables: null
    },

    ctx_function_cont_get: function(idx, scope) {
        var ret = {'type': 'cont'};
        ret['id'] = $(scope).find('input[type="text"][name="id"]').val();
        ret['imt'] = $(scope).find('input[type="text"][name="imt"]').val();
        ret['no-damage-limit'] = $(scope).find('input[type="text"][name="no-damage-limit"]').val();
        ret['min-impls'] = $(scope).find('input[type="text"][name="min-impls"]').val();
        ret['max-impls'] = $(scope).find('input[type="text"][name="max-impls"]').val();
        ret['table'] = ff_obj.o.find('[name="tableDiv' + (idx + 1) + '"]').handsontable("getInstance").getData();

        return ret;
    },

    ctx_function_discr_get: function(idx, scope) {
        var ret = {'type': 'discr'};
        ret['id'] = $(scope).find('input[type="text"][name="id"]').val();
        ret['imt'] = $(scope).find('input[type="text"][name="imt"]').val();
        ret['no-damage-limit'] = $(scope).find('input[type="text"][name="no-damage-limit"]').val();
        ret['table'] = ff_obj.o.find('[name="tableDiv' + (idx + 1) + '"]').handsontable("getInstance").getData();

        return ret;
    },

    ctx_tables_get: function(obj) {
        var ret = [];
        var $funcs = ff_obj.o.find('.tables_gid');

        for (var i = 0 ; i < $funcs.length ; i++) {
            var ty = $($funcs[i]).attr('data-gem-func-type');
            if (ty == 'cont') {
                ret.push(obj.ctx_function_cont_get(i, $funcs[i]));
            }
            else if (ty == 'discr') {
                ret.push(obj.ctx_function_discr_get(i, $funcs[i]));
            }
            else {
                console.log("Fragility function type [" + ty + "] not recognized");
            }
        }
        return ret;
    },

    ctx_get: function (obj) {
        var ctx = obj.ctx;

        ctx.functionId = ff_obj.o.find('input#functionId').val();
        ctx.assetCategory = ff_obj.o.find('input#assetCategory').val();
        ctx.lossCategory = ff_obj.o.find('select#lossCategory').val();
        ctx.functionDescription = ff_obj.o.find('textarea#functionDescription').val();
        ctx.limitStates = ff_obj.o.find('textarea#limitStates').val();
        ctx.tables = obj.ctx_tables_get(obj);
    },

    ctx_save: function (obj) {
        if (window.localStorage == undefined) {
            return false;
        }
        obj.ctx_get(obj);
        var ser = JSON.stringify(obj.ctx);
        window.localStorage.setItem('gem_ipt_fragility', ser);
        console.log(ser);
    },

    ctx_load_func_cont_step_gen: function (obj, load_step, load_funcs_step, step_cur, ctx)
    {
        function ctx_load_func_cont_step()
        {
            var changed = false;
            var table = ctx.tables[load_funcs_step];

            while (changed == false) {
                switch(step_cur) {
                case 0:
                    ff_obj.o.find('button#addContFunc').click();
                    changed = true;
                    break;
                case 1:
                    ff_obj.o.find('div.tables_gid:last input[type="text"][name="id"]').val(
                        table['id']).change();
                    changed = true;
                    break;
                case 2:
                    ff_obj.o.find('div.tables_gid:last input[type="text"][name="imt"]').val(
                        table['imt']).change();
                    changed = true;
                    break;
                case 3:
                    ff_obj.o.find('div.tables_gid:last input[type="text"][name="no-damage-limit"]').val(
                        table['no-damage-limit']).change();
                    changed = true;
                    break;
                case 4:
                    ff_obj.o.find('div.tables_gid:last input[type="text"][name="min-impls"]').val(
                        table['min-impls']).change();
                    changed = true;
                    break;
                case 5:
                    ff_obj.o.find('div.tables_gid:last input[type="text"][name="max-impls"]').val(
                        table['max-impls']).change();
                    changed = true;
                    break;
                case 6:
                    var htable = ff_obj.o.find('div.tables_gid:last div[name^="tableDiv"]').handsontable("getInstance");
                    htable.loadData(table.table);

                    changed = true;
                    break;
                default:
                    var ctx_load_funcs_step = obj.ctx_load_funcs_step_gen(
                        obj, load_step, load_funcs_step + 1, ctx);
                    ctx_load_funcs_step();
                    return;
                    break;
                }

                step_cur++;
            }
            setTimeout(ctx_load_func_cont_step, 0);
        }

        return ctx_load_func_cont_step;
    },

    ctx_load_func_discr_step_gen: function (obj, load_step, load_funcs_step, step_cur, ctx)
    {
        function ctx_load_func_discr_step()
        {
            var changed = false;
            var table = ctx.tables[load_funcs_step];

            while (changed == false) {
                switch(step_cur) {
                case 0:
                    ff_obj.o.find('button#addDiscrFunc').click();
                    changed = true;
                    break;
                case 1:
                    ff_obj.o.find('div.tables_gid:last input[type="text"][name="id"]').val(
                        table['id']).change();
                    changed = true;
                    break;
                case 2:
                    ff_obj.o.find('div.tables_gid:last input[type="text"][name="imt"]').val(
                        table['imt']).change();
                    changed = true;
                    break;
                case 3:
                    ff_obj.o.find('div.tables_gid:last input[type="text"][name="no-damage-limit"]').val(
                        table['no-damage-limit']).change();
                    changed = true;
                    break;
                case 4:
                    var htable = ff_obj.o.find('div.tables_gid:last div[name^="tableDiv"]').handsontable("getInstance");
                    htable.loadData(table.table);

                    changed = true;
                    break;
                default:
                    var ctx_load_funcs_step = obj.ctx_load_funcs_step_gen(
                        obj, load_step, load_funcs_step + 1, ctx);
                    ctx_load_funcs_step();
                    return;
                    break;
                }

                step_cur++;
            }
            setTimeout(ctx_load_func_discr_step, 0);
        }

        return ctx_load_func_discr_step;
    },

    ctx_load_funcs_step_gen: function (obj, load_step, step_cur, ctx) {
        function ctx_load_funcs_step() {
            var tables = ctx.tables;
            wrapping4load(obj.pfx + '*', true);

            if (gl_wrapping4load_counter != 0) {
                // console.log("ctx_load_funcs_step: gl_wrapping4load_counter != 0 (" + gl_wrapping4load_counter + ")");
                gl_wrapping4load_counter = 0;
                setTimeout(ctx_load_funcs_step, 0);
                // console.log('retry later');
                return;
            }
            // else {
            //     console.log('ctx_load_funcs_step, advance');
            // }
            if (step_cur < tables.length) {
                if (tables[step_cur].type == 'cont') {
                    var ctx_load_func_cont_step = obj.ctx_load_func_cont_step_gen(
                        obj, load_step, step_cur, 0, ctx);
                    ctx_load_func_cont_step();
                    return;
                }
                else if (tables[step_cur].type == 'discr') {
                    var ctx_load_func_discr_step = obj.ctx_load_func_discr_step_gen(
                        obj, load_step, step_cur, 0, ctx);
                    ctx_load_func_discr_step();
                    return;
                }
                else {
                    console.log('Unknown table type: ' + tables[step_cur].type);
                }
            }
            else {
                // return to ctx_load
                var ctx_load_step = obj.ctx_load_step_gen(obj, load_step + 1, ctx);
                ctx_load_step();
            }
        }
        return ctx_load_funcs_step;
    },

    ctx_load_step_gen: function(obj, step_cur, ctx) {

        function ctx_load_step() {
            console.log('step pre');
            wrapping4load(obj.pfx + '*', true);

            if (gl_wrapping4load_counter != 0) {
                // console.log("ctx_load_step: gl_wrapping4load_counter != 0 (" + gl_wrapping4load_counter + ")");
                gl_wrapping4load_counter = 0;
                setTimeout(ctx_load_step, 0);
                // console.log('retry later');
                return;
            }
            // else {
            //     console.log('ctx_load_step: advance');
            // }
            var changed = false;
            while (changed == false) {
                switch(step_cur) {
                case 0:
                    if (ff_obj.o.find('input#functionId').val() != ctx.functionId) {
                        ff_obj.o.find('input#functionId').val(ctx.functionId).change();
                        changed = true;
                    }
                    break;
                case 1:
                    if (ff_obj.o.find('input#assetCategory').val() != ctx.assetCategory) {
                        ff_obj.o.find('input#assetCategory').val(ctx.assetCategory).change();
                        changed = true;
                    }
                    break;
                case 2:
                    if (ff_obj.o.find('select#lossCategory').val() != ctx.lossCategory) {
                        ff_obj.o.find('select#lossCategory').val(ctx.lossCategory).change();
                        changed = true;
                    }
                    break;
                case 3:
                    if (ff_obj.o.find('textarea#functionDescription').val() != ctx.functionDescription) {
                        ff_obj.o.find('textarea#functionDescription').val(ctx.functionDescription);
                        changed = true;
                    }
                    break;
                case 4:
                    if (ff_obj.o.find('textarea#limitStates').val() != ctx.limitStates) {
                        ff_obj.o.find('textarea#limitStates').val(ctx.limitStates).change();
                        changed = true;
                    }
                    break;
                case 5:
                    ff_obj.o.find('button[name="destroy_table"]').click();
                    changed = true;
                    break;
                case 6:
                    var ctx_load_funcs_step = obj.ctx_load_funcs_step_gen(obj, step_cur, 0, ctx);
                    ctx_load_funcs_step();
                    return;
                    break;
                default:
                    console.log('dewrapping');
                    wrapping4load(obj.pfx + '*', false);
                    ff_obj.is_interactive = true;
                    return;
                    break;
                }

                step_cur++;
            }
            setTimeout(ctx_load_step, 0);
        };
        return ctx_load_step;
    },

    ctx_load: function (obj) {
        if (window.localStorage == undefined) {
            return false;
        }
        var ser = window.localStorage.getItem('gem_ipt_fragility');
        if (ser == null)
            return false;

        var ctx = JSON.parse(ser);

        ctx_load_step = obj.ctx_load_step_gen(obj, 0, ctx);

        ff_obj.is_interactive = false;
        ctx_load_step();
    }
};

function ff_sh2full(funcType)
{
    if (funcType == 'cont')
        return 'continuous';
    else if (funcType == 'discr')
        return 'discrete';
}

function ff_sh2long(funcType)
{
    if (funcType == 'cont')
        return 'continuous function';
    else if (funcType == 'discr')
        return 'discrete function';
}


var activeTablesObj = {};

function ff_addTable (funcType) {
    var table;
    var format_name = ff_sh2long(funcType);

    // Get info from the form and build the table header
    ff_obj.limitStates = ff_obj.o.find('#limitStates').val().split(',');
    var limitStatesHeader = [];
    for (var i = 0; i < ff_obj.limitStates.length; i++) {
        ff_obj.limitStates[i] = ff_obj.limitStates[i].toString().trim();
        limitStatesHeader.push(ff_obj.limitStates[i]);
    }

    limitStatesHeader.unshift('intensity measure');
    var limitStateLength = ff_obj.limitStates.length;

    var colWidth;
    // disable the fragility function form
    ff_obj.o.find('#limitStates').prop('disabled', true);
    // Setup the header
    if (funcType == 'discr') {
        header = limitStatesHeader;
        limitStateLength = 1;
    } else if (funcType == 'cont') {
        header = ['damage state', 'mean', 'stddev'];
        colWidth = 100;
    }

    var headerLength = header.length;

    // Create the table containers, as many as the user wants
    ff_obj.tbl_idx += 1;
    var tbl_idx = ff_obj.tbl_idx;

    var imls;
    // Imls value needs to be an array for discrete functions,
    // and minIML & maxIML for continuous
    if (funcType == 'discr') {
        imls = '';
    } else if (funcType == 'cont') {
        imls =
            '<label> MinIML: </label>' +
            '<input name="min-impls" class="ffsTable" type="text"><br>' +
            '<label> MaxIML: </label>' +
            '<input name="max-impls" class="ffsTable" type="text">';
    }

    // Create the fragility function set (ffs)
    ff_obj.o.find('#tables').append(
        '<div id="table'+ff_obj.tbl_idx+'" class="tables_gid table'+ff_obj.tbl_idx+'_id' +
            ' ffsTableDiv panel panel-default" data-gem-func-type="'+ funcType + '">' +
          '<strong class="ffsTitle">' + format_name.toUpperCase() + '</strong><button type="button" name="destroy_table" class="destroyTable btn-danger btn">Remove Function</button><br>' +
            '<div class="ffsForm" >' +
                '<label> Id: </label>' +
                '<input name="id" class="ffsTable" type="text"><br>' +
                '<label> IMT: </label>' +
                '<input name="imt" class="ffsTable" type="text" placeholder="PGA"><br>' +
                '<label> Damage Limit: </label>' +
                '<input name="no-damage-limit" class="ffsTable" type="text"><br>' +
                imls +
                '<br>' +
            '</div>'+
            '<div style="width: 45%; float: right;">' +
              '<div name="tableDiv'+ff_obj.tbl_idx+ '"' +
              (funcType == 'discr' ? ' style="width: 100%; height: 100px; overflow: hidden;"' : '') +
              ' class="theTable"></div><br>' +
            (funcType == 'discr' ?
              '<button id="new_row_add" type="button" style="clear: right; float: right; margin-top: 4px;" class="btn">Add Row</button><br>' :
             '') +
           '</div>' +
         '</div>'
    );

    // force bootstrap style
    ff_obj.o.find('.btn-danger').css({'background-color': '#da4f49'});


    ////////////////////////////////
    /// fragility Table Settings ///
    ////////////////////////////////

    var handson_params = {
        colHeaders: header,
        startCols: headerLength,
        maxCols: headerLength,
        startRows: limitStateLength,
        colWidths: colWidth
    };

    if (funcType == 'discr') {
        handson_params.rowHeaders = true;
        handson_params.contextMenu = true;
        handson_params.manualColumnResize = true;
        handson_params.manualRowResize = true;
    }
    else if (funcType == 'cont') {
        handson_params.rowHeaders = false;
        handson_params.contextMenu = false;
        handson_params.manualColumnResize = false;
        handson_params.manualRowResize = false;
        handson_params.maxRows = ff_obj.limitStates.length;
        handson_params.columns = [
            {readOnly: true,
             className: "htLeft"},
            {className: "htRight"},
            {className: "htRight"}
        ];

        // this function is a callback called by handsontable during table creation
        // to retrieve cellProperties of each cell
        handson_params.cells = function(r,c, prop) {
            var cellProperties = {};
            if (c===0) cellProperties.readOnly = true;
            return cellProperties;
        };
    }

    ff_obj.o.find('[name="tableDiv'+ff_obj.tbl_idx+'"]').handsontable(handson_params);
    ff_obj.tbl[ff_obj.tbl_idx] = ff_obj.o.find('[name="tableDiv'+ff_obj.tbl_idx+'"]').handsontable("getInstance");
    table = ff_obj.tbl[ff_obj.tbl_idx];

    // Populate the table with limit states
    if (funcType == 'cont') {
        for (var i = 0; i < ff_obj.limitStates.length; i++) {
            table.setDataAtCell(i, 0, ff_obj.limitStates[i]);
        }
    }

    if (funcType == 'discr') {
        var tbl = ff_obj.tbl[ff_obj.tbl_idx];
        var $box = ff_obj.o.find('[name="tableDiv'+ff_obj.tbl_idx+'"]');

        setTimeout(function() {
            return gem_tableHeightUpdate($box);
        }, 0);

        tbl.addHook('afterCreateRow', function() {
            return gem_tableHeightUpdate($box);
        });

        tbl.addHook('afterRemoveRow', function() {
            return gem_tableHeightUpdate($box);
        });
    }

    ff_obj.o.find('#outputText').empty();
    ff_obj.o.find('#convertBtn').show();

    // use tbl_idx to fix with a closure the idx value inside click and change callbacks
    var tbl_idx = ff_obj.tbl_idx;

    // Logic to remove a table
    ff_obj.o.find('.table' + tbl_idx + '_id [name="destroy_table"]').click(function() {
        if (ff_obj.is_interactive) {
            if (confirm("Do you really want to remove this function?") == false)
                return;
        }
        ff_obj.o.find('#table' + tbl_idx).remove();
        delete ff_obj.tbl[tbl_idx];
        if (Object.keys(ff_obj.tbl).length == 0) {
            ff_obj.o.find('#limitStates').prop('disabled', false);
            ff_obj.o.find('#convertBtn').hide();
            ff_obj.o.find('#outputDiv').hide();
        }
    });

    // Logic to manage newRow button
    ff_obj.o.find('.table' + tbl_idx + '_id #new_row_add').click(function() {
        var table;
        table = ff_obj.o.find('[name="tableDiv'+ff_obj.tbl_idx+'"]').handsontable("getInstance");
        table.alter('insert_row', table.countRows());
    });

    // Increase the ffs panel when many limit states are defined
    if (limitStateLength > 5) {
        ff_obj.o.find('.ffsTableDiv').height(240 + (limitStateLength * 1.5));
    }

}

ff_obj.o.find('#downloadBtn').click(function() {
    sendbackNRML(ff_obj.nrml, 'ff');
});
if (typeof gem_api != 'undefined') {
    ff_obj.o.find('#delegateDownloadBtn').click(function() {
        var uu = delegate_downloadNRML(ff_obj.nrml, 'ff', delegate_downloadNRML_cb);
        console.log("fired cmd with uuid: " + uu);
    });
    ff_obj.o.find('#delegateCollectBtn').click(function() {
        var uu = delegate_downloadNRML(ff_obj.nrml, 'ff', delegate_collectNRML_cb);
        console.log("fired cmd with uuid: " + uu);
    });
}

ff_obj.o.find('#convertBtn').click(function() {
    var tabs_data = {};

    // get the data for each table
    for(var k in ff_obj.tbl) {
        tabs_data[k] = ff_obj.tbl[k].getData();
    }

    for(var k in tabs_data) {
        var $pfx = ff_obj.o.find('.table'+k+'_id');
        var tab_data = tabs_data[k];

        for (var i = 0; i < tab_data.length; i++) {
            for (var j = 0; j < tab_data[i].length; j++) {
                if (tab_data[i][j] === null || tab_data[i][j].toString().trim() == "") {
                    var funcType = $pfx.attr('data-gem-func-type');
                    var funcId = $pfx.find('[name="id"]').val();
                    var error_msg = "empty cell detected at coords (" + (i+1) + ", " + (j+1) + ") of " +
                        ff_sh2long(funcType)+ " with ID " + funcId;

                    output_manager('ff', error_msg, null, null);
                    return;
                }
            }
        }
    }

    var functionId = ff_obj.o.find('#functionId').val();
    var assetCategory = ff_obj.o.find('#assetCategory').val();
    var lossCategory = ff_obj.o.find('#lossCategory').val();
    var functionDescription = ff_obj.o.find('#functionDescription').val();

    // Opening limit state tag
    var limitStatesXML = '\t\t<limitStates>';

    // Dynamic limit state tag(s)
    limitStatesXML += ff_obj.limitStates.join(' ');

    // Closing limit state tag
    limitStatesXML += '</limitStates>\n';

    ////////////////
    // Create ffs //
    ////////////////

    var fragilityFunction = '';
    // Create the ffs elements
    for (var k in ff_obj.tbl) {
        var $pfx = ff_obj.o.find('.table'+k+'_id');
        var tab_data = tabs_data[k];
        var funcType = $pfx.attr('data-gem-func-type');

        var ffs;
        // Opening ffs tag
        if (funcType == 'discr') {
            ffs = '\t\t<fragilityFunction id="'+$pfx.find('[name="id"]').val()+'" format="'+
                ff_sh2full(funcType)+'">\n';
        } else if (funcType == 'cont') {
            ffs = '\t\t<fragilityFunction id="'+$pfx.find('[name="id"]').val()+'" format="'+
                ff_sh2full(funcType)+'" shape="logncdf">\n';
        }
        // Create the imls tag
        var imlsTag;
        if (funcType == 'discr') {
            // Opening IML tag
            imlsTag = '\t\t\t<imls imt="'+$pfx.find('[name="imt"]').val()+'" noDamageLimit="'+
                $pfx.find('[name="no-damage-limit"]').val()+'">';

            for (var i = 0; i < tab_data.length; i++) {
                // IML values
                imlsTag += (i == 0 ? "" : " ") + tab_data[i][0];
            }
            // Closing IML tag
            imlsTag += '</imls>\n';
        } else if (funcType == 'cont') {
            imlsTag = '\t\t\t<imls imt="'+$pfx.find('[name="imt"]').val()+
                '" noDamageLimit="'+$pfx.find('[name="no-damage-limit"]').val()+
                '" minIML="'+$pfx.find('[name="min-impls"]').val()+
                '" maxIML="'+$pfx.find('[name="max-impls"]').val()+
                '"/>\n';
        }
        // Dynamic imls tag
        ffs += imlsTag;

        // Dynamic ffs tag(s)
        if (funcType == 'discr') {
            for (var i = 0 ; i < ff_obj.limitStates.length ; i++) {
                // Opening poes tag
                ffs += '\t\t\t<poes ls="'+ff_obj.limitStates[i].replace(/ /g,'')+'">';
                for (var j = 0; j < tab_data.length; j++) {
                    // The intensity measure is the first column in the table,
                    // so we need to shift one column to the right ( i + 1 )
                    ffs += (j == 0 ? "" : " ") + tab_data[j][i + 1];
                }
                // Closing poes tag
                ffs += '</poes>\n';
            }

        } else if (funcType == 'cont') {
            for (var i = 0; i < ff_obj.limitStates.length; i++) {
                ffs += '\t\t\t<params ls="'+ff_obj.limitStates[i].replace(/ /g,'')+
                    '" mean="'+tab_data[i][1]+
                    '" stddev="'+tab_data[i][2]+'"/>\n';
                }
            }

        // Closing ffs tags
        ffs += '\t\t</fragilityFunction>\n';
        fragilityFunction += ffs;
    }

    // Create a NRML element
    var nrml =
        '<?xml version="1.0" encoding="UTF-8"?>\n' +
        '<nrml xmlns="http://openquake.org/xmlns/nrml/0.5">\n' +
            '\t<fragilityModel id="'+functionId+'" assetCategory="'+assetCategory+'" lossCategory="'+lossCategory+'">\n' +
                '\t\t<description>'+functionDescription+'</description>\n' +
                limitStatesXML +
                fragilityFunction +
            '\t</fragilityModel>\n' +
        '</nrml>\n';

    validateAndDisplayNRML(nrml, 'ff', ff_obj);
});


// initialization function
$(document).ready(function (){
    ff_obj.o.find('#outputDiv').hide();

    ff_obj.o.find('#addDiscrFunc').click(function() {
        var funcType = 'discr';
        ff_addTable(funcType);
        ff_obj.o.find('#outputDiv').hide();
    });

    ff_obj.o.find('#addContFunc').click(function() {
        var funcType = 'cont';
        ff_addTable(funcType);
        ff_obj.o.find('#outputDiv').hide();
    });

});

