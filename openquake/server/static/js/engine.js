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

function capitalizeFirstLetter(val) {
    return String(val).charAt(0).toUpperCase() + String(val).slice(1);
}

(function ($, Backbone, _) {
    var calculation_table;

    var progressHandlingFunction = function (progress) {
        var percent = progress.loaded / progress.total * 100;
        $('.bar').css('width', percent + '%');
        if (percent == 100) {
            dialog.hide();
        }
    };

    var htmlEscape = function (record) {
        // record[3] is the log message
        record[3] = record[3].replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        return record
    };

    var dialog = (function ()
                  {
                      var pleaseWaitDiv = $('<div class="modal hide" id="pleaseWaitDialog" data-backdrop="static" data-keyboard="false"><div class="modal-header"><h1>Processing...</h1></div><div class="modal-body"><div class="progress progress-striped active"><div class="bar" style="width: 0%;"></div></div></div></div>');
                      return {
                          show: function (msg, progress) {
                              $('h1', pleaseWaitDiv).text(msg);
                              if (progress) {
                                  progressHandlingFunction({loaded: 0, total: 1});
                              } else {
                                  progressHandlingFunction({loaded: 1, total: 1});
                              }
                              pleaseWaitDiv.modal('show');
                          },
                          hide: function () {
                              pleaseWaitDiv.modal('hide');
                          }
                      };
                  })();

    var diaerror = (function ()
                  {
                      var errorDiv = $('<div id="errorDialog" class="modal hide" data-keyboard="true" tabindex="-1">\
                <div class="modal-dialog">\
                  <div class="modal-content">\
                    <div class="modal-header">\
                      <h4 class="modal-title">Calculation not accepted: traceback</h4>\
                    </div>\
                    <div class="modal-body" style="font-size: 12px;"><pre style="font-size: 12px;" class="modal-body-pre"></pre>\
                    </div>\
                    <div class="modal-footer">\
                      <span id="diaerror_scroll_enabled_box" style="display: none;"><input type="checkbox" id="diaerror_scroll_enabled" checked>\
                      Auto Scroll</span>&nbsp;&nbsp;&nbsp;\
                      <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>\
                    </div>\
                  </div>\
                </div>\
</div>');
                      errorDiv.bind('hide', function () { calculation_table.hide_log(); });
                      return {
                          getdiv: function () {
                              return errorDiv;
                          },

                          show: function (is_large, title, msg) {
                              if (title != null) {
                                  $('.modal-title', errorDiv).html(title);
                              }
                              if (msg != null) {
                                  $('.modal-body-pre', errorDiv).html(msg);
                              }
                              if (is_large) {
                                  errorDiv.addClass("errorDialogLarge");
                              }
                              else {
                                  errorDiv.removeClass("errorDialogLarge");
                              }
                              errorDiv.modal('show');
                          },

                          append: function (title, msg) {
                              if (title != null) {
                                  $('.modal-title', errorDiv).html(title);
                              }
                              $( msg ).appendTo( $('.modal-body-pre', errorDiv) );
                          },

                          scroll_to_bottom: function (ctx) {
                              ctx.scrollTop(ctx[0].scrollHeight);
                          },

                          hide: function () {
                              errorDiv.modal('hide');
                          }
                      };
                  })();

    var CalculationTable = Backbone.View.extend(
        {
            /* the html element where the table is rendered */
            el: $('#my-calculations'),

            logXhr: null,
            logId: -1,
            logIsNew: false,
            logLinesAll: 0,
            logLines: 0,
            logTimeout: null,

            initialize: function (options) {

                /* whatever happens to any calculation, re-render the table */
                _.bindAll(this, 'render');
                this.calculations = options.calculations;
                this.calculations.bind('reset', this.render);
                this.calculations.bind('add', this.render);
                this.calculations.bind('remove', this.render);

                /* if false, it prevents the table to be refreshed */
                this.can_be_rendered = true;

                this.render();
            },

            events: {
                "click .btn-abort": "confirm_abort_calculation",
                "click .btn-share": "confirm_share_calculation",
                "click .btn-unshare": "confirm_unshare_calculation",
                "click .btn-remove": "confirm_remove_calculation",
                "click .btn-traceback": "show_traceback",
                "click .btn-log": "show_log",
                "click .btn-file": "on_run_risk_clicked",
                "change .btn-file input": "on_run_risk_queued"
            },

            /* When an input dialog is opened, it is very important to not re-render the table */
            on_run_risk_clicked: function (e) {
                /* if a file input dialog has been opened do not refresh the calc table */
                this.can_be_rendered = false;
            },

            on_run_risk_queued: function (e) {
                this.can_be_rendered = true;
            },

            confirm_share_calculation: function(e) {
                this.confirm_modify_calculation(e, 'share');
            },

            confirm_unshare_calculation: function(e) {
                this.confirm_modify_calculation(e, 'unshare');
            },

            confirm_remove_calculation: function(e) {
                this.confirm_modify_calculation(e, 'remove');
            },

            confirm_abort_calculation: function(e) {
                this.confirm_modify_calculation(e, 'abort');
            },

            confirm_modify_calculation: function(e, action) {
              e.preventDefault();
              const calc_id = $(e.target).attr('data-calc-id');
              const calc_desc = $(e.target).attr('data-calc-desc');
              showModal({
                calc_id,
                title: capitalizeFirstLetter(action) + ' calculation',
                body: `Are you sure you want to ${action} calculation ${calc_id}?<br><em>"${calc_desc}"</em>`,
                confirmText: `Yes, ${action}`,
                cancelText: 'No',
                confirmAction: () => this.modify_calculation(e, action),
              });
            },

            modify_calculation: function(e, action) {  // e.g. remove, share or abort
                const action_ing = action.endsWith("e") ? action.slice(0, -1) + "ing" : action + "ing";
                const action_ed = action.endsWith("e") ? action + "d" : action + "ed";
                e.preventDefault();
                var calc_id = $(e.target).attr('data-calc-id');
                var calc_desc = $(e.target).attr('data-calc-desc');
                var view = this;
                diaerror.show(false, capitalizeFirstLetter(action_ing) + " calculation " + calc_id, "...");

                var hide_or_back = (function (e) {
                    this.conf_hide = $('#confirmDialog' + calc_id).hide();
                    this.back_conf_hide = $('.back_confirmDialog' + calc_id).hide();
                    setTimer();
                })();

                var myXhr = $.ajax({url: gem_oq_server_url + "/v1/calc/" + calc_id + "/" + action,
                                    type: "POST",
                                    error: function (jqXHR, textStatus, errorThrown) {
                                        if (jqXHR.status == 403) {
                                            diaerror.show(false, "Error", JSON.parse(jqXHR.responseText).error);
                                        }
                                    },
                                    success: function (data, textStatus, jqXHR) {
                                        if(data.error) {
                                            diaerror.show(false, "Error", data.error);
                                        } else {
                                            diaerror.show(false, "Calculation " + action_ed, 'Calculation ' + calc_id + ' "' + calc_desc + '"</b> has been ' + action_ed);
                                            if (action == 'abort') {
                                                view.calculations.remove([view.calculations.get(calc_id)]);
                                            }
                                            calculations.fetch({reset: true});
                                        }
                                    }});
            },

            show_traceback: function (e) {
                e.preventDefault();
                var calc_id = $(e.target).attr('data-calc-id');
                var myXhr = $.ajax({url: gem_oq_server_url + "/v1/calc/" + calc_id + "/traceback",
                                    error: function (jqXHR, textStatus, errorThrown) {
                                        if (jqXHR.status == 404) {
                                            diaerror.show(false, "Calculation " + calc_id + " not found.");
                                        }
                                        else {
                                            diaerror.show(false, "Error retrieving traceback for calculation " + calc_id, textStatus);
                                        }
                                        // alert("Error: " + textStatus);
                                    },
                                    success: function (data, textStatus, jqXHR) {
                                        if (data.length == 0) {
                                            diaerror.show(true, "Traceback not found for calculation " + calc_id, []);
                                        }
                                        else {
                                            var out = "";
                                            var ct = 0;
                                            for (s in data) {
                                                if (data[s] == "")
                                                    continue;
                                                out += '<p ' + (ct % 2 == 1 ? 'style="background-color: #ffffff;"' : '') + '>' + data[s] + '</p>';
                                                ct++;
                                            }
                                            diaerror.show(true, "Traceback of calculation " + calc_id, out);
                                        }
                                        // alert("Success: " + textStatus);
                                    }});
            },

            _show_log_priv: function (is_new, calc_id, is_running, from) {
                var was_running = is_running;

                // TO CHECK hide_log method enable console.log and take a look
                // console.log("_show_log_priv: begin");
                if (this.logXhr != null) {
                    this.logXhr.abort();
                    this.logXhr = null;
                }
                if (is_new) {
                    if (this.logTimeout != null) {
                        window.clearTimeout(this.logTimeout);
                        this.logTimeout = null;
                    }
                }
                var obj = this;

                this.logXhr = $.ajax({url: gem_oq_server_url + "/v1/calc/" + calc_id + "/log/" + from + ":",
                                      error: function (jqXHR, textStatus, errorThrown) {
                                          if (jqXHR.status == 404) {
                                              diaerror.show(true, "Log of calculation " + calc_id + " not found.");
                                          }
                                          else {
                                              diaerror.show(true, "Error retrieving log for calculation " + calc_id, textStatus);
                                          }
                                          obj.logIsNew = false;
                                      },
                                      success: function (data, textStatus, jqXHR) {
                                          var delay = 250;

                                          if (is_new) {
                                              obj.logLines = 0;
                                              obj.logLinesAll = 0;
                                          }
                                          else {
                                              // if data is empty check if job is still running
                                              if (is_running) {
                                                  if (data.length == 0) {
                                                      var ajax, status;

                                                      delay = 1000;

                                                      ajax = $.ajax({url: gem_oq_server_url + "/v1/calc/" + calc_id + "/status",
                                                                     async: false}).done(function (data) { status = data.is_running; });
                                                      if (status !== true) {
                                                          is_running = false;
                                                      }
                                                  }
                                              }
                                          }
                                          var out = "";

                                          for (s in data) {
                                              if (data[s] == "") {
                                                  obj.logLinesAll++;
                                                  continue;
                                              }
                                              out += '<p ' + (obj.logLines % 2 == 1 ? 'style="background-color: #ffffff;"' : '') + '>' + htmlEscape(data[s]) + '</p>';
                                              obj.logLines++;
                                              obj.logLinesAll++;
                                          }

                                          var title;
                                          if (is_running) {
                                              var dt;
                                              dt = new Date();
                                              title = "Log of calculation " + calc_id + " - " + dt.toString();
                                          }
                                          else if (was_running != is_running) {
                                              title = "Log of calculation " + calc_id + " - finished";
                                          }
                                          else {
                                              title = "Log of calculation " + calc_id;
                                          }

                                          if (obj.logIsNew) {
                                              diaerror.show(true, title, out);
                                          }
                                          else {
                                              diaerror.append(title, out);
                                          }
                                          if ($("#diaerror_scroll_enabled").prop( "checked" ) || was_running == false) {
                                              diaerror.scroll_to_bottom($('.modal-body', diaerror.getdiv()));
                                          }

                                          if (is_running) {
                                              function log_update(obj)
                                              {
                                                  obj._show_log_priv(false, obj.logId, true, obj.logLinesAll);
                                              }

                                              obj.logTimeout = window.setTimeout(log_update, delay, obj);
                                          }
                                          else {
                                              $('#diaerror_scroll_enabled_box').hide();
                                          }

                                          obj.logIsNew = false;
                                      }});
            },

            show_log: function (e) {
                e.preventDefault();
                var calc_id = $(e.target).attr('data-calc-id');
                var is_running = ($(e.target).attr('is-running') == "true");

                this.logId = calc_id;
                this.logIsNew = true;

                if (is_running)
                    $('#diaerror_scroll_enabled_box', diaerror.getdiv()).show();
                else
                    $('#diaerror_scroll_enabled_box', diaerror.getdiv()).hide();

                this._show_log_priv(true, calc_id, is_running, "0");
            },

            hide_log: function (e) {
                if (this.logTimeout != null) {
                    window.clearTimeout(this.logTimeout);
                    this.logTimeout = null;
                }
                if (this.logXhr != null) {
                    this.logXhr.abort();
                    this.logXhr = null;
                }
                $('#diaerror_scroll_enabled_box').hide();
            },

            render: function () {
                if (!this.can_be_rendered) {
                    return;
                };
                this.$el.html(_.template($('#calculation-table-template').html(),
                                         { calculations: this.calculations.models }));
            }
        });

    var Calculation = Backbone.Model.extend({
        defaults: {
            map: null,
            layers: []
        }
    });

    var Calculations = Backbone.Collection.extend(
        {
            model: Calculation,
            url: gem_oq_server_url + "/v1/calc/list"
        });
    var calculations = new Calculations();

    var refresh_calcs;

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

    function setTimer() {
        refresh_calcs = setInterval(function () { calculations.fetch({reset: true}) }, 3000);
    }

    function closeTimer() {
        refresh_calcs = clearInterval(refresh_calcs);
    }

    function use_shakemap() {
        approach_selector = $('input[name="impact_approach"]');
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

    var site_classes = {}  // populated via a ajax call to the web API
    // NOTE: avoiding to call it DEFAULT_SITE_CLASS to avoid confusion with the 'default' one
    const PRESELECTED_SITE_CLASS = 'BC';

    var impact_form_defaults = {};

    function require_usgs_id() {
        approach_selector = $('input[name="impact_approach"]');
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
        approach_selector = $('input[name="impact_approach"]');
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

    /* classic event management */
    $(document).ready(
        function () {
            calculation_table = new CalculationTable({ calculations: calculations });
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
                        $input_vs30.val(site_classes[site_class]['vs30']);
                        $input_vs30.attr('placeholder', vs30_original_placeholder);
                    }
                }
            });

            $('#asce_version').on('change', function() {
                const asce_version = $(this).val();
                const $site_class_select = $('select#site_class');
                const $input_vs30 = $('input#vs30');
                $site_class_select.empty();
                if (asce_version === 'ASCE7-16') {
                    $site_class_select.append($('<option>', {value: PRESELECTED_SITE_CLASS, text: PRESELECTED_SITE_CLASS}));
                    $input_vs30.val(site_classes[PRESELECTED_SITE_CLASS]['vs30']);
                } else if (asce_version === 'ASCE7-22') {
                    for (const site_class of Object.keys(site_classes)) {
                        $site_class_select.append(
                            $("<option>", {
                                value: site_class,
                                text: site_classes[site_class]['display_name'],
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
                        $input_vs30.val(site_classes[site_class]['vs30']);
                    }
                }
            });

            // NOTE: if not in aelo mode, aelo_run_form does not exist, so this can never be triggered
            $("#aelo_run_form").submit(function (event) {
                $('#submit_aelo_calc').prop('disabled', true);
                var site_class = $('select#site_class').val();
                var vs30;
                if (site_class === 'custom') {
                    vs30 = $("input#vs30").val();
                } else {
                    vs30 = site_classes[site_class]['vs30'];
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
                    asce_version: $("#asce_version").val(),
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

            if (window.application_mode === 'ARISTOTLE') {
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


function showModal({ id, title, body, confirmText = 'Yes', cancelText = 'No', confirmAction }) {
  const modal = document.querySelector('#confirmModal');
  modal.querySelector('.modal-title').innerHTML = title;
  modal.querySelector('.modal-body-pre').innerHTML = body;
  modal.querySelector('.btn-confirm').textContent = confirmText;
  modal.querySelector('.btn-cancel').textContent = cancelText;

  // Attach confirmation action
  const confirmButton = modal.querySelector('.btn-confirm');
  confirmButton.onclick = () => {
    if (typeof confirmAction === 'function') {
      confirmAction();
    }
    closeModal();
  };

  // Show the modal
  modal.classList.remove('hide');
  modal.classList.add('in');
}

function closeModal() {
  const modal = document.querySelector('#confirmModal');
  modal.classList.remove('in');
  modal.classList.add('hide');
}
