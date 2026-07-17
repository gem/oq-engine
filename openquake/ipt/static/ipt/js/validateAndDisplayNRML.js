function dumb_cb(uuid, msg)
{
    return;
}

function sfx2name(sfx)
{
    var map = { 'ex': 'exposure',
                'ff': 'fragility',
                'co': 'consequence',
                'vf': 'vulnerability',
                'sc': 'site',
                'er': 'earthquake_rupture' };

    return map[sfx];
}


function row_split(row_in)
{
    var el = null, data_in = row_in.trim();
    var divisor = ["	", ",", ";"];
    for (var d in divisor) {
        if (data_in.indexOf(divisor[d]) > -1) {
            el = data_in.split(divisor[d]);
            for (var i = 0 ; i < el.length ; i++) {
                el[i] = el[i].trim();
            }
            break;
        }
    }
    if (el == null) {
        el = data_in.split(' ');
    }
    return el;
}

function sendbackNRML(nrml, sfx)
{
    var funcType = sfx2name(sfx);
    var $form = $('.' + sfx + '_gid #downloadForm');
    $form.empty();
    $form.append(csrf_token);
    $form.attr({'action': SENDBACK_URL});
    $new_input = $('<input/>');
    $new_input.attr('type', 'hidden').attr({'name': 'xml_text', 'value': nrml });
    $form.append($new_input);
    $new_input = $('<input/>');
    $new_input.attr('type', 'hidden').attr({'name': 'func_type', 'value': funcType });
    $form.append($new_input);
    $form[0].submit();
}

function delegate_downloadNRML_cb(uuid, msg)
{
    if (msg.complete) {
        var res = msg.result;
        if (res.success == false) {
            gem_ipt.error_msg(res.reason);
            return;
        }

        function save_as_cb(uuid, msg)
        {

            if (msg.complete) {
                gem_api.delete_file(dumb_cb, res.realpath);
            }
        }

        gem_api.save_as(save_as_cb, res.realpath, res.content);
    }
}

function delegate_collectNRML_cb(uuid, msg)
{

    var dir_mapping = {
        'exposure_model.xml': 'exposure_model',
        'fragility_model.xml': 'fragility_model',
        'consequence_model.xml': 'fragility_cons',
        'vulnerability_model.xml': 'vulnerability_model',
        'site_model.xml': 'site_conditions',
        'earthquake_rupture_model.xml': 'rupture_file'
    };

    if (msg.complete) {
        var res = msg.result;
        if (res.success == false) {
            gem_ipt.error_msg(res.reason);
            return;
        }

        if (!(res.content in dir_mapping)) {
            gem_api.delete_file(dumb_cb, res.realpath);
            gem_ipt.error_msg('File [' + res.content + '] type not collectable');
            return;
        }

        var target_subdir = dir_mapping[res.content];
        var target_file = target_subdir + '/' + res.content;

        function move_file_cb(uuid, msg)
        {
            var res = msg.result;

            if (msg.complete) {
                if (res.success) {
                    populate_selects(target_subdir);
                    gem_ipt.info_msg('File collected as "' + target_file + '"');
                    return;
                }
                else {
                    gem_ipt.error_msg('Move file to [' + target_file + '] failed with the reason: ' + res.content + '.');
                    gem_api.delete_file(dumb_cb, res.realpath);
                }
            }
        }
        gem_api.move_file(move_file_cb, res.realpath, target_file);
    }
}

function delegate_downloadNRML(nrml, sfx, cb)
{
    if (typeof gem_api == 'undefined')
        return false;

    var spli_url = getLocation(window.location.href);

    var funcType = sfx2name(sfx);
    var csrf_name = $(csrf_token).attr('name');
    var csrf_value = $(csrf_token).attr('value');
    // FIXME: take csrf cookie from headers
    // var cookie_csrf = {'name': csrf_name, 'value': csrf_value};
    var cookie_csrf = {'name': 'csrftoken', 'value': csrf_value};
    var cookies = [cookie_csrf];
    var dd_headers = [ipt_cookie_builder(cookies)];
    var dd_data = [{'name': 'csrfmiddlewaretoken', 'value': csrf_value},
                   {'name': 'xml_text', 'value': nrml },
                   {'name': 'func_type', 'value': funcType }];

    // action (url), method (string like 'POST'), headers (list of strings),
    //               data (list of dictionaries {name (string), value(string)}
    //               delegate_downloadNRML_cb == function(obj_suffix, ... )

    var spli_url = getLocation(window.location.href);
    var pathname = spli_url['pathname'];
    pathname = pathname.substr(0, pathname.lastIndexOf('/')) + '/';
    var base_url = spli_url['protocol'] + '//' + spli_url['host'] + pathname;

    var uu = gem_api.delegate_download(
        cb, base_url + SENDBACK_URL, 'POST', dd_headers, dd_data);

    return uu;
}

function validationErrorShow(funcType, error_msg){
    $('.' + funcType + '_gid #validationErrorMsg').text(
        'Validation error: ' + error_msg.replace(/\/tmp\/[a-zA-Z0-9-_]*\.xml/, 'this NRML file') + '.');
    $('.' + funcType + '_gid #validationErrorMsg').show();
}

function validationErrorHide(funcType){
    $('.' + funcType + '_gid #validationErrorMsg').hide();
}

function infoMessageShow(funcType, textBox){
    $('.' + funcType + '_gid #infoMsg').show();
    selectAllTextareaText(textBox);
}


function infoMessageHide(funcType){
    $('.' + funcType + '_gid #infoMsg').hide();
}


function output_manager(funcType, error_msg, error_line, nrml)
{
    var textarea = null;

    // Provide the user with the xml output
    $('.' + funcType + '_gid #outputText').empty();
    if (nrml) {
        var $textarea = $('<textarea/>').attr({id: 'textarea' + funcType, readonly: 'readonly',
                                               style: 'width: 600px; height: 700px;'}).val(nrml);
        $('.' + funcType + '_gid #outputText').append($textarea);
        textarea = $textarea.get(0);
    }

    if (error_msg) {
        validationErrorShow(funcType, error_msg);
        if (nrml && error_line) {
            selectTextareaLine(textarea, error_line);
        }
        $('.' + funcType + '_gid #infoMsg').hide();
        $('.' + funcType + '_gid #downloadLink').hide();
        $('.' + funcType + '_gid #outputDiv').show();
        return false;
    }
    else {
        if (textarea)
            infoMessageShow(funcType, textarea);
        validationErrorHide(funcType);
        $('.' + funcType + '_gid #downloadLink').show();
        $('.' + funcType + '_gid #outputDiv').show();
        return true;
    }

}

function validateAndDisplayNRML(nrml, funcType, retobj){
    // funcType can be 'ex', 'ff', 'vf', 'sc' or 'er'

    // Call the engine server api to check if the NRML is valid
    $.post(VALIDATION_URL, {xml_text: nrml})
        .done(function(resp){
            output_manager(funcType, resp.error_msg, resp.error_line, nrml);
            if (!resp.error_msg) {
                retobj.nrml = nrml;
            }
        })
        .fail(function(resp){
            var error_msg = "The call to the validation API failed, returning following error message: " +
                resp.statusText;
            output_manager(funcType, error_msg, null, null);
        });
}

