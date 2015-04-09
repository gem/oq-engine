/*
 Copyright (c) 2015, GEM Foundation.

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

(function($, Backbone, _) {
    var progressHandlingFunction = function(progress) {
        var percent = progress.loaded / progress.total * 100;
        $('.bar').css('width', percent + '%');
        if (percent == 100) {
            dialog.hidePleaseWait();
        }
    };

    var dialog = (function ()
                  {
                      var pleaseWaitDiv = $('<div class="modal hide" id="pleaseWaitDialog" data-backdrop="static" data-keyboard="false"><div class="modal-header"><h1>Processing...</h1></div><div class="modal-body"><div class="progress progress-striped active"><div class="bar" style="width: 0%;"></div></div></div></div>');
                      return {
                          showPleaseWait: function(msg, progress) {
                          $('h1', pleaseWaitDiv).text(msg);
                          if (progress) {
                          progressHandlingFunction({loaded: 0, total: 1});
                          } else {
                          progressHandlingFunction({loaded: 1, total: 1});
                      }
                              pleaseWaitDiv.modal();
                          },
                          hidePleaseWait: function () {
                              pleaseWaitDiv.modal('hide');
                          }
                      };
                  })();

    var diaerror = (function ()
                  {
                      var errorDiv = $('<div class="modal fade" style="display: none;" data-keyboard="true" tabindex="-1">\
                <div class="modal-dialog">\
                  <div class="modal-content">\
                    <div class="modal-header">\
                      <h4 class="modal-title">Calculation not accepted: traceback</h4>\
                    </div>\
                    <div class="modal-body" style="font-size: 12px;"><pre style="font-size: 12px;" class="modal-body-pre"></pre>\
                    </div>\
                    <div class="modal-footer">\
                      <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>\
                    </div>\
                  </div>\
                </div>\
</div>');

// <div class="modal hide"  id="errorDialog" data-backdrop="static" data-keyboard="true"><div class="modal-header"><h1>Error</h1></div><div class="modal-body" style="font-size: 12px;"></div><span class="btn btn-default">Close</span></div>');
//                      errorDiv.on("click", function(e) {
//                          this.hideDiaError();
//                      })
                      return {
                          showDiaError: function(title, msg) {
                              if (title != null) {
                                  $('.modal-title', errorDiv).html(title);
                              }
                              if (msg != null) {
                                  $('.modal-body-pre', errorDiv).html(msg);
                              }
                              errorDiv.modal();
                          },
                          hideDiaError: function () {
                              errorDiv.modal('hide');
                          }
                      };
                  })();

    var CalculationTable = Backbone.View.extend(
        {
            /* the html element where the table is rendered */
            el: $('#my-calculations'),

            initialize: function(options) {

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
                "click .btn-danger": "remove_calculation",
                "click .btn-traceback": "show_traceback",
                "click .btn-file": "on_run_risk_clicked",
                "change .btn-file input": "on_run_risk_queued"
            },

            /* When an input dialog is opened, it is very important to not re-render the table */
            on_run_risk_clicked: function(e) {
                /* if a file input dialog has been opened do not refresh the calc table */
                this.can_be_rendered = false;
            },

            on_run_risk_queued: function(e) {
                this.can_be_rendered = true;
            },

            remove_calculation: function(e) {
                e.preventDefault();
                var calc_id = $(e.target).attr('data-calc-id');
                var view = this;
                diaerror.showDiaError("Removing calculation " + calc_id, "...");
                $.post(gem_oq_server_url + "/v1/calc/" + calc_id + "/remove"
                     ).success(
                         function(data, textStatus, jqXHR)
                         {
                             diaerror.showDiaError("Removing calculation " + calc_id, "Calculation " + calc_id + " removed.");
                             view.calculations.remove([view.calculations.get(calc_id)]);
                         }
                     ).error(
                         function(jqXHR, textStatus, errorThrown)
                         {
                             if (jqXHR.status == 404) {
                                 diaerror.showDiaError("Removing calculation " + calc_id + ".", "Failed: calculation " + calc_id + " not found.");
                             }
                             else {
                                 diaerror.showDiaError("Removing calculation " + calc_id + ".", "Failed: " + textStatus);
                             }
                         }
                     );
            },

            show_traceback: function(e) {
                var calc_id = $(e.target).attr('data-calc-id');

                var myXhr = $.ajax({url: gem_oq_server_url + "/v1/calc/" + calc_id + "/traceback",
                                    error: function (jqXHR, textStatus, errorThrown) {
                                        if (jqXHR.status == 404) {
                                            diaerror.showDiaError("Calculation " + calc_id + " not found.");
                                        }
                                        else {
                                            diaerror.showDiaError("Error retrieving traceback for calculation " + calc_id + ".", textStatus);
                                        }
                                        // alert("Error: " + textStatus);
                                    },
                                    success: function (data, textStatus, jqXHR) {
                                        if (data.length == 0) {
                                            diaerror.showDiaError("Traceback not found for calculation " + calc_id + ".", []);
                                        }
                                        else {
                                            out = ""
                                            for (s in data) {
                                                if (data[s] == "")
                                                    continue;
                                                out += data[s] + '\n';
                                            }
                                            diaerror.showDiaError("Traceback of calculation " + calc_id + ".", out);
                                        }
                                        // alert("Success: " + textStatus);
                                    }});
            },

            render: function() {
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
            url: gem_oq_server_url + "/v1/calc/list?relevant=true"
        });
    var calculations = new Calculations();

    var refresh_calcs;

    function setTimer() {
        refresh_calcs = setInterval(function() { calculations.fetch({reset: true}) }, 3000);
    }


    /* classic event management */
    $(document).ready(
        function() {
            var calculation_table = new CalculationTable({ calculations: calculations });
            calculations.fetch({reset: true});
            setTimer();

            /* XXX. Reset the input file value to ensure the change event
               will be always triggered */
            $(document).on("click", 'input[name=archive]',
                           function(e) { this.value = null; });
            $(document).on("change", 'input[name=archive]',
                           function(e) {
                               dialog.showPleaseWait('Uploading calculation', true);
                               var input = $(e.target);
                               var form = input.parents('form')[0];

                               $(form).ajaxSubmit(
                                   {
                                    xhr: function() {  // custom xhr to add progress bar management
                                        var myXhr = $.ajaxSettings.xhr();
                                        if(myXhr.upload){ // if upload property exists
                                            myXhr.upload.addEventListener('progress', progressHandlingFunction, false);
                                        }
                                        return myXhr;
                                    },
                                    success: function(data) {
                                        calculations.add(new Calculation(data));
                                    },
                                    error: function(xhr) {
                                        dialog.hidePleaseWait();
                                        var s, out, ret = $.parseJSON(xhr.responseText);
                                        out = ""
                                        for (s in ret) {
                                            if (ret[s] == "")
                                                continue;
                                            out += ret[s] + '\n';
                                        }
                                        diaerror.showDiaError("Calculation not accepted: traceback", out);
                                    }});
                           });

            $(document).on('hidden.bs.modal', 'div[id^=traceback-]',
                           function(e) {
                               setTimer();
                           });

        });
})($, Backbone, _, gem_oq_server_url);
