$(document).ready(function () {
    $('.er_gid input[name="magnitude"]').val("6.65");
    $('.er_gid input[name="rake"]').val(45);
    $('.er_gid input[name="hypo_lon"]').val(-76.65862517);
    $('.er_gid input[name="hypo_lat"]').val( 3.482826188);
    $('.er_gid input[name="hypo_depth"]').val(7.132923867);
    $('.er_gid input:radio[name="rupture_type"][value="complex"]'
     ).attr('checked', 'checked').trigger("click");

    $('.er_gid button[name="add_interm_edge"]').trigger("click");
    $('.er_gid button[name="add_interm_edge"]').trigger("click");
    
    var data1 = [[-76.66883, 3.37929, 0],
                 [-76.67236844, 3.424117133, 0],
                 [-76.67590722, 3.468944250, 0],
                 [-76.67944633, 3.513771361, 0],
                 [-76.68298578, 3.558598450, 0],
                 [-76.68652557, 3.603425530, 0]];

    var table1 = $('.er_gid div[name="complex-0"] [name="top-geometry-0"]').handsontable('getInstance');
    table1.loadData(data1);

    var data2 = [[-76.65613003, 3.373602382, 4.755282578],
                 [-76.65966788, 3.418429515, 4.755282578],
                 [-76.66320606, 3.463256634, 4.755282578],
                 [-76.66674456, 3.50808374, 4.755282578],
                 [-76.6702834, 3.552910832, 4.755282578],
                 [-76.67382257, 3.597737911, 4.755282578]];

    var table2 = $('.er_gid div[name="complex-0"] [name="middle-geometry-0-0"]').handsontable('getInstance');
    table2.loadData(data2);

    var data3 = [[-76.6434302, 3.367914599, 9.510565156],
                 [-76.64696746, 3.412741728, 9.510565156]];

    var table3 = $('.er_gid div[name="complex-0"] [name="middle-geometry-0-1"]').handsontable('getInstance');
    table3.loadData(data3);

    var data4 = [[-76.63073052, 3.36222651, 14.2658],
                 [-76.6342672, 3.407053775, 14.2658]];

    var table4 = $('.er_gid div[name="complex-0"] [name="bottom-geometry-0"]').handsontable('getInstance');
    table4.loadData(data4);

    $('.er_gid #convertBtn').trigger('click');

    window.gem_example_completed = true;
});
