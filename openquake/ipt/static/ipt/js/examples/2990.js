$(document).ready(function () {
    $('.ff_gid #functionId').val('111vv1');
    $('.ff_gid #assetCategory').val('buildings');
    $('.ff_gid #functionDescription').val('the description');
    // $('.ff_gid #limitStates').val('slight, moderate, extensive, complete');

    // create first prob mass func
    $('.ff_gid #addDiscrFunc').trigger('click');
    { // blocks are used to reflect DOM hierarchy
        var table = $('.ff_gid [name="tableDiv1"]').handsontable('getInstance');
        $('.ff_gid .table1_id [name="id"]').val('111');
        $('.ff_gid .table1_id [name="imt"]').val('PGA');
        $('.ff_gid .table1_id [name="no-damage-limit"]').val('0.8');

        var data = [ [ ], [ ] ];
        for (var e = 0 ; e < 2 ; e++) {
            for (var i = 0 ; i < table.countCols() ; i++) {
                data[e][i] = e + parseFloat(i) / 10.0;
            }
        }
        table.loadData(data);
    }

    // create second prob mass func
    $('.ff_gid #addContFunc').trigger('click');
    {
        var table = $('.ff_gid [name="tableDiv2"]').handsontable('getInstance');
        $('.ff_gid .table2_id [name="id"]').val('222');
        $('.ff_gid .table2_id [name="imt"]').val('PGA');
        $('.ff_gid .table2_id [name="no-damage-limit"]').val('0.9');
        $('.ff_gid .table2_id [name="min-impls"]').val('0.2');
        $('.ff_gid .table2_id [name="max-impls"]').val('0.95');

        var data = table.getData(0, 0, table.countRows() - 1, table.countCols() - 1);
        for (var e = 0 ; e < 4 ; e++) {
            for (var i = 1 ; i < 3 ; i++) {
                data[e][i] = i / 10.0 + e;
            }
        }
        table.loadData(data);
    }

    $('.ff_gid #convertBtn').trigger('click');
    window.gem_example_completed = true;
});
