var site_classes = {}  // populated via a ajax call to the web API
// NOTE: avoiding to call it DEFAULT_SITE_CLASS to avoid confusion with the 'default' one
const PRESELECTED_SITE_CLASS = 'BC';

var vs30_original_placeholder;
$('select#site_class').on('change', function() {
    const site_class = $(this).val();
    const $input_vs30 = $('input#vs30');
    const asce_version = $("#asce_version").val();
    if (site_class === 'custom') {
        $input_vs30.prop('disabled', false);
        $input_vs30.val('');
        $input_vs30.attr('placeholder', vs30_original_placeholder);
    } else {
        $input_vs30.prop('disabled', true);
        if (site_class === 'default') {
            $input_vs30.val('');
            $input_vs30.attr('placeholder', '');
        } else {
            $input_vs30.val(site_classes[asce_version][site_class]['vs30']);
            $input_vs30.attr('placeholder', vs30_original_placeholder);
            check_vs30_below_200();
        }
    }
});

$('#asce_version').on('change', function() {
    const asce_version = $(this).val();
    const $site_class_select = $('select#site_class');
    const $input_vs30 = $('input#vs30');
    $site_class_select.empty();
    if (asce_version === 'ASCE7-16') {
        $site_class_select.append($('<option>', {
            value: PRESELECTED_SITE_CLASS,
            text: site_classes[asce_version][PRESELECTED_SITE_CLASS]['display_name']}));
        $input_vs30.val(site_classes[asce_version][PRESELECTED_SITE_CLASS]['vs30']);
    } else if (asce_version === 'ASCE7-22') {
        for (const site_class of Object.keys(site_classes[asce_version])) {
            $site_class_select.append(
                $("<option>", {
                    value: site_class,
                    text: site_classes[asce_version][site_class]['display_name'],
                    selected: site_class === PRESELECTED_SITE_CLASS
                })
            );
        }
    }
    const site_class = $site_class_select.val();
    if (site_class === 'custom') {
        $input_vs30.prop('disabled', false);
        $input_vs30.val('');
    } else {
        $input_vs30.prop('disabled', true);
        if (site_class === 'default') {
            $input_vs30.val('');
        } else {
            const site_class = $site_class_select.val();
            $input_vs30.val(site_classes[asce_version][site_class]['vs30']);
            check_vs30_below_200();
        }
    }
});

const vs30_below_200_warning = `
The Vs30 is less than 200 m/s. Some ground motion models are poorly
constrained at this Vs30. In accordance with an ASCE 7-22
supplement currently being proposed, it is recommended that the
ground-motion spectra from this very low Vs30 be floored by those
for Site Class D. In lieu of this conservative flooring, a
site-specific hazard and site response could be warranted.`;
function check_vs30_below_200() {
    let value = parseFloat($("input#vs30").val());
    if (value >= 200 || isNaN(value)) {
        return;
    }
    showNotificationModal("WARNING", vs30_below_200_warning);
}

let typingTimer = null;
const DONE_TYPING_DELAY = 600;  // ms
$("input#vs30").on("input", function () {
    clearTimeout(typingTimer);
    // Start a new timer; validation happens only after user stops typing
    typingTimer = setTimeout(check_vs30_below_200, DONE_TYPING_DELAY);
});

// NOTE: if not in aelo mode, aelo_run_form does not exist, so this can never be triggered
$("#aelo_run_form").submit(function (event) {
    $('#submit_aelo_calc').prop('disabled', true);
    const site_class = $('select#site_class').val();
    const asce_version = $("#asce_version").val();
    var vs30;
    if (site_class === 'custom') {
        vs30 = $("input#vs30").val();
    } else {
        vs30 = site_classes[asce_version][site_class]['vs30'];
        if (Array.isArray(vs30)) { // the default site class has 3 Vs30 values
            vs30 = vs30.join(' ');
        } else {
            vs30 = vs30.toString();
        }
    }
    var formData = {
        lon: $("#lon").val(),
        lat: $("#lat").val(),
        siteid: $("#siteid").val(),
        asce_version: asce_version,
        site_class: site_class,
        vs30: vs30
    };
    $.ajax({
        type: "POST",
        url: gem_oq_server_url + "/v1/calc/aelo_run",
        data: formData,
        dataType: "json",
        encode: true,
    }).done(function (data) {
        // console.log(data);
    }).error(function (data) {
        var resp = JSON.parse(data.responseText);
        if ("invalid_inputs" in resp) {
            for (var i = 0; i < resp.invalid_inputs.length; i++) {
                var input_id = resp.invalid_inputs[i];
                $("#aelo_run_form > input#" + input_id).css("background-color", "#F2DEDE");
            }
        }
        var err_msg = resp.error_msg;
        diaerror.show(false, "Error", err_msg);
    }).always(function () {
        $('#submit_aelo_calc').prop('disabled', false);
    });
    event.preventDefault();
});

$("#aelo_run_form > input").click(function() {
    $(this).css("background-color", "white");
});


