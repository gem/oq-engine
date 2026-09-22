/*
 Copyright (C) 2015-2026 GEM Foundation

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
var refresh_calcs;
var calc_page = 0;
var calc_page_size = 10;
var calc_total = 0;

var Calculation = Backbone.Model.extend({
    defaults: {
        map: null,
        layers: []
    }
});

var Calculations = Backbone.Collection.extend({
    model: Calculation,
    url: gem_oq_server_url + "/v1/calc/list"
});
var calculations = new Calculations();

var CalculationTable = Backbone.View.extend({
    /* the html element where the table is rendered */
    el: $('#my-calculations'),

    logXhr: null,
    logTimeout: null,
    logLines: 0,
    logLinesAll: 0,
    logIsNew: false,

    initialize: function (options) {
        /* whatever happens to any calculation, re-render the table */
        _.bindAll(this, 'render');
        this.calculations = options.calculations;
        this.calculations.on('reset add remove', this.render);

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
        "change .btn-file input": "on_run_risk_queued",
        "click .calc-page-first": "first_page",
        "click .calc-page-prev": "previous_page",
        "click .calc-page-next": "next_page",
        "click .calc-page-last": "last_page"
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

    confirm_modify_calculation: function (e, action) {
        e.preventDefault();
        const calc_id = $(e.target).data('calc-id');
        const calc_desc = $(e.target).data('calc-desc');

        showConfirmationModal({
            title: capitalizeFirstLetter(action) + ' calculation',
            body: `Are you sure you want to ${action} calculation ${calc_id}?<br><em>"${calc_desc}"</em>`,
            confirmText: `Yes, ${action}`,
            confirmAction: () => this.modify_calculation(e, action)
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
                                    fetch_calc_page();
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

    first_page: function (e) {
        e.preventDefault();
        if (calc_page > 0) {
            calc_page = 0;
            fetch_calc_page();
        }
    },

    previous_page: function (e) {
        e.preventDefault();
        if (calc_page > 0) {
            calc_page--;
            fetch_calc_page();
        }
    },

    next_page: function (e) {
        e.preventDefault();
        if ((calc_page + 1) * calc_page_size < calc_total) {
            calc_page++;
            fetch_calc_page();
        }
    },

    last_page: function (e) {
        e.preventDefault();
        var last_page = Math.max(0, Math.ceil(
            calc_total / calc_page_size) - 1);
        if (calc_page < last_page) {
            calc_page = last_page;
            fetch_calc_page();
        }
    },

    render_pagination: function () {
        var pages = Math.max(1, Math.ceil(calc_total / calc_page_size));
        var last_page = pages - 1;
        var html = '<div class="pagination">';
        html += '<button class="btn calc-page-first" ';
        html += calc_page == 0 ? 'disabled>First</button>' : '>First</button>';
        html += ' <button class="btn calc-page-prev" ';
        html += calc_page == 0 ? 'disabled>Previous</button>' : '>Previous</button>';
        html += ' <span>Page ' + (calc_page + 1) + ' of ' + pages + '</span> ';
        html += '<button class="btn calc-page-next" ';
        html += calc_page >= last_page ?
            'disabled>Next</button>' : '>Next</button>';
        html += ' <button class="btn calc-page-last" ';
        html += calc_page >= last_page ?
            'disabled>Last</button>' : '>Last</button>';
        html += '</div>';
        this.$el.append(html);
    },

    render: function () {
        if (!this.can_be_rendered) return;
        this.$el.html(_.template($('#calculation-table-template').html(), {
            calculations: this.calculations.models
        }));
        this.render_pagination();
    }
});
var calculation_table = new CalculationTable({ calculations: calculations });
$(document).on('errorDialog:hidden', function () {
    calculation_table.hide_log();
});

function setTimer() {
    closeTimer();
    refresh_calcs = setInterval(function () {
        refresh_tag_selector();
        fetch_calc_page();
    }, 3000);
}

function closeTimer() {
    refresh_calcs = clearInterval(refresh_calcs);
}

function get_calc_list_params() {
    var params = {
        limit: calc_page_size,
        offset: calc_page * calc_page_size,
        relevant_only: '1'
    };
    if ($('input#list_preferred_only').is(':checked')) {
        params.preferred_only = '1';
    }
    var filter_by_tag = $('select#tag_selector').val();
    if (filter_by_tag) {
        params.filter_by_tag = filter_by_tag;
    }
    return params;
}

function fetch_calc_count() {
    var params = get_calc_list_params();
    delete params.limit;
    delete params.offset;
    params.count_only = '1';
    $.getJSON(gem_oq_server_url + "/v1/calc/list/count?" +
              $.param(params), function (count) {
        calc_total = count;
        var last_page = Math.max(0, Math.ceil(
            calc_total / calc_page_size) - 1);
        if (calc_page > last_page) {
            calc_page = last_page;
            fetch_calc_page();
        } else {
            calculation_table.render();
        }
    });
}

function fetch_calc_page() {
    var params = get_calc_list_params();
    calculations.url = gem_oq_server_url + "/v1/calc/list?" +
        $.param(params);
    calculations.fetch({reset: true});
    fetch_calc_count();
}

function set_calc_list_params() {
    calc_page = 0;
    fetch_calc_page();
}

function refresh_tag_selector() {
    $.getJSON('/v1/calc/list_tags', function(resp) {
        if (resp.tags.length == 0) {
            $("div#tag-filters").hide();
        } else {
            $("div#tag-filters").show();
        }
        const tag_selector = $('#tag_selector');
        const selected_tag = tag_selector.val();
        tag_selector.empty();
        tag_selector.append('<option value="">All tags</option>');
        $.each(resp.tags, function(_, tag) {
            const safeTag = $('<div>').text(tag).html(); // escape HTML
            tag_selector.append(`<option value="${safeTag}">${safeTag}</option>`);
        });
        // Try to restore previous selection if still available
        if (selected_tag && resp.tags.includes(selected_tag)) {
            tag_selector.val(selected_tag);
        }
    }).fail(function(jqXHR, textStatus, errorThrown) {
        console.error('Error fetching tags:', textStatus, errorThrown);
    });
}

$('input#list_preferred_only').change(function() {
    set_calc_list_params();

});

$('select#tag_selector').change(function() {
    set_calc_list_params();
});

