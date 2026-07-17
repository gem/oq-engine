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

var sc_obj = {
    pfx: 'div.sc_gid ',
    o: $('div.sc_gid'),
    tbl_file: null,
    tbl: {},
    nrml: "",
    header: [],

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
            sc_obj.o.find('#perArea').show();
        else
            sc_obj.o.find('#perArea').hide();
    }
};

sc_obj.o.find('#costStruc').change(function() {
    // There is a bug in the handsontable lib where one can not
    // paste values into the table when the user has made a selection
    // from a dropdown menu. The reason for this error is that the focus
    // remains on the menu.
    // The workaround for this is to un-focus the selection menu with blur()
    // More info: https://github.com/handsontable/handsontable/issues/2973
    $(this).blur();
    sc_obj.perAreaManager($(this).val(), $(this).context.id);
    if ($(this).val() != 'none') {
        sc_obj.o.find('#structural_costs_units_div').show();
        sc_obj.o.find('#retrofittingSelect').show();
        sc_obj.o.find('#limitDiv').show();
        sc_obj.o.find('#deductibleDiv').show();
    } else {
        sc_obj.o.find('#structural_costs_units_div').hide();
        sc_obj.o.find('#retrofittingSelect').hide();
        sc_obj.o.find('#limitDiv').hide();
        sc_obj.o.find('#deductibleDiv').hide();
        // Uncheck retrofitting
        sc_obj.o.find('#retroChbx').attr('checked', false);
        // Unselect the limit & deductible
        sc_obj.o.find('#limitSelect').val('0');
        sc_obj.o.find('#deductibleSelect').val('0');
    }
});

sc_obj.o.find('#costNonStruc').change(function() {
    // unfocus the selection menu, see the note at the costStruc change event
    $(this).blur();

    if ($(this).val() != 'none') {
        sc_obj.o.find('#nonstructural_costs_units_div').show();
    }
    else {
        sc_obj.o.find('#nonstructural_costs_units_div').hide();
    }
    sc_obj.perAreaManager($(this).val(), $(this).context.id);
});

sc_obj.o.find('#costContent').change(function() {
    if ($(this).val() != 'none') {
        sc_obj.o.find('#contents_costs_units_div').show();
    }
    else {
        sc_obj.o.find('#contents_costs_units_div').hide();
    }
    // unfocus the selection menu, see the note at the costStruc change event
    $(this).blur();
    sc_obj.perAreaManager($(this).val(), $(this).context.id);
});

sc_obj.o.find('#costBusiness').change(function() {
    if ($(this).val() != 'none') {
        sc_obj.o.find('#busi_inter_costs_units_div').show();
    }
    else {
        sc_obj.o.find('#busi_inter_costs_units_div').hide();
    }

    // unfocus the selection menu, see the note at the costStruc change event
    $(this).blur();
    sc_obj.perAreaManager($(this).val(), $(this).context.id);
});

sc_obj.o.find('#form').change(function() {
    // unfocus the selection menu, see the note at the costStruc change event
    $(this).blur();
    sc_updateTable();
    sc_obj.o.find('#outputDiv').hide();
});

function checkForValueInHeader(header, argument) {
    var inx = sc_obj.header.indexOf(argument);
    return inx;
}

