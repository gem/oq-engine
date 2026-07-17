$(document).ready(function () {
    $('a[href="#subtabs-3"]').click();
    $(cf_obj['e_b'].pfx + ' div[name="exposure-model-html"] select[name="file_html"]').val('exposure_model' + gem_path_sep + 'exposure_model.xml');
    $(cf_obj['e_b'].pfx + ' div[name="vulnerability-model"] input[type="checkbox"][name="losstype"][value="occupants"]').prop('checked', true).triggerHandler('click');

    $(cf_obj['e_b'].pfx + ' div[name="vm-structural-html"] select[name="file_html"]').val('vulnerability_model' + gem_path_sep + 'modelo_vulnerabilidad_estructural.xml');
    $(cf_obj['e_b'].pfx + ' div[name="vm-occupants-html"] select[name="file_html"]').val('vulnerability_model' + gem_path_sep + 'modelo_vulnerabilidad_ocupantes.xml');

    $(cf_obj['e_b'].pfx + ' div[name="source-model-logic-tree-file-html"] select[name="file_html"]').val("source_model_logic_tree_file' + gem_path_sep + 'source_model_logic_tree.xml");

    $(cf_obj['e_b'].pfx + ' div[name="source-model-file-html"] select[name="file_html"]').val("source_model_file' + gem_path_sep + 'source_model_Antioquia_200km.xml");

    $(cf_obj['e_b'].pfx + ' div[name="gsim-logic-tree-file-html"] select[name="file_html"]').val("gsim_logic_tree_file' + gem_path_sep + 'gmpe_logic_tree_col2016_redux.xml");
    


    $(cf_obj['e_b'].pfx + ' div[name="hazard-model"] input[type="checkbox"][name="rupture_mesh_spacing_choice"]').prop('checked', true).triggerHandler('click');
    $(cf_obj['e_b'].pfx + ' div[name="hazard-model"] input[type="checkbox"][name="area_source_discretization_choice"]').prop('checked', true).triggerHandler('click');

    $(cf_obj['e_b'].pfx + ' div[name="site-conditions"] input[type="radio"][name="hazard_sitecond"][value="from-file"]').prop('checked', true).triggerHandler('click');

    $(cf_obj['e_b'].pfx + ' div[name="hazard-sitecond_from-file"] select[name="file_html"]').val('site_conditions' + gem_path_sep + 'site_model_surrogate.xml');

    // $(cf_obj['e_b'].pfx + ' button[name="download"]').click();
    window.gem_example_completed = true;
});
