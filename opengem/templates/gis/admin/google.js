{% extends "gis/admin/openlayers.js" %}
{% block base_layer %}
new OpenLayers.Layer.Google("Google Terrain", {type: G_PHYSICAL_MAP, 'sphericalMercator': true});
{% endblock %}

{% block extra_layers %}
 {{ module }}.layers.overlay = new OpenLayers.Layer.OSM.Mapnik("OpenStreetMap (Mapnik)");
 {{ module }}.map.addLayer({{ module }}.layers.overlay);
{% endblock %}