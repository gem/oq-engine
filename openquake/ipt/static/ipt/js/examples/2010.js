$(document).ready(function () {
    $('.ff_gid #functionId').val('fragility_model_MUR');
    $('.ff_gid #assetCategory').val('buildings');
    $('.ff_gid #functionDescription').val('Different fragility models to test MUR\nBased on Antioquia example');

    // create CONTINUOS FRAGILITY function
    $('.ff_gid #addContFunc').trigger('click');
    {
        var table = $('.ff_gid [name="tableDiv1"]').handsontable('getInstance');
        $('.ff_gid .table1_id [name="id"]').val('MUR/H:1');
        $('.ff_gid .table1_id [name="imt"]').val('PGA');
        $('.ff_gid .table1_id [name="no-damage-limit"]').val('0.05');
        $('.ff_gid .table1_id [name="min-impls"]').val('0.0');
        $('.ff_gid .table1_id [name="max-impls"]').val('1.5');
        $('.ff_gid #limitStates').val('slight, moderate, extensive, collapse');
        $('.ff_gid #limitStates').trigger('change');

        var data = [
        [ 'slight', 1.30351, 0.65425],
        [ 'moderate', 2.39949, 1.65558],
        [ 'extensive', 2.98182, 2.16212],      
        [ 'collapse', 5.0809, 4.73784]
        ];
        table.loadData(data);
    }

    $('.ff_gid #addContFunc').trigger('click');
    {
        var table = $('.ff_gid [name="tableDiv2"]').handsontable('getInstance');
        $('.ff_gid .table2_id [name="id"]').val('MUR/H:2');
        $('.ff_gid .table2_id [name="imt"]').val('PGA');
        $('.ff_gid .table2_id [name="no-damage-limit"]').val('0.05');
        $('.ff_gid .table2_id [name="min-impls"]').val('0.0');
        $('.ff_gid .table2_id [name="max-impls"]').val('1.5');
        $('.ff_gid #limitStates').val('slight, moderate, extensive, collapse');
        $('.ff_gid #limitStates').trigger('change');

        var data = [
        [ 'slight', 0.45446, 0.13365],
        [ 'moderate', 0.73629, 0.2902],
        [ 'extensive', 1.0083, 0.4132],
        [ 'collapse', 1.38991, 0.64721]
        ];
        table.loadData(data);
    }

    $('.ff_gid #addContFunc').trigger('click');
    {
        var table = $('.ff_gid [name="tableDiv3"]').handsontable('getInstance');
        $('.ff_gid .table3_id [name="id"]').val('MUR/H:3');
        $('.ff_gid .table3_id [name="imt"]').val('SA(0.1)');
        $('.ff_gid .table3_id [name="no-damage-limit"]').val('0.075');
        $('.ff_gid .table3_id [name="min-impls"]').val('0.0');
        $('.ff_gid .table3_id [name="max-impls"]').val('2.0');
        $('.ff_gid #limitStates').val('slight, moderate, extensive, collapse');
        $('.ff_gid #limitStates').trigger('change');

        var data = [
        [ 'slight', 0.32408, 0.09496],
        [ 'moderate', 0.45016, 0.15025],
        [ 'extensive', 0.59408, 0.22361],
        [ 'collapse', 0.77838, 0.24303]
        ];
        table.loadData(data);
    }

//    create DISCRETE FRAGILITY functions
    $('.ff_gid #addDiscrFunc').trigger('click');
    { // blocks are used to reflect DOM hierarchy
        var table = $('.ff_gid [name="tableDiv4"]').handsontable('getInstance');
        $('.ff_gid .table4_id [name="id"]').val('MUR/H:4');
        $('.ff_gid .table4_id [name="imt"]').val('PGA');
        $('.ff_gid .table4_id [name="no-damage-limit"]').val('0.1');
        
        var data = [ 
        [ 0.025, 0, 0, 0, 0 ],
        [ 0.05, 0.0037, 0, 0, 0 ],
        [ 0.075, 0.0595, 0.0003, 0, 0 ],
        [ 0.1, 0.2224, 0.008, 0, 0 ],
        [ 0.125, 0.4413, 0.0558, 0.0004, 0 ],
        [ 0.15, 0.6391, 0.1779, 0.0061, 0 ],
        [ 0.175, 0.7828, 0.3598, 0.0361, 0.0005 ],
        [ 0.2, 0.8751, 0.5518, 0.1179, 0.0059 ],
        [ 0.225, 0.93, 0.7128, 0.2594, 0.0326 ],
        [ 0.25, 0.9614, 0.8283, 0.4357, 0.1072 ],
        [ 0.275, 0.9788, 0.9026, 0.6085, 0.2429 ],
        [ 0.3, 0.9884, 0.9469, 0.75, 0.4208 ],
        [ 0.325, 0.9936, 0.9718, 0.8512, 0.6016 ],
        [ 0.35, 0.9965, 0.9854, 0.9164, 0.7521 ],
        [ 0.375, 0.9981, 0.9925, 0.9552, 0.8589 ],
        [ 0.4, 0.9989, 0.9962, 0.9769, 0.9256 ],
        [ 0.425, 0.9994, 0.9981, 0.9885, 0.9633 ],
        [ 0.45, 0.9997, 0.999, 0.9944, 0.9829 ],
        [ 0.475, 0.9998, 0.9995, 0.9973, 0.9924 ],
        [ 0.5, 0.9999, 0.9998, 0.9987, 0.9967 ],
        [ 0.525, 0.9999, 0.9999, 0.9994, 0.9986 ],
        [ 0.55, 1, 0.9999, 0.9997, 0.9995 ],
        [ 0.575, 1, 1, 0.9999, 0.9998 ],
        [ 0.6, 1, 1, 0.9999, 0.9999 ]
        ];
        table.loadData(data);
    }

    $('.ff_gid #convertBtn').trigger('click');
    window.gem_example_completed = true;
});
