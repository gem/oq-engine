$(document).ready(function () {
    $('.ex_gid input[name="exposure-type"][value="csv"]').prop('checked', true).triggerHandler('click');

    $csv_files = ex_obj.o.find("div[name='exposure-csv-html'] select[name='file_html'] option")
    for (var i = 0 ; i < $csv_files.length ; i++) {
        $csv_item = $($csv_files[i]);
        if ($csv_item.val() == 'exposure_csv/exposure_good.csv'
            // || $csv_item.val() == 'exposure_csv/exposure_good2.csv'
            // || $csv_item.val() == 'exposure_csv/exposure_wrong_header.csv'
            // || $csv_item.val() == 'exposure_csv/exposure_wrong_ncol.csv'
           )
            $csv_item.attr('selected','selected');
    }

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

    // add three tags
    $('.ex_gid #tags').tagsinput('add', 'first');
    $('.ex_gid #tags').tagsinput('add', 'second');
    $('.ex_gid #tags').tagsinput('add', 'third');

    var table = $('.ex_gid div[name="table-0"]').handsontable('getInstance');

    var data = [];

    // add 2 rows of data to example table
    for (var e = 0 ; e < 2 ; e++) {
        data[e] = [];
        // for each column add a calculated value
        for (var i = 0 ; i < table.countCols() ; i++) {
            // add a special case to skip population of a tag cell
            if (e == 1 && i == 15)
                continue;

            var cell_val = "" + (parseFloat(e) + parseFloat(i) / 100.0);
            // trim 2 digits after dot.
            data[e][i] = cell_val.match(/^[0-9]+\.?[0-9]?[0-9]?/)[0];
        }
    }
    $('.ex_gid #convertBtn').trigger('click');

    setTimeout(function () {
        if ($('.ex_gid button[id="downloadBtn"]').is(":visible")) {
            $('.ex_gid button[id="downloadBtn"]').click();
        }
        window.gem_example_completed = true;
    }, 1000);
});
