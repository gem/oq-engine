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

var ex_obj = {
    pfx: 'div.ex_gid ',
    o: $('div.ex_gid'),
    tbl_file: {},
    tbl: {},
    tbl_cur: 0,
    nrml: "",
    header: [],
    headerbase_len: 0,

    ctx: {
        description: null,
        costStruc: null,
        structural_costs_units: null,
        retroChbx: null,
        limitSelect: null,
        deductibleSelect: null,
        costNonStruc: null,
        nonstructural_costs_units: null,
        costContent: null,
        contents_costs_units: null,
        costBusiness: null,
        busi_inter_costs_units: null,
        perAreaSelect: null,
        area_units: null,
        occupants_day: null,
        occupants_night: null,
        occupants_transit: null,
        tags: null,
        table: null,
        table_file: null,

        exposure_type: ''
    },

    // perAreaRefCount is used to keep track of any time perArea is selected
    perAreaRefCount: {
        costStruc : false,
        costNonStruc : false,
        costContent : false,
        costBusiness : false
    },

    perAreaUpdate: function(selectedValue, element) {
        // Manage all define cost elements that are using perArea
        if (selectedValue == 'per_area') {
            this.perAreaRefCount[element] = true;
        }
        else {
            this.perAreaRefCount[element] = false;
        }
    },

    perAreaIsVisible: function() {
        // If perAreaRefCountManager returnes false then we can hide the area
        // option from the form

        for(var k in this.perAreaRefCount) {
            if (this.perAreaRefCount[k] === true) {
                return true;
            }
        }
        return false;
    },

    perAreaManager: function(selectedValue, element) {
        // Manage all define cost elements that are using perArea
        this.perAreaUpdate(selectedValue, element);

        if (this.perAreaIsVisible())
            ex_obj.o.find('#perArea').show();
        else
            ex_obj.o.find('#perArea').hide();
    },

    ctx_get: function (obj) {
        var ctx = obj.ctx;

        ctx.description = obj.o.find('textarea#description').val();
        ctx.costStruc = obj.o.find('select#costStruc').val();
        ctx.structural_costs_units = obj.o.find('input#structural_costs_units').val();
        ctx.retroChbx = obj.o.find('input#retroChbx').is(':checked');
        ctx.limitSelect = obj.o.find('select#limitSelect').val();
        ctx.deductibleSelect = obj.o.find('select#deductibleSelect').val();
        ctx.costNonStruc = obj.o.find('select#costNonStruc').val();
        ctx.nonstructural_costs_units = obj.o.find('input#nonstructural_costs_units').val();
        ctx.costContent = obj.o.find('select#costContent').val();
        ctx.contents_costs_units = obj.o.find('input#contents_costs_units').val();
        ctx.costBusiness = obj.o.find('select#costBusiness').val();
        ctx.busi_inter_costs_units = obj.o.find('input#busi_inter_costs_units').val();
        ctx.perAreaSelect = obj.o.find('select#perAreaSelect').val();
        ctx.area_units = obj.o.find('input#area_units').val();

        ctx.occupants_day = obj.o.find('div#occupantsCheckBoxes input[type="checkbox"][value="day"]').is(':checked');
        ctx.occupants_night = obj.o.find('div#occupantsCheckBoxes input[type="checkbox"][value="night"]').is(':checked');
        ctx.occupants_transit = obj.o.find('div#occupantsCheckBoxes input[type="checkbox"][value="transit"]').is(':checked');
        ctx.tags = obj.o.find('#tags').tagsinput('items');
        $tables = obj.o.find('div[name^="table-"]');
        ctx.table = new Array($tables.length);
        for (var tbl_id = 0 ; tbl_id < $tables.length ; tbl_id++) {
            var $tbl = $($tables[tbl_id]);
            ctx.table[tbl_id] = $tbl.handsontable('getInstance').getData();
        }
        $table_files = obj.o.find('input[id="table_file"]');
        ctx.table_file = new Array($tables.length);
        for (var tbl_id = 0 ; tbl_id < $table_files.length ; tbl_id++) {
            var $tbl_file = $($table_files[tbl_id]);
            ctx.table_file[tbl_id] = $tbl_file.val().replace(/.*[\/\\]/, '');
        }
    },

    ctx_save: function (obj) {
        if (window.localStorage == undefined) {
            return false;
        }
        obj.ctx_get(obj);
        var ser = JSON.stringify(obj.ctx);
        window.localStorage.setItem('gem_ipt_exposure', ser);
        console.log(ser);
    },

    ctx_load_step_gen: function(obj, step_cur, ctx) {
        function ctx_load_step() {
            wrapping4load(obj.pfx + '*', true);

            if (gl_wrapping4load_counter != 0) {
                // console.log("ctx_load_step: gl_wrapping4load_counter != 0 (" + gl_wrapping4load_counter + ")");
                gl_wrapping4load_counter = 0;
                setTimeout(ctx_load_step, 0);
                // console.log('retry later');
                return;
            }
            // else {
            //     console.log('ctx_load_step, advance');
            // }
            var changed = false;
            while (changed == false) {
                switch(step_cur) {
                case 0:
                    if (obj.o.find('textarea#description').val() != ctx.description) {
                        obj.o.find('textarea#description').val(ctx.description).change();
                        changed = true;
                    }
                    break;
                case 1:
                    if (obj.o.find('select#costStruc').val() != ctx.costStruc) {
                        obj.o.find('select#costStruc').val(ctx.costStruc).change();
                        changed = true;
                    }
                    break;
                case 2:
                    if (obj.o.find('input#structural_costs_units').val() != ctx.structural_costs_units) {
                        obj.o.find('input#structural_costs_units').val(ctx.structural_costs_units).change();
                        changed = true;
                    }
                    break;
                case 3:
                    if (obj.o.find('input#retroChbx').is(':checked') != ctx.retroChbx) {
                        obj.o.find('input#retroChbx').prop('checked', ctx.retroChbx).change();
                        changed = true;
                    }
                    break;
                case 4:
                    if (obj.o.find('select#limitSelect').val() != ctx.limitSelect) {
                        obj.o.find('select#limitSelect').val(ctx.limitSelect).change();
                        changed = true;
                    }
                    break;
                case 5:
                    if (obj.o.find('select#deductibleSelect').val() != ctx.deductibleSelect) {
                        obj.o.find('select#deductibleSelect').val(ctx.deductibleSelect).change();
                        changed = true;
                    }
                    break;
                case 6:
                    if (obj.o.find('select#costNonStruc').val() != ctx.costNonStruc) {
                        obj.o.find('select#costNonStruc').val(ctx.costNonStruc).change();
                        changed = true;
                    }
                    break;
                case 7:
                    if (obj.o.find('input#nonstructural_costs_units').val() != ctx.nonstructural_costs_units) {
                        obj.o.find('input#nonstructural_costs_units').val(ctx.nonstructural_costs_units).change();
                        changed = true;
                    }
                    break;
                case 8:
                    if (obj.o.find('select#costContent').val() != ctx.costContent) {
                        obj.o.find('select#costContent').val(ctx.costContent).change();
                        changed = true;
                    }
                    break;
                case 9:
                    if (obj.o.find('input#contents_costs_units').val() != ctx.contents_costs_units) {
                        obj.o.find('input#contents_costs_units').val(ctx.contents_costs_units).change();
                        changed = true;
                    }
                    break;
                case 10:
                    if (obj.o.find('select#costBusiness').val() != ctx.costBusiness) {
                        obj.o.find('select#costBusiness').val(ctx.costBusiness).change();
                        changed = true;
                    }
                    break;
                case 11:
                    if (obj.o.find('input#busi_inter_costs_units').val() != ctx.busi_inter_costs_units) {
                        obj.o.find('input#busi_inter_costs_units').val(ctx.busi_inter_costs_units);
                        changed = true;
                    }
                    break;
                case 12:
                    if (obj.o.find('select#perAreaSelect').val() != ctx.perAreaSelect) {
                        obj.o.find('select#perAreaSelect').val(ctx.perAreaSelect).change();
                        changed = true;
                    }
                    break;
                case 13:

                    if (obj.o.find('input#area_units').val() != ctx.area_units) {
                        obj.o.find('input#area_units').val(ctx.area_units).change();
                        changed = true;
                    }
                    break;
                case 14:
                    if (obj.o.find('div#occupantsCheckBoxes input[type="checkbox"][value="day"]').is(
                        ':checked') != ctx.occupants_day) {
                        obj.o.find('div#occupantsCheckBoxes input[type="checkbox"][value="day"]').prop(
                            'checked', ctx.occupants_day).change();
                        changed = true;
                    }
                    break;
                case 15:
                    if (obj.o.find('div#occupantsCheckBoxes input[type="checkbox"][value="night"]').is(
                        ':checked') != ctx.occupants_night) {
                        obj.o.find('div#occupantsCheckBoxes input[type="checkbox"][value="night"]').prop(
                            'checked', ctx.occupants_night).change();
                        changed = true;
                    }
                    break;
                case 16:
                    if (obj.o.find('div#occupantsCheckBoxes input[type="checkbox"][value="transit"]').is(
                        ':checked') != ctx.occupants_transit) {
                        obj.o.find('div#occupantsCheckBoxes input[type="checkbox"][value="transit"]').prop(
                            'checked', ctx.occupants_transit).change();
                        changed = true;
                    }
                    break;
                case 17:
                    var eq = false;
                    var tags_cur = obj.o.find('#tags').tagsinput('items');
                    if (ctx.tags.length == tags_cur.length) {
                        eq = true;
                        for (var i = 0 ; i < ctx.tags.length ; i++) {
                            if (ctx.tags[i] != tags_cur[i]) {
                                eq = false;
                                break;
                            }
                        }
                    }
                    if (eq == false) {
                        for (var i = 0 ; i < ctx.tags.length ; i++) {
                            obj.o.find('#tags').tagsinput('add', ctx.tags[i]);
                        }
                        changed = true;
                    }
                    break;
                case 18:
                    console.log('pre-load');
                    var table = obj.o.find('#table').handsontable('getInstance');
                    table.loadData(ctx.table);
                    changed = true;
                    break;
                default:
                    console.log('dewrapping');
                    wrapping4load(obj.pfx + '*', false);
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
        var ser = window.localStorage.getItem('gem_ipt_exposure');
        if (ser == null)
            return false;

        var ctx = JSON.parse(ser);
        var load_step = 0;

        var ctx_load_step = obj.ctx_load_step_gen(obj, 0, ctx);

        setTimeout(ctx_load_step, 0);
    },

    /*****************
     *               *
     *  EXPOSURETAB  *
     *               *
     *****************/
    exposuretbl_del: function (obj) {
        var id = obj.target.getAttribute("data-gem-id");
        var item = ex_obj.o.find('div[name="exposuretbls"] div[name="exposuretbl-' + id + '"]');
        delete(ex_obj.tbl[id]);
        item.remove();
    },

    exposuretbl_newrow: function (obj) {
        var id = obj.target.getAttribute("data-gem-id");
        ex_obj.tbl[id].alter('insert_row');
        var tbl_box = $(obj.target).closest("div[name='exposuretbl-" + id + "']").find("div[name='table-" + id + "']");

        setTimeout(function() {
            return gem_tableHeightUpdate(tbl_box);
        }, 0);
    },


    exposuretbl_add: function () {
        var ct = ex_obj.tbl_cur;
        var ctx = '\
<div name="exposuretbl-' + ct + '">\n\
<div class="menuItems" style="margin-top: 12px;">\n\
<div style="display: inline-block; float: left;"><h4>Exposure ' + (ct + 1) + ' </h4></div>';
        ctx += (ct == 0 ? '<div style="clear: both;"></div>' : '<button type="button" data-gem-id="' + ct + '" class="btn" style="margin-top: 8px; margin-bottom: 8px;" name="delete_exposuretbl">Delete #' + (ct + 1 ) + '</button>');
        ctx += '\
<div><input style="float: left;" type="file" id="table_file" data-gem-id="' + ct + '" accept="text/csv,application/csv,csv"></div>\n\
<div style="clear: both;"></div>\n\
<div style="overflow: hidden;">\n\
<div name="table-' + ct + '" style="height: 100px; overflow=hidden;"></div>\n\
</div>\n\
<button name="new_row_add" type="button" data-gem-id="' + ct + '" class="btn">New Row</button><br>\n\
<br>\n\
</div>\n\
</div>\n';
        ex_obj.o.find('div[name="exposuretbls"]').append(ctx);
        $tbl_new = ex_obj.o.find('div[name="exposuretbls"] div[name="exposuretbl-' + ct + '"]');

        $tbl_new.find('button[name="delete_exposuretbl"]').click(ex_obj.exposuretbl_del);
        $tbl_new.find('button[name="new_row_add"]').click(ex_obj.exposuretbl_newrow);

        var $table_id = $tbl_new.find('div[name="table-' + ct + '"]');
        var headerLength = ex_obj.header.length;
        var ht_config = {
            colHeaders: ex_obj.header.slice(),
            rowHeaders: true,
            contextMenu: true,
            startRows: 3,
            startCols: headerLength,
            maxCols: headerLength + 50,
            stretchH: 'all',
            className: "htRight"
        };
        $table_id.handsontable(ht_config);
        ex_obj.tbl[ct] = $table_id.handsontable('getInstance');
        ex_obj.tbl_cur++;
        $tbl_new.find('input#table_file').on(
            'change', function ipt_table_vect_file_mgmt_cb(evt) {
                ipt_table_vect_file_mgmt(evt, ex_obj, 1, -180, 180);
            });
    }
};

ex_obj.o.find('#costStruc').change(function() {
    // There is a bug in the handsontable lib where one can not
    // paste values into the table when the user has made a selection
    // from a dropdown menu. The reason for this error is that the focus
    // remains on the menu.
    // The workaround for this is to un-focus the selection menu with blur()
    // More info: https://github.com/handsontable/handsontable/issues/2973
    $(this).blur();
    ex_obj.perAreaManager($(this).val(), $(this).context.id);
    if ($(this).val() != 'none') {
        ex_obj.o.find('#structural_costs_units_div').show();
        ex_obj.o.find('#retrofittingSelect').show();
        ex_obj.o.find('#limitDiv').show();
        ex_obj.o.find('#deductibleDiv').show();
    } else {
        ex_obj.o.find('#structural_costs_units_div').hide();
        ex_obj.o.find('#retrofittingSelect').hide();
        ex_obj.o.find('#limitDiv').hide();
        ex_obj.o.find('#deductibleDiv').hide();
        // Uncheck retrofitting
        ex_obj.o.find('#retroChbx').attr('checked', false);
        // Unselect the limit & deductible
        ex_obj.o.find('#limitSelect').val('0');
        ex_obj.o.find('#deductibleSelect').val('0');
    }
});

ex_obj.o.find('#costNonStruc').change(function() {
    // unfocus the selection menu, see the note at the costStruc change event
    $(this).blur();

    if ($(this).val() != 'none') {
        ex_obj.o.find('#nonstructural_costs_units_div').show();
    }
    else {
        ex_obj.o.find('#nonstructural_costs_units_div').hide();
    }
    ex_obj.perAreaManager($(this).val(), $(this).context.id);
});

ex_obj.o.find('#costContent').change(function() {
    if ($(this).val() != 'none') {
        ex_obj.o.find('#contents_costs_units_div').show();
    }
    else {
        ex_obj.o.find('#contents_costs_units_div').hide();
    }
    // unfocus the selection menu, see the note at the costStruc change event
    $(this).blur();
    ex_obj.perAreaManager($(this).val(), $(this).context.id);
});

ex_obj.o.find('#costBusiness').change(function() {
    if ($(this).val() != 'none') {
        ex_obj.o.find('#busi_inter_costs_units_div').show();
    }
    else {
        ex_obj.o.find('#busi_inter_costs_units_div').hide();
    }

    // unfocus the selection menu, see the note at the costStruc change event
    $(this).blur();
    ex_obj.perAreaManager($(this).val(), $(this).context.id);
});

ex_obj.o.find('#form').change(function() {
    // unfocus the selection menu, see the note at the costStruc change event
    $(this).blur();
    ex_updateTable();
    ex_obj.o.find('#outputDiv').hide();
});

function checkForValueInHeader(header, argument) {
    var inx = ex_obj.header.indexOf(argument);
    return inx;
}

function ex_updateTableTags(delta) {
    var tags = ex_obj.o.find('#tags').tagsinput('items');
    var $tbls = ex_obj.o.find('div[name^="table"]');
    var tbl;

    for (var tbl_id in ex_obj.tbl) {
        tbl = ex_obj.tbl[tbl_id];
        var cols_cur = tbl.countCols();
        var cols_headers = tbl.getColHeader();

        for (var i = ex_obj.headerbase_len, ti = 0 ; i < cols_cur ; i++, ti++) {
            if (cols_headers[i] != "tag_" + tags[ti]) {
                if (delta > 0)
                    gem_ipt.error_msg("WARNING: tag [" + tags[ti] + "] not found");
                break;
            }
        }
        if (delta > 0) {
            tbl.alter('insert_col', i);
            cols_headers.push("tag_" + tags[ti]);
            tbl.updateSettings({'colHeaders': false});
            tbl.updateSettings({'colHeaders': cols_headers});
        }
        else {
            if (i == cols_cur) {
                gem_ipt.error_msg("WARNING: tag column to delete not found");
            }
            else {
                tbl.alter('remove_col', i);
                continue;
            }
        }
    }
}

function ex_updateTable() {
    var $tbl, $table, tbl_id, tbls = ex_obj.o.find('div[name="exposuretbls"] div[name^="exposuretbl-"]');

    // Default columns
    ex_obj.header = ['id', 'lon', 'lat', 'taxonomy', 'number'];
    function checkForValue (argument, valueArg) {
        // Modify the table header only when the menu is altered
        // This constraint will allow Limit, Deductible and Occupant elements to be
        // added to the header
        if (argument != 'none' && valueArg === undefined) {
            if (checkForValueInHeader(ex_obj.header, argument) == -1) {
                ex_obj.header.push(argument);
            }
            // This constraint will allow structural, nonstructural, contents and business
            // costs to be added to the header
        } else if (argument != 'none' && valueArg !== undefined) {
            if (checkForValueInHeader(ex_obj.header, valueArg) == -1) {
                ex_obj.header.push(valueArg);
            }
        }
    }

    // Get info from the expsure form and use it to build the table header
    ex_obj.o.find('#costStruc option:selected').each(function() {
        checkForValue($(this).attr('value'), 'structural');
    });

    ex_obj.o.find('#costNonStruc option:selected').each(function() {
        checkForValue($(this).attr('value'), 'nonstructural');
    });

    ex_obj.o.find('#costContent option:selected').each(function() {
        checkForValue($(this).attr('value'), 'contents');
    });

    ex_obj.o.find('#costBusiness option:selected').each(function() {
        checkForValue($(this).attr('value'), 'business');
    });

    ex_obj.o.find('#limitSelect option:selected').each(function() {
        checkForValue($(this).attr('value'), 'limit');
    });

    ex_obj.o.find('#deductibleSelect option:selected').each(function() {
        checkForValue($(this).attr('value'), 'deductible');
    });

    var perAreaVisible = ex_obj.o.find('#perArea:visible').length;
    if (perAreaVisible === 1) {
        ex_obj.header.push('area');
    }

    ex_obj.o.find('#occupantsCheckBoxes input:checked').each(function() {
        ex_obj.header.push($(this).attr('value'));
        // unfocus the selection menu, see the note at the exposure costStruc change event
        $(this).blur();
    });

    ex_obj.o.find('#retrofittingSelect input:checked').each(function() {
        ex_obj.header.push($(this).attr('value'));
        // unfocus the selection menu, see the note at the exposure costStruc change event
        $(this).blur();
    });

    ex_obj.headerbase_len = ex_obj.header.length;

    // manage tags
    ex_obj.header_exam = ex_obj.header.concat([]);
    var tags = ex_obj.o.find('#tags').tagsinput('items');
    for (var i = 0 ; i < tags.length ; i++) {
        ex_obj.header.push("tag_" + tags[i]);
        ex_obj.header_exam.push(tags[i]);
    }
    var headerLength = ex_obj.header.length;

    for (tbl_id = 0 ; tbl_id < tbls.length ; tbl_id++) {
        $tbl = $(tbls[tbl_id]);
        var id = $tbl.attr('name').substring(12);

        $tbl.find('#table_file').val("");
        ex_obj.tbl_file[id] = null;

        $table = $tbl.find('div[name^="table"]');
        // Remove any existing table, if already exists
        if ($table.handsontable('getInstance') !== undefined) {
            $table.handsontable('destroy');
        }

        // Create the table
        ///////////////////////////////
        /// Exposure Table Settings ///
        ///////////////////////////////
        $table.handsontable({
            colHeaders: ex_obj.header.slice(),
            rowHeaders: true,
            contextMenu: true,
            startRows: 3,
            startCols: headerLength,
            maxCols: headerLength + 50,
            stretchH: 'all',
            className: "htRight"
        });
        ex_obj.tbl[id] = $table.handsontable('getInstance');
        setTimeout(function() {
            return gem_tableHeightUpdate($table);
        }, 0);

        ex_obj.tbl[id].addHook('afterCreateRow', function() {
            return gem_tableHeightUpdate(ex_obj.o.find('div[name^="table-"]'));
        });

        ex_obj.tbl[id].addHook('afterRemoveRow', function() {
            return gem_tableHeightUpdate(ex_obj.o.find('div[name^="table-"]'));
        });

        ex_obj.tbl[id].addHook('afterChange', function(changes, source) {
            // when loadData is used, for performace reasons, changes are 'null'
            if (changes != null || source != 'loadData') {
                $tbl.find('#table_file').val("");
                ex_obj.tbl_file[id] = null;
            }
        });
    }
    ex_obj.o.find('#outputText').empty();
    ex_obj.o.find('#convertBtn').show();

    var $tr_exam_exp = $('<tr>');
    for (var i = 0 ; i < ex_obj.header_exam.length ; i++) {
        $tr_exam_exp.append($('<th>').text(ex_obj.header_exam[i]));
    }
    var $tbl_exam_exp = ex_obj.o.find('table.tbl-exam-exposure');
    $tbl_exam_exp.empty();
    $tbl_exam_exp.append($tr_exam_exp);
}

ex_obj.o.find('#downloadBtn').click(function() {
    sendbackNRML(ex_obj.nrml, 'ex');
});

if (typeof gem_api != 'undefined') {
    ex_obj.o.find('#delegateDownloadBtn').click(function() {
        var uu = delegate_downloadNRML(ex_obj.nrml, 'ex', delegate_downloadNRML_cb);
        console.log("fired cmd with uuid: " + uu);
    });
    ex_obj.o.find('#delegateCollectBtn').click(function() {
        var uu = delegate_downloadNRML(ex_obj.nrml, 'ex', delegate_collectNRML_cb);
        console.log("fired cmd with uuid: " + uu);
    });
}

function ex_csv_check(field_names, csv_files)
{
    var data = new FormData();
    data.append('data', JSON.stringify({field_names: field_names, csv_files: csv_files}));
    $.ajax({
        url: 'ex-csv-check',
        type: 'POST',
        data: data,
        cache: false,
        processData: false,
        contentType: false,
        success: function (data) {
            if (data.ret == 0) {
                ex_convert2nrml(2);
            }
            else {
                gem_ipt.error_msg(data.ret_s);
            }
        },
        error: function () {
            gem_ipt.error_msg('some error occured during csv headers check');
        }
    });
    return false;
}



function ex_convert2nrml(step)
{
    var data = [];
    var files_list = [];
    var ret = {
        ret: -1,
        str: ''
    };

    var exp_type = ex_obj.o.find('input:radio[name="exposure-type"]:checked').val();

    if (exp_type == 'csv' && step == 1) {
        var $csv_files = ex_obj.o.find("div[name='exposure-csv-html'] select[name='file_html']"
                                      ).children("option:selected");
        var csv_files = [];
        for (var i = 0 ; i < $csv_files.length ; i++) {
            var $csv_file = $($csv_files[i]);
            csv_files.push($csv_file.val());
        }
        var field_names = ex_obj.header_exam.slice();
        ex_csv_check(field_names, csv_files);
        return;
    }
    else if (exp_type == 'xml') {
        step = 2;
        $tbls = ex_obj.o.find('div[name="exposuretbls"] div[name^="exposuretbl-"]');
        for (var i = 0 ; i < $tbls.length ; i++) {
            $tbl = $($tbls[i]);
            if ($tbl.find('input#table_file')[0].files.length > 0) {
                var id = $tbl.find('input#table_file').attr('data-gem-id');
                data = data.concat(ex_obj.tbl_file[id]);
            }
            else {
                // Get the values from the table
                $tbl_tab = $tbl.find('div[name^="table-"]');
                data = data.concat($tbl_tab.handsontable('getInstance').getData());
        }
        }
        var not_empty_rows = not_empty_rows_get(data);

        // Check for null values
        for (var i = 0; i < not_empty_rows ; i++) {
            // tags columns can be empty
            var no_tags_col = (data[i].length < ex_obj.headerbase_len ? data[i].length : ex_obj.headerbase_len);
            for (var j = 0; j < no_tags_col ; j++) {
                var s = data[i][j] + " ";
                if (data[i][j] === null || data[i][j].toString().trim() == "") {
                    output_manager('ex', "empty cell at coords (" + (i+1) + ", " + (j+1) + ")", null, null);
                    return;
                }
            }
        }
    }

    // Check for header match
    function checkHeaderMatch (argument) {
        return ex_obj.header.indexOf(argument);
    }

    var description = ex_obj.o.find('#description').val();

    var asset = '';
    var lon = 'lon';
    var lat = 'lat';
    var taxonomy = 'taxonomy';
    var number = 'number';
    var area = 'area';
    var structural = 'structural';
    var non_structural = 'nonstructural';
    var contents = 'contents';
    var business = 'business';
    var day = 'day';
    var night = 'night';
    var transit = 'transit';
    var insuranceLimit = '';
    var deductible = '';
    var retrofitting = '';
    var limit = '';
    var assetId = 'id';

    // list of tags
    var asset_tags;
    var tags = ex_obj.o.find('#tags').tagsinput('items');

    // Get the the index for each header element
    var latInx = checkHeaderMatch(lat);
    var lonInx = checkHeaderMatch(lon);
    var taxonomyInx = checkHeaderMatch(taxonomy);
    var numberInx = checkHeaderMatch(number);
    var areaInx = checkHeaderMatch(area);
    var structuralInx = checkHeaderMatch(structural);
    var non_structuralInx = checkHeaderMatch(non_structural);
    var contentsInx = checkHeaderMatch(contents);
    var businessInx = checkHeaderMatch(business);
    var dayInx = checkHeaderMatch(day);
    var nightInx = checkHeaderMatch(night);
    var transitInx = checkHeaderMatch(transit);
    var retrofittingInx = checkHeaderMatch('retrofitting');
    var limitInx = checkHeaderMatch('limit');
    var deductibleInx = checkHeaderMatch('deductible');
    var assetIdInx = checkHeaderMatch(assetId);

    // Pre area selection
    var areaType = "";
    var areaTypeSelected = ex_obj.o.find('#perAreaSelect').val();
    if (ex_obj.o.find('#perArea').is(":visible")) {
        areaType += '\t\t\t<area type="'+areaTypeSelected+'" unit="' + ex_obj.o.find('#area_units').val() + '" />\n';
    }

    // Cost Type
    var costType= '';
    var costTypeStruc = ex_obj.o.find('#costStruc option:selected').val();
    if (costTypeStruc !== 'none') {
        costType += '\t\t\t\t<costType name="structural" type="'+costTypeStruc+'" unit="' + ex_obj.o.find('#structural_costs_units').val() + '"/>\n';
    }

    var costTypeNonStruc = ex_obj.o.find('#costNonStruc option:selected').val();
    if (costTypeNonStruc !== 'none') {
        costType += '\t\t\t\t<costType name="nonstructural" type="'+costTypeNonStruc+'" unit="' + ex_obj.o.find('#nonstructural_costs_units').val() + '"/>\n';
    }

    var costTypeContent = ex_obj.o.find('#costContent option:selected').val();
    if (costTypeContent !== 'none') {
        costType += '\t\t\t\t<costType name="contents" type="'+costTypeContent+'" unit="' + ex_obj.o.find('#contents_costs_units').val() + '"/>\n';
    }

    var costTypeBusiness = ex_obj.o.find('#costBusiness option:selected').val();
    if (costTypeBusiness !== 'none') {
        costType += '\t\t\t\t<costType name="business_interruption" type="'+costTypeBusiness+'" unit="' + ex_obj.o.find('#busi_inter_costs_units').val() + '"/>\n';
    }

    var limitState = ex_obj.o.find('#limitSelect option:selected').val();
    if (limitState == 'absolute') {
        insuranceLimit = '\t\t\t<insuranceLimit isAbsolute="true"/>\n';
    } else if (limitState == 'relative') {
        insuranceLimit = '\t\t\t<insuranceLimit isAbsolute="false"/>\n';
    }

    var deductibleState = ex_obj.o.find('#deductibleSelect option:selected').val();
    if (deductibleState == 'absolute') {
        deductible = '\t\t\t<deductible isAbsolute="true"/>\n';
    } else if (deductibleState == 'relative') {
        deductible = '\t\t\t<deductible isAbsolute="false"/>\n';
    }

    var retrofittingSelect = ex_obj.o.find('#retrofittingSelect input:checked').val();
    if (exp_type == 'xml') {
        // Create the asset
        for (var i = 0; i < not_empty_rows ; i++) {
            var costTypes = '\t\t\t<costTypes>\n';
            var costs ='\t\t\t\t<costs>\n';
            var occupancies = "";

            if (numberInx > -1 ) {
                number = 'number="'+ data[i][numberInx]+'"';
            } else {
                number = '';
            }
            if (latInx > -1 ) {
                lat = 'lat="'+ data[i][latInx]+'"';
            } else {
                lat = '';
            }
            if (lonInx > -1 ) {
                lon = 'lon="'+ data[i][lonInx]+'"';
            } else {
                lon = '';
            }
            if (taxonomyInx > -1 ) {
                taxonomy = 'taxonomy="'+ data[i][taxonomyInx]+'"';
            } else {
                taxonomy = '';
            }
            if (areaInx > -1 ) {
                area = 'area="'+ data[i][areaInx]+'"';
            } else {
                area = '';
            }
            if (assetIdInx > -1 ) {
                id = data[i][assetIdInx];
            } else {
                id = '';
            }

            // Insurance Limit
            var limitValue = '';
            if (limitState == 'absolute') {
                limitValue = ' insuranceLimit="'+data[i][limitInx]+'"';
            } else if (limitState == 'relative') {
                limitValue = ' insuranceLimit="'+data[i][limitInx]+'"';
            }

            // Retrofitted
            if (retrofittingSelect == 'retrofitting') {
                retrofitting = ' retrofitted="'+data[i][retrofittingInx]+'"';
            }

            // deductibleSelect
            var deductibleValue = '';
            if (deductibleState == 'absolute') {
                deductibleValue = ' deductible="'+data[i][deductibleInx]+'"';
            } else if (deductibleState == 'relative') {
                deductibleValue = ' deductible="'+data[i][deductibleInx]+'"';
            }

            // Economic Cost
            if (structuralInx > -1 ) {
                costTypes += '\t\t\t\t<costType name="structural" type="per_asset" unit="USD" />\n';
                costs += '\t\t\t\t\t<cost type="structural" value="'+ data[i][structuralInx]+'"'+retrofitting+deductibleValue+limitValue+'/>\n';
            }
            if (non_structuralInx > -1 ) {
                costs += '\t\t\t\t\t<cost type="nonstructural" value="'+ data[i][non_structuralInx]+'"/>\n';
            }
            if (contentsInx > -1 ) {
                costs += '\t\t\t\t\t<cost type="contents" value="'+ data[i][contentsInx]+'"/>\n';
            }
            if (businessInx > -1 ) {
                costs += '\t\t\t\t\t<cost type="business_interruption" value="'+ data[i][businessInx]+'"/>\n';
            }

            // Occupancies
            if (dayInx > -1 ) {
                occupancies += '\t\t\t\t\t<occupancy occupants="'+ data[i][dayInx]+'" period="day"/>\n';
            }
            if (nightInx > -1 ) {
                occupancies += '\t\t\t\t\t<occupancy occupants="'+ data[i][nightInx]+'" period="night"/>\n';
            }
            if (transitInx > -1 ) {
                occupancies += '\t\t\t\t\t<occupancy occupants="'+ data[i][transitInx]+'" period="transit"/>\n';
            }

            costs += '\t\t\t\t</costs>\n';
            if (occupancies != "") {
                occupancies = '\t\t\t\t<occupancies>\n' + occupancies + '\t\t\t\t</occupancies>\n';
            }

            asset_tags = "";
            for (var t_id = 0, e = ex_obj.headerbase_len ; e < ex_obj.headerbase_len + tags.length ; e++, t_id++) {
                if (data[i][e] !== null && data[i][e].length != 0) {
                    asset_tags += (asset_tags == "" ? "" : " ") + tags[t_id] + "=\"" + data[i][e] + "\"";
                }
            }
            if (asset_tags.length != 0) {
                asset_tags = "\t\t\t\t<tags " + asset_tags + " />\n";
            }

            asset +=
                '\t\t\t<asset id="'+id+'" '+number+' '+area+' '+taxonomy+' >\n' +
                '\t\t\t\t<location '+lon+' '+lat+' />\n' +
                costs +
                occupancies +
                asset_tags +
                '\t\t\t</asset>\n';
        }
    }
    else if (exp_type == 'csv') {
        var ex_csv = ex_obj.o.find('div[name="exposure-csv-html"] select').val();

        if (ex_csv == null || ex_csv.length < 1) {
            ret.str += "'Exposure csv files': at least one file must be selected.\n";
        }
        if (ex_csv != null) {
            for (f_id in ex_csv) {
                fname = ex_csv[f_id];
                uniqueness_add(files_list, 'exposure csv model: item #' + (parseInt(f_id) + 1), fname);
                ret.str += uniqueness_check(files_list);
                asset += '\t\t\t' + basename(ex_csv[f_id]) + '\n';
            }
        }
    }
    else {
        ret.str += 'Unknown type of exposure [' + exp_type + ']';
    }
    var tagNames = "";
    if (tags.length > 0) {
        tagNames = "\t\t<tagNames>";
        for (var i = 0 ; i < tags.length ; i++) {
            tagNames += (i == 0 ? "" : " ") + tags[i];
        }
        tagNames += "</tagNames>\n";
    }

    var occupancyPeriods = "";
    if (exp_type == 'csv') {
        occupancyPeriods = "\t\t<occupancyPeriods>";

        var occus = ["day", "night", "transit"];
        for (var occu_idx in occus ) {
            var occu = occus[occu_idx];

            if (ex_obj.o.find('div#occupantsCheckBoxes input[type="checkbox"][value="' + occu + '"]').is(':checked')) {
                occupancyPeriods += occu + " ";
            }
        }
        occupancyPeriods += "</occupancyPeriods>\n";
    }
    // Create a NRML element
    var nrml =
        '<?xml version="1.0" encoding="UTF-8"?>\n' +
        '<nrml xmlns="http://openquake.org/xmlns/nrml/0.4">\n' +
            '\t<exposureModel id="ex1" category="buildings" taxonomySource="GEM taxonomy">\n' +
                '\t\t<description>' + description + '</description>\n' +
                '\t\t<conversions>\n' +
                    areaType +
                    '\t\t\t<costTypes>\n' +
                    costType +
                    '\t\t\t</costTypes>\n' +
                    insuranceLimit +
                    deductible +
                '\t\t</conversions>\n' +
                tagNames +
                occupancyPeriods +
                '\t\t<assets>\n' +
                    asset +
                '\t\t</assets>\n' +
            '\t</exposureModel>\n' +
        '</nrml>\n';

    if (ret.str == '') {
        ret.ret = 0;
        validateAndDisplayNRML(nrml, 'ex', ex_obj);
    }
    else {
        gem_ipt.error_msg(ret.str);
    }
}

function ex_convert2nrml_cb(e)
{
    $('.ex_gid #outputDiv').hide();
    ex_convert2nrml(1);
}


ex_obj.o.find('#convertBtn').click(ex_convert2nrml_cb);

function exposure_tags_cb(event)
{
    var ret;
    if (event.type == 'beforeItemAdd') {
        if (event.item.search(/^[a-zA-Z_]\w*$/g) == -1) {
            event.cancel = true;
            gem_ipt.error_msg('Tag name not valid, must start with a letter or "_", followed optionally by letters and/or digits and/or "_".\n');
        }
    }
    else if (event.type == "itemAdded")
        ret = ex_updateTableTags(+1);
    else if (event.type == "itemRemoved")
        ret = ex_updateTableTags(-1);
    else
        ret = false;
    ex_updateTable();
    return ret;
}

function exposure_manager()
{
    console.log('exposure_manager');
    var exp_type = ex_obj.o.find('input:radio[name="exposure-type"]:checked').val();
    var to_hide = false;

    if (exp_type == 'xml') {
        if (ex_obj.o.find('.exposure-type-xml').is(":hidden")) {
            to_hide = true;
        }
        ex_obj.o.find('.exposure-type-xml').show();
        ex_obj.o.find('.exposure-type-csv').hide();
    }
    else if (exp_type == 'csv') {
        if (ex_obj.o.find('.exposure-type-xml').is(":visible")) {
            to_hide = true;
        }
        ex_obj.o.find('.exposure-type-xml').hide();
        ex_obj.o.find('.exposure-type-csv').show();
    }

    if (to_hide) {
        $('.ex_gid #downloadLink').hide();
        $('.ex_gid #outputDiv').hide();
    }

}

function exposure_csv_fileNew_upload(event)
{
    form = $(event.target).parent('form').get(0);
    return generic_fileNew_upload('ex', form, event);
}

function exposure_csv_fileNew_collect(event, reply)
{
    return generic_fileNew_collect('ex', reply, event);
}

function exposure_csv_fileNew_cb(e) {
    if (typeof gem_api == 'undefined') {

        /* generic callback to show upload div (init) */
        $(ex_obj.pfx + ' div[name="' + e.target.name + '"]').slideToggle();
        if ($(ex_obj.pfx + ' div[name="' + e.target.name + '"]').css('display') != 'none') {
            if (typeof window.gem_not_interactive == 'undefined') {
                $(ex_obj.pfx + ' div[name="' + e.target.name + '"] input[type="file"]').click();
                var name = e.target.name;

                function uploader_rollback() {
                    if ($(ex_obj.pfx + ' div[name="' + name +
                          '"] input[type="file"]').val().length > 0) {
                        $(document.body).off('focusin', uploader_rollback);
                        return;
                    }

                    var $msg = $(ex_obj.pfx + ' div[name="' + name + '"] div[name="msg"]');
                    $msg.html("Upload file cancelled.");
                    $(ex_obj.pfx + ' div[name="' + name + '"]').delay(3000).slideUp({
                        done: function () {
                            $(ex_obj.pfx + ' div[name="' + name + '"] div[name="msg"]').html('');
                        }
                    });
                    $(document.body).off('focusin', uploader_rollback);
                }
                $(document.body).on('focusin', uploader_rollback);
            }
        }
    }
    else { // if (typeof gem_api == 'undefined') {
        var event = e;
        var $msg = $(ex_obj.pfx + ' div[name="' + e.target.name + '"] div[name="msg"]');
        $(ex_obj.pfx + ' div[name="' + e.target.name + '"]').slideToggle();

        var $sibling = $(e.target).siblings("select[name='file_html']");
        var subdir = $sibling.attr('data-gem-subdir');
        var sel_grp = $sibling.attr('data-gem-group');
        var is_multiple = $sibling.is("[multiple]");

        function cb(uuid, app_msg) {
            if (! app_msg.complete)
                return;

            var cmd_msg = app_msg.result;
            if (cmd_msg.success) {
                $msg.html("File '" + cmd_msg.content[0] + "' collected correctly.");
                exposure_csv_fileNew_collect(event, cmd_msg);
            }
            else {
                $msg.html(cmd_msg.reason);
            }
            $(ex_obj.pfx + ' div[name="' + event.target.name + '"]').delay(3000).slideUp();
        }
        gem_api.select_and_copy_file(cb, subdir, is_multiple);
    }
}

function exposure_init() {
    /////////////////////////////////////////////////////////
    // Manage the visibility of the perArea selection menu //
    /////////////////////////////////////////////////////////
    ex_obj.o.find('#perArea').hide();

    ex_obj.o.find('#retrofittingSelect').hide();
    ex_obj.o.find('#limitDiv').hide();
    ex_obj.o.find('#deductibleDiv').hide();
    ex_obj.o.find('#structural_costs_units_div').hide();
    ex_obj.o.find('#nonstructural_costs_units_div').hide();
    ex_obj.o.find('#contents_costs_units_div').hide();
    ex_obj.o.find('#busi_inter_costs_units_div').hide();

    ex_updateTable();
    ex_obj.o.find('div[name="exposuretbl"] button#new_exposuretbl_add').click(
        ex_obj.exposuretbl_add);
    ex_obj.exposuretbl_add();

    ex_obj.o.find('#outputDiv').hide();
    // tag events 'itemAddedOnInit', 'beforeItemAdd' and 'beforeItemRemove' are not still managed
    ex_obj.o.find('#tags').on('beforeItemAdd', exposure_tags_cb);
    ex_obj.o.find('#tags').on('itemAdded', exposure_tags_cb);
    ex_obj.o.find('#tags').on('itemRemoved', exposure_tags_cb);

    ex_obj.o.find("input[name='exposure-type']").click(exposure_manager);
    file_uploader_init(ex_obj.o, 'exposure-csv', exposure_csv_fileNew_cb, exposure_csv_fileNew_upload);

    exposure_manager();
}

// tab initialization
$(document).ready(function () {
    exposure_init();

    $('#absoluteSpinner').hide();

});
