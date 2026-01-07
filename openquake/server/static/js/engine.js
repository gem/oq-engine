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
                vs30_original_placeholder = $('input#vs30').attr('placeholder');
            } else if (window.application_mode === 'IMPACT') {
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
                function toggleRunCalcBtnState() {
                    var lonValue = $('#lon').val();
                    if (typeof lonValue !== 'undefined') {
                        lonValue = lonValue.trim();
                    }
                    $('#submit_impact_calc').prop('disabled', lonValue === '');
                }
                toggleRunCalcBtnState();
            }
        });
})($, Backbone, _, gem_oq_server_url);
