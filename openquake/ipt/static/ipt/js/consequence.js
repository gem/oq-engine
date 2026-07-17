/*
   Copyright (c) 2016-2019, GEM Foundation.

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

var co_obj = {
    pfx: 'div.co_gid ',
    o: $('div.co_gid'),
    damage_states: null,
    tbl: null,
    tbl_file: null,
    header: null,

    ctx: {
        assetCat: null,
        lossCategory: null,
        descr: null,
        damageStates: null,
        probDistrib: null,
        table: null
    },

    ctx_get: function(obj) {
        var ctx = obj.ctx;

        ctx.assetCat = obj.o.find('input[name="asset-cat"]').val();
        ctx.lossCategory = obj.o.find('select#lossCategory').val();
        ctx.descr = obj.o.find('textarea[name="descr"]').val();
        ctx.damageStates = obj.o.find('input[name="damage-states"]').val();
        ctx.probDistrib = obj.o.find('input[name="asset-cat"]').val();
        ctx.table = obj.o.find('#table').handsontable('getInstance').getData();
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
                    if (obj.o.find('input[name="asset-cat"]').val() != ctx.assetCat) {
                        obj.o.find('input[name="asset-cat"]').val(ctx.assetCat).change();
                        changed = true;
                    }
                    break;
                case 1:
                    if (obj.o.find('select#lossCategory').val() != ctx.lossCategory) {
                        obj.o.find('select#lossCategory').val(ctx.lossCategory).change();
                        changed = true;
                    }
                    break;
                case 2:
                    if (obj.o.find('textarea[name="descr"]').val() != ctx.descr) {
                        obj.o.find('textarea[name="descr"]').val(ctx.descr).change();
                        changed = true;
                    }
                    break;
                case 3:
                    if (obj.o.find('input[name="damage-states"]').val() != ctx.damageStates) {
                        obj.o.find('input[name="damage-states"]').val(ctx.damageStates).change();
                        changed = true;
                    }
                    break;
                case 4:
                    if (obj.o.find('input[name="asset-cat"]').val() != ctx.probDistrib) {
                        obj.o.find('input[name="asset-cat"]').val(ctx.probDistrib).change();
                        changed = true;
                    }
                    break;
                case 5:
                    obj.o.find('#table').handsontable('getInstance').loadData(ctx.table);
                    changed = true;
                    break;
                default:
                    // console.log('dewrapping');
                    wrapping4load(obj.pfx + '*', false);
                    return;
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
        var ser = window.localStorage.getItem('gem_ipt_consequence');
        if (ser == null) {
            return false;
        }

        var ctx = JSON.parse(ser);

        var ctx_load_step = obj.ctx_load_step_gen(obj, 0, ctx);

        ctx_load_step();
    }
};

// tab initialization
function co_updateTable() {
    co_obj.o.find('#table_file').val("");
    co_obj.tbl_file = null;

    // Remove any existing table, if already exists
    if (co_obj.o.find('#table').handsontable('getInstance') !== undefined) {
        co_obj.o.find('#table').handsontable('destroy');
    }

    // Default columns
    co_obj.header = ['taxonomy'];
    co_obj.damage_states = [];
    co_obj.damage_states = $(co_obj.pfx + "input[name='damage-states']").val().split(',');
    for (var i = 0 ; i < co_obj.damage_states.length ; i++) {
        co_obj.damage_states[i] = co_obj.damage_states[i].toString().trim();
        co_obj.header.push(co_obj.damage_states[i] + "<br>mean");
        co_obj.header.push(co_obj.damage_states[i] + "<br>std dev");
    }

    var headerLength = co_obj.header.length;

    // Create the table

    ///////////////////////////////
    /// Exposure Table Settings ///
    ///////////////////////////////
    co_obj.o.find('#table').handsontable({
        colHeaders: co_obj.header,
        rowHeaders: true,
        contextMenu: true,
        startRows: 3,
        startCols: headerLength,
        maxCols: headerLength,
        className: "htRight"
    });
    co_obj.tbl = co_obj.o.find('#table').handsontable('getInstance');
    setTimeout(function() {
        return gem_tableHeightUpdate(co_obj.o.find('#table'));
    }, 0);

    co_obj.tbl.addHook('afterCreateRow', function() {
        return gem_tableHeightUpdate(co_obj.o.find('#table'));
    });

    co_obj.tbl.addHook('afterRemoveRow', function() {
        return gem_tableHeightUpdate(co_obj.o.find('#table'));
    });
    co_obj.tbl.addHook('afterChange', function(changes, source) {
        // when loadData is used, for performace reasons, changes are 'null'
        if (changes != null || source != 'loadData') {
            co_obj.o.find('#table_file').val("");
            co_obj.tbl_file = null;
        }
    });

    co_obj.o.find('#outputText').empty();
    co_obj.o.find('#convertBtn').show();
}

co_obj.o.find('#downloadBtn').click(function() {
    sendbackNRML(co_obj.nrml, 'co');
});

if (typeof gem_api != 'undefined') {
    co_obj.o.find('#delegateDownloadBtn').click(function() {
        var uu = delegate_downloadNRML(co_obj.nrml, 'co', delegate_downloadNRML_cb);
        console.log("fired cmd with uuid: " + uu);
    });
    co_obj.o.find('#delegateCollectBtn').click(function() {
        var uu = delegate_downloadNRML(co_obj.nrml, 'co', delegate_collectNRML_cb);
        console.log("fired cmd with uuid: " + uu);
    });
}

co_obj.o.find('#convertBtn').click(function() {
    var data = null
    if (co_obj.o.find('input#table_file')[0].files.length > 0) {
        data = co_obj.tbl_file;
    }
    else {
        // Get the values from the table
        data = co_obj.tbl.getData();
    }

    var not_empty_rows = not_empty_rows_get(data);

    // Check for null values
    for (var i = 0; i < not_empty_rows; i++) {
        for (var j = 0; j < data[i].length; j++) {
            var s = data[i][j] + " ";
            if (data[i][j] === null || data[i][j].toString().trim() == "" || parseInt(data[i][j]) < 0.0) {
                output_manager('co', "empty or negative cell at coords (" + (i+1) + ", " + (j+1) + ")", null, null);
                return;
            }
        }
    }

    var description = $(co_obj.pfx + "textarea[name='descr']").val();
    var asset = $(co_obj.pfx + "input[name='asset-cat']").val();
    var loss_cat = $(co_obj.pfx + "select#lossCategory").val();
    // damage states use co_obj attribute
    var prob_dist = $(co_obj.pfx + "select#prob_distrib").val();

/*
    <consequenceFunction id="Concrete" dist="LN">
      <params ls="slight" mean="0.04" stddev="0.00"/>
      <params ls="moderate" mean="0.31" stddev="0.00"/>
      <params ls="extreme" mean="0.60" stddev="0.00"/>
      <params ls="collapse" mean="1.00" stddev="0.00"/>
    </consequenceFunction>
*/
    // Create consequences
    var cons_func = ""
    for (var i = 0 ; i < not_empty_rows ; i++) {
        cons_func += '\t\t<consequenceFunction id="' + data[i][0] + '" dist="' + prob_dist + '">\n';
        for (var e = 1 ; e < data[i].length ; e+=2) {
            cons_func += '\t\t\t<params ls="' + co_obj.damage_states[(e - 1) / 2] + '" mean="' + parseFloat(data[i][e]) + '" stddev="' + parseFloat(data[i][e+1])+ '"/>\n'
        }
        cons_func += "\t\t</consequenceFunction>\n"
    }

    // Create a NRML element
    var nrml =
        '<?xml version="1.0" encoding="utf-8"?>\n' +
        '<nrml xmlns="http://openquake.org/xmlns/nrml/0.5">\n' +
        '\t<consequenceModel id="' + 'consequence-from-IPT' + '" assetCategory="' + asset + '" lossCategory="' + loss_cat + '">\n' +
        '\t\t<description>' + description + '</description>\n' +
        '\t\t<limitStates>' + co_obj.damage_states.join(' ') + '</limitStates>\n' +
        cons_func +
        '\t</consequenceModel>\n' +
        '</nrml>\n';
    validateAndDisplayNRML(nrml, 'co', co_obj);
});

$(document).ready(function () {

    co_obj.o.find('input#table_file').on(
        'change', function co_table_file_mgmt(evt) { ipt_table_file_mgmt(evt, co_obj, 1, null, null); });

    co_updateTable();
    co_obj.o.find('#new_row_add').click(function() {
        co_obj.tbl.alter('insert_row');
    });

    $(co_obj.pfx + "input[name='damage-states']").on('change', co_updateTable);

    co_obj.o.find('#outputDiv').hide();
    $('#absoluteSpinner').hide();
});
