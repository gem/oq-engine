$(document).ready(function () {
    $('.vf_gid #functionId').val('Vulnerability_test02');
    $('.vf_gid #assetCategory').val('buildings');
    $('.vf_gid #functionDescription').val('Vulnerability curves for MUR in Antioquia\nFixed consequence model');

    // create DISCRETE function 1
    $('.vf_gid #addDiscreteFunc').trigger('click');
    {
        var table = $('.vf_gid [name="tableDiv1"]').handsontable('getInstance');
        $('.vf_gid .table1_id [name="id"]').val('MUR/H:1');
        $('.vf_gid .table1_id [name="imt"]').val('PGA');

        var data = [
        [ 0.025, 0.001, 1.499993 ] ,
        [ 0.05, 0.003, 1.488915 ] ,
        [ 0.075, 0.006006, 1.319811 ] ,
        [ 0.1, 0.023845, 0.784661 ] ,
        [ 0.125, 0.05541, 0.397836 ] ,
        [ 0.15, 0.101325, 0.37947 ] ,
        [ 0.175, 0.161288, 0.355485 ] ,
        [ 0.2, 0.235614, 0.325754 ] ,
        [ 0.225, 0.326435, 0.289426 ] ,
        [ 0.25, 0.435387, 0.245845 ] ,
        [ 0.275, 0.558104, 0.196758 ] ,
        [ 0.3, 0.681537, 0.147385 ] ,
        [ 0.325, 0.789743, 0.104103 ] ,
        [ 0.35, 0.872486, 0.071005 ] ,
        [ 0.375, 0.928431, 0.048628 ] ,
        [ 0.4, 0.962465, 0.029277 ] ,
        [ 0.425, 0.981418, 0.014494 ] ,
        [ 0.45, 0.991232, 0.006839 ] ,
        [ 0.475, 0.996021, 0.003104 ] ,
        [ 0.5, 0.998248, 0.001366 ] ,
        [ 0.525, 0.999247, 0.000588 ] ,
        [ 0.55, 0.999681, 0.000249 ] ,
        [ 0.575, 0.999866, 0.000104 ] ,
        [ 0.6, 0.999944, 0.000044 ]
        ];

        table.loadData(data);

    }

    // create DISCRETE function 2
    $('.vf_gid #addDiscreteFunc').trigger('click');
    {
        var table = $('.vf_gid [name="tableDiv2"]').handsontable('getInstance');
        $('.vf_gid .table2_id [name="id"]').val('MUR/H:2');
        $('.vf_gid .table2_id [name="imt"]').val('PGA');

        var data = [
        [ 0.025, 0.000621, 0 ] ,
        [ 0.05, 0.034401, 0 ] ,
        [ 0.075, 0.109619, 0 ] ,
        [ 0.1, 0.10971, 0 ] ,
        [ 0.125, 0.146987, 0 ] ,
        [ 0.15, 0.238893, 0 ] ,
        [ 0.175, 0.31012, 0 ] ,
        [ 0.2, 0.317773, 0 ] ,
        [ 0.225, 0.380724, 0 ] ,
        [ 0.25, 0.428463, 0 ] ,
        [ 0.275, 0.446674, 0 ] ,
        [ 0.3, 0.456104, 0 ] ,
        [ 0.325, 0.480333, 0 ] ,
        [ 0.35, 0.536784, 0 ] ,
        [ 0.375, 0.615071, 0 ] ,
        [ 0.4, 0.620671, 0 ] ,
        [ 0.425, 0.706434, 0 ] ,
        [ 0.45, 0.778461, 0 ] ,
        [ 0.475, 0.803128, 0 ] ,
        [ 0.5, 0.842213, 0 ] ,
        [ 0.525, 0.850487, 0 ] ,
        [ 0.55, 0.883643, 0 ] ,
        [ 0.575, 0.920004, 0 ] ,
        [ 0.6, 0.988817, 0 ]
        ];

        table.loadData(data);

    }

    // create DISCRETE function 3
    $('.vf_gid #addDiscreteFunc').trigger('click');
    {
        var table = $('.vf_gid [name="tableDiv3"]').handsontable('getInstance');
        $('.vf_gid .table3_id [name="id"]').val('MUR/H:3');
        $('.vf_gid .table3_id [name="imt"]').val('SA(0.1)');

        var data = [
        [ 0.05, 0.005, 0 ] ,
        [ 0.1, 0.0983, 0 ] ,
        [ 0.15, 0.1506, 0 ] ,
        [ 0.2, 0.191627, 0 ] ,
        [ 0.25, 0.208749, 0 ] ,
        [ 0.3, 0.22587, 0 ] ,
        [ 0.35, 0.244658, 0 ] ,
        [ 0.4, 0.256778, 0 ] ,
        [ 0.45, 0.2789, 0 ] ,
        [ 0.5, 0.296545, 0 ] ,
        [ 0.55, 0.308474, 0 ] ,
        [ 0.6, 0.456104, 0 ] ,
        [ 0.65, 0.429906, 0 ] ,
        [ 0.7, 0.465048, 0 ] ,
        [ 0.75, 0.50019, 0 ] ,
        [ 0.8, 0.535331, 0 ] ,
        [ 0.85, 0.570473, 0 ] ,
        [ 0.9, 0.605615, 0 ] ,
        [ 0.95, 0.640757, 0 ] ,
        [ 1, 0.675898, 0 ] ,
        [ 1.05, 0.71104, 0 ] ,
        [ 1.1, 0.746182, 0 ] ,
        [ 1.15, 0.8955, 0 ] ,
        [ 1.2, 0.957, 0 ]
        ];

        table.loadData(data);

    }

    // create a PMF
    $('.vf_gid #addProbMassFunc').trigger('click');
    { // blocks are used to reflect DOM hierarchy
        var table = $('.vf_gid [name="tableDiv4"]').handsontable('getInstance');
        $('.vf_gid .table4_id [name="id"]').val('111');
        $('.vf_gid .table4_id [name="imt"]').val('PGA');
        $('.vf_gid .table4_id [name="imls"]').val('0.2 0.3 0.4 0.5 0.7 0.8');
        $('.vf_gid .table4_id [name="imls"]').trigger('change');

        var data = table.getData(0,0, table.countRows() - 1, table.countCols() - 1);
        console.log("probmass:: rows " + table.countRows() + " cols: " + table.countCols());

        for (var e = 0 ; e < table.countRows() ; e++) {
            for (var i = 0 ; i < table.countCols() ; i++) {
                data[e][i] = (i / 100.0) + (e / 10.0);
            }
        }
        table.loadData(data);
    }

    $('.vf_gid #convertBtn').trigger('click');
    window.gem_example_completed = true;
});
