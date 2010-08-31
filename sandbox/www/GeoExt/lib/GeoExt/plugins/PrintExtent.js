/**
 * Copyright (c) 2008-2010 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */
Ext.namespace("GeoExt.plugins");

/** api: (define)
 *  module = GeoExt.plugins
 *  class = PrintExtent
 */

/** api: example
 *  Sample code to create a MapPanel with a PrintExtent, and print it
 *  immediately:
 * 
 *  .. code-block:: javascript
 *
 *      var printExtent = new GeoExt.plugins.PrintExtent({
 *          printProvider: new GeoExt.data.PrintProvider({
 *              capabilities: printCapabilities
 *          })
 *      });
 *     
 *      var mapPanel = new GeoExt.MapPanel({
 *          border: false,
 *          renderTo: "div-id",
 *          layers: [new OpenLayers.Layer.WMS("Tasmania", "http://demo.opengeo.org/geoserver/wms",
 *              {layers: "topp:tasmania_state_boundaries"}, {singleTile: true})],
 *          center: [146.56, -41.56],
 *          zoom: 6,
 *          plugins: printExtent
 *      });
 *
 *      // print the map
 *      printExtent.print();
 */

/** api: constructor
 *  .. class:: PrintExtent
 * 
 *  Provides a way to show and modify the extents of print pages on the map. It
 *  uses a layer to render the page extent and handle features of print pages,
 *  and provides a control to modify them. Must be set as a plugin to a
 *  :class:`GeoExt.MapPanel`.
 */

GeoExt.plugins.PrintExtent = function(config) {
    config = config || {};

    Ext.apply(this, config);
    this.initialConfig = config;

    if(!this.pages) {
        this.pages = [new GeoExt.data.PrintPage({
            printProvider: this.printProvider
        })];
    }

    if(!this.printProvider) {
        this.printProvider = this.pages[0].printProvider;
    }
};

