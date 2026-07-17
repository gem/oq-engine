$(document).ready(function () {
    $('.er_gid input[name="magnitude"]').val("6.3");
    $('.er_gid input[name="rake"]').val(135);
    $('.er_gid input[name="hypo_lon"]').val(-74.0182);
    $('.er_gid input[name="hypo_lat"]').val(4.6854);
    $('.er_gid input[name="hypo_depth"]').val(6.44);
    $('.er_gid input:radio[name="rupture_type"][value="planar"]'
     ).attr('checked', 'checked').trigger("click");

    $('.er_gid div[name="planar-0"] input:text[name="strike"]').val(358);
    $('.er_gid div[name="planar-0"] input:text[name="dip"]').val(75);


    var data = [[-74.03375769, 4.625506588, 0],
                [-74.03375037, 4.74543305, 0],
                [-74.00261703, 4.625506588, 12.88082791],
                [-74.00261703, 4.625506588, 12.88082791]];

    var table = $('.er_gid div[name="planar-0"] [name="geometry-0"]').handsontable('getInstance');
    table.loadData(data);
    
    $('.er_gid #convertBtn').trigger('click');

    window.gem_example_completed = true;
});
