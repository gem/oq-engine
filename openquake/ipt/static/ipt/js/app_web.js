/**
 *
 * @source: hybridge (chrome) ipt.js
 * @author: Matteo Nastasi <nastasi@alternativeoutout.it>
 * @link: https://github.com/nastasi/hybridge
 *
 * @licstart  The following is the entire license notice for the
 *  JavaScript code in this page.
 *
 * Copyright (C) 2018-2019 Matteo Nastasi
 *
 *
 * The JavaScript code in this page is free software: you can
 * redistribute it and/or modify it under the terms of the GNU
 * General Public License (GNU GPL) as published by the Free Software
 * Foundation, either version 3 of the License, or (at your option)
 * any later version.  The code is distributed WITHOUT ANY WARRANTY;
 * without even the implied warranty of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE.  See the GNU GPL for more details.
 *
 * As additional permission under GNU GPL version 3 section 7, you
 * may distribute non-source (e.g., minimized or compacted) forms of
 * that code without the copy of the GNU GPL normally required by
 * section 4, provided you include this license notice and a URL
 * through which recipients can access the Corresponding Source.
 *
 * @licend  The above is the entire license notice
 * for the JavaScript code in this page.
 *
 */

function manage_error_cb(uuid, msg)
{
    if ('result' in msg) {
        if ('reason' in msg.result) {
            gem_ipt.error_msg(msg.result.reason);
            return;
        }
    }
    if (type(console) !== 'undefined') {
        if ('log' in console) {
            console.log('manage_error_cb');
            console.log(msg);
            gem_ipt.error_msg('A command executed by QGIS returned a malformed reply, take a look to console.log for more information');
        }
    }
}

function select_update(sel, options)
{
    var $sel = $(sel);
    var old_sel;

    old_sel = $sel.val();

    var ct = $sel.attr('data-gem-counter');
    if (typeof(ct) == 'undefined')
        ct = 0;
    else
        ct = parseInt(ct);
    ct += 1;
    $sel.attr('data-gem-counter', ct);
    $sel.empty();
    if (! $sel.is("[multiple]")) {
        $("<option />", {value: '', text: '---------'}).appendTo($sel);
    }

    for (var ii = 0 ; ii < options.length ; ii++) {
        $("<option />", {value: options[ii][0], text: options[ii][1]}).appendTo($sel);
    }
    $sel.val(old_sel);
}

function populate_selects()
{
    var el, families = {};
    if (arguments.length == 0) {
        var $sel = $("select[name='file_html']");
    }
    else {
        var $sel = $("select[name='file_html'][data-gem-subdir='" + arguments[0] + "']");
    }
    for (var i = 0 ; i < $sel.length ; i++) {
        el = $sel[i];
        subdir = $(el).attr('data-gem-subdir');
        if (subdir in families) {
            families[subdir].push(el);
        }
        else {
            families[subdir] = [el];
        }
    }

    function subdir_ls_cbgen(k, family_ext)
    {
        var family = family_ext.slice();

        return function subdir_ls_cb(uuid, msg) {
            var options = [];
            var app_msg;

            app_msg = msg.result;
            for (var i = 0 ; i < app_msg.content.length ; i++) {
                var v = app_msg.content[i];
                options.push([k + '/' + v, v]);
            }
            for (var i = 0 ; i < family.length ; i++) {
                select_update(family[i], options);
            }
        }
    }

     for (var k in families) {
        if (families.hasOwnProperty(k)) {
            var family_ = families[k].slice();
            {
                var family = family_;

                subdir_ls_cb = subdir_ls_cbgen(k, family);
            }
            gem_api.ls(subdir_ls_cb, k);
        }
    }
}

