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

(function($, Backbone, _, oq_server_url, calc_id) {

    var OutputTable = Backbone.View.extend(
        {
            /* the html element where the table is rendered */
            el: $('#my-outputs'),

            initialize: function(options) {

                /* whatever happens to any calculation, re-render the table */
                _.bindAll(this, 'render');
                this.outputs = options.outputs;
                this.outputs.bind('reset', this.render);
                this.outputs.bind('add', this.render);
                this.outputs.bind('remove', this.render);

                /* if false, it prevents the table to be refreshed */
                this.can_be_rendered = true;

                this.render();
            },

            render: function() {
                if (!this.can_be_rendered) {
                    return;
                };
                this.$el.html(_.template($('#output-table-template').html(),
                                         { outputs: this.outputs.models }));
            }
        });


    var Output = Backbone.Model.extend(
        {
            calc: function() {
                return outputs.get(this.get('calculation')) || new Output({ 'calculation_type': undefined });
            }
        });

    var Outputs = Backbone.Collection.extend(
        {
            model: Output,
            url: oq_server_url + "/v1/calc/" + calc_id + "/result/list"
        });
    var outputs = new Outputs();

    /* classic event management */
    $(document).ready(
        function() {
            var output_table = new OutputTable({ outputs: outputs });
            outputs.fetch({reset: true});
        });
})($, Backbone, _, gem_oq_server_url, gem_calc_id);
