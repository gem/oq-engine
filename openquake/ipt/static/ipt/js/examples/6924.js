$(document).ready(function () {
    window.gem_example_completed = false;

    $(cf_obj['vol'].pfx + ' input[type="checkbox"][name="lavaflow"]').prop('checked', true).triggerHandler('click');
    $(cf_obj['vol'].pfx + ' input[type="checkbox"][name="ashfall"]').prop('checked', false).triggerHandler('click');

    $(cf_obj['vol'].pfx + ' div[name="lavaflow-input"] select[name="in-type"]').val('text-to-wkt').triggerHandler('change');


    setTimeout(function () {
        $(cf_obj['vol'].pfx + ' div[name="lavaflow-file-html"] select[name="file_html"]').val('lavaflow_file/lava_flow_Q-LavaHa.asc');
        $(cf_obj['vol'].pfx + ' div[name="lavaflow-input"]  input[type="text"][name="epsg"]').val('32633');

        $(cf_obj['vol'].pfx + ' div[name="exposure-model-html"] select[name="file_html"]').val('exposure_model/exposure_model_vol_full.zip');

        // Click to download EventBase.zip
        setTimeout(function () {
            $(cf_obj['vol'].pfx + ' button[name="download"]').click();
            window.gem_example_completed = true;
        }, 1000);
    }, 1000);

    return;
});
