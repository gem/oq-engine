 /**
  * @class Ext.ux.plugin.VisibilityMode
  * @version 1.3.1
  * @author Doug Hendricks. doug[always-At]theactivegroup.com
  * @copyright 2007-2010, Active Group, Inc.  All rights reserved.
  * @license <a href="http://www.gnu.org/licenses/gpl.html">GPL 3.0</a>
  * Commercial Developer License (CDL) is available at http://licensing.theactivegroup.com.
  * @singleton
  * @static
  * @desc This plugin provides an alternate mechanism for hiding Ext.Elements and a new hideMode for Ext.Components.<br />
  * <p>It is generally designed for use with all browsers <b>except</b> Internet Explorer, but may used on that Browser as well.
  * <p>If included in a Component as a plugin, it sets it's hideMode to 'nosize' and provides a new supported
  * CSS rule that sets the height and width of an element and all child elements to 0px (rather than
  * 'display:none', which causes DOM reflow to occur and re-initializes nested OBJECT, EMBED, and IFRAMES elements)
  * @example
   var div = Ext.get('container');
   new Ext.ux.plugin.VisibilityMode().extend(div);
   //You can override the Element (instance) visibilityCls to any className you wish at any time
   div.visibilityCls = 'my-hide-class';
   div.hide() //or div.setDisplayed(false);

   // In Ext Layouts:
   someContainer.add({
     xtype:'flashpanel',
     plugins: [new Ext.ux.plugin.VisibilityMode() ],
     ...
    });

   // or, Fix a specific Container only and all of it's child items:
   // Note: An upstream Container may still cause Reflow issues when hidden/collapsed

    var V = new Ext.ux.plugin.VisibilityMode({ bubble : false }) ;
    new Ext.TabPanel({
     plugins     : V,
     defaults    :{ plugins: V },
     items       :[....]
    });
  */

 Ext.namespace('Ext.ux.plugin');
 Ext.onReady(function(){

   /* This important rule solves many of the <object/iframe>.reInit issues encountered
    * when setting display:none on an upstream(parent) element (on all Browsers except IE).
    * This default rule enables the new Panel:hideMode 'nosize'. The rule is designed to
    * set height/width to 0 cia CSS if hidden or collapsed.
    * Additional selectors also hide 'x-panel-body's within layouts to prevent
    * container and <object, img, iframe> bleed-thru.
    */
    var CSS = Ext.util.CSS;
    if(CSS){
        CSS.getRule('.x-hide-nosize') || //already defined?
            CSS.createStyleSheet('.x-hide-nosize{height:0px!important;width:0px!important;border:none!important;zoom:1;}.x-hide-nosize * {height:0px!important;width:0px!important;border:none!important;zoom:1;}');
        CSS.refreshCache();
    }

});

