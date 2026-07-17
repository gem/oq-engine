$(document).ready(function () {
    window.gem_example_completed = false;
    // this is a workaround for a bug fixed in jquery 1.9 (checked is toggled after that handler is fired
    $(cf_obj['vol'].pfx + ' input[type="checkbox"][name="lahar"]').prop('checked', true).triggerHandler('click');
    $(cf_obj['vol'].pfx + ' input[type="checkbox"][name="lavaflow"]').prop('checked', true).triggerHandler('click');
    $(cf_obj['vol'].pfx + ' input[type="checkbox"][name="ashfall"]').prop('checked', false).triggerHandler('click');
    $(cf_obj['vol'].pfx + ' div[name="lavaflow-input"] select[name="in-type"]').val('shape-to-wkt').triggerHandler('change');
    $(cf_obj['vol'].pfx + ' div[name="lahar-input"] select[name="in-type"]').val('shape-to-wkt').triggerHandler('change');



    setTimeout(function () {
        $(cf_obj['vol'].pfx + ' div[name="lavaflow-file-html"] select[name="file_html"]').val('lavaflow_file' + gem_path_sep + 'lava-geom-shp.zip');
        $(cf_obj['vol'].pfx + ' div[name="lahar-file-html"] select[name="file_html"]').val('lahar_file' + gem_path_sep + 'lahar-geom.zip');

        $(cf_obj['vol'].pfx + ' div[name="exposure-model-html"] select[name="file_html"]').val('exposure_model' + gem_path_sep + 'exposure_model_vol_full.zip');

        $(cf_obj['vol'].pfx + ' div[name="fm-ashfall-file-html"] select[name="file_html"]').val('fragility_model' + gem_path_sep + 'fragility_model_vol_full.xml');

        $(cf_obj['vol'].pfx + ' input[type="checkbox"][name="is-cons-models"]').prop('checked', true).triggerHandler('click');
        $(cf_obj['vol'].pfx + ' div[name="fm-ashfall-cons-html"] select[name="file_html"]').val('fragility_cons' + gem_path_sep + 'consequence_model_vol_full.xml');

        // Click to download EventBase.zip
        setTimeout(function () {
            $(cf_obj['vol'].pfx + ' button[name="download"]').click();
            window.gem_example_completed = true;
        }, 1000);
    }, 1000);

    return;
});