GeoExt.plugins.PrintExtent.prototype = {

    /** private: initialConfig
     *  ``Object`` Holds the initial config object passed to the
     *  constructor.
     */
    initialConfig: null,

    /** api: config[printProvider]
     *  :class:`GeoExt.data.PrintProvider` The print provider this form
     *  is connected to. Optional if pages are provided.
     */
    /** api: property[printProvider]
     *  :class:`GeoExt.data.PrintProvider` The print provider this form
     *  is connected to. Read-only.
     */
    printProvider: null,
    
    /** private: property[map]
     *  ``OpenLayers.Map`` The map the layer and control are added to.
     */
    map: null,
    
    /** api: config[layer]
     *  ``OpenLayers.Layer.Vector`` The layer used to render extent and handle
     *  features to. Optional, will be created if not provided.
     */
    /** private: property[layer]
     *  ``OpenLayers.Layer.Vector`` The layer used to render extent and handle
     *  features to.
     */
    layer: null,
    
    /** private: property[control]
     *  ``OpenLayers.Control.TransformFeature`` The control used to change
     *      extent, center, rotation and scale.
     */
    control: null,
    
    /** api: config[pages]
     *  Array of :class:`GeoExt.data.PrintPage` The pages that this form
     *  controls. Optional. If not provided, it will be created with one page
     *  that fits the current map extent.
     *  
     *  .. note:: All pages must use the same PrintProvider.
     */
    /** api: property[pages]
     *  Array of :class:`GeoExt.data.PrintPage` The pages that this component
     *  controls. Read-only.
     */
    pages: null,

    /** api: property[page]
     *  :class:`GeoExt.data.PrintPage` The page currently set for
     *  transformation.
     */
    page: null,

    /** api: method[print]
     *  :param options: ``Object`` Options to send to the PrintProvider's
     *      print method. See :class:`GeoExt.data.PrintProvider` :: ``print``.
     *  
     *  Prints all pages as shown on the map.
     */
    print: function(options) {
        this.printProvider.print(this.map, this.pages, options);
    },

    /** private: method[init]
     *  :param mapPanel: class:`GeoExt.MapPanel`
     *  
     *  Initializes the plugin.
     */
    init: function(mapPanel) {
        this.map = mapPanel.map;
        mapPanel.on("destroy", this.onMapPanelDestroy, this);
        this.setUp();
    },

    /** api: method[setUp]
     *  Sets up the plugin, initializing the ``OpenLayers.Layer.Vector``
     *  layer and ``OpenLayers.Control.TransformFeature``, and centering
     *  the first page if no pages were specified in the configuration.
     */
    setUp: function() {
        this.initLayer();

        this.initControl();
        this.map.addControl(this.control);
        this.control.activate();

        this.printProvider.on("layoutchange", this.updateBox, this);

        if(!this.initialConfig.pages) {
            this.page = this.pages[0];
            var map = this.map;
            if(map.getCenter()) {
                this.fitPage();
            } else {
                map.events.register("moveend", this, function() {
                    map.events.unregister("moveend", this, arguments.callee);
                    this.fitPage();
                });
            }
        }
    },

    /** private: method[tearDown]
     *  Tear downs the plugin, removing the
     *  ``OpenLayers.Control.TransformFeature`` control and
     *  the ``OpenLayers.Layer.Vector`` layer.
     */
    tearDown: function() {
        // note: we need to be extra cautious when destroying OpenLayers
        // objects here (the tests will fail if we're not cautious anyway).
        // We use obj.events to test whether an OpenLayers object is
        // destroyed or not.

        this.printProvider.un("layoutchange", this.updateBox, this);

        var map = this.map;

        var control = this.control;
        if(control && control.events) {
            control.deactivate();
            if(map && map.events && control.map) {
                map.removeControl(control);
            }
        }

        var layer = this.layer;
        if(layer && layer.events) {
            for(var i=0, len=this.pages.length; i<len; ++i) {
                var page = this.pages[i];
                page.un("change", this.onPageChange, this);
                layer.removeFeatures([page.feature]);
            }
        }

        if(!this.initialConfig.layer &&
           map && map.events &&
           layer && layer.map) {
            map.removeLayer(layer);
        }
    },

    /** private: method[onMapPanelDestroy]
     */
    onMapPanelDestroy: function() {
        this.tearDown();

        var map = this.map;

        var control = this.control;
        if(map && map.events &&
           control && control.events) {
            control.destroy();
        }

        var layer = this.layer;
        if(!this.initialConfig.layer &&
           map && map.events &&
           layer && layer.events) {
            layer.destroy();
        }

        delete this.layer;
        delete this.control;
        delete this.page;
        this.map = null;
    },

    /** private: method[initLayer]
     */
    initLayer: function() {
        if(!this.layer) {
            this.layer = new OpenLayers.Layer.Vector(null, {
                displayInLayerSwitcher: false
            });
        }
        for(var i=0, len=this.pages.length; i<len; ++i) {
            var page = this.pages[i];
            this.layer.addFeatures([page.feature]);
            page.on("change", this.onPageChange, this);
        }
        if(!this.layer.map) {
            this.map.addLayer(this.layer);
        }
    },
    
    /** private: method[initControl]
     */
    initControl: function() {
        var pages = this.pages;

        if(!this.control) {
            this.control = new OpenLayers.Control.TransformFeature(this.layer, {
                preserveAspectRatio: true,
                eventListeners: {
                    "beforesetfeature": function(e) {
                        for(var i=0, len=this.pages.length; i<len; ++i) {
                            if(this.pages[i].feature === e.feature) {
                                this.page = this.pages[i];
                                e.object.rotation = -this.pages[i].rotation;
                                break;
                            }
                        }
                    },
                    "beforetransform": function(e) {
                        this._updating = true;
                        var page = this.page;
                        if(e.rotation) {
                            if(this.printProvider.layout.get("rotation")) {
                                page.setRotation(-e.object.rotation);
                            } else {
                                e.object.setFeature(page.feature);
                            }
                        } else if(e.center) {
                            page.setCenter(OpenLayers.LonLat.fromString(
                                e.center.toShortString()
                            ));
                        } else {
                            page.fit(e.object.box);
                            var minScale = this.printProvider.scales.getAt(0);
                            var maxScale = this.printProvider.scales.getAt(
                                this.printProvider.scales.getCount() - 1);
                            var boxBounds = e.object.box.geometry.getBounds();
                            var pageBounds = page.feature.geometry.getBounds();
                            var tooLarge = page.scale === minScale &&
                                boxBounds.containsBounds(pageBounds);
                            var tooSmall = page.scale === maxScale &&
                                pageBounds.containsBounds(boxBounds);
                            if(tooLarge === true || tooSmall === true) {
                                this.updateBox();
                            }
                        }
                        delete this._updating;
                        return false;
                    },
                    "transformcomplete": this.updateBox,
                    scope: this
                }
            });
        }
    },

    /** private: method[fitPage]
     *  Fits the current print page to the map.
     */
    fitPage: function() {
        if(this.page) {
            this.page.fit(this.map);
        }
    },

    /** private: method[updateBox]
     *  Updates the transformation box after setting a new scale or
     *  layout, or to fit the box to the extent feature after a tranform.
     */
    updateBox: function() {
        var page = this.page;
        this.control.setFeature(page.feature, {rotation: -page.rotation});
    },

    /** private: method[onPageChange]
     *  Handler for a page's change event.
     */
    onPageChange: function(page, mods) {
        if(!this._updating) {
            this.control.setFeature(page.feature, {rotation: -page.rotation});
        }
    }
};

/** api: ptype = gx_printextent */
Ext.preg && Ext.preg("gx_printextent", GeoExt.plugins.PrintExtent);
