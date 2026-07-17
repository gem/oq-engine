$(document).ready(function () {
    window.gem_example_completed = false;

    $(cf_obj['vol'].pfx + ' input[type="checkbox"][name="lahar"]').prop('checked', true).triggerHandler('click');
    $(cf_obj['vol'].pfx + ' input[type="checkbox"][name="ashfall"]').prop('checked', false).triggerHandler('click');

    $(cf_obj['vol'].pfx + ' div[name="lahar-input"] select[name="in-type"]').val('text-to-wkt').triggerHandler('change');


    setTimeout(function () {
        $(cf_obj['vol'].pfx + ' div[name="lahar-file-html"] select[name="file_html"]').val('lahar_file/lahar_LaharZ.asc');
        $(cf_obj['vol'].pfx + ' div[name="lahar-input"]  input[type="text"][name="epsg"]').val('26710');

        $(cf_obj['vol'].pfx + ' div[name="exposure-model-html"] select[name="file_html"]').val('exposure_model/exposure_model_vol_full.zip');

        // Click to download EventBase.zip
        setTimeout(function () {
            $(cf_obj['vol'].pfx + ' button[name="download"]').click();
            window.gem_example_completed = true;
        }, 1000);
    }, 1000);

    return;
});
