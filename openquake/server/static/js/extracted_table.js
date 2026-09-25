/*
 Copyright (C) 2015-2026 GEM Foundation

 This program is free software: you can redistribute it and/or modify it
 under the terms of the GNU Affero General Public License as published by
 the Free Software Foundation, either version 3 of the License, or (at your
 option) any later version.

 This program is distributed in the hope that it will be useful, but WITHOUT
 ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public
 License for more details.
*/

(function($) {
    'use strict';

    function isMissing(value) {
        var normalized = $.trim(value).toLowerCase();
        return normalized === '' || normalized === 'nan' ||
            normalized === 'none' || normalized === 'null';
    }

    function compareCells(left, right, ascending) {
        var leftValue = left.cell.attr('data-sort-value');
        var rightValue = right.cell.attr('data-sort-value');
        var type = left.cell.attr('data-sort-type');
        var leftNumber;
        var rightNumber;
        var leftMissing = isMissing(leftValue);
        var rightMissing = isMissing(rightValue);

        if (type === 'number') {
            leftNumber = parseFloat(leftValue);
            rightNumber = parseFloat(rightValue);
            leftMissing = leftMissing || isNaN(leftNumber);
            rightMissing = rightMissing || isNaN(rightNumber);
        }

        // Keep missing values at the bottom in either direction.
        if (leftMissing || rightMissing) {
            if (leftMissing && rightMissing) {
                return 0;
            }
            return leftMissing ? 1 : -1;
        }

        var result = type === 'number'
            ? leftNumber - rightNumber
            : leftValue.toLowerCase().localeCompare(
                rightValue.toLowerCase());
        return ascending ? result : -result;
    }

    function initializeTable(table) {
        var headers = $(table).find('thead th.sortable-table-header');
        var body = table.tBodies[0];
        var activeColumn = -1;
        var ascending = true;

        function updateIndicators(column) {
            headers.attr('aria-sort', 'none').removeClass(
                'sort-ascending sort-descending');
            headers.find('.sort-indicator').text('');
            var header = headers.filter('[data-column-index="' + column + '"]');
            header.attr('aria-sort', ascending ? 'ascending' : 'descending');
            header.addClass(ascending ? 'sort-ascending' :
                            'sort-descending');
            header.find('.sort-indicator').text(ascending ? ' ▲' : ' ▼');
        }

        function sortByColumn(column) {
            if (column === activeColumn) {
                ascending = !ascending;
            } else {
                activeColumn = column;
                ascending = true;
            }

            var rows = $.map($(body).find('tr'), function(row, index) {
                return {
                    row: row,
                    cell: $(row.cells[column]),
                    index: index
                };
            });
            rows.sort(function(left, right) {
                var result = compareCells(left, right, ascending);
                return result || left.index - right.index;
            });
            $.each(rows, function(index, item) {
                body.appendChild(item.row);
            });
            updateIndicators(column);
        }

        headers.on('click', function() {
            sortByColumn(parseInt($(this).attr('data-column-index'), 10));
        });
        headers.on('keydown', function(event) {
            if (event.which === 13 || event.which === 32) {
                event.preventDefault();
                $(this).trigger('click');
            }
        });
    }

    $(function() {
        var table = document.getElementById('extracted_html_table');
        if (table && table.tBodies.length) {
            initializeTable(table);
        }
    });
}(jQuery));
