var tab_id = 0, cf_subtab_id = 0;
var multi_accept = {{ multi_accept|safe }};

help = document.getElementById("help_url");
csrf_token = '{% csrf_token %}';

if(help != null) {
    help.href+='/explore/';
}
var tab_id_s = "{{ request.GET.tab_id }}";
var tab_id_int = parseInt(tab_id_s) - 1;
if (tab_id_int >= 0 && tab_id_int < 7) {
    tab_id = tab_id_int;
}

var subtab_id_s = "{{ request.GET.subtab_id|default:"0" }}", subtab_id_int;
var subtab_id_int = parseInt(subtab_id_s) - 1;

switch (tab_id) {
    // just for config file case
case 5:
    if (subtab_id_int >= 0 && subtab_id_int < 4) {
        cf_subtab_id = subtab_id_int;
    }
    break;
default:
    break;
}

$( "#tabs" ).tabs({active: tab_id });
$( "#cf_subtabs" ).tabs({active: cf_subtab_id });

var VALIDATION_URL = 'valid';
var SENDBACK_URL = 'sendback';
var g_gmpe = {{ g_gmpe|safe }};
var g_gmpe_options = [];

for (var i = 0 ; i < g_gmpe.length ; i++) {
    g_gmpe_options[i] = { type: "option", value: g_gmpe[i], label: g_gmpe[i] };
}

{
    var gem_onload_parent = window.onload;
    window.onload = function() {
        if (gem_onload_parent != null) {
            gem_onload_parent();
        }
{%if gem_qgis != None %}
        gem_api = new AppWeb('ipt');
        console.log("create gem_api");
        console.log(gem_api);
{% endif %}
    }
}
