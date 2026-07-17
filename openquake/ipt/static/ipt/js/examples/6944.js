$(document).ready(function () {
    window.gem_example_completed = false;

    $(cf_obj['vol'].pfx + ' input[type="checkbox"][name="ashfall"]').prop('checked', true).triggerHandler('click');
    $(cf_obj['vol'].pfx + ' input[type="checkbox"][name="lavaflow"]').prop('checked', true).triggerHandler('click');
    $(cf_obj['vol'].pfx + ' input[type="checkbox"][name="lahar"]').prop('checked', true).triggerHandler('click');
    $(cf_obj['vol'].pfx + ' input[type="checkbox"][name="pyroclasticflow"]').prop('checked', true).triggerHandler('click');


    $(cf_obj['vol'].pfx + ' div[name="ashfall-input"] select[name="in-type"]').val('shape').triggerHandler('change');
    $(cf_obj['vol'].pfx + ' div[name="lavaflow-input"] select[name="in-type"]').val('openquake').triggerHandler('change');
    $(cf_obj['vol'].pfx + ' div[name="lahar-input"] select[name="in-type"]').val('openquake').triggerHandler('change');
    $(cf_obj['vol'].pfx + ' div[name="pyroclasticflow-input"] select[name="in-type"]').val('openquake').triggerHandler('change');


    setTimeout(function () {
        $(cf_obj['vol'].pfx + ' div[name="ashfall-file-html"] select[name="file_html"]').val('ashfall_file' + gem_path_sep + 'ashfall_geom.zip');
        $(cf_obj['vol'].pfx + ' div[name="ashfall-file-html"] select[name="file_html"]').triggerHandler('change');
        $(cf_obj['vol'].pfx + ' div[name="lavaflow-file-html"] select[name="file_html"]').val('lavaflow_file' + gem_path_sep + 'lavaflow_vol_full.csv');
        $(cf_obj['vol'].pfx + ' div[name="lahar-file-html"] select[name="file_html"]').val('lahar_file' + gem_path_sep + 'lahar_vol_full.csv');
        $(cf_obj['vol'].pfx + ' div[name="pyroclasticflow-file-html"] select[name="file_html"]').val('pyroclasticflow_file' + gem_path_sep + 'pyroclasticflow_vol_full.csv');
        
        $(cf_obj['vol'].pfx + '  div[name="ashfall-input"] input[type="text"][name="spec-ass-haz-dist"]').val(10.0)
        $(cf_obj['vol'].pfx + '  div[name="lavaflow-input"] input[type="text"][name="spec-ass-haz-dist"]').val(12.0)
        $(cf_obj['vol'].pfx + '  div[name="lahar-input"] input[type="text"][name="spec-ass-haz-dist"]').val(14.0)
        $(cf_obj['vol'].pfx + '  div[name="pyroclasticflow-input"] input[type="text"][name="spec-ass-haz-dist"]').val(16.0)
        
        
        $(cf_obj['vol'].pfx + ' div[name="exposure-model-html"] select[name="file_html"]').val('exposure_model' + gem_path_sep + 'exposure_model_vol_full.zip');

        $(cf_obj['vol'].pfx + ' div[name="fm-ashfall-file-html"] select[name="file_html"]').val('fragility_model' + gem_path_sep + 'fragility_model_vol_full.xml');

        $(cf_obj['vol'].pfx + ' input[type="checkbox"][name="is-cons-models"]').prop('checked', true).triggerHandler('click');
        $(cf_obj['vol'].pfx + ' div[name="fm-ashfall-cons-html"] select[name="file_html"]').val('fragility_cons' + gem_path_sep + 'consequence_model_vol_full.xml');

        // Click to download EventBase.zip
        setTimeout(function () {
            $(cf_obj['vol'].pfx + ' div[name="ashfall-input"] select[name="haz-field"]').val('value');
            
            $(cf_obj['vol'].pfx + ' button[name="download"]').click();
            window.gem_example_completed = true;
        }, 1000);
    }, 1000);

    return;
});