function sc_updateTable() {
    // Remove any existing table, if already exists
    if (sc_obj.o.find('#table').handsontable('getInstance') !== undefined) {
        sc_obj.o.find('#table').handsontable('destroy');
    }

    sc_obj.o.find('#table_file').val("");
    sc_obj.tbl_file = null;

    // Default columns
    sc_obj.header = [ 'Longitude', 'Latitude', 'Vs30', 'Vs30 Type', 'Depth 1 km/s', 'Depth 2.5 km/s'];

    function checkForValue (argument, valueArg) {
        // Modify the table header only when the menu is altered
        // This constraint will allow Limit, Deductible and Occupant elements to be
        // added to the header
        if (argument != 'none' && valueArg === undefined) {
            if (checkForValueInHeader(sc_obj.header, argument) == -1) {
                sc_obj.header.push(argument);
            }
        // This constraint will allow structural, nonstructural, contents and business
        // costs to be added to the header
        } else if (argument != 'none' && valueArg !== undefined) {
            if (checkForValueInHeader(sc_obj.header, valueArg) == -1) {
                sc_obj.header.push(valueArg);
            }
        }
    }

    // Get info from the expsure form and use it to build the table header
    sc_obj.o.find('#costStruc option:selected').each(function() {
        checkForValue($(this).attr('value'), 'structural');
    });

    sc_obj.o.find('#costNonStruc option:selected').each(function() {
        checkForValue($(this).attr('value'), 'nonstructural');
    });

    sc_obj.o.find('#costContent option:selected').each(function() {
        checkForValue($(this).attr('value'), 'contents');
    });

    sc_obj.o.find('#costBusiness option:selected').each(function() {
        checkForValue($(this).attr('value'), 'business');
    });

    sc_obj.o.find('#limitSelect option:selected').each(function() {
        checkForValue($(this).attr('value'), 'limit');
    });

    sc_obj.o.find('#deductibleSelect option:selected').each(function() {
        checkForValue($(this).attr('value'), 'deductible');
    });

    var perAreaVisible = sc_obj.o.find('#perArea:visible').length;
    if (perAreaVisible === 1) {
        sc_obj.header.push('area');
    }

    sc_obj.o.find('#occupantsCheckBoxes input:checked').each(function() {
        sc_obj.header.push($(this).attr('value'));
        // unfocus the selection menu, see the note at the exposure costStruc change event
        $(this).blur();
    });

    sc_obj.o.find('#retrofittingSelect input:checked').each(function() {
        sc_obj.header.push($(this).attr('value'));
        // unfocus the selection menu, see the note at the exposure costStruc change event
        $(this).blur();
    });

    var headerLength = sc_obj.header.length;

    // Create the table
    ///////////////////////////////
    /// Exposure Table Settings ///
    ///////////////////////////////
    sc_obj.o.find('#table').handsontable({
        colHeaders: sc_obj.header,
        rowHeaders: true,
        contextMenu: true,
        startRows: 3,
        startCols: headerLength,
        maxCols: headerLength,
        className: "htRight"
    });
    sc_obj.tbl = sc_obj.o.find('#table').handsontable('getInstance');
    setTimeout(function() {
        return gem_tableHeightUpdate(sc_obj.o.find('#table'));
    }, 0);

    sc_obj.tbl.addHook('afterCreateRow', function() {
        return gem_tableHeightUpdate(sc_obj.o.find('#table'));
    });

    sc_obj.tbl.addHook('afterRemoveRow', function() {
        return gem_tableHeightUpdate(sc_obj.o.find('#table'));
    });

    sc_obj.tbl.addHook('afterChange', function(changes, source) {
        // when loadData is used, for performace reasons, changes are 'null'
        if (changes != null || source != 'loadData') {
            sc_obj.o.find('#table_file').val("");
            sc_obj.tbl_file = null;
        }
    });

    sc_obj.o.find('#outputText').empty();
    sc_obj.o.find('#convertBtn').show();
}

sc_obj.o.find('#downloadBtn').click(function() {
    sendbackNRML(sc_obj.nrml, 'sc');
});

if (typeof gem_api != 'undefined') {
    sc_obj.o.find('#delegateDownloadBtn').click(function() {
        var uu = delegate_downloadNRML(sc_obj.nrml, 'sc', delegate_downloadNRML_cb);
        console.log("fired cmd with uuid: " + uu);
    });
    sc_obj.o.find('#delegateCollectBtn').click(function() {
        var uu = delegate_downloadNRML(sc_obj.nrml, 'sc', delegate_collectNRML_cb);
        console.log("fired cmd with uuid: " + uu);
    });
}

sc_obj.o.find('#convertBtn').click(function() {
    var tab_data = null;

    // Get the values from the table
    if (sc_obj.o.find('input#table_file')[0].files.length > 0) {
        tab_data = sc_obj.tbl_file;
    }
    else {
        tab_data = sc_obj.tbl.getData();
    }

    var not_empty_rows = not_empty_rows_get(tab_data);

    for (var i = 0; i < not_empty_rows ; i++) {
        for (var j = 0; j < tab_data[i].length; j++) {
            if (tab_data[i][j] === null || tab_data[i][j].toString().trim() == "") {
                var error_msg = "empty cell detected at table coords (" + (i+1) + ", " + (j+1) + ")";
                output_manager('sc', error_msg, null, null);
                return;
            }
        }
    }
    var sites = '';
    // Check for null values
    for (var i = 0; i < not_empty_rows ; i++) {
        sites += '\t<site lon="' + tab_data[i][0] + '" lat="' + tab_data[i][1] + '" vs30="' + tab_data[i][2] +
             '" vs30Type="' + tab_data[i][3] + '" z1pt0="' + tab_data[i][4] + '" z2pt5="' + tab_data[i][5] +'"/>\n';
    }

    // Create a NRML element
    var nrml = '<?xml version="1.0" encoding="utf-8"?>\n' +
            '<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">\n' +
            '  <siteModel>\n' +
            sites +
            '  </siteModel>\n' +
        '</nrml>\n';

    validateAndDisplayNRML(nrml, 'sc', sc_obj);
});

// tab initialization
$(document).ready(function () {
    /////////////////////////////////////////////////////////
    // Manage the visibility of the perArea selection menu //
    /////////////////////////////////////////////////////////
    sc_updateTable();
    sc_obj.o.find('input#table_file').on(
        'change', function sc_table_file_mgmt(evt) { ipt_table_file_mgmt(evt, sc_obj, 0, -180, 180); });
    sc_obj.o.find('#new_row_add').click(function() {
        sc_obj.tbl.alter('insert_row');
    });
    sc_obj.o.find('#outputDiv').hide();
    $('#absoluteSpinner').hide();
});
