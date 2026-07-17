$(document).ready(function () {
    window.gem_example_completed = false;
    // this is a workaround for a bug fixed in jquery 1.9 (checked is toggled after that handler is fired
/*
    $(cf_obj['vol'].pfx + " div[name='vm-structural-new'] input[name='file_upload']").submit();
    $(cf_obj['vol'].pfx + " div[name='source-model-logic-tree-file-new'] input[name='file_upload']").submit();
    $(cf_obj['vol'].pfx + " div[name='source-model-file-new'] input[name='file_upload']").submit();
    $(cf_obj['vol'].pfx + " div[name='gsim-logic-tree-file-new'] input[name='file_upload']").submit();
    $(cf_obj['vol'].pfx + " div[name='vm-structural-new'] input[name='file_upload']").submit();

    $(cf_obj['vol'].pfx + " div[name='ashfall-file-new'] input[name='file_upload']").submit();
*/

    $(cf_obj['vol'].pfx + ' textarea#description').val('');

    $(cf_obj['vol'].pfx + ' input[type="checkbox"][name="ashfall"]').prop('checked', true).triggerHandler('click');
    $(cf_obj['vol'].pfx + ' input[type="checkbox"][name="lavaflow"]').prop('checked', true).triggerHandler('click');
    $(cf_obj['vol'].pfx + ' input[type="checkbox"][name="lahar"]').prop('checked', true).triggerHandler('click');
    $(cf_obj['vol'].pfx + ' input[type="checkbox"][name="pyroclasticflow"]').prop('checked', true).triggerHandler('click');


    $(cf_obj['vol'].pfx + ' div[name="ashfall-input"] select[name="in-type"]').val('shape').triggerHandler('change');
    $(cf_obj['vol'].pfx + ' div[name="lavaflow-input"] select[name="in-type"]').val('shape-to-wkt').triggerHandler('change');
    $(cf_obj['vol'].pfx + ' div[name="lahar-input"] select[name="in-type"]').val('shape-to-wkt').triggerHandler('change');
    $(cf_obj['vol'].pfx + ' div[name="pyroclasticflow-input"] select[name="in-type"]').val('shape-to-wkt').triggerHandler('change');


    setTimeout(function () {
        $(cf_obj['vol'].pfx + ' div[name="ashfall-file-html"] select[name="file_html"]').val('');
        $(cf_obj['vol'].pfx + ' input[type="text"][name="wet-ampl"]').val('');
        $(cf_obj['vol'].pfx + ' input[type="text"][name="discr-dist"]').val('');
        $(cf_obj['vol'].pfx + ' div[name="lavaflow-file-html"] select[name="file_html"]').val('');
        $(cf_obj['vol'].pfx + ' div[name="lahar-file-html"] select[name="file_html"]').val('');
        $(cf_obj['vol'].pfx + ' div[name="pyroclasticflow-file-html"] select[name="file_html"]').val('');

        $(cf_obj['vol'].pfx + ' div[name="exposure-model-html"] select[name="file_html"]').val('');

        $(cf_obj['vol'].pfx + ' div[name="fm-ashfall-file-html"] select[name="file_html"]').val('');

        $(cf_obj['vol'].pfx + ' div[name="exposure-model"] input[type="text"][name="asset_hazard_distance"]').val('');

        $(cf_obj['vol'].pfx + ' input[type="checkbox"][name="is-cons-models"]').prop('checked', true).triggerHandler('click');
        $(cf_obj['vol'].pfx + ' div[name="fm-ashfall-cons-html"] select[name="file_html"]').val('');

        // Click to download EventBase.zip
        setTimeout(function () {
            $(cf_obj['vol'].pfx + ' button[name="download"]').click();
            window.gem_example_completed = true;
        }, 1000);
    }, 1000);

    return;
});
