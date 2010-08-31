/**
 * Copyright (c) 2008-2010 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

Ext.namespace("GeoExt.tree");

/** api: (define)
 *  module = GeoExt.tree
 *  class = RadioButtonMixin
 */

/** api: constructor
 *  A mixin to create tree node UIs with radio buttons. Can be mixed in
 *  any ``Ext.tree.TreeNodeUI`` class, and in particular in
 *  :class:`GeoExt.data.LayerNodeUI`.
 *
 *  A tree node using an ``Ext.tree.TreeNodeUI`` with a
 *  ``GeoExt.tree.RadioButtonMixin`` mixed into it generates a ``radiochange``
 *  event when the radio button is clicked. A ``radiochange`` listener
 *  receives the tree node whose radio button was clicked as its first
 *  argument.
 *
 *  If the node has a radioGroup attribute configured, the node will be
 *  rendered with a radio button next to the checkbox. This works like the
 *  checkbox with the checked attribute, but radioGroup is a string that
 *  identifies the options group.
 * 
 */

/** api: example
 *  Sample code to create a layer node UI with a radio button:
 *
 *  .. code-block:: javascript
 *
 *      var uiClass = Ext.extend(
 *          GeoExt.tree.LayerNodeUI,
 *          GeoExt.tree.RadioButtonMixin
 *      );
 *
 *  Sample code to create a tree node UI with a radio button:
 *
 *  .. code-block:: javascript
 *
 *      var uiClass = Ext.extend(
 *          Ext.tree.TreeNodeUI,
 *          new GeoExt.tree.RadioButtonMixin
 *      );
 */

GeoExt.tree.RadioButtonMixin = function() {
    return (function() {
        /** private: property[superclass]
         *  ``Ext.tree.TreeNodeUI`` A reference to the superclass that is
         *  extended with this mixin object.
         */
        var superclass;

        return {
            /** private: method[constructor]
             *  :param node: ``Ext.tree.TreeNode`` The tree node.
             */
            constructor: function(node) {
                node.addEvents(
                    "radiochange"
                );
                superclass = arguments.callee.superclass;
                superclass.constructor.apply(this, arguments);
            },

            /** private: method[render]
             *  :param bulkRender: ``Boolean``
             */
            render: function(bulkRender) {
                if(!this.rendered) {
                    superclass.render.apply(this, arguments);
                    var a = this.node.attributes;
                    if(a.radioGroup) {
                        Ext.DomHelper.insertBefore(this.anchor,
                            ['<input type="radio" class="gx-tree-radio" name="',
                            a.radioGroup, '_radio"></input>'].join(""));
                    }
                }
            },

            /** private: method[onClick]
             *  :param e: ``Object``
             */
            onClick: function(e) {
                var el = e.getTarget('.gx-tree-radio', 1); 
                if(el) {
                    el.defaultChecked = el.checked;
                    this.fireEvent("radiochange", this.node);
                } else {
                    superclass.onClick.apply(this, arguments);
                }
            }
        };
    })();
};
