function populateTrtSelector(selected_trt) {
    $('#trt').empty();
    var trts = $('#mosaic_model').find(':selected').data('value').split(',');
    $.each(trts, function(index, trt) {
        var selected = '';
        if (selected_trt && trt == selected_trt) {
            selected = ' selected';
        }
        $('#trt').append('<option value="' + trt + '"' + selected + '>' + trt + '</option>');
    });
}

function use_shakemap() {
    const approach_selector = $('input[name="impact_approach"]');
    if (approach_selector.length > 0) {
        return $('input[name="impact_approach"]:checked').val() === 'use_shakemap_from_usgs';
    } else {
        // in interface level 1 the approach selector doesn't exist and we always use the ShakeMap
        return true;
    }
}

const approaches_requiring_usgs_id = [
    'use_shakemap_from_usgs',
    'use_pnt_rup_from_usgs',
    'build_rup_from_usgs',
    'use_shakemap_fault_rup_from_usgs',
    'use_finite_fault_model_from_usgs'
];

// The ShakeMap version is needed to download stations accordingly
const approaches_requiring_shakemap_version = approaches_requiring_usgs_id

const retrieve_data_btn_txt_map = {
    'use_shakemap_from_usgs': {
        'initial': 'Retrieve ShakeMap data',
        'running': 'Retrieving ShakemapData (it may take more than 10 seconds)...'},
    'use_pnt_rup_from_usgs': {
        'initial': 'Retrieve rupture data',
        'running': 'Retrieving rupture data...'},
    'build_rup_from_usgs': {
        'initial': 'Build rupture',
        'running': 'Building rupture...',
        'retrieving_nodal_planes': 'Retrieving nodal planes...'},
    'use_shakemap_fault_rup_from_usgs': {
        'initial': 'Retrieve ShakeMap fault rupture',
        'running': 'Retrieving ShakeMap fault rupture...'},
    'use_finite_fault_model_from_usgs': {
        'initial': 'Retrieve finite fault model',
        'running': 'Retrieving finite fault model...'},
    'provide_rup': {
        'initial': 'Retrieve rupture data',
        'running': 'Retrieving rupture data...'},
    'provide_rup_params': {
        'initial': 'Build rupture',
        'running': 'Building rupture...'}
}

var impact_form_defaults = {};

function require_usgs_id() {
    const approach_selector = $('input[name="impact_approach"]');
    if (approach_selector.length > 0) {
        const selected_approach = get_selected_approach();
        if (selected_approach == 'provide_rup') {
            // usgs_id is expected to be 'FromFile'
            return true;
        }
        return approaches_requiring_usgs_id.includes(selected_approach);
    } else {
        // in interface level 1 the approach selector doesn't exist and we always use the ShakeMap
        return true;
    }
}

function get_selected_approach() {
    const approach_selector = $('input[name="impact_approach"]');
    var selected_approach;
    if (approach_selector.length > 0) {
        selected_approach = $('input[name="impact_approach"]:checked').val();
    }
    else {
        selected_approach = 'use_shakemap_from_usgs';
    }
    return selected_approach;
}

function set_retrieve_data_btn_txt(state) { // state can be 'initial', 'running', 'retrieving_nodal_planes'
    const approach = get_selected_approach();
    const btn_txt = retrieve_data_btn_txt_map[approach][state];
    $('#submit_impact_get_rupture').text(btn_txt);
}

function reset_rupture_form_inputs() {
    var rupture_form_fields = [
        'lon', 'lat', 'dep', 'mag', 'aspect_ratio', 'rake', 'dip', 'strike']
    for (field of rupture_form_fields) {
        $('input#' + field).val(impact_form_defaults[field]);
    }
    $('input#rupture_was_loaded').val('');
    // nodal planes are re-populated when loading rupture data; msrs are populated only once
    $('select#nodal_plane').empty();
    $('select#msr').val('WC1994');
    $('#rupture-map').hide();
}

function set_shakemap_version_selector() {
    $('#submit_impact_get_rupture').prop('disabled', true);
    $('#submit_impact_get_rupture').text('Retrieving ShakeMap versions...');
    $('input[name="impact_approach"]').prop('disabled', true);
    var formData = new FormData();
    const usgs_id = $.trim($("#usgs_id").val());
    formData.append('usgs_id', usgs_id);
    $.ajax({
        type: "POST",
        url: gem_oq_server_url + "/v1/impact_get_shakemap_versions",
        data: formData,
        processData: false,
        contentType: false,
        encode: true,
    }).done(function (data) {
        let $select = $("#shakemap_version");
        $select.empty();
        if (data.shakemap_versions_issue) {
            $select.append(`<option value="error">${data.shakemap_versions_issue}</option>`);
        } else {
            if (data.shakemap_versions.length > 0) {
                data.shakemap_versions.forEach(function (shakemap_version) {
                    var usgs_preferred = shakemap_version.id == data.usgs_preferred_version ? " (USGS preferred)" : "";
                    $select.append(`<option value="${shakemap_version.id}">v${shakemap_version.number}: ${shakemap_version.utc_date_time}${usgs_preferred}</option>`);
                });
            } else {
                $select.append('<option value="">No versions available</option>');
            }
        }
        $('#submit_impact_get_rupture').prop('disabled', false);
        set_retrieve_data_btn_txt('initial');
    }).error(function (data) {
        let $select = $("#shakemap_version");
        $select.empty();
        $select.append('<option value="error">Unable to retrieve data</option>');
        var resp = JSON.parse(data.responseText);
        var err_msg = resp.error_msg;
        diaerror.show(false, "Error", err_msg);
    }).always(function (data) {
        $('input[name="impact_approach"]').prop('disabled', false);
        set_retrieve_data_btn_txt('initial');
    });
}

function reset_impact_forms() {
    for (field in impact_form_defaults) {
        var input = $('input#' + field);
        if (input.length) {
            input.val(impact_form_defaults[field]);
        }
    }
    const selectors = ['#shakemap_version', '#mosaic_model', '#trt'];
    for (select_id of selectors) {
        let $select = $(select_id);
        $select.empty();
    }
    $('#time_event').val(impact_form_defaults['time_event']);
    $('#no_uncertainty').prop('checked', false);
    $('#rupture-map').hide();
    $('#shakemap-image-row').hide();
}

function populate_nodal_plane_selector(nodal_planes) {
    const $select = $('select#nodal_plane');
    $select.empty();
    $.each(nodal_planes, function(key, values) {
        const optionText = `${key} (Dip: ${values.dip}, Rake: ${values.rake}, Strike: ${values.strike})`;
        const $option = $('<option>')
            .val(key) // Use the key as the value
            .text(optionText) // Display the formatted text
            .data('details', values); // Attach the object as data
        $select.append($option);
    });
    const nodal_plane = $select.find(':selected').data('details');
    $('#rake').val(nodal_plane.rake);
    $('#dip').val(nodal_plane.dip);
    $('#strike').val(nodal_plane.strike);
}
