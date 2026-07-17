$(document).ready(function () {
    window.gem_example_completed = false;
    // this is a workaround for a bug fixed in jquery 1.9 (checked is toggled after that handler is fired)
    $(cf_obj['scen'].pfx + ' input[type="checkbox"][name="hazard"]').prop('checked', true).triggerHandler('click');

    $(cf_obj['scen'].pfx + " div[name='rupture-file-new'] input[name='file_upload']").submit();

    $(cf_obj['scen'].pfx + " div[name='region-grid'] input[name='grid_spacing']").val("5.0");

    $(cf_obj['scen'].pfx + " div[name='region-grid'] input[type='radio'][name='region_grid']" +
      "[value='infer-from-exposure']").prop('checked', true).triggerHandler('click');

    var data = [
        [ "40", "40" ], ["30", "30"], ["20", "20" ]
    ];
    
    var table = $(cf_obj['scen'].pfx + ' div[name="table"]').handsontable('getInstance');
    table.loadData(data);
    
    $(cf_obj['scen'].pfx + ' div[name="hazard-gmpe_specify-gmpe"] input[type="text"]').focus();
    setTimeout(function () {
        $(cf_obj['scen'].pfx + ' div[name="exposure-model-html"] select[name="file_html"]').val('exposure_model' + gem_path_sep + 'exposure_model_vol_full.zip');
        
        $(cf_obj['scen'].pfx + ' div[name="rupture-file-html"] select[name="file_html"]').val('rupture_file' + gem_path_sep + 'earthquake_rupture_model.xml');
        // waiting for gmpe list population
        $(cf_obj['scen'].pfx + ' div[name="hazard-gmpe_specify-gmpe"] div.sol-label-text:contains("AbrahamsonEtAl2014RegCHN")'
         ).click()
        $(cf_obj['scen'].pfx + ' button[name="download"]').click();
        window.gem_example_completed = true;
    }, 1000);
});