(function(){

      var El = Ext.Element, A = Ext.lib.Anim, supr = El.prototype;
      var VISIBILITY = "visibility",
        DISPLAY = "display",
        HIDDEN = "hidden",
        NONE = "none";

      var fx = {};

      fx.El = {

            /**
             * Sets the CSS display property. Uses originalDisplay if the specified value is a boolean true.
             * @param {Mixed} value Boolean value to display the element using its default display, or a string to set the display directly.
             * @return {Ext.Element} this
             */
           setDisplayed : function(value) {
                var me=this;
                me.visibilityCls ? (me[value !== false ?'removeClass':'addClass'](me.visibilityCls)) :
                    supr.setDisplayed.call(me, value);
                return me;
            },

            /**
             * Returns true if display is not "none" or the visibilityCls has not been applied
             * @return {Boolean}
             */
            isDisplayed : function() {
                return !(this.hasClass(this.visibilityCls) || this.isStyle(DISPLAY, NONE));
            },
            // private
            fixDisplay : function(){
                var me = this;
                supr.fixDisplay.call(me);
                me.visibilityCls && me.removeClass(me.visibilityCls);
            },

            /**
             * Checks whether the element is currently visible using both visibility, display, and nosize class properties.
             * @param {Boolean} deep (optional) True to walk the dom and see if parent elements are hidden (defaults to false)
             * @return {Boolean} True if the element is currently visible, else false
             */
            isVisible : function(deep) {
                var vis = this.visible ||
                    (!this.isStyle(VISIBILITY, HIDDEN) &&
                        (this.visibilityCls ?
                            !this.hasClass(this.visibilityCls) :
                                !this.isStyle(DISPLAY, NONE))
                      );

                  if (deep !== true || !vis) {
                    return vis;
                  }

                  var p = this.dom.parentNode,
                      bodyRE = /^body/i;

                  while (p && !bodyRE.test(p.tagName)) {
                    if (!Ext.fly(p, '_isVisible').isVisible()) {
                      return false;
                    }
                    p = p.parentNode;
                  }
                  return true;

            },
            //Assert isStyle method for Ext 2.x
            isStyle: supr.isStyle || function(style, val) {
                return this.getStyle(style) == val;
            }

        };

 //Add basic capabilities to the Ext.Element.Flyweight class
 Ext.override(El.Flyweight, fx.El);

 Ext.ux.plugin.VisibilityMode = function(opt) {

    Ext.apply(this, opt||{});

    var CSS = Ext.util.CSS;

    if(CSS && !Ext.isIE && this.fixMaximizedWindow !== false && !Ext.ux.plugin.VisibilityMode.MaxWinFixed){
        //Prevent overflow:hidden (reflow) transitions when an Ext.Window is maximize.
        CSS.updateRule ( '.x-window-maximized-ct', 'overflow', '');
        Ext.ux.plugin.VisibilityMode.MaxWinFixed = true;  //only updates the CSS Rule once.
    }

   };


  Ext.extend(Ext.ux.plugin.VisibilityMode , Object, {

       /**
        * @cfg {Boolean} bubble If true, the VisibilityMode fixes are also applied to parent Containers which may also impact DOM reflow.
        * @default true
        */
      bubble              :  true,

      /**
      * @cfg {Boolean} fixMaximizedWindow If not false, the ext-all.css style rule 'x-window-maximized-ct' is disabled to <b>prevent</b> reflow
      * after overflow:hidden is applied to the document.body.
      * @default true
      */
      fixMaximizedWindow  :  true,

      /**
       *
       * @cfg {array} elements (optional) A list of additional named component members to also adjust visibility for.
       * <br />By default, the plugin handles most scenarios automatically.
       * @default null
       * @example ['bwrap','toptoolbar']
       */

      elements       :  null,

      /**
       * @cfg {String} visibilityCls A specific CSS classname to apply to Component element when hidden/made visible.
       * @default 'x-hide-nosize'
       */

      visibilityCls   : 'x-hide-nosize',

      /**
       * @cfg {String} hideMode A specific hideMode value to assign to affected Components.
       * @default 'nosize'
       */
      hideMode  :   'nosize' ,

      ptype     :  'uxvismode',
      /**
      * Component plugin initialization method.
      * @param {Ext.Component} c The Ext.Component (or subclass) for which to apply visibilityMode treatment
      */
      init : function(c) {

        var hideMode = this.hideMode || c.hideMode,
            plugin = this,
            bubble = Ext.Container.prototype.bubble,
            changeVis = function(){

                var els = [this.collapseEl, this.actionMode].concat(plugin.elements||[]);

                Ext.each(els, function(el){
                    plugin.extend( this[el] || el );
                },this);

                var cfg = {
                    visFixed  : true,
                    animCollapse : false,
                    animFloat   : false,
                    hideMode  : hideMode,
                    defaults  : this.defaults || {}
                };

                cfg.defaults.hideMode = hideMode;

                Ext.apply(this, cfg);
                Ext.apply(this.initialConfig || {}, cfg);

            };

         c.on('render', function(){

            // Bubble up the layout and set the new
            // visibility mode on parent containers
            // which might also cause DOM reflow when
            // hidden or collapsed.
            if(plugin.bubble !== false && this.ownerCt){

               bubble.call(this.ownerCt, function(){
                  this.visFixed || this.on('afterlayout', changeVis, this, {single:true} );
               });
             }

             changeVis.call(this);

          }, c, {single:true});

     },
     /**
      * @param {Element/Array} el The Ext.Element (or Array of Elements) to extend visibilityCls handling to.
      * @param {String} visibilityCls The className to apply to the Element when hidden.
      * @return this
      */
     extend : function(el, visibilityCls){
        el && Ext.each([].concat(el), function(e){

            if(e && e.dom){
                 if('visibilityCls' in e)return;  //already applied or defined?
                 Ext.apply(e, fx.El);
                 e.visibilityCls = visibilityCls || this.visibilityCls;
            }
        },this);
        return this;
     }

  });

  Ext.preg && Ext.preg('uxvismode', Ext.ux.plugin.VisibilityMode );
  /** @sourceURL=<uxvismode.js> */
  Ext.provide && Ext.provide('uxvismode');
})();