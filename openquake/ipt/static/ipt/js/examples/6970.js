$(document).ready(function () {
    $('a[href="#subtabs-3"]').click();

    $(cf_obj['e_b'].pfx + ' div[name="exposure-model-html"] select[name="file_html"]'
     ).val('data/exposure_model/exposure_model.xml');
    $(cf_obj['e_b'].pfx + ' div[name="vm-structural-html"] select[name="file_html"]'
     ).val('data/vulnerability_model/structural_vulnerability_model.xml');
    $(cf_obj['e_b'].pfx + ' div[name="source-model-logic-tree-file-html"] select[name="file_html"]'
     ).val('data/source_model_logic_tree_file/source_model.xml');
    $(cf_obj['e_b'].pfx + ' div[name="gsim-logic-tree-file-html"] select[name="file_html"]'
     ).val('data/gsim_logic_tree_file/gmpe_logic_tree.xml');
    $(cf_obj['e_b'].pfx + ' div[name="hazard-model"] div[name="source-model-file-html"] select').val(['data/source_model_file/source_model01.xml']);

    $(cf_obj['e_b'].pfx + ' button[name="download"]').click();
    window.gem_example_completed = true;
});
