$(document).ready(function () {
    $('.er_gid input[name="magnitude"]').val("6.0");
    $('.er_gid input[name="rake"]').val(90);
    $('.er_gid input[name="hypo_lon"]').val(-78.45);
    $('.er_gid input[name="hypo_lat"]').val(12.45);
    $('.er_gid input[name="hypo_depth"]').val(11);
    $('.er_gid input:radio[name="rupture_type"][value="simple"]'
     ).attr('checked', 'checked').trigger("click");

    $('.er_gid input[name="dip"]').val(35);
    $('.er_gid input[name="upper_ses_dep"]').val(5);
    $('.er_gid input[name="lower_ses_dep"]').val(15);

    var data = [[-78.34, 12.11],
                [-78.12, 12.35],
                [-77.78, 12.47]];

    var table = $('.er_gid [name="geometry"]').handsontable('getInstance');
    table.loadData(data);

    $('.er_gid #convertBtn').trigger('click');

    window.gem_example_completed = true;
});
