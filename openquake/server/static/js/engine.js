/*
 Copyright (C) 2015-2019 GEM Foundation

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU Affero General Public License as
 published by the Free Software Foundation, either version 3 of the
 License, or (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Affero General Public License for more details.

 You should have received a copy of the GNU Affero General Public License
 along with this program.  If not, see <https://www.gnu.org/licenses/agpl.html>.
 */

(function ($, Backbone, _) {
    /* classic event management */
    $(document).ready(
        function () {
            refresh_tag_selector();
            $('input#list_preferred_only').change(function() {
                set_calc_list_params();

            });
            $('select#tag_selector').change(function() {
                set_calc_list_params();
            });

            calculations.fetch({reset: true});
            setTimer();

            if (!disable_version_warning) {
                ajax = $.ajax({url: gem_oq_server_url + "/v1/engine_latest_version",
                              async: true}).done(function (data) {
                                  /* None is returned in case of an error,
                                      but we don't care about errors here */
                                  if(data && data != 'None') {
                                      $('#new-release-box').html(data).show()
                                  }
                              });
            }

            /* XXX. Reset the input file value to ensure the change event
               will be always triggered */
            $(document).on("click", 'input[name=archive]',
                           function (e) { this.value = null; });
            $(document).on("change", 'input[name=archive]',
                           function (e) {
                               dialog.show('Uploading calculation', true);
                               var input = $(e.target);
                               var form = input.parents('form')[0];

                               $(form).ajaxSubmit(
                                   {
                                    xhr: function () {  // custom xhr to add progress bar management
                                        var myXhr = $.ajaxSettings.xhr();
                                        if(myXhr.upload){ // if upload property exists
                                            myXhr.upload.addEventListener('progress', progressHandlingFunction, false);
                                        }
                                        return myXhr;
                                    },
                                    success: function (data) {
                                        calculations.add(new Calculation(data), {at: 0});
                                    },
                                    error: function (xhr) {
                                        dialog.hide();
                                        var s, out, data = $.parseJSON(xhr.responseText);
                                        var out = "";
                                        var ct = 0;
                                        for (s in data) {
                                            if (data[s] == "")
                                                continue;
                                            out += '<p ' + (ct % 2 == 1 ? 'style="background-color: #ffffff;"' : '') + '>' + data[s] + '</p>';
                                            ct++;
                                        }
                                        diaerror.show(false, "Calculation not accepted: traceback", out);
                                    }});
                           });

            $(document).on('hidden.bs.modal', 'div[id^=traceback-]',
                           function (e) {
                               setTimer();
                           });

            if (window.application_mode === 'AELO') {
                $.ajax({
                    url:  "/v1/aelo_site_classes",
                    method: "GET",
                    dataType: "json",
                    success: function(data) {
                        site_classes = data;
                        $('#asce_version').trigger('change');
                    },
                    error: function(xhr, status, error) {
                        console.error("Error loading site classes:", error);
                    }
                });
            }

            var vs30_original_placeholder = $('input#vs30').attr('placeholder');
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


            // IMPACT

            if (window.application_mode === 'IMPACT') {
                set_shakemap_version_selector();
                $.ajax({
                    url:  "/v1/get_impact_form_defaults",
                    method: "GET",
                    dataType: "json",
                    success: function(data) {
                        impact_form_defaults = data;
                    },
                    error: function(xhr, status, error) {
                        console.error("Error loading impact_from_defaults:", error);
                    }
                });
            }

            function toggleRunCalcBtnState() {
                var lonValue = $('#lon').val();
                if (typeof lonValue !== 'undefined') {
                    lonValue = lonValue.trim();
                }
                $('#submit_impact_calc').prop('disabled', lonValue === '');
            }
            toggleRunCalcBtnState();

            $('input[name="usgs_id"]').on('input', function() {
                reset_rupture_form_inputs();
                const selected_approach = get_selected_approach();
                if (approaches_requiring_shakemap_version.includes(selected_approach)) {
                    set_shakemap_version_selector();
                }
                if (selected_approach === 'build_rup_from_usgs') {
                    // retrieve nodal planes only when building rupture from USGS nodal plane solutions
                    var formData = {
                        usgs_id: $.trim($("#usgs_id").val()),
                    };
                    $('#submit_impact_get_rupture').prop('disabled', true);
                    $('input[name="impact_approach"]').prop('disabled', true);
                    set_retrieve_data_btn_txt('retrieving_nodal_planes');
                    $.ajax({
                        type: "POST",
                        url: gem_oq_server_url + "/v1/impact_get_nodal_planes_and_info",
                        data: formData,
                        dataType: "json",
                        encode: true,
                    }).done(function (data) {
                        if ('nodal_planes' in data && data.nodal_planes) {
                            populate_nodal_plane_selector(data.nodal_planes);
                            $('input#lon').val(data.info.lon);
                            $('input#lat').val(data.info.lat);
                            $('input#dep').val(data.info.dep);
                            $('input#mag').val(data.info.mag);
                        }
                        if ('nodal_planes_issue' in data && data.nodal_planes_issue) {
                            $nodal_plane = $('select#nodal_plane');
                            $nodal_plane.empty();
                            const $option = $('<option>').val('').text('Unable to retrieve nodal planes');
                            $nodal_plane.append($option);
                            diaerror.show(false, "Note", data.nodal_planes_issue);
                        }
                    }).error(function (data) {
                        diaerror.show(false, "Error", "Unable to retrieve nodal planes");
                    }).always(function (data) {
                        $('#submit_impact_get_rupture').prop('disabled', false);
                        $('input[name="impact_approach"]').prop('disabled', false);
                        set_retrieve_data_btn_txt('initial');
                    });
                }
            });

            $('input#no_uncertainty').on('change', function() {
                if ($(this).is(':checked')) {
                    $('#number_of_ground_motion_fields').val('1');
                    $('#truncation_level').val('0')
                } else {
                    $('#number_of_ground_motion_fields').val(
                        impact_form_defaults.number_of_ground_motion_fields);
                    $('#truncation_level').val(impact_form_defaults.truncation_level)
                }
            });

            $('input#number_of_ground_motion_fields').on('input', function() {
                if ($(this).val() != '1') {
                    $('input#no_uncertainty').prop('checked', false);
                }
            });

            $('input#truncation_level').on('input', function() {
                if ($(this).val() != '0') {
                    $('input#no_uncertainty').prop('checked', false);
                }
            });

            $('input[name="impact_approach"]').change(function () {
                const selected_approach = $(this).val();
                set_retrieve_data_btn_txt('initial');
                reset_impact_forms();
                if (approaches_requiring_usgs_id.includes(selected_approach)) {
                    $('.usgs_id_grp').removeClass('hidden');
                } else {
                    $('.usgs_id_grp').addClass('hidden');
                }
                if (['use_shakemap_fault_rup_from_usgs', 'use_finite_fault_model_from_usgs'].includes(selected_approach)) {
                    $('#rupture_from_usgs_grp').removeClass('hidden');
                } else {
                    $('#rupture_from_usgs_grp').addClass('hidden');
                }
                if (selected_approach == 'provide_rup') {
                    $('#upload_rupture_grp').removeClass('hidden');
                    $("#usgs_id").val('FromFile');
                } else {
                    $('#upload_rupture_grp').addClass('hidden');
                    $('#usgs_id').val('');
                }
                if (['provide_rup_params', 'build_rup_from_usgs'].includes(selected_approach)) {
                    $('#rup_params').removeClass('hidden');
                    $('div#msr').removeClass('hidden');
                    $('div#aspect_ratio').removeClass('hidden');
                    if (selected_approach == 'provide_rup_params') {
                        $('#usgs_id').val('UserProvided');
                    }
                } else {
                    $('#rup_params').addClass('hidden');
                    $('div#msr').addClass('hidden');
                    $('div#aspect_ratio').addClass('hidden');
                }
                if (selected_approach == 'build_rup_from_usgs') {
                    $('div#nodal_plane').removeClass('hidden');
                } else {
                    $('div#nodal_plane').addClass('hidden');
                }
                if (selected_approach == 'use_shakemap_from_usgs') {
                    $('div.hidden-for-shakemap').addClass('hidden');
                } else {
                    $('div.hidden-for-shakemap').removeClass('hidden');
                    if (!approaches_requiring_usgs_id.includes(selected_approach)) {
                        $('.usgs_id_grp').addClass('hidden');
                    }
                }
                if (approaches_requiring_shakemap_version.includes(selected_approach)) {
                    $('div#shakemap_version_grp').removeClass('hidden');
                } else {
                    $('div#shakemap_version_grp').addClass('hidden');
                }
            });

            $('select#nodal_plane').change(function () {
                const nodal_plane = $(this).find(':selected').data('details');
                $('#rake').val(nodal_plane.rake);
                $('#dip').val(nodal_plane.dip);
                $('#strike').val(nodal_plane.strike);
            });

            // NOTE: if not in impact mode, impact_run_form does not exist, so this can never be triggered
            $("#impact_get_rupture_form").submit(function (event) {
                $('#submit_impact_get_rupture').prop('disabled', true);
                $('input[name="impact_approach"]').prop('disabled', true);
                set_retrieve_data_btn_txt('running');
                var formData = new FormData();
                const selected_approach = get_selected_approach();
                formData.append('approach', selected_approach);
                formData.append('rupture_file', $('#rupture_file_input')[0].files[0]);
                const usgs_id = $.trim($("#usgs_id").val());
                if (require_usgs_id() || get_selected_approach() == 'provide_rup_params') {
                    // when providing rupture parameters, usgs_id is set to 'UserProvided'
                    formData.append('usgs_id', usgs_id);
                    if (approaches_requiring_shakemap_version.includes(selected_approach)) {
                        formData.append('shakemap_version', $("#shakemap_version").val());
                    }
                }
                formData.append('use_shakemap', use_shakemap());
                if (['provide_rup_params', 'build_rup_from_usgs'].includes(selected_approach)) {
                    // NOTE: for...of works like array.forEach(str => {
                    for (const param of ['lon', 'lat', 'dep', 'mag', 'rake', 'dip', 'strike', 'aspect_ratio']) {
                        var value = $('input#' + param).val();
                        if (selected_approach == 'provide_rup_params') {
                            formData.append(param, value);
                        }
                        else if (value != '') {
                            // 'build_rup_from_usgs' permits some params to be left blank by the user
                            // and to be populated from USGS data
                            formData.append(param, value);
                        }
                    }
                    formData.append('msr', $("select#msr").find(':selected').val());
                }
                $.ajax({
                    type: "POST",
                    url: gem_oq_server_url + "/v1/calc/impact_get_rupture_data",
                    data: formData,
                    processData: false,
                    contentType: false,
                    encode: true,
                }).done(function (data) {
                    // console.log(data);
                    $('.impact_time_grp').css('display', 'inline-block');
                    $('div.impact_time_grp').css('display', 'block');
                    $('#lon').val(data.lon);
                    toggleRunCalcBtnState();
                    $('#lat').val(data.lat);
                    $('#dep').val(data.dep);
                    $('#mag').val(data.mag);
                    $('#rake').val(data.rake);
                    $('#dip').val('dip' in data ? data.dip : '90');
                    $('#strike').val('strike' in data ? data.strike : '0');
                    $('#local_timestamp').val(data.local_timestamp);
                    $('#time_event').val(data.time_event);
                    // NOTE: due to security restrictions in web browsers, it is not possible to programmatically
                    //       set a specific file in an HTML file input element using JavaScript or jQuery,
                    //       therefore we can not pre-populate the rupture_file_input with the rupture_file
                    //       obtained converting the USGS rupture.json, and we use a separate field referencing it
                    $('#rupture_from_usgs').val(data.rupture_file);
                    $('#rupture_was_loaded').val(data.rupture_was_loaded ? 'Loaded' : 'N.A.');
                    var conversion_issues = '';
                    if ('rupture_issue' in data) {
                        conversion_issues += '<p>' + data.rupture_issue + '</p>';
                        $('#rupture_was_loaded').val('N.A. (conversion issue)');
                    }
                    if ('warning_msg' in data) {
                        conversion_issues += '<p>' + data.warning_msg + '</p>';
                    }
                    if (conversion_issues != '') {
                        diaerror.show(false, "Note", conversion_issues);
                    }
                    $('#mosaic_model').empty();
                    $.each(data.mosaic_models, function(index, mosaic_model) {
                        var selected = '';
                        if ('mosaic_model' in data && mosaic_model == data.mosaic_model) {
                            selected = ' selected';
                        }
                        var mosaic_model_trts = data.trts[mosaic_model];
                        $('#mosaic_model').append('<option value="' + mosaic_model + '" data-value=\'' + mosaic_model_trts + '\'' + selected + '>' + mosaic_model + '</option>');
                    });
                    populateTrtSelector(data.trt);
                    if (data.mmi_map_png) {
                        const imgElement = `<img src="data:image/jpeg;base64,${data.mmi_map_png}" alt="Intensity Map">`;
                        $('#intensity-map').html(imgElement);
                        $('shakemap-image-row').show();
                        $('#intensity-map').show();
                    }
                    else {
                        if (data.rupture_png) {
                            $('#intensity-map').hide();
                        }
                        else {
                            $('#intensity-map').html('<p>No intensity map available</p>');
                        }
                    }
                    if (data.pga_map_png) {
                        const imgElement = `<img src="data:image/jpeg;base64,${data.pga_map_png}" alt="PGA Map">`;
                        $('#pga-map').html(imgElement);
                        $('#shakemap-image-row').show();
                        $('#pga-map').show();
                    }
                    else {
                        if (data.rupture_png) {
                            $('#pga-map').hide();
                        }
                        else {
                            $('#pga-map').html('<p>No PGA map available</p>');
                        }
                    }
                    if (data.rupture_png) {
                        const imgElement = `<img src="data:image/jpeg;base64,${data.rupture_png}" alt="Rupture">`;
                        $('#rupture-map').html(imgElement);
                        $('#rupture-image-row').show();
                        $('#rupture-map').show();
                    }
                    else {
                        if (data.pga_map_png || data.mmi_map_png) {
                            $('#rupture-map').hide();
                        }
                        else {
                            $('#rupture-map').html('<p>No rupture image available</p>');
                        }
                    }
                    var desc = $('#usgs_id').val() + ': ';
                    if (data.title) {
                        desc += data.title;
                    }
                    else {
                        desc += 'M ' + data.mag + ' (' + data.lon + ', ' + data.lat + ')';
                    }
                    $('#description').val(desc);
                }).error(function (data) {
                    var resp = JSON.parse(data.responseText);
                    if ("invalid_inputs" in resp) {
                        for (var i = 0; i < resp.invalid_inputs.length; i++) {
                            var input_id = resp.invalid_inputs[i];
                            $("input#" + input_id).css("background-color", "#F2DEDE");
                        }
                    }
                    var err_msg = resp.error_msg;
                    diaerror.show(false, "Error", err_msg);
                    $('#intensity-map').hide();
                    $('#pga-map').hide();
                    // $('#rupture_png').hide();
                    $('#shakemap-image-row').hide();
                }).always(function (data) {
                    $('#submit_impact_get_rupture').prop('disabled', false);
                    $('input[name="impact_approach"]').prop('disabled', false);
                    set_retrieve_data_btn_txt('initial');
                });
                event.preventDefault();
            });

            $("#getStationDataFromUsgs").click(function () {
                $('#submit_impact_calc').prop('disabled', true);
                $('#getStationDataFromUsgs').text('Loading...');
                $('input[name="impact_approach"]').prop('disabled', true);
                $('#station_data_file_loaded').val('');
                var formData = new FormData();
                const usgs_id = $.trim($("#usgs_id").val());
                formData.append('usgs_id', usgs_id);
                formData.append('shakemap_version', $("#shakemap_version").val());
                $.ajax({
                    type: "POST",
                    url: gem_oq_server_url + "/v1/impact_get_stations_from_usgs",
                    data: formData,
                    processData: false,
                    contentType: false,
                    encode: true,
                }).done(function (data) {
                    // NOTE: these are stations downloaded from the USGS and not those uploaded by the user
                    $('#station_data_file_from_usgs').val(data.station_data_file);
                    if (data.station_data_issue) {
                        $('#station_data_file_loaded').val('N.A. (conversion issue)');
                        diaerror.show(false, "Note", '<p>' + data.station_data_issue + '</p>');
                    } else {
                        $('#station_data_file_loaded').val(data.station_data_file ? data.n_stations + ' stations were loaded' : 'N.A.');
                    }
                }).error(function (data) {
                    $('#station_data_file_loaded').val('');
                    var resp = JSON.parse(data.responseText);
                    var err_msg = resp.error_msg;
                    diaerror.show(false, "Error", err_msg);
                }).always(function (data) {
                    $('#submit_impact_calc').prop('disabled', false);
                    $('#getStationDataFromUsgs').text('Retrieve from the USGS');
                    $('input[name="impact_approach"]').prop('disabled', false);
                });
            });

            $('#mosaic_model').change(function() {
                populateTrtSelector();
            });
            $('#clearRuptureFile').click(function() {
                $('#rupture_file_input').val('');
            });
            $('#clearStationDataFile').click(function() {
                $('#station_data_file_input').val('');
            });
            $('#clearStationDataFromUsgs').click(function() {
                $('#station_data_file_from_usgs').val('');
                $('#station_data_file_loaded').val('');
                $('#station_data_file').val('');
            });
            $("#impact_run_form > input").click(function() {
                $(this).css("background-color", "white");
            });
            $("#impact_run_form").submit(function (event) {
                $('#submit_impact_calc').prop('disabled', true);
                $('#submit_impact_calc').text('Processing...');
                var formData = new FormData();
                const selected_approach = get_selected_approach();
                formData.append('approach', selected_approach);
                formData.append('rupture_from_usgs', $('#rupture_from_usgs').val());
                formData.append('rupture_was_loaded', $('#rupture_was_loaded').val() == 'Loaded');
                formData.append('rupture_file', $('#rupture_file_input')[0].files[0]);
                formData.append('usgs_id', $("#usgs_id").val());
                if (approaches_requiring_shakemap_version.includes(selected_approach)) {
                    formData.append('shakemap_version', $("#shakemap_version").val());
                }
                formData.append('use_shakemap', use_shakemap());
                formData.append('lon', $("#lon").val());
                formData.append('lat', $("#lat").val());
                formData.append('dep', $("#dep").val());
                formData.append('mag', $("#mag").val());
                formData.append('aspect_ratio', $("input#aspect_ratio").val());
                formData.append('rake', $("#rake").val());
                formData.append('dip', $("#dip").val());
                formData.append('strike', $("#strike").val());
                formData.append('time_event', $("#time_event").val());
                formData.append('maximum_distance', $("#maximum_distance").val());
                formData.append('mosaic_model', $('#mosaic_model').val());
                formData.append('trt', $('#trt').val());
                formData.append('truncation_level', $('#truncation_level').val());
                formData.append('number_of_ground_motion_fields',
                                $('#number_of_ground_motion_fields').val());
                formData.append('asset_hazard_distance', $('#asset_hazard_distance').val());
                formData.append('ses_seed', $('#ses_seed').val());
                formData.append('station_data_file_from_usgs', $('#station_data_file_from_usgs').val());
                formData.append('local_timestamp', $("#local_timestamp").val());
                formData.append('station_data_file', $('#station_data_file_input')[0].files[0]);
                formData.append('maximum_distance_stations', $("#maximum_distance_stations").val());
                const $msr_selector = $("select#msr");
                if ($msr_selector.length && $msr_selector.is(":has(option)")) {
                    formData.append('msr', $msr_selector.find(':selected').val());
                }
                formData.append('description', $('#description').val());
                $.ajax({
                    type: "POST",
                    url: gem_oq_server_url + "/v1/calc/impact_run",
                    data: formData,
                    processData: false,
                    contentType: false,
                    encode: true
                }).done(function (data) {
                    // console.log(data);
                }).error(function (data) {
                    var resp = JSON.parse(data.responseText);
                    if ("invalid_inputs" in resp) {
                        for (var i = 0; i < resp.invalid_inputs.length; i++) {
                            var input_id = resp.invalid_inputs[i];
                            $("input#" + input_id).css("background-color", "#F2DEDE");
                        }
                    }
                    var err_msg = resp.error_msg;
                    diaerror.show(false, "Error", err_msg);
                }).always(function () {
                    $('#submit_impact_calc').prop('disabled', false);
                    $('#submit_impact_calc').text('Launch impact calculation');
                });
                event.preventDefault();
            });
            $("#impact_run_form > input").click(function() {
                $(this).css("background-color", "white");
            });
        });
})($, Backbone, _, gem_oq_server_url);
