/**
 * Copyright (c) 2008-2009 The Open Source Geospatial Foundation
 *
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

/** api: (define)
 *  module = GeoExt.ux
 *  class = GeonamesSearchCombo
 *  base_link = `Ext.form.ComboBox <http://extjs.com/deploy/dev/docs/?class=Ext.form.ComboBox>`_
 */

Ext.namespace("GeoExt.ux.form");

GeoExt.ux.form.GeoNamesSearchCombo = Ext.extend(Ext.form.ComboBox, {
    /** api: config[map]
     *  ``OpenLayers.Map or Object``  A configured map or a configuration object
     *  for the map constructor, required only if :attr:`zoom` is set to
     *  value greater than or equal to 0.
     */
    /** private: property[map]
     *  ``OpenLayers.Map``  The map object.
     */
    map: null,

    /** api: config[width]
     *  See http://www.extjs.com/deploy/dev/docs/source/BoxComponent.html#cfg-Ext.BoxComponent-width,
     *  default value is 350.
     */
    width: 350,

    /** api: config[listWidth]
     *  See http://www.extjs.com/deploy/dev/docs/source/Combo.html#cfg-Ext.form.ComboBox-listWidth,
     *  default value is 350.
     */
    listWidth: 350,

    /** api: config[loadingText]
     *  See http://www.extjs.com/deploy/dev/docs/source/Combo.html#cfg-Ext.form.ComboBox-loadingText,
     *  default value is "Search in Geonames...".
     */
    loadingText: 'Search in Geonames...',

    /** api: config[emptyText]
     *  See http://www.extjs.com/deploy/dev/docs/source/TextField.html#cfg-Ext.form.TextField-emptyText,
     *  default value is "Search location in Geonames".
     */
    emptyText: 'Search location in Geonames',

    /** api: config[zoom]
     *  ``Number`` Zoom level for recentering the map after search, if set to
     *  a negative number the map isn't recentered, defaults to 8.
     */
    /** private: property[zoom]
     *  ``Number``
     */
    zoom: 8,

    /** api: config[minChars]
     *  ``Number`` Minimum number of characters to be typed before
     *  search occurs, defaults to 1.
     */
    minChars: 1,

    /** api: config[queryDelay]
     *  ``Number`` Delay before the search occurs, defaults to 50 ms.
     */
    queryDelay: 50,

    /** api: config[maxRows]
     *  `String` The maximum number of rows in the responses, defaults to 20,
     *  maximum allowed value is 1000.
     *  See: http://www.geonames.org/export/geonames-search.html
     */
    /** private: property[maxRows]
     *  ``String``
     */
    maxRows: '20',

    /** api: config[tpl]
     *  ``Ext.XTemplate or String`` Template for presenting the result in the
     *  list (see http://www.extjs.com/deploy/dev/docs/output/Ext.XTemplate.html),
     *  if not set a default value is provided.
     */
    tpl: '<tpl for="."><div class="x-combo-list-item"><h1>{name}<br></h1>{fcodeName} - {countryName}</div></tpl>',

    /** api: config[lang]
     *  ``String`` Place name and country name will be returned in the specified
     *  language. Default is English (en). See: http://www.geonames.org/export/geonames-search.html
     */
    /** private: property[lang]
     *  ``String``
     */
    lang: 'en',

    /** api: config[countryString]
     *  ``String`` Country in which to make a GeoNames search, default is all countries.
     *  Providing several countries can be done like: countryString: country=FR&country=GP
     *  See: http://www.geonames.org/export/geonames-search.html
     */
    /** private: property[countryString]
     *  ``String``
     */
    countryString: '',

    /** api: config[continentCode]
     *  ``String`` Restricts the search for toponym of the given continent,
     *  default is all continents.
     *  See: http://www.geonames.org/export/geonames-search.html
     */
    /** private: property[continentCode]
     *  ``String``
     */
    continentCode: '',
    
    /** api: config[adminCode1]
     *  ``String`` Code of administrative subdivision, default is all
     *  administrative subdivisions.
     *  See: http://www.geonames.org/export/geonames-search.html
     */
    /** private: property[adminCode1]
     *  ``String``
     */
    adminCode1: '',

    /** api: config[adminCode2]
     *  ``String`` Code of administrative subdivision, default is all administrative
     *  subdivisions.
     *  See: http://www.geonames.org/export/geonames-search.html
     */
    /** private: property[adminCode2]
     *  ``String``
     */
    adminCode2: '',

    /** api: config[adminCode3]
     *  ``String`` Code of administrative subdivision, default is all administrative
     *  subdivisions.
     *  See: http://www.geonames.org/export/geonames-search.html
     */
    /** private: property[adminCode3]
     *  ``String``
     */
    adminCode3: '',

    /** api: config[featureClassString]
     *  ``String`` Feature classes in which to make a GeoNames search, default is all
     *  feature classes.
     *  Providing several feature classes can be done with
     *  ``featureClassString: "featureClass=P&featureClass=A"``
     *  See: http://www.geonames.org/export/geonames-search.html
     */
    /** private: property[featureClassString]
     *  ``String``
     */
    featureClassString: '',

    /** api: config[featureCodeString]
     *  ``String`` Feature code in which to make a GeoNames search, default is all
     *  feature codes.
     *  Providing several feature codes can be done with
     *  ``featureCodeString: "featureCode=PPLC&featureCode=PPLX"``
     *  See: http://www.geonames.org/export/geonames-search.html
     */
    /** private: property[featureCodeString]
     *  ``String``
     */
    featureCodeString: '',

    /** api: config[tag]
     *  ``String`` Search for toponyms tagged with the specified tag, default
     *  is all tags.
     *  See: http://www.geonames.org/export/geonames-search.html
     */
    /** private: property[tag]
     *  ``String``
     */
    tag: '',

    /** api: config[charset]
     *  `String` Defines the encoding used for the document returned by
     *  the web service, defaults to 'UTF8'.
     *  See: http://www.geonames.org/export/geonames-search.html
     */
    /** private: property[charset]
     *  ``String``
     */
    charset: 'UTF8',

    /** private: property[hideTrigger]
     *  Hide trigger of the combo.
     */
    hideTrigger: true,

    /** private: property[displayField]
     *  Display field name
     */
    displayField: 'name',

    /** private: property[forceSelection]
     *  Force selection.
     */
    forceSelection: true,

    /** private: property[queryParam]
     *  Query parameter.
     */
    queryParam: 'name_startsWith',

    /** private: property[url]
     *  Url of the GeoNames service: http://www.GeoNames.org/export/GeoNames-search.html
     */
    url: 'http://ws.geonames.org/searchJSON?',

    /** private: constructor
     */
    initComponent: function() {
        GeoExt.ux.form.GeoNamesSearchCombo.superclass.initComponent.apply(this, arguments);

        var urlAppendString = '';

        if (this.countryString.length > 0) {
            urlAppendString = urlAppendString + this.countryString;      
        }

        if (this.featureClassString.length > 0) {
            urlAppendString = urlAppendString + this.featureClassString;
        }

        if (this.featureCodeString.length > 0) {
            urlAppendString = urlAppendString + this.featureCodeString;
        }
        
        this.store = new Ext.data.Store({
            proxy: new Ext.data.ScriptTagProxy({
                url: this.url + urlAppendString,
                method: 'GET'
            }),
            baseParams: {
                maxRows: this.maxRows,
                lang: this.lang,
                continentCode: this.continentCode,
                adminCode1: this.adminCode1,
                adminCode2: this.adminCode2,
                adminCode3: this.adminCode3,
                tag: this.tag,
                charset: this.charset
            },
            reader: new Ext.data.JsonReader({
                idProperty: 'geonameId',
                root: "geonames",
                totalProperty: "totalResultsCount",
                fields: [
                    {
                        name: 'geonameId'
                    },
                    {
                        name: 'countryName'
                    },
                    {
                        name: 'lng'
                    },
                    {
                        name: 'lat'
                    },
                    {
                        name: 'name'
                    },
                    {
                        name: 'fcodeName'
                    },
                    {
                        name: 'adminCode1'
                    },
                    {
                        name: 'fclName'
                    },
                    {
                        name: 'countryCode'
                    },
                    {
                        name: 'fcl'
                    },
                    {
                        name: 'fcode'
                    },
                    {
                        name: 'population'
                    },
                    {
                        name: 'adminName1'
                    }
                ]
            })
        });

        if(this.zoom > 0) {
            this.on("select", function(combo, record, index) {
                var position = new OpenLayers.LonLat(
                    record.data.lng, record.data.lat
                );
                position.transform(
                    new OpenLayers.Projection("EPSG:4326"),
                    this.map.getProjectionObject()
                );
                this.map.setCenter(position, this.zoom);
            }, this);
        }
    }
});

/** api: xtype = gxux_geonamessearchcombo */
Ext.reg('gxux_geonamessearchcombo', GeoExt.ux.form.GeoNamesSearchCombo);
