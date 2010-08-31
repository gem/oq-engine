 /**
 * Copyright (c) 2008-2010 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

/** api: example[print-preview]
 *  Printing with a Preview
 *  ----------------------------------------
 *  Using PrintMapPanel for an interactive print preview.
 */

var mapPanel, printDialog;

Ext.onReady(function() {
    // The PrintProvider that connects us to the print service
    var printProvider = new GeoExt.data.PrintProvider({
        method: "GET", // "POST" recommended for production use
        capabilities: printCapabilities, // provide url instead for lazy loading
        customParams: {
            mapTitle: "GeoExt Printing Demo",
            comment: "This demo shows how to use GeoExt.PrintMapPanel"
        }
    });
    
    // A MapPanel with a "Print..." button
    mapPanel = new GeoExt.MapPanel({
        renderTo: "content",
        width: 500,
        height: 350,
        layers: [new OpenLayers.Layer.WMS("Tasmania State Boundaries",
            "http://demo.opengeo.org/geoserver/wms",
            {layers: "topp:tasmania_state_boundaries"}, {singleTile: true})],
        center: [146.56, -41.56],
        zoom: 6,
        bbar: [{
            text: "Print...",
            handler: function(){
                // A window with the PrintMapPanel, which we can use to adjust
                // the print extent before creating the pdf.
                printDialog = new Ext.Window({
                    title: "Print Preview",
                    items: [{
                        xtype: "gx_printmappanel",
                        sourceMap: mapPanel,
                        printProvider: printProvider
                    }],
                    bbar: [{
                        text: "Create PDF",
                        handler: function(){ printDialog.items.get(0).print(); }
                    }]
                });
                printDialog.show();
            }
        }]
    });

});