var track_status_ct = 0;
function track_status_cb(uuid, msg)
{
    console.log('track_status of QGIS connection (no UI at the moment): ' + (msg.success ? '' : 'NOT ') + 'CONNECTED');
    track_status_ct++;

    if (msg.success) {
        if (typeof gem_api != 'undefined') {
            // set folders to save collected files
            function init_ls_cb(uuid, msg) {
                console.log('init_ls_cb');
                if (!msg.complete) {
                    return;
                }

                app_msg = msg.result;
                if (app_msg.success != true)
                    return manage_error_cb(uuid, app_msg);

                var ct_sync = allowed_dirs.length;

                for (var i = 0 ; i < allowed_dirs.length ; i++) {
                    all_dir = allowed_dirs[i];

                    if (app_msg.content.indexOf(all_dir + '/') == -1) {
                        // folder not found, create it
                        function init_mkdir_cb(uuid, app_msg)
                        {
                            ct_sync--;
                            if (ct_sync == 0) {
                                populate_selects();
                            }
                        }
                        gem_api.mkdir(init_mkdir_cb, all_dir);
                    }
                    else {
                        ct_sync--;
                        if (ct_sync == 0) {
                            populate_selects();
                        }
                    }
                }
            }
            gem_api.ls(init_ls_cb);
        }

        console.log("msg_close ...");
        gem_ipt.qgis_msg_close();
    }
    else {
        console.log("msg_open ...");
        gem_ipt.qgis_msg_open('The web-application was required by a browser with an enabled OpenQuake extension, but no QGIS application is currently running. Please:\nlaunch QGIS - OR - disable the OpenQuake extension by clicking its icon on the browser and reloading the page.');
    }
}

function AppWeb(name)
{
    this.name = name;
    this.hybridge = new HyBridge(this);

    // TODO: add to hybridge push pop of things to do on ext_app connect/disconnect

    console.log('before');

    this.track_uuid = this.hybridge.send(
        {'command': 'hybridge_track_status'}, track_status_cb);

    // bg-side it register cb in on_open, on_close and fire back the current
    // connection status

    console.log('after');
}

AppWeb.prototype = {
    name: null,
    hybridge: null,
    track_uuid: null,
    allowed_meths: ['set_cells'],

    register: function (hybridge) {
        this.hybridge = hybridge;
    },

    /* this function is called when a malformed message is received */
    on_notstd_msg_cb: function(msg) {
        console.log("client ipt received:");
        console.log(msg);
    },

    set_cells: function(arg_a, arg_b) {
        document.getElementById("arg-a").innerHTML = arg_a;
        document.getElementById("arg-b").innerHTML = arg_b;

        return {'success': true};
    },

    send: function(msg, cmd_cb) {
        return this.hybridge.send(msg, cmd_cb);
    },

    delegate_download: function(cb, url, action, headers, data)
    {
        var uu = this.send({'command': 'delegate_download',
                            'args': [url, action, headers, data]}, cb);
        return uu;
    },

    ls: function(cb) {
        var uu = this.send(
            {'command': 'ls',
             'args': (arguments.length > 1 ? [arguments[1]] : [])
            }, cb);

        return uu;
    },

    mkdir: function(cb, dirname) {
        var uu = this.send({'command': 'create_dir',
                            'args': [dirname]}, cb);
        return uu;
    },

    select_file: function(cb) {
        var args = [];
        for (var i = 1 ; i < arguments.length ; i++) {
            args.push(arguments[i]);
        }
        var uu = this.send({'command': 'select_file',
                            'args': args}, cb);
        return uu;
    },

    select_and_copy_file: function(cb) {
        var args = [];
        for (var i = 1 ; i < arguments.length ; i++) {
            args.push(arguments[i]);
        }
        var uu = this.send({'command': 'select_and_copy_file_to_dir',
                            'args': args}, cb);
        return uu;
    },

    build_zip: function(cb, content, zipname) {
        var uu = this.send({'command': 'build_zip',
                            'args': [content, zipname]}, cb);
        return uu;
    },

    run_oq_engine_calc: function(cb, zipname) {
        var uu = this.send({'command': 'run_oq_engine_calc',
                            'args': [[zipname]]}, cb);
        return uu;
    },

    save_as: function(cb, file_src, suggested_name) {
        var uu = this.send({'command': 'save_as',
                            'args': [file_src, suggested_name]}, cb);
        return uu;
    },

    delete_file: function(cb, file_path) {
        var uu = this.send({'command': 'delete_file',
                            'args': [file_path]}, cb);
        return uu;
    },

    move_file: function(cb, old_path, new_path) {
        var uu = this.send({'command': 'move_file',
                            'args': [old_path, new_path]}, cb);
        return uu;
    }

}
