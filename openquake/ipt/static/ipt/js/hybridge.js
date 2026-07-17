/**
 *
 * @source: hybridge (chrome) hybridge.js
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

function HyBridge(app, on_msg_cb)
{
    this.app = app;
    app.register(this);
    this.on_msg_cb = on_msg_cb;
    this.connect();
}

var _hybridge_id = null;

try {
    _hybridge_id = hybridge_id;
} catch {
    console.log('no hybridge_id found');
}

HyBridge.prototype = {
    hybridge_id: _hybridge_id,
    app: null,
    name: null,
    port: null,
    pending: {},

    // connect to hybridge
    connect: function() {
        var _this = this;
        if (this.port != null) {
            // FIXME close previous
        }
        console.log('NAME: ' + this.app.name);
        this.port = chrome.runtime.connect(
            this.hybridge_id, {name: this.app.name});
        this.port.onMessage.addListener(function(msg) { return _this.receive(msg)});
    },

    // receive from hybridge
    receive: function(api_msg) {
        console.log("receive");
        console.log(api_msg);
        if ('uuid' in api_msg) {
            if (api_msg['uuid'] in this.pending &&
                'reply' in api_msg) {

                // reply from a command

                console.log('Reply received!');
                var uu = api_msg['uuid'];
                var reply = api_msg['reply'];
                if (this.pending[uu].cb) {
                    console.log('reply cb fired!');
                    this.pending[uu].cb(uu, reply);
                }
                if (reply.complete === undefined || reply['complete']) {
                    console.log('pending removed!');
                    delete this.pending[uu];
                }
            }
            else if ('msg' in api_msg) {
                var app_msg = api_msg['msg'];

                if (!('command' in app_msg) || !('args' in app_msg)) {
                    // FIXME reply error properly
                    return false;
                }

                // special case to manage early disconnection
                if (app_msg['command'] == 'conn_status') {
                    this.app['conn_status'].apply(
                    this.app, app_msg.args);
                    return (false);
                }

                if (this.app.allowed_meths.indexOf(
                    app_msg.command) == -1) {
                       // FIXME reply error properly2
                    return false;
                }
                console.log('pre_call');
                console.log(app_msg);
                var app_reply = this.app[app_msg.command].apply(
                    this.app, app_msg.args);

                var api_reply = {'reply': app_reply, 'uuid': api_msg.uuid};
                if (this.port == null) {
                    return false;
                }
                console.log('reply');
                console.log(api_reply);
                this.port.postMessage(api_reply);
            }
        }
        else {
            // not a reply or malformed msg, use user defined cb
            if ('on_notstd_msg_cb' in this.app) {
                this.app.on_notstd_msg_cb(api_msg);
            }
        }
    },

    // send to hybridge
    // { 'msg': {'command', 'args', [ ]}, uuid: <UUID> }
    send: function(msg, on_reply_cb) {
        console.log('send: begin');
        var uu = uuid();
        var api_msg = { 'msg': msg,
                        'uuid': uu
                        // maybe the time
                      };
        if (this.port == null) {
            return false;
        }
        console.log(api_msg);
        this.port.postMessage(api_msg);
        this.pending[uu] = { 'msg': api_msg, 'cb': on_reply_cb };
        return uu;
    }
}
