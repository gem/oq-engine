$(document).ready(function () {
    $('.ex_gid input[name="exposure-type"][value="xml"]').prop('checked', true).triggerHandler('click');

    $('.ex_gid #description').val('The description of exposure function');
    $('.ex_gid #costStruc').val('per_asset');
    $('.ex_gid #costStruc').trigger('change');
    { // blocks are used to reflect DOM hierarchy
        $('.ex_gid #structural_costs_units').val('GBP');
        $('.ex_gid #structural_costs_units').trigger('change');

        $('.ex_gid #retroChbx').prop('checked', true);
        $('.ex_gid #retroChbx').trigger('change');
        $('.ex_gid #limitSelect').val('relative');
        $('.ex_gid #limitSelect').trigger('change');
        $('.ex_gid #deductibleSelect').val('absolute');
        $('.ex_gid #deductibleSelect').trigger('change');
    }
    $('.ex_gid #costNonStruc').val('aggregated');
    $('.ex_gid #costNonStruc').trigger('change');
    {
        $('.ex_gid #nonstructural_costs_units').val('CAD');
        $('.ex_gid #nonstructural_costs_units').trigger('change');
    }

    $('.ex_gid #costContent').val('per_area');
    $('.ex_gid #costContent').trigger('change');
    {
        $('.ex_gid #contents_costs_units').val('AUD');
        $('.ex_gid #contents_costs_units').trigger('change');

        $('.ex_gid #perAreaSelect').val('aggregated');
        $('.ex_gid #perAreaSelect').trigger('change');
        $('.ex_gid #area_units').val('Km²');
        $('.ex_gid #area_units').trigger('change');
    }
    $('.ex_gid #costBusiness').val('aggregated');
    $('.ex_gid #costBusiness').trigger('change');
    {
        $('.ex_gid #busi_inter_costs_units').val('NOK/day');
        $('.ex_gid #busi_inter_costs_units').trigger('change');
    }

    $('.ex_gid #occupantsCheckBoxes [value="night"]').prop('checked', true);
    $('.ex_gid #occupantsCheckBoxes [value="night"]').trigger('change');

    var data = [[]];
    var table = $('.ex_gid div[name="table-0"]').handsontable('getInstance');

    // for each column add a calculated value
    for (var i = 0 ; i < table.countCols() ; i++) {
        if (i == 5) {
            // we want to show what happens when a cell is left empty
            data[0][i] = "";
        }
        else {
            data[0][i] = parseFloat(i) / 100.0;
        }
    }

    table.loadData(data);

    $('.ex_gid #convertBtn').trigger('click');
    window.gem_example_completed = true;
});
