	
	//Google Earth API stuff
        google.load("earth", "1");
        google.load("maps", "2.xx");
    
Ext.onReady(function (){

// If we had to use the form for real, this would not work
var loginUsernameField = function(fieldId)
{
	return new Ext.form.FormPanel({
		width: 100, 
		height: 22,				
		labelWidth: .1,         
		defaults: { width: 100 },
		items: [{
			id: fieldId,
			xtype: "textfield",
			emptyText: "username"
		}]
	});
};

var loginPasswordField = function(fieldId)
{
	return new Ext.form.FormPanel({
		width: 100, 
		height: 22,				
		labelWidth: .1,         
		defaults: { width: 100 },
		items: [{
			id: fieldId,
			xtype: "textfield",
			emptyText: "password"
		}]
	});
}
		// loss table 

		var myData = [
			[3.00E-08,0.931,0.978,0.792,1.001],
			[3.09E-07,0.809,0.849,0.687,1.001],
			[2.22E-06,0.614,0.644,0.522,0.798],
			[1.19E-05,0.394,0.414,0.335,0.513],
			[5.03E-05,0.215,0.226,0.161,0.279],
			[1.75E-04,0.098,0.103,0.074,0.128],
			[5.15E-04,0.037,0.038,0.027,0.048],
			[1.32E-03,0.010,0.010,0.007,0.012],
			[3.01E-03,0,0,0,0],
			[6.19E-03,0,0,0,0],
			[1.17E-02,0,0,0,0],
			
			];
		 
			var myReader = new Ext.data.ArrayReader({}, [
				{name: 'Loss Ratio'},
				{name: '5', type: 'float'},
				{name: '6', type: 'float'},
				{name: 'temp', type: 'float'},
				{name: 'temp2', type: 'float'}
			]);
		 
			var lossGrid = new Ext.grid.GridPanel({
				tbar: [
					'Probability of exceedance',
					'->', 
					{iconCls:'icon-save'}, 
					{iconCls:'icon-pdf'},
					{iconCls:'icon-excel'},                     					                      
					{iconCls:'icon-print'}
				],
				store: new Ext.data.Store({
					data: myData,
					reader: myReader
				}),
				columns: [
					{header: 'Loss Ratio', width: 10, sortable: true},
					{header: 'Site A', width: 10, sortable: true},
					{header: 'Site B', width: 10, sortable: true},
					{header: 'Site C', width: 10, sortable: true},
					{header: 'Site D', width: 10, sortable: true}

				
						//renderer: Ext.util.Format.dateRenderer('m/d/Y'), 
									//dataIndex: 'lastChange'}
				],
				viewConfig: {
					forceFit: true
				},
				//renderTo: 'content',
				//title: 'Conditional Loss Ratio Exceedance Matrix for Turkey (considering the hazard)',
				//width: 600,
				//autoFitColumns: true,
				autoScroll: true,
				//autoHeight: true,
				//frame: true
			});
		 
			//lossGrid.getSelectionModel().selectFirstRow();
		


  //form1 (lat long pic)

	OpenLayers.Control.Click = OpenLayers.Class(OpenLayers.Control, {                
		defaultHandlerOptions: {
			'single': true,
			'double': false,
			'pixelTolerance': 0,
			'stopSingle': false,
			'stopDouble': false
		},
		initialize: function(options) {
			this.handlerOptions = OpenLayers.Util.extend(
				{}, this.defaultHandlerOptions
			);
			OpenLayers.Control.prototype.initialize.apply(
				this, arguments
			); 
			this.handler = new OpenLayers.Handler.Click(
				this, {
					'click': this.onClick
				}, this.handlerOptions
			);
		}, 
		onClick: function(e) {
			lonlat = map.getLonLatFromViewPortPx(e.xy);    //GLOBAL
			//alert("You clicked near " + lonlat.lat + " N, " +
				//						+ lonlat.lon + " E");
			
			
			
			var latAndLong = lonlat.lat + ", " + lonlat.lon;
			var latAndLong2 = lonlat.lat + ", " + lonlat.lon;
			
			Ext.getCmp("lat").setValue(lonlat.lat);
			Ext.getCmp("long").setValue(lonlat.lon);
			Ext.getCmp("latlong").setValue(latAndLong);
			Ext.getCmp("latlong2").setValue(latAndLong);
			

		}
	});


	
 

	//Ext.QuickTips.init();

		var simpleForm1 = new Ext.FormPanel ({
		labelWidth: 40, 		// label settings here cascade unless overridden
        url:'data/save-form.php',	// when this form submitted, data goes here
        frame: false,
        //title: 'Add Pirates Crew',
        bodyStyle:'padding:5px 5px 0',
        //width: 200,
       // defaults: {width: 200},
        defaultType: 'textfield',
		id: "simpleForm1",
		frame: false,
			items: [{
					
					//	here same as <input type="text" name="name" /> in HTML
					fieldLabel: 'Lat',
					//name: 'Lat1',
					id:"lat",
					allowBlank:true
					
				},{
					fieldLabel: 'Long',
					//name: 'Long1'
					id:"long",
				},
			{
            xtype:'fieldset',
            checkboxToggle:true,
            title: 'Or enter an area ',
            autoHeight:true,
			labelWidth: 120, 
            defaults: {width: 220},
            defaultType: 'textfield',
            collapsed: true,
			//frame: false,
				items :[{
						fieldLabel: 'Upper right vertex',
						name: 'LatLong1',
						allowBlank:false,
						id:"latlong"
					},{
						fieldLabel: 'Lower left vertex',
						name: 'LatLong2',
						allowBlank:false,
						id:"latlong2"
					}
				]
        },

		],	


			
	});
	
	
	
//data store for form2

		Ext.namespace('LCombo', 'LCombo.asset', 'LCombo.vulnerability', 'LCombo.loss', 'LCombo.expo', 'LCombo.building'); 
		 
		LCombo.asset = [
			['PO', 'Population'],
			['BL', 'Buildings'],
			['NL', 'Contents'],
			['NL', 'Occupants'],
			['NL', 'Economic output']
		];

		LCombo.vulnerability = [
			[1, 'PO', 'PAGER Empirical Global Vulnerability'],
			[2, 'BL', 'ATC-13 Expert Opinion Vulnerability'],
			[3, 'NL', 'Not available']

		];
		LCombo.loss = [
			[1, 'PO', 'Fatality'],
			[2, 'BL', 'Structural Repair Cost'],
			[3, 'BL', 'Collapses'],
			[4, 'NL', 'Not available']

		];
		LCombo.expo = [
			[1, 'PO', 'LandScanTM 2008 Population'],
			[2, 'BL', 'KOERI Marmara Region'],
			[3, 'BL', 'HAZUS Los Angeles Region'],
			[4, 'NL', 'Not available']

		];
		LCombo.building = [
			[1, 'PO', 'Not applicable'],
			[2, 'BL', 'All'],
			[3, 'BL', 'List of building typologies to come'],
			[4, 'NL', 'Not available']

		];




	//form2 (maps tab)
 
	//Ext.QuickTips.init();

		var simpleForm2 = new Ext.FormPanel ({
		labelWidth: 40, 		// label settings here cascade unless overridden
		height: 500,
        url:'data/save-form.php',	// when this form submitted, data goes here
        frame: false,
        //title: 'Add Pirates Crew',
        bodyStyle:'padding:5px 5px 0',
        //width: 200,
       // defaults: {width: 200},
        defaultType: 'textfield',
		id: "simpleForm2",
		frame: false,
			items: [{
            xtype:'fieldset',
            //checkboxToggle:true,
            title: 'Select Scenario',
            autoHeight:true,
			//labelWidth: 120, 
            defaults: {width: 120},
            defaultType: 'textfield',
            collapsed: false,
			//frame: false,
            	 items:[{
					labelWidth: 120, 
					defaults: {width: 120},
					xtype:'combo',
					fieldLabel:'Select',
					resizable:true,
					minListWidth:120,
					//pageSize:5,
					// could be undefined as we use custom template
					displayField:'persLastName',
					// query all records on trigger click
					triggerAction:'all',
					// minimum characters to start the search
					minChars:2,
					// do not allow arbitrary values
					forceSelection:true,
					// otherwise we will not receive key events
					enableKeyEvents:true,
					emptyText: "Select a scenario...",
					store:['scenario list 1', 'scenario list 2', 'scenario list 3'],
					
					 }
            ]
        },
		
		{
            xtype:'fieldset',
            //checkboxToggle:true,
            title: 'Select Asset Type',
            autoHeight:true,
			//labelWidth: 120, 
            defaults: {width: 120},
            defaultType: 'textfield',
            collapsed: false,
			//frame: false,
            	 items:[{
					xtype:'combo',
					fieldLabel:'Select',
					resizable:true,
					valueField:'cid',
					//hiddenName: 'bob',
					minListWidth:120,
					displayField:'asset',
					triggerAction:'all',					
					minChars:2,
					forceSelection:true,
					enableKeyEvents:true,
					emptyText: "Select an asset...",
					store: new Ext.data.SimpleStore({
                        fields:['cid', 'asset']
                        ,data:LCombo.asset
                    }),
					mode:'local',
					listeners:{select:{fn:function(combo, value) {
                        var comboAsset = Ext.getCmp('combo-vuln');
						var comboLoss = Ext.getCmp('combo-loss');
						var comboExpo = Ext.getCmp('combo-expo');
						var comboBuilding = Ext.getCmp('combo-building');
						
                        comboAsset.clearValue();
                        comboAsset.store.filter('cid', combo.getValue());
                        
						comboLoss.clearValue();
                        comboLoss.store.filter('cid', combo.getValue());
						
						comboExpo.clearValue();
                        comboExpo.store.filter('cid', combo.getValue());
						
						comboBuilding.clearValue();
                        comboBuilding.store.filter('cid', combo.getValue());
                        }}
                    }
					//store:['Population', 'Buildings', 'Contents', 'Occupants', 'Economic output'],
					
					 }
            ]
        },
		
		{
            xtype:'fieldset',
            //checkboxToggle:true,
            title: 'Select Loss Type',
            autoHeight:true,
			//labelWidth: 120, 
            defaults: {width: 200},
            defaultType: 'textfield',
            collapsed: false,
			//frame: false,
            	 items:[{
					xtype:'combo',
					fieldLabel:'Select',
					displayField:'loss',
					valueField:'id',
					id:'combo-loss',
                    store: new Ext.data.SimpleStore({
                         fields:['id', 'cid', 'loss']
                        ,data:LCombo.loss
                    }),
					resizable:true,
					minListWidth:200,
					triggerAction:'all',
					loadingText: "Loading...",
					emptyText: "Select asset type first...",
					forceSelection: true,
					editable: false,
					mode:'local',
                    lastQuery:''
					//store:['PAGER Empirical Global Vulnerability', 'ATC-13 Expert Opinion Vulnerability'],
					
					 }
            ]
        },
		
		{
            xtype:'fieldset',
            //checkboxToggle:true,
            title: 'Select Vulnerability Model',
            autoHeight:true,
			//labelWidth: 120, 
            defaults: {width: 200},
            defaultType: 'textfield',
            collapsed: false,
			//frame: false,
            	 items:[{
					xtype:'combo',
					fieldLabel:'Select',
					displayField:'vuln',
					valueField:'id',
					id:'combo-vuln',
                    store: new Ext.data.SimpleStore({
                         fields:['id', 'cid', 'vuln']
                        ,data:LCombo.vulnerability
                    }),
					resizable:true,
					minListWidth:200,
					triggerAction:'all',
					loadingText: "Loading...",
					emptyText: "Select loss type first...",
					forceSelection: true,
					editable: false,
					mode:'local',
                    lastQuery:''
					//store:['PAGER Empirical Global Vulnerability', 'ATC-13 Expert Opinion Vulnerability'],
					
					 }
            ]
        },
		
		{
            xtype:'fieldset',
            //checkboxToggle:true,
            title: 'Select Exposure Model',
            autoHeight:true,
			//labelWidth: 120, 
            defaults: {width: 200},
            defaultType: 'textfield',
            collapsed: false,
			//frame: false,
            	 items:[{
					xtype:'combo',
					fieldLabel:'Select',
					displayField:'expo',
					valueField:'id',
					id:'combo-expo',
                    store: new Ext.data.SimpleStore({
                        fields:['id', 'cid', 'expo'],
                        data:LCombo.expo
                    }),
                    mode:'local',
					resizable:true,
					minListWidth:200,
					triggerAction:'all',
					loadingText: "Loading...",
					emptyText: "Select vulnerability first...",
					forceSelection: true,
					editable: false,
                    lastQuery:''
					//store:['PAGER Empirical Global Vulnerability', 'ATC-13 Expert Opinion Vulnerability'],
					
					 }
            ]
        },
				
		{
            xtype:'fieldset',
            //checkboxToggle:true,
            title: 'Select Building Typology',
            autoHeight:true,
			//labelWidth: 120, 
            defaults: {width: 200},
            defaultType: 'textfield',
            collapsed: false,
			//frame: false,
            	 items:[{
					xtype:'combo',
					fieldLabel:'Select',
					displayField:'building',
					valueField:'id',
					id:'combo-building',
                    store: new Ext.data.SimpleStore({
                        fields:['id', 'cid', 'building'],
                        data:LCombo.building
                    }),
                    mode:'local',
					resizable:true,
					minListWidth:200,
					triggerAction:'all',
					loadingText: "Loading...",
					emptyText: "Select exposure first...",
					forceSelection: true,
					editable: false,
                    lastQuery:''
					//store:['PAGER Empirical Global Vulnerability', 'ATC-13 Expert Opinion Vulnerability'],
					
					 }
            ]
        },
		{
            xtype:'fieldset',
            //checkboxToggle:true,
            title: 'Select Output Type',
            autoHeight:true,
			//labelWidth: 120, 
            defaults: {width: 200},
            defaultType: 'textfield',
            collapsed: false,
			//frame: false,
            	 items:[{
					xtype:'combo',
					fieldLabel:'Select',
					resizable:true,
					minListWidth:200,
					//pageSize:5,
					// could be undefined as we use custom template
					displayField:'persLastName',
					// query all records on trigger click
					triggerAction:'all',
					// minimum characters to start the search
					minChars:2,
					// do not allow arbitrary values
					forceSelection:true,
					// otherwise we will not receive key events
					enableKeyEvents:true,
					emptyText: "Select an output type...",
					store:['Absolute Loss', 'Loss Ratio'],
					}
            ]
        },
		
		
		
		],	
		/*
        buttons: [{
            text: 'Submit',
			handler: function () {
				// when this button clicked, sumbit this form
				simpleForm2.getForm().submit({
					waitMsg: 'Saving...',		// Wait Message
					success: function () {		// When saving data success
						Ext.MessageBox.alert ('Message','Data has been saved');
						// clear the form
						simpleForm2.getForm().reset();
					},
					failure: function () {		// when saving data failed
						Ext.MessageBox.alert ('Message','Saving data failed');
					}
				});
			}
        }
		*/
		/*{
            text: 'Cancel',
			handler: function () {
				// when this button clicked, reset this form
				simpleForm2.getForm().reset();
			}
			
        }*/
	/*	
		]

*/
	
	});

	//form3 (maps tab)
 
	//Ext.QuickTips.init();

		var simpleForm3 = new Ext.FormPanel ({
		labelWidth: 40, 		// label settings here cascade unless overridden
		height: 500,
        url:'data/save-form.php',	// when this form submitted, data goes here
        frame: false,
        //title: 'Add Pirates Crew',
        bodyStyle:'padding:5px 5px 0',
        //width: 200,
       // defaults: {width: 200},
        defaultType: 'textfield',
		id: "simpleForm3",
		frame: false,
			items: [{
            xtype:'fieldset',
            //checkboxToggle:true,
            title: 'Select Hazard Model',
            autoHeight:true,
			//labelWidth: 120, 
            defaults: {width: 120},
            defaultType: 'textfield',
            collapsed: false,
			//frame: false,
            	 items:[{
					labelWidth: 120, 
					defaults: {width: 120},
					xtype:'combo',
					fieldLabel:'Select',
					resizable:true,
					minListWidth:120,
					//pageSize:5,
					// could be undefined as we use custom template
					displayField:'persLastName',
					// query all records on trigger click
					triggerAction:'all',
					// minimum characters to start the search
					minChars:2,
					// do not allow arbitrary values
					forceSelection:true,
					// otherwise we will not receive key events
					enableKeyEvents:true,
					store:['To be defined'],
					
					 }
            ]
        },
		
		{
            xtype:'fieldset',
            //checkboxToggle:true,
            title: 'Select Asset Type',
            autoHeight:true,
			//labelWidth: 120, 
            defaults: {width: 120},
            defaultType: 'textfield',
            collapsed: false,
			//frame: false,
            	 items:[{
					xtype:'combo',
					fieldLabel:'Select',
					resizable:true,
					minListWidth:120,
					//pageSize:5,
					// could be undefined as we use custom template
					displayField:'persLastName',
					// query all records on trigger click
					triggerAction:'all',
					// minimum characters to start the search
					minChars:2,
					// do not allow arbitrary values
					forceSelection:true,
					// otherwise we will not receive key events
					enableKeyEvents:true,
					store:['Population', 'Buildings', 'Contents', 'Occupants', 'Economic output'],
					
					 }
            ]
        },
		{
            xtype:'fieldset',
            //checkboxToggle:true,
            title: 'Select Loss Type',
            autoHeight:true,
			//labelWidth: 120, 
            defaults: {width: 130},
            defaultType: 'textfield',
            collapsed: false,
			//frame: false,
            	 items:[{
					xtype:'combo',
					fieldLabel:'Select',
					resizable:true,
					minListWidth:130,
					//pageSize:5,
					// could be undefined as we use custom template
					displayField:'persLastName',
					// query all records on trigger click
					triggerAction:'all',
					// minimum characters to start the search
					minChars:2,
					// do not allow arbitrary values
					forceSelection:true,
					// otherwise we will not receive key events
					enableKeyEvents:true,
					store:['Fatality'],
					
					 }
            ]
        },
		{
            xtype:'fieldset',
            //checkboxToggle:true,
            title: 'Select Vulnerability Model',
            autoHeight:true,
			//labelWidth: 120, 
            defaults: {width: 200},
            defaultType: 'textfield',
            collapsed: false,
			//frame: false,
            	 items:[{
					xtype:'combo',
					fieldLabel:'Select',
					resizable:true,
					minListWidth:200,
					//pageSize:5,
					// could be undefined as we use custom template
					displayField:'persLastName',
					// query all records on trigger click
					triggerAction:'all',
					// minimum characters to start the search
					minChars:2,
					// do not allow arbitrary values
					forceSelection:true,
					// otherwise we will not receive key events
					enableKeyEvents:true,
					store:['PAGER Empirical Global Vulnerability'],
					
					 }
            ]
        },
		{
            xtype:'fieldset',
            //checkboxToggle:true,
            title: 'Select Exposure Model',
            autoHeight:true,
			//labelWidth: 120, 
            defaults: {width: 200},
            defaultType: 'textfield',
            collapsed: false,
			//frame: false,
            	 items:[{
					xtype:'combo',
					fieldLabel:'Select',
					resizable:true,
					minListWidth:200,
					//pageSize:5,
					// could be undefined as we use custom template
					displayField:'persLastName',
					// query all records on trigger click
					triggerAction:'all',
					// minimum characters to start the search
					minChars:2,
					// do not allow arbitrary values
					forceSelection:true,
					// otherwise we will not receive key events
					enableKeyEvents:true,
					store:['LandScanTM 2008 Population', 'No exposure'],
					
					 }
            ]
        },
		{
            xtype:'fieldset',
            //checkboxToggle:true,
            title: 'Select Probability of Exceedance/50 yrs',
            autoHeight:true,
			//labelWidth: 120, 
            defaults: {width: 200},
            defaultType: 'textfield',
            collapsed: false,
			//frame: false,
            	 items:[{
					xtype:'combo',
					fieldLabel:'Select',
					resizable:true,
					minListWidth:200,
					//pageSize:5,
					// could be undefined as we use custom template
					displayField:'persLastName',
					// query all records on trigger click
					triggerAction:'all',
					// minimum characters to start the search
					minChars:2,
					// do not allow arbitrary values
					forceSelection:true,
					// otherwise we will not receive key events
					enableKeyEvents:true,
					store:['1%', '2%', '5%', '10%'],
					
					 }
            ]
        },
		{
            xtype:'fieldset',
            //checkboxToggle:true,
            title: 'Select Output Type',
            autoHeight:true,
			//labelWidth: 120, 
            defaults: {width: 200},
            defaultType: 'textfield',
            collapsed: false,
			//frame: false,
            	 items:[{
					xtype:'combo',
					fieldLabel:'Select',
					resizable:true,
					minListWidth:200,
					//pageSize:5,
					// could be undefined as we use custom template
					displayField:'persLastName',
					// query all records on trigger click
					triggerAction:'all',
					// minimum characters to start the search
					minChars:2,
					// do not allow arbitrary values
					forceSelection:true,
					// otherwise we will not receive key events
					enableKeyEvents:true,
					store:['Absolute Loss', 'Loss Ratio'],
					}
            ]
        },

		],	
		/*
        buttons: [{
            text: 'Submit',
			handler: function () {
				// when this button clicked, sumbit this form
				simpleForm3.getForm().submit({
					waitMsg: 'Saving...',		// Wait Message
					success: function () {		// When saving data success
						Ext.MessageBox.alert ('Message','Data has been saved');
						// clear the form
						simpleForm3.getForm().reset();
					},
					failure: function () {		// when saving data failed
						Ext.MessageBox.alert ('Message','Saving data failed');
					}
				});
			}
        }
		{
            text: 'Cancel',
			handler: function () {
				// when this button clicked, reset this form
				simpleForm.getForm().reset();
			}
			
        }
		
		]
		*/
	});

	//chart example


	var chart1 = new Ext.BoxComponent({

					    height: 75, // give north and south regions a height
						autoEl: {
							tag: 'div',
							html: '<img src="images/Albania_loss_curve.png" />',
						}
					});
//  var chart1 = new Ext.panel({
  //      html: '<img src="images/Albania_loss_curve.png" />',
        
        
    //});





	//Albania_loss_curve.png


	
//chart

		Ext.chart.Chart.CHART_URL = 'extjs/resources/charts.swf';

		var store = new Ext.data.JsonStore({
			fields:['name', 'LR'],
			data: [
				{name:'5.0', LR: 196},
				{name:'5.5', LR: 2530},
				{name:'6.0', LR: 8000},
				{name:'6.5', LR: 8310},
				{name:'7.0', LR: 35200}
			]
		});
		var chart = new Ext.chart.LineChart({
			//renderTo: Ext.getBody(),
			tbar: [
			'Conditional Loss Ratio Exceedance Matrix for Turkey (considering the hazard)',
			'->', 
			{iconCls:'icon-save'}, 
			{iconCls:'icon-pdf'}, 
			{iconCls:'icon-print'}
			],
			width: 300,
			height: 300,
			id: 'chart',
			store: store,
			xField: 'name',
			yAxis: new Ext.chart.NumericAxis({
				displayName: 'LR',
				labelRenderer: Ext.util.Format.numberRenderer('0,0')
			}),
			tipRenderer: function(chart, record, index, series) {
				if (series.yField == 'LR') {
					return Ext.util.Format.number(record.data.LR, '0,0') + ' LR ' + record.data.name;
				} if (series.yField == 'music') {
					return Ext.util.Format.number(record.data.music, '0,0') + ' CD\'s in ' + record.data.name;
				}
				else {
					return Ext.util.Format.number(record.data.movies, '0,0') + ' movies in ' + record.data.name;
				}
			},
			extraStyle: {
				padding: 10,
				animationEnabled: true,
				font: {
					name: 'Tahoma',
					color: 0x444444,
					size: 11
				},
				legend: {
					display: 'bottom'
				},
				dataTip: {
					padding: 5,
					border: {
						color: 0x99bbe8,
						size: 1
					},
					background: {
						color: 0xDAE7F6,
						alpha: .9
					},
					font: {
						name: 'Tahoma',
						color: 0x15428B,
						size: 10,
						bold: true
					}
				},
				xAxis: {
					color: 0x69aBc8,
					majorTicks: { color: 0x69aBc8, length: 4 },
					minorTicks: { color: 0x69aBc8, length: 2 },
					majorGridLines: { size: 1, color: 0xeeeeee }
				},
				yAxis: {
					color: 0x69aBc8,
					majorTicks: { color: 0x69aBc8, length: 1 },
					minorTicks: { color: 0x69aBc8, length: 1 },
					majorGridLines: { size: .0005, color: 0xdfe8f6 }
				}
			},
			series: [{
				type: 'line',
				displayName: '_',
				yField: 'movies',
				style: {
					color: 0xCCCCCC,
					image: 'img/star_red.png',
					mode: 'stretch'
				}
			}, {
				type: 'line',
				displayName: 'Example Chart',
				yField: 'LR',
				style: {
					color: 0xCCCCCC,
					image: 'img/star_green.png',
					mode: 'stretch'
				}
			}, {
				type: 'line',
				displayName: '_',
				yField: 'music',
				style: {
					color: 0xCCCCCC,
					image: 'img/star_blue.png',
					mode: 'stretch'
				}
			}]

		});


	//GE map

            // Google Earth panel
            var earthPanel = new Ext.ux.GEarthPanel({
                border: false,
                width: 700,
                height: 500,
                earthLayers: {
					LAYER_BORDERS:   false,
					LAYER_ROADS:     false,
					LAYER_BUILDINGS: false,
					LAYER_TERRAIN:   true,
                }
          
            });

            // Fly to Oslo
            earthPanel.on('earthLoaded', function(){
            earthPanel.findLocation('Port-au-prince');
            });	

	var map = new OpenLayers.Map("map");
	var map2 = new OpenLayers.Map("map2");
	var map3 = new OpenLayers.Map("map3");
	
	
	    var scaleStore = new GeoExt.data.ScaleStore({map: map});
    var zoomSelector = new Ext.form.ComboBox({
        store: scaleStore,
        emptyText: "Zoom Level",
        tpl: '<tpl for="."><div class="x-combo-list-item">1 : {[parseInt(values.scale)]}</div></tpl>',
        editable: false,
        triggerAction: 'all', // needed so that the combo box doesn't filter by its current content
        mode: 'local' // keep the combo box from forcing a lot of unneeded data refreshes
    });

    zoomSelector.on('select', 
        function(combo, record, index) {
            map.zoomTo(record.data.level);
        },
        this
    );     

    map.events.register('zoomend', this, function() {
        var scale = scaleStore.queryBy(function(record){
            return this.map.getZoom() == record.data.level;
        });

        if (scale.length > 0) {
            scale = scale.items[0];
            zoomSelector.setValue("1 : " + parseInt(scale.data.scale));
        } else {
            if (!zoomSelector.rendered) return;
            zoomSelector.clearValue();
        }
    });

	var mouse = map.addControl(new OpenLayers.Control.MousePosition());
	
var mapTools =  new Ext.Window({
                //title: "Preview: " + record.get("title"),
                id: 'mapTools',
                width: 512,
                height: 300,
                layout: "fit",
                items: [{
                    html: '<H2>Tools</H2><br><br><img src="images/tools.png">',
                }]
            });
            
          var slider = new Ext.Slider({
        			//renderTo: 'basic-slider',
        			width: 214,
        			fieldLabel:'Opacity',
        			title: 'Opacity',
        			increment: 10,
        			minValue: 0,
        			maxValue: 100
   				 });
            
	var MapTools = new Ext.FormPanel({
			labelWidth: 120, // label settings here cascade unless overridden
			//url:'save-form.php',
			//frame:true,
			//title: 'Select',
			bodyStyle:'padding:5px 5px 0',
			width: 350,
			defaults: {width: 230},
			defaultType: 'textfield',
	
			items: [{
				xtype:'combo',
				fieldLabel:'Layer',
				store:['Australia ALRM', 'Canada ALRM', 'East Asia ALRM', 'Europe ALRM', 'Mexico ALRM']
				},{
				xtype:'combo',
				fieldLabel:'Value Min',
				store:['0.000000494', '0.000126420', '0.000881512', '0.002022716', '0.004022253', '0.012056327', '0.021829660']
				},
				{
				xtype:'combo',
				fieldLabel:'Value Max',
				store:['0.000000494', '0.000126420', '0.000881512', '0.002022716', '0.004022253', '0.012056327', '0.021829660']
				},
				{
				xtype:'combo',
				fieldLabel:'Color',
				store:['Green to Red']
				},
				slider,

			],
	
/*			buttons: [{*/
/*				text: 'Export'*/
/*			},{*/
/*				text: 'Cancel'*/
/*			}]*/
		});

    var formMapTools = new Ext.Window({
    	id: "formMapTools",
        title: 'Filter Selection',
        collapsible: true,
        maximizable: true,
        closeAction: "hide",
        width: 410,
        height: 290,
        minWidth: 300,
        minHeight: 200,
        layout: 'fit',
        plain: true,
        bodyStyle: 'padding:5px;',
        buttonAlign: 'center',
        items: [MapTools],
        buttons: [{
            text: 'Select'
        },{
            text: 'Cancel'
        }]
    });


//here is the MAP
//here is the MAP
//here is the MAP
//here is the MAP

        var mapPanel = new GeoExt.MapPanel({
            region:'center',
            height: 400,
            width: 600,
            map: map,
			center: [3, 1.4],
			zoom: 2,
			tbar: [
				zoomSelector,
				{iconCls:'icon-info'},
				{
				xtype: 'tbbutton',
				hideBorders: true,
				//text: 'Modify Dashboard',
				iconCls:'icon-settings',
				listeners: {
					click: function() {
						Ext.getCmp("formMapTools").show();
					}
				}
				},
				
				'->', 
				{iconCls:'icon-save'}, 
				{iconCls:'icon-pdf'}, 
				{iconCls:'icon-kml'}, 
				{iconCls:'icon-print'}, 
				loginUsernameField("username1"), 
				loginPasswordField("password1")
				],
			items: [{
				xtype: "gx_zoomslider",
				vertical: true,
				height: 100,
				x: 16,
				y: 130,
				plugins: new GeoExt.ZoomSliderTip()
			}],
			layers: [

	
			new OpenLayers.Layer.WMS("Administration Level 2",
				"http://demo:gem2010DEMO@opengem.globalquakemodel.org/geoserver/wms", 			
			{layers: 	[
						//"nurc:Img_Sample",
					 	"GAUL Admin 2",
						"world_adm0"
						],
						 transparent: true,
						//format: "image/gif"
						}, 
						
						{
                    isBaseLayer: false,
					buffer: 0,
					//displayInLayerSwitcher: false,
                    visibility: false
                    
                }
            ),

			
			new OpenLayers.Layer.WMS("Administration Level 1",
				"http://demo:gem2010DEMO@opengem.globalquakemodel.org/geoserver/wms", 
			{layers: 	[
						//"nurc:Img_Sample",
					 	"GAUL Admin 1",
						"world_adm0"
						],
						 transparent: true,
						//format: "image/gif"
						}, 
						
						{
                    isBaseLayer: false,
					buffer: 0,
					//displayInLayerSwitcher: false,
                    visibility: false
                    
                }
            ),
			
			new OpenLayers.Layer.WMS("Administration Level 0",
				"http://demo:gem2010DEMO@opengem.globalquakemodel.org/geoserver/wms", 
				{layers: 	[
						//"nurc:Img_Sample",
					 	"world_adm0"
						],
						 transparent: true,
						//format: "image/gif"
						}, 
						
						{
                    isBaseLayer: false,
                    //displayInLayerSwitcher: false,
					buffer: 0,
					//displayInLayerSwitcher: false,
                    visibility: false
                    
                }
            ),


			new OpenLayers.Layer.WMS(
				"Bluemarble",
				"http://maps.opengeo.org/geowebcache/service/wms",
				{layers: "bluemarble"}, {
						isBaseLayer: true,
						buffer: 0,
						//visibility: false
				}
            ),

   


			new OpenLayers.Layer.WMS("NASA Global Mosaic",
                "http://wms.jpl.nasa.gov/wms.cgi", {
                    //extent: "-180,-90,180,90",
					srs: "epsg:4326",
					format: "image/png",
					layers: [
					"modis,global_mosaic",
					]
                }, {
                  	isBaseLayer: true,
					buffer: 0,
                    //visibility: false
                }
            ),


			new OpenLayers.Layer.WMS("OpenLayers WMS",
                "http://labs.metacarta.com/wms/vmap0", {
                    //extent: "-180,-90,180,90",
					srs: "epsg:4326",
					format: "image/png",
					layers: [
					"basic",
					]
                }, {
                  	isBaseLayer: true,
					buffer: 0,
                    //visibility: false
                }
            ),
            
           
            
			/*
			new OpenLayers.Layer.WMS("Demis",
                "http://www2.demis.nl/wms/wms.asp?wms=WorldMap", {
                    extent: "-180,-90,180,90",
					srs: "epsg:4326",
					format: "image/png",
					layers: [
					"Bathymetry",
					"Topography",
					"Waterbodies",
					"Coastlines",
					"Hillshading",
					"Cities",
					
					]
                }, {
                  	isBaseLayer: true,
					buffer: 0,
                    //visibility: false
                }
            ),
            */
        ],

    });
    
    
 //here is the MAP2

        var mapPanel2 = new GeoExt.MapPanel({
            region:'center',
            height: 400,
            width: 650,
            map: map2,
			center: [-96.67, 18.39],
			zoom: 4,
			layers: [

	
			new OpenLayers.Layer.WMS("Mexico",
				"http://demo:gem2010DEMO@opengem.globalquakemodel.org/geoserver/wms", 			
			{layers: 	[
						//"nurc:Img_Sample",
						"GEM1:LRM_AA_MEX_50_05"
						],
						 transparent: true,
						//format: "image/gif"
						}, 
						
						{
                    isBaseLayer: false,
					buffer: 0,
					//displayInLayerSwitcher: false,
                    visibility: true
                    
                }
            ),
            
            			new OpenLayers.Layer.WMS("central",
				"http://demo:gem2010DEMO@opengem.globalquakemodel.org/geoserver/wms", 			
			{layers: 	[
						//"nurc:Img_Sample",
						"GEM1:LRM_AA_CentralAmerica_50_05"
						],
						 transparent: true,
						//format: "image/gif"
						}, 
						
						{
                    isBaseLayer: false,
					buffer: 0,
					//displayInLayerSwitcher: false,
                    visibility: true
                    
                }
            ),


			new OpenLayers.Layer.WMS(
				"Bluemarble",
				"http://maps.opengeo.org/geowebcache/service/wms",
				{layers: "bluemarble"}, {
						isBaseLayer: true,
						buffer: 0,
						//visibility: false
				}
            ),

			new OpenLayers.Layer.WMS("OpenLayers WMS",
                "http://labs.metacarta.com/wms/vmap0", {
                    //extent: "-180,-90,180,90",
					srs: "epsg:4326",
					format: "image/png",
					layers: [
					"basic",
					]
                }, {
                  	isBaseLayer: true,
					buffer: 0,
                    //visibility: false
                }
            ),
            

        ],

    });
    
    
 //here is the MAP3

        var mapPanel3 = new GeoExt.MapPanel({
            region:'center',
            height: 400,
            width: 650,
            map: map3,
			center: [7.32, 47.47],
			zoom: 4,
			layers: [

	
			new OpenLayers.Layer.WMS("Mexico",
				"http://demo:gem2010DEMO@opengem.globalquakemodel.org/geoserver/wms", 			
			{layers: 	[
						//"nurc:Img_Sample",
						"GEM1:LRM_AA_Europe1_50_05"
						],
						 transparent: true,
						//format: "image/gif"
						}, 
						
						{
                    isBaseLayer: false,
					buffer: 0,
					//displayInLayerSwitcher: false,
                    visibility: true
                    
                }
            ),
            
			new OpenLayers.Layer.WMS("Mexico",
				"http://demo:gem2010DEMO@opengem.globalquakemodel.org/geoserver/wms", 			
			{layers: 	[
						//"nurc:Img_Sample",
						"GEM1:LRM_AA_Europe2_50_05"
						],
						 transparent: true,
						//format: "image/gif"
						}, 
						
						{
                    isBaseLayer: false,
					buffer: 0,
					//displayInLayerSwitcher: false,
                    visibility: true
                    
                }
            ),
            
           new OpenLayers.Layer.WMS("Mexico",
				"http://demo:gem2010DEMO@opengem.globalquakemodel.org/geoserver/wms", 			
			{layers: 	[
						//"nurc:Img_Sample",
						"GEM1:LRM_AA_Europe3_50_05"
						],
						 transparent: true,
						//format: "image/gif"
						}, 
						
						{
                    isBaseLayer: false,
					buffer: 0,
					//displayInLayerSwitcher: false,
                    visibility: true
                    
                }
            ),
			new OpenLayers.Layer.WMS("Mexico",
				"http://demo:gem2010DEMO@opengem.globalquakemodel.org/geoserver/wms", 			
			{layers: 	[
						//"nurc:Img_Sample",
						"GEM1:LRM_AA_Europe4_50_05"
						],
						 transparent: true,
						//format: "image/gif"
						}, 
						
						{
                    isBaseLayer: false,
					buffer: 0,
					//displayInLayerSwitcher: false,
                    visibility: true
                    
                }
            ),

			new OpenLayers.Layer.WMS(
				"Bluemarble",
				"http://maps.opengeo.org/geowebcache/service/wms",
				{layers: "bluemarble"}, {
						isBaseLayer: true,
						buffer: 0,
						//visibility: false
				}
            ),

			new OpenLayers.Layer.WMS("OpenLayers WMS",
                "http://labs.metacarta.com/wms/vmap0", {
                    //extent: "-180,-90,180,90",
					srs: "epsg:4326",
					format: "image/png",
					layers: [
					"basic",
					]
                }, {
                  	isBaseLayer: true,
					buffer: 0,
                    //visibility: false
                }
            ),
            

        ],

    });
       


 	
			var Europe = new OpenLayers.Layer.WMS("LRM Europe 01",
				"http://demo:gem2010DEMO@opengem.globalquakemodel.org/geoserver/wms", 			
			{layers: 	[
						//"nurc:Img_Sample",
					 	"LRM_AA_Europe1_50_01",
					 	"LRM_AA_Europe2_50_01",
					 	"LRM_AA_Europe3_50_01",
					 	"LRM_AA_Europe4_50_01"
						],
						 transparent: true,
						//format: "image/gif"
						}, 
						
						{
                    isBaseLayer: false,
                    id: Europe,
					buffer: 0,
					//displayInLayerSwitcher: false,
                    visibility: false
                    
                }
            );
            
            var groupLayer = new OpenLayers.Layer.WMS("US_West",
            "http://demo:gem2010DEMO@opengem.globalquakemodel.org/geoserver/wms",
            {layers: 	[
                    //"nurc:Img_Sample",
                    "US_West"
                    ],
                     transparent: true,
                    //format: "image/gif"
                    },

                    {
                isBaseLayer: false,
                buffer: 0,
                //displayInLayerSwitcher: true,
                visibility: true

            }
            );

		var overview = new OpenLayers.Control.OverviewMap();
		map.addControl(overview);

//TREE
	var layerRoot = new Ext.tree.TreeNode
	        ({
		    text: "All Layers",
		    expanded: true
		    });

		layerRoot.appendChild(new GeoExt.tree.BaseLayerContainer
		    ({
		    text: "Base Layers",
		    //layerStore: layerTree,
		    radio: true,
		    animate:true,
		    //enableDrop:true,
		    //enableDragDrop: true,
		    //dropConfig: {appendOnly:true},
		    expanded: true
		    })
        );

		layerRoot.appendChild(new GeoExt.tree.OverlayLayerContainer
		    ({
		    text: "Overlays",
		    //map: map,
		    expanded: true,
		    animate:true,
		    enableDD:true,
		    dropConfig: {appendOnly:true},
		    ddGroup: 'targetDrop',
		    //LayerLoader: groupLayer.Layers,
		    layer: "US_West",
		    //nodeType: "gx_layer",
		    })
        );


              /*
        layerRoot.appendChild(new GeoExt.tree.OverlayLayerContainer
		    ({
		    text: "Overlays",
		    map: map,
		    expanded: true
		    })
        );
          */

		var Tree1 = new Ext.tree.TreePanel
		    ({
		    //title: "Map Layers",
		    root: layerRoot,
		    autoHeight: true,
		    animate:true,
		    enableDD:true,
		    dropConfig: {appendOnly:true},
		    enableDD: true,
		    //collapsible: true,
		    //height: 200,
		    //expanded: true,
		    });
	
	
	
	
	/*
	 var Tree1 = new Ext.tree.TreePanel({
      //renderTo: 'ext-test',
      //frame:true,
      //title: 'Tree Panel',
      iconCls: 'icon-basket',
      collapsible:true,
      titleCollapse: true,
      style: 'padding-bottom: 5px',
      loader: new Ext.tree.TreeLoader(),
      rootVisible: false,
      lines: false,
      root: new Ext.tree.AsyncTreeNode({
        id: 'isroot',
        expanded: true,
        children: ["layerTree",
        {
          id:'layerTree',text:'Menu1',  leaf: false, children:
          [ {id:'layerTree',text: 'test', leaf: true } ]
        },
        { id:'2',text:'Menu2',leaf: true }
        ]
      })
    });
	*/
	
	
	
		
/*		 var googlet = new OpenLayers.Layer.Google
                        (
                          "Atlas", 

                          {
                            displayInLayerSwitcher: true,
                          }
                        );
		map.addLayer(googlet);
	*/	
		var click = new OpenLayers.Control.Click();
		map.addControl(click);
		click.activate();
		
	
	
	
	
	
	//TREE2
	var layerRoot2 = new Ext.tree.TreeNode
	        ({
		    text: "All Layers",
		    expanded: true
		    });

		layerRoot2.appendChild(new GeoExt.tree.BaseLayerContainer
		    ({
		    text: "Base Layers",
		    //layerStore: layerTree,
		    radio: true,
		    expanded: true
		    })
        );

		layerRoot2.appendChild(new GeoExt.tree.OverlayLayerContainer
		    ({
		    text: "Overlays",
		    //map: map,
		    expanded: true,
		    //LayerLoader: groupLayer.Layers,
		    layer: "US_West",
		    //nodeType: "gx_layer",
		    })
        );


              /*
        layerRoot.appendChild(new GeoExt.tree.OverlayLayerContainer
		    ({
		    text: "Overlays",
		    map: map,
		    expanded: true
		    })
        );
          */

		var Tree2 = new Ext.tree.TreePanel
		    ({
		    //title: "Map Layers",
		    root: layerRoot2,
		    autoHeight: true,
		    enableDD: true,
		    //collapsible: true,
		    //height: 200,
		    //expanded: true,
		    });
	
	
	
	
	/*
	 var Tree1 = new Ext.tree.TreePanel({
      //renderTo: 'ext-test',
      //frame:true,
      //title: 'Tree Panel',
      iconCls: 'icon-basket',
      collapsible:true,
      titleCollapse: true,
      style: 'padding-bottom: 5px',
      loader: new Ext.tree.TreeLoader(),
      rootVisible: false,
      lines: false,
      root: new Ext.tree.AsyncTreeNode({
        id: 'isroot',
        expanded: true,
        children: ["layerTree",
        {
          id:'layerTree',text:'Menu1',  leaf: false, children:
          [ {id:'layerTree',text: 'test', leaf: true } ]
        },
        { id:'2',text:'Menu2',leaf: true }
        ]
      })
    });
	*/
	
	
	
		
/*		 var googlet = new OpenLayers.Layer.Google
                        (
                          "Atlas", 

                          {
                            displayInLayerSwitcher: true,
                          }
                        );
		map.addLayer(googlet);
	*/	
		var click = new OpenLayers.Control.Click();
		map.addControl(click);
		click.activate();

/*
//Vextor Layer Store

    // create feature store, binding it to the vector layer
    vector_store = new GeoExt.data.FeatureStore({
        layer: vecLayer,
        fields: [
            {name: 'name', type: 'string'},
            {name: 'elevation', type: 'float'}
        ],
        proxy: new GeoExt.data.ProtocolProxy({
            protocol: new OpenLayers.Protocol.HTTP({
                url: "data/summits.json",
                format: new OpenLayers.Format.GeoJSON()
            })
        }),
        autoLoad: true
    });


*/


	

// WMS menue 

		 var menubar = new Ext.Toolbar({
			//renderTo: document.body,
			items:
				[{
				xtype: 'button',
				iconCls:'icon-node',
				text: 'Deterministic Scenario-Based',
					menu: {  
						items: [
							{
							text: 'Mean Loss Maps',
							iconCls:'icon-agrid',
							handler: gridHandler1,
							}, {
							text: 'Mean Loss Ratio Maps'
							}
						]
					},
					
				 },
				 {
                   xtype: 'tbspacer'
                  },
				   {
                    xtype: 'tbseparator'
                    },
                    {
                     xtype: 'tbspacer'
                    },
				 {
				xtype: 'button',
				iconCls:'icon-node',
				text: 'Probabilistic Scenario-Based',
				menu: [{
				    text: 'Loss Maps',
				    iconCls:'icon-agrid',                    
					menu: {        // <-- submenu by nested config object
						items: [
							{
							text: 'PE 1% 50 yrs',
							iconCls:'icon-agrid',
							handler: PELM01,
							}, {
							text: 'PE 2% 50 yrs',
							iconCls:'icon-agrid',
							handler: PELM02,
							}, {
							text: 'PE 5% 50 yrs',
							iconCls:'icon-agrid',
							handler: PELM05,
							}, {
							text: 'PE 10% 50 yrs',
							iconCls:'icon-agrid',
							handler: PELM10,
							}
						]
					},
	
					},
					{
			  		text: 'Loss Ratio Maps',
					iconCls:'icon-agrid',
					menu: {        // <-- submenu by nested config object
						items: [
							{
							text: 'PE 1% 50 yrs',
							iconCls:'icon-agrid',
							handler: PELRM01,
							}, {
							text: 'PE 2% 50 yrs',
							iconCls:'icon-agrid',
							handler: PELRM02,
							}, {
							text: 'PE 5% 50 yrs',
							iconCls:'icon-agrid',
							handler: PELRM05,
							}, {
							text: 'PE 10% 50 yrs',
							iconCls:'icon-agrid',
							handler: PELRM10,
							}
						]
					}
				},
				{
			   text: 'Mean Loss Maps',
			   iconCls:'icon-agrid',
			   handler: PEALM
				},
				{
			   text: 'Mean Loss Ratio Maps',
			   iconCls:'icon-agrid',
			   handler: PEALRM
				}
				
				]
			 }
		 ]
	  });
		

		/*
		var wmsAll = new Ext.Panel({
			//title: 'Layers',
			//html: "&nbsp;",
			//renderTo: document.body,
			//cls:"&nbsp;"
			//enableDragDrop: true,
			items:[tb],
			//autoScroll: true
		});
		*/

//WMS Store1 = Deterministic Scenarios, Loss Maps 

    // create a new WMS capabilities store
    store = new GeoExt.data.WMSCapabilitiesStore({
        url: "data/wms_store1.xml"
    });
    // load the store with records derived from the doc at the above url
    store.load();

	function gridHandler1() {
	//		alert('called');
    // create a grid to display records from the store
    var grid = new Ext.grid.GridPanel({
        title: "Deterministic Scenario-Based Loss Maps",
		id: "grid",
        store: store,
		stripeRows: true,
		//iconCls:'icon-agrid',
		//frame:true,
		collapsible:true,
		autoScroll: true,
		enableDragDrop: true,
		//collapsed: true,
		//ddGroup : 'mygrid-dd',  
		//ddText : 'Place this row.',
        columns: [
            {header: "Title", dataIndex: "title", sortable: true, width: 175},
            //{header: "Name", dataIndex: "name", sortable: true, width: 175},
            //{header: "Queryable", dataIndex: "queryable", sortable: true, width: 70},
            {id: "description", header: "Description", dataIndex: "abstract"}
        ],
		sm: new Ext.grid.RowSelectionModel({singleSelect:false}),
        autoExpandColumn: "description",
        tbar: [ 
			"Select a layer to add to the map, double click to preview.",
			'->', 
			//{iconCls:'icon-save'}, 
			//{iconCls:'icon-pdf'},		
			//{iconCls:'icon-print'},
			{
            text:"Add Layer",
			iconCls: 'icon-add',
			//displayInfo:true,
			prependButtons: true,
            handler: function() {
                var record = grid.getSelectionModel().getSelected();
								//alert(record);
                if(record) {
                    var copy = record.copy();
                    //copy.set("layer", record.get("layer"));
                    copy.get("layer").mergeNewParams({
                        format: "image/png",
                        transparent: "true"
                    });
                    mapPanel.layers.add(copy);
                    mapPanel.map.zoomToExtent(
                        OpenLayers.Bounds.fromArray(copy.get("llbbox"))
                    );
                }
            }
        },
		{handler: function() {
			Ext.getCmp("grid").hide();
			}, iconCls:'icon-delete'},
		{
            xtype: 'tbspacer'
          },
          		{
            xtype: 'tbspacer'
          },
          		{
            xtype: 'tbspacer'
          },
          		{
            xtype: 'tbspacer'
          },
          		{
            xtype: 'tbspacer'
          }
		],
        autoHeight: true,
        //width: 650,
        listeners: {
            rowdblclick: mapPreview
        }
    });
	
	Ext.getCmp('WMS').add(grid);
	Ext.getCmp('WMS').doLayout();
	};


    //WMS Store5 = Probabilistic Scenarios, Loss Maps for 1%

        // create a new WMS capabilities store
        store5 = new GeoExt.data.WMSCapabilitiesStore({
            url: "data/PELM01.xml"
        });
        
        // create a new WMS capabilities store
        store5a = new GeoExt.data.WMSCapabilitiesStore({
            url: "data/PELM01_alt.xml"
        });
        
        // load the store with records derived from the doc at the above url
        store5.load();
        
        store5a.load();

    	function PELM01() {
        // create a grid to display records from the store 5
        grid5 = new Ext.grid.GridPanel({
            title: "Loss maps for an investigation interval of 50 years for a probability of exceedance of 1%",
            store: store5,
    		id: "grid5",
    		stripeRows: true,
    		collapsible:true,
    		//iconCls:'icon-agrid',
    		//frame:true,
    		autoScroll: true,
    		enableDragDrop: true,
    		//collapsed: true,
    		//ddGroup : 'mygrid-dd',
    		//ddText : 'Place this row.',
            columns: [
                {header: "Title", dataIndex: "title", sortable: true, width: 175},
                //{header: "Name", dataIndex: "name", sortable: true, width: 175},
                //{header: "Queryable", dataIndex: "queryable", sortable: true, width: 70},
                {id: "description", header: "Description", dataIndex: "abstract"}
            ],
    		sm: new Ext.grid.RowSelectionModel
    		({singleSelect:false}),
            autoExpandColumn: "description",
            tbar: [
    			"Select a layer to add to the map, double click to preview.",
    			'->',
    			//{iconCls:'icon-save'},
    			//{iconCls:'icon-pdf'},
    			//{iconCls:'icon-print'},
    			{
                text: "Add Layer",
    			iconCls: 'icon-add',
    			//displayInfo:true,
    			prependButtons: true,
                handler: function() {
                    var record = grid5.getSelectionModel().getSelected();
    								//alert(record);
                    if(record) {
                        var copy = record.copy();
                        //copy.set("layer", record.get("layer"));
                        copy.get("layer").mergeNewParams({
                            format: "image/png",
                            transparent: "true"
                        });
                        mapPanel.layers.add(copy);
                        mapPanel.map.zoomToExtent(
                            OpenLayers.Bounds.fromArray(copy.get("llbbox"))
                        );
                    }
                }
            },
    		{handler: function() {
    			Ext.getCmp("grid5").hide();
    			}, iconCls:'icon-delete'},
    		  {
                xtype: 'tbspacer'
              },
              		{
                xtype: 'tbspacer'
              },
              		{
                xtype: 'tbspacer'
              },
              		{
                xtype: 'tbspacer'
              },
              		{
                xtype: 'tbspacer'
              }
    		],
            autoHeight: true,
            //width: 650,
            listeners: {
                rowdblclick: mapPreview
            }
        });
    	Ext.getCmp('WMS').add(grid5);
    	Ext.getCmp('WMS').doLayout();
    	};

        function mapPreview(grid5, index) {
            var record = grid5.getStore().getAt(index);
            var layer = record.get("layer").clone();


    		var border = new OpenLayers.Layer.WMS(
    			"Bluemarble",
    			"http://maps.opengeo.org/geowebcache/service/wms",
    			{
    			layers: ["bluemarble"],
    			transparent: true,
    			}
    		);

            var win = new Ext.Window({
                title: "Preview: " + record.get("title"),
                width: 512,
                height: 300,
                layout: "fit",
                items: [{
                    xtype: "gx_mappanel",
                    layers: [border, layer],
                    extent: record.get("llbbox")
                }]
            });
            win.show();
        };



    		
        

//WMS Store6 = Probabilistic Scenarios, Loss Maps for 1%

           // create a new WMS capabilities store
           store6 = new GeoExt.data.WMSCapabilitiesStore({
               url: "data/PELM02.xml"
           });
           // load the store with records derived from the doc at the above url
           store6.load();

        function PELM02() {
           // create a grid to display records from the store 6
           var grid6 = new Ext.grid.GridPanel({
               title: "Loss maps for an investigation interval of 50 years for a probability of exceedance of 2%",
               store: store6,
            id: "grid6",
            stripeRows: true,
            collapsible:true,
            //iconCls:'icon-agrid',
            //frame:true,
            autoScroll: true,
            enableDragDrop: true,
            //collapsed: true,
            //ddGroup : 'mygrid-dd',
            //ddText : 'Place this row.',
               columns: [
                   {header: "Title", dataIndex: "title", sortable: true, width: 175},
                   //{header: "Name", dataIndex: "name", sortable: true, width: 175},
                   //{header: "Queryable", dataIndex: "queryable", sortable: true, width: 70},
                   {id: "description", header: "Description", dataIndex: "abstract"}
               ],
            sm: new Ext.grid.RowSelectionModel
            ({singleSelect:false}),
               autoExpandColumn: "description",
               tbar: [
                "Select a layer to add to the map, double click to preview.",
                '->',
                //{iconCls:'icon-save'},
                //{iconCls:'icon-pdf'},
                //{iconCls:'icon-print'},
                {
                   text: "Add Layer",
                iconCls: 'icon-add',
                //displayInfo:true,
                prependButtons: true,
                   handler: function() {
                       var record = grid6.getSelectionModel().getSelected();
                                    //alert(record);
                       if(record) {
                           var copy = record.copy();
                           //copy.set("layer", record.get("layer"));
                           copy.get("layer").mergeNewParams({
                               format: "image/png",
                               transparent: "true"
                           });
                           mapPanel.layers.add(copy);
                           mapPanel.map.zoomToExtent(
                               OpenLayers.Bounds.fromArray(copy.get("llbbox"))
                           );
                       }
                   }
               },
            {handler: function() {
                Ext.getCmp("grid6").hide();
                }, iconCls:'icon-delete'},
              {
                   xtype: 'tbspacer'
                 },
                        {
                   xtype: 'tbspacer'
                 },
                        {
                   xtype: 'tbspacer'
                 },
                        {
                   xtype: 'tbspacer'
                 },
                        {
                   xtype: 'tbspacer'
                 }
            ],
               autoHeight: true,
               //width: 650,
               listeners: {
                   rowdblclick: mapPreview
               }
           });
        Ext.getCmp('WMS').add(grid6);
        Ext.getCmp('WMS').doLayout();
        };

           function mapPreview(grid6, index) {
               var record = grid6.getStore().getAt(index);
               var layer = record.get("layer").clone();


            var border = new OpenLayers.Layer.WMS(
                "Bluemarble",
                "http://maps.opengeo.org/geowebcache/service/wms",
                {
                layers: ["bluemarble"],
                transparent: true,
                }
            );

               var win = new Ext.Window({
                   title: "Preview: " + record.get("title"),
                   width: 512,
                   height: 300,
                   layout: "fit",
                   items: [{
                       xtype: "gx_mappanel",
                       layers: [border, layer],
                       extent: record.get("llbbox")
                   }]
               });
               win.show();
           };


//WMS Store7 = Probabilistic Scenarios, Loss Maps for 1%

           // create a new WMS capabilities store
           store7 = new GeoExt.data.WMSCapabilitiesStore({
               url: "data/PELM05.xml"
           });
           // load the store with records derived from the doc at the above url
           store7.load();

        function PELM05() {
           // create a grid to display records from the store 7
           var grid7 = new Ext.grid.GridPanel({
               title: "Loss maps for an investigation interval of 50 years for a probability of exceedance of 5%",
               store: store7,
            id: "grid7",
            stripeRows: true,
            collapsible:true,
            //iconCls:'icon-agrid',
            //frame:true,
            autoScroll: true,
            enableDragDrop: true,
            //collapsed: true,
            //ddGroup : 'mygrid-dd',
            //ddText : 'Place this row.',
               columns: [
                   {header: "Title", dataIndex: "title", sortable: true, width: 175},
                   //{header: "Name", dataIndex: "name", sortable: true, width: 175},
                   //{header: "Queryable", dataIndex: "queryable", sortable: true, width: 70},
                   {id: "description", header: "Description", dataIndex: "abstract"}
               ],
            sm: new Ext.grid.RowSelectionModel
            ({singleSelect:false}),
               autoExpandColumn: "description",
               tbar: [
                "Select a layer to add to the map, double click to preview.",
                '->',
                //{iconCls:'icon-save'},
                //{iconCls:'icon-pdf'},
                //{iconCls:'icon-print'},
                {
                   text: "Add Layer",
                iconCls: 'icon-add',
                //displayInfo:true,
                prependButtons: true,
                   handler: function() {
                       var record = grid7.getSelectionModel().getSelected();
                                    //alert(record);
                       if(record) {
                           var copy = record.copy();
                           //copy.set("layer", record.get("layer"));
                           copy.get("layer").mergeNewParams({
                               format: "image/png",
                               transparent: "true"
                           });
                           mapPanel.layers.add(copy);
                           mapPanel.map.zoomToExtent(
                               OpenLayers.Bounds.fromArray(copy.get("llbbox"))
                           );
                       }
                   }
               },
            {handler: function() {
                Ext.getCmp("grid7").hide();
                }, iconCls:'icon-delete'},
              {
                   xtype: 'tbspacer'
                 },
                        {
                   xtype: 'tbspacer'
                 },
                        {
                   xtype: 'tbspacer'
                 },
                        {
                   xtype: 'tbspacer'
                 },
                        {
                   xtype: 'tbspacer'
                 }
            ],
               autoHeight: true,
               //width: 650,
               listeners: {
                   rowdblclick: mapPreview
               }
           });
        Ext.getCmp('WMS').add(grid7);
        Ext.getCmp('WMS').doLayout();
        };

           function mapPreview(grid7, index) {
               var record = grid7.getStore().getAt(index);
               var layer = record.get("layer").clone();


            var border = new OpenLayers.Layer.WMS(
                "Bluemarble",
                "http://maps.opengeo.org/geowebcache/service/wms",
                {
                layers: ["bluemarble"],
                transparent: true,
                }
            );

               var win = new Ext.Window({
                   title: "Preview: " + record.get("title"),
                   width: 512,
                   height: 300,
                   layout: "fit",
                   items: [{
                       xtype: "gx_mappanel",
                       layers: [border, layer],
                       extent: record.get("llbbox")
                   }]
               });
               win.show();
           };



//WMS Store8 = Probabilistic Scenarios, Loss Maps for 1%

           // create a new WMS capabilities store
           store8 = new GeoExt.data.WMSCapabilitiesStore({
               url: "data/PELM10.xml"
           });
           // load the store with records derived from the doc at the above url
           store8.load();

        function PELM10() {
           // create a grid to display records from the store 8
           var grid8 = new Ext.grid.GridPanel({
               title: "Loss maps for an investigation interval of 50 years for a probability of exceedance of 10%",
               store: store8,
            id: "grid8",
            stripeRows: true,
            collapsible:true,
            //iconCls:'icon-agrid',
            //frame:true,
            autoScroll: true,
            enableDragDrop: true,
            //collapsed: true,
            //ddGroup : 'mygrid-dd',
            //ddText : 'Place this row.',
               columns: [
                   {header: "Title", dataIndex: "title", sortable: true, width: 175},
                   //{header: "Name", dataIndex: "name", sortable: true, width: 175},
                   //{header: "Queryable", dataIndex: "queryable", sortable: true, width: 70},
                   {id: "description", header: "Description", dataIndex: "abstract"}
               ],
            sm: new Ext.grid.RowSelectionModel
            ({singleSelect:false}),
               autoExpandColumn: "description",
               tbar: [
                "Select a layer to add to the map, double click to preview.",
                '->',
                //{iconCls:'icon-save'},
                //{iconCls:'icon-pdf'},
                //{iconCls:'icon-print'},
                {
                   text: "Add Layer",
                iconCls: 'icon-add',
                //displayInfo:true,
                prependButtons: true,
                   handler: function() {
                       var record = grid8.getSelectionModel().getSelected();
                                    //alert(record);
                       if(record) {
                           var copy = record.copy();
                           //copy.set("layer", record.get("layer"));
                           copy.get("layer").mergeNewParams({
                               format: "image/png",
                               transparent: "true"
                           });
                           mapPanel.layers.add(copy);
                           mapPanel.map.zoomToExtent(
                               OpenLayers.Bounds.fromArray(copy.get("llbbox"))
                           );
                       }
                   }
               },
            {handler: function() {
                Ext.getCmp("grid8").hide();
                }, iconCls:'icon-delete'},
              {
                   xtype: 'tbspacer'
                 },
                        {
                   xtype: 'tbspacer'
                 },
                        {
                   xtype: 'tbspacer'
                 },
                        {
                   xtype: 'tbspacer'
                 },
                        {
                   xtype: 'tbspacer'
                 }
            ],
               autoHeight: true,
               //width: 650,
               listeners: {
                   rowdblclick: mapPreview
               }
           });
        Ext.getCmp('WMS').add(grid8);
        Ext.getCmp('WMS').doLayout();
        };

           function mapPreview(grid8, index) {
               var record = grid8.getStore().getAt(index);
               var layer = record.get("layer").clone();


            var border = new OpenLayers.Layer.WMS(
                "Bluemarble",
                "http://maps.opengeo.org/geowebcache/service/wms",
                {
                layers: ["bluemarble"],
                transparent: true,
                }
            );

               var win = new Ext.Window({
                   title: "Preview: " + record.get("title"),
                   width: 512,
                   height: 300,
                   layout: "fit",
                   items: [{
                       xtype: "gx_mappanel",
                       layers: [border, layer],
                       extent: record.get("llbbox")
                   }]
               });
               win.show();
           };



//WMS Store9 = Probabilistic Scenarios, Loss Maps for 1%

    // create a new WMS capabilities store
    store9 = new GeoExt.data.WMSCapabilitiesStore({
        url: "data/PELRM01.xml"		
    });
    // load the store with records derived from the doc at the above url
    store9.load();
	
	function PELRM01() {
    // create a grid to display records from the store 9
    var grid9 = new Ext.grid.GridPanel({
        title: "Loss ratio maps for an investigation interval of 50 years for a probability of exceedance of 1%",
        store: store9,
		id: "grid9",
		stripeRows: true,
		collapsible:true,
		//iconCls:'icon-agrid',
		//frame:true,
		autoScroll: true,
		enableDragDrop: true,
		//collapsed: true,
		//ddGroup : 'mygrid-dd',  
		//ddText : 'Place this row.',
        columns: [
            {header: "Title", dataIndex: "title", sortable: true, width: 175},
            //{header: "Name", dataIndex: "name", sortable: true, width: 175},
            //{header: "Queryable", dataIndex: "queryable", sortable: true, width: 70},
            {id: "description", header: "Description", dataIndex: "abstract"}
        ],
		sm: new Ext.grid.RowSelectionModel
		({singleSelect:false}),
        autoExpandColumn: "description",
        tbar: [
			"Select a layer to add to the map, double click to preview.",
			'->',
			//{iconCls:'icon-save'}, 
			//{iconCls:'icon-pdf'},		
			//{iconCls:'icon-print'},
			{
            text: "Add Layer",
			iconCls: 'icon-add',
			//displayInfo:true,
			prependButtons: true,
            handler: function() {
                var record = grid9.getSelectionModel().getSelected();
								//alert(record);
                if(record) {
                    var copy = record.copy();
                    //copy.set("layer", record.get("layer"));
                    copy.get("layer").mergeNewParams({
                        format: "image/png",
                        transparent: "true"
                    });
                    mapPanel.layers.add(copy);
                    mapPanel.map.zoomToExtent(
                        OpenLayers.Bounds.fromArray(copy.get("llbbox"))
                    );
                }
            }
        },
		{handler: function() {
			Ext.getCmp("grid9").hide();
			}, iconCls:'icon-delete'},
		  {
            xtype: 'tbspacer'
          },
          		{
            xtype: 'tbspacer'
          },
          		{
            xtype: 'tbspacer'
          },
          		{
            xtype: 'tbspacer'
          },
          		{
            xtype: 'tbspacer'
          }
		],
        autoHeight: true,
        //width: 650,
        listeners: {
            rowdblclick: mapPreview
        }
    });
	Ext.getCmp('WMS').add(grid9);
	Ext.getCmp('WMS').doLayout();
	};

    function mapPreview(grid9, index) {
        var record = grid9.getStore().getAt(index);
        var layer = record.get("layer").clone();
		
		
		var border = new OpenLayers.Layer.WMS(
			"Bluemarble",
			"http://maps.opengeo.org/geowebcache/service/wms",
			{
			layers: ["bluemarble"],
			transparent: true,
			}
		);

        var win = new Ext.Window({
            title: "Preview: " + record.get("title"),
            width: 512,
            height: 300,
            layout: "fit",
            items: [{
                xtype: "gx_mappanel",
                layers: [border, layer],
                extent: record.get("llbbox")
            }]
        });
        win.show();
    };



//WMS Store10 = Probabilistic Scenarios, Loss Maps for 1%

    // create a new WMS capabilities store
    store10 = new GeoExt.data.WMSCapabilitiesStore({
        url: "data/PELRM02.xml"
    });
    // load the store with records derived from the doc at the above url
    store10.load();

	function PELRM02() {
    // create a grid to display records from the store 10
    var grid10 = new Ext.grid.GridPanel({
        title: "Loss ratio maps for an investigation interval of 50 years for a probability of exceedance of 2%",
        store: store10,
		id: "grid10",
		stripeRows: true,
		collapsible:true,
		//iconCls:'icon-agrid',
		//frame:true,
		autoScroll: true,
		enableDragDrop: true,
		//collapsed: true,
		//ddGroup : 'mygrid-dd',
		//ddText : 'Place this row.',
        columns: [
            {header: "Title", dataIndex: "title", sortable: true, width: 175},
            //{header: "Name", dataIndex: "name", sortable: true, width: 175},
            //{header: "Queryable", dataIndex: "queryable", sortable: true, width: 70},
            {id: "description", header: "Description", dataIndex: "abstract"}
        ],
		sm: new Ext.grid.RowSelectionModel
		({singleSelect:false}),
        autoExpandColumn: "description",
        tbar: [
			"Select a layer to add to the map, double click to preview.",
			'->',
			//{iconCls:'icon-save'},
			//{iconCls:'icon-pdf'},
			//{iconCls:'icon-print'},
			{
            text: "Add Layer",
			iconCls: 'icon-add',
			//displayInfo:true,
			prependButtons: true,
            handler: function() {
                var record = grid10.getSelectionModel().getSelected();
								//alert(record);
                if(record) {
                    var copy = record.copy();
                    //copy.set("layer", record.get("layer"));
                    copy.get("layer").mergeNewParams({
                        format: "image/png",
                        transparent: "true"
                    });
                    mapPanel.layers.add(copy);
                    mapPanel.map.zoomToExtent(
                        OpenLayers.Bounds.fromArray(copy.get("llbbox"))
                    );
                }
            }
        },
		{handler: function() {
			Ext.getCmp("grid10").hide();
			}, iconCls:'icon-delete'},
		  {
            xtype: 'tbspacer'
          },
          		{
            xtype: 'tbspacer'
          },
          		{
            xtype: 'tbspacer'
          },
          		{
            xtype: 'tbspacer'
          },
          		{
            xtype: 'tbspacer'
          }
		],
        autoHeight: true,
        //width: 650,
        listeners: {
            rowdblclick: mapPreview
        }
    });
	Ext.getCmp('WMS').add(grid10);
	Ext.getCmp('WMS').doLayout();
	};

    function mapPreview(grid10, index) {
        var record = grid10.getStore().getAt(index);
        var layer = record.get("layer").clone();


		var border = new OpenLayers.Layer.WMS(
			"Bluemarble",
			"http://maps.opengeo.org/geowebcache/service/wms",
			{
			layers: ["bluemarble"],
			transparent: true,
			}
		);

        var win = new Ext.Window({
            title: "Preview: " + record.get("title"),
            width: 512,
            height: 300,
            layout: "fit",
            items: [{
                xtype: "gx_mappanel",
                layers: [border, layer],
                extent: record.get("llbbox")
            }]
        });
        win.show();
    };



//WMS Store11 = Probabilistic Scenarios, Loss Maps for 1%

    // create a new WMS capabilities store
    store11 = new GeoExt.data.WMSCapabilitiesStore({
        url: "data/PELRM05.xml"
    });
    // load the store with records derived from the doc at the above url
    store11.load();

	function PELRM05() {
    // create a grid to display records from the store 11
    var grid11 = new Ext.grid.GridPanel({
        title: "Loss ratio maps for an investigation interval of 50 years for a probability of exceedance of 5%",
        store: store11,
		id: "grid11",
		stripeRows: true,
		collapsible:true,
		//iconCls:'icon-agrid',
		//frame:true,
		autoScroll: true,
		enableDragDrop: true,
		//collapsed: true,
		//ddGroup : 'mygrid-dd',
		//ddText : 'Place this row.',
        columns: [
            {header: "Title", dataIndex: "title", sortable: true, width: 175},
            //{header: "Name", dataIndex: "name", sortable: true, width: 175},
            //{header: "Queryable", dataIndex: "queryable", sortable: true, width: 70},
            {id: "description", header: "Description", dataIndex: "abstract"}
        ],
		sm: new Ext.grid.RowSelectionModel
		({singleSelect:false}),
        autoExpandColumn: "description",
        tbar: [
			"Select a layer to add to the map, double click to preview.",
			'->',
			//{iconCls:'icon-save'},
			//{iconCls:'icon-pdf'},
			//{iconCls:'icon-print'},
			{
            text: "Add Layer",
			iconCls: 'icon-add',
			//displayInfo:true,
			prependButtons: true,
            handler: function() {
                var record = grid11.getSelectionModel().getSelected();
								//alert(record);
                if(record) {
                    var copy = record.copy();
                    //copy.set("layer", record.get("layer"));
                    copy.get("layer").mergeNewParams({
                        format: "image/png",
                        transparent: "true"
                    });
                    mapPanel.layers.add(copy);
                    mapPanel.map.zoomToExtent(
                        OpenLayers.Bounds.fromArray(copy.get("llbbox"))
                    );
                }
            }
        },
		{handler: function() {
			Ext.getCmp("grid11").hide();
			}, iconCls:'icon-delete'},
		  {
            xtype: 'tbspacer'
          },
          		{
            xtype: 'tbspacer'
          },
          		{
            xtype: 'tbspacer'
          },
          		{
            xtype: 'tbspacer'
          },
          		{
            xtype: 'tbspacer'
          }
		],
        autoHeight: true,
        //width: 650,
        listeners: {
            rowdblclick: mapPreview
        }
    });
	Ext.getCmp('WMS').add(grid11);
	Ext.getCmp('WMS').doLayout();
	};

    function mapPreview(grid11, index) {
        var record = grid11.getStore().getAt(index);
        var layer = record.get("layer").clone();


		var border = new OpenLayers.Layer.WMS(
			"Bluemarble",
			"http://maps.opengeo.org/geowebcache/service/wms",
			{
			layers: ["bluemarble"],
			transparent: true,
			}
		);

        var win = new Ext.Window({
            title: "Preview: " + record.get("title"),
            width: 512,
            height: 300,
            layout: "fit",
            items: [{
                xtype: "gx_mappanel",
                layers: [border, layer],
                extent: record.get("llbbox")
            }]
        });
        win.show();
    };

	
//WMS Store12 = Probabilistic Scenarios, Loss Maps 10% 

    // create a new WMS capabilities store
    store12 = new GeoExt.data.WMSCapabilitiesStore({
        url: "data/PELRM10.xml"
    });
    // load the store with records derived from the doc at the above url
    store12.load();
	
	function PELRM10() {
    // create a grid to display records from the store
    var grid12 = new Ext.grid.GridPanel({
        title: "Loss ratio maps for an investigation interval of 50 years for a probability of exceedance of 10%",
        store: store12,
		id: "grid12",
		stripeRows: true,
		collapsible:true,
		//iconCls:'icon-agrid',
		//frame:true,
		autoScroll: true,
		enableDragDrop: true,
		//collapsed: true,
		//ddGroup : 'mygrid-dd',  
		//ddText : 'Place this row.',
        columns: [
            {header: "Title", dataIndex: "title", sortable: true, width: 175},
            //{header: "Name", dataIndex: "name", sortable: true, width: 175},
            //{header: "Queryable", dataIndex: "queryable", sortable: true, width: 70},
            {id: "description", header: "Description", dataIndex: "abstract"}
        ],
		sm: new Ext.grid.RowSelectionModel({singleSelect:false}),
        autoExpandColumn: "description",
        tbar: [
			"Select a layer to add to the map, double click to preview.",
			'->',
			//{iconCls:'icon-save'}, 
			//{iconCls:'icon-pdf'},		
			//{iconCls:'icon-print'},
			{
            text: "Add Layer",
			iconCls: 'icon-add',
			//displayInfo:true,
			prependButtons: true,
            handler: function() {
                var record = grid12.getSelectionModel().getSelected();
								//alert(record);
                if(record) {
                    var copy = record.copy();
                    //copy.set("layer", record.get("layer"));
                    copy.get("layer").mergeNewParams({
                        format: "image/png",
                        transparent: "true"
                    });
                    mapPanel.layers.add(copy);
                    mapPanel.map.zoomToExtent(
                        OpenLayers.Bounds.fromArray(copy.get("llbbox"))
                    );
                }
            }
        },
		{handler: function() {
			Ext.getCmp("grid12").hide();
			}, iconCls:'icon-delete'},
		  {
            xtype: 'tbspacer'
          },
          		{
            xtype: 'tbspacer'
          },
          		{
            xtype: 'tbspacer'
          },
          		{
            xtype: 'tbspacer'
          },
          		{
            xtype: 'tbspacer'
          }
		],
        autoHeight: true,
        //width: 650,
        listeners: {
            rowdblclick: mapPreview
        }
    });
	Ext.getCmp('WMS').add(grid12);
	Ext.getCmp('WMS').doLayout();
	};

    function mapPreview(grid12, index) {
        var record = grid12.getStore().getAt(index);
        var layer = record.get("layer").clone();
		
		
		var border = new OpenLayers.Layer.WMS(
			"Bluemarble",
			"http://maps.opengeo.org/geowebcache/service/wms",
			{
			layers: ["bluemarble"],
			transparent: true,
			}
		);

        var win = new Ext.Window({
            title: "Preview: " + record.get("title"),
            width: 512,
            height: 300,
            layout: "fit",
            items: [{
                xtype: "gx_mappanel",
                layers: [border, layer],
                extent: record.get("llbbox")
            }]
        });
        win.show();
    };




//WMS Store13 = Probabilistic Scenarios, Loss Maps 10%

    // create a new WMS capabilities store
    store13 = new GeoExt.data.WMSCapabilitiesStore({
        url: "data/PEALM.xml"
    });
    // load the store with records derived from the doc at the above url
    store13.load();

	function PEALM() {
    // create a grid to display records from the store
    var grid13 = new Ext.grid.GridPanel({
        title: "Mean loss maps for an investigation interval of 50 years",
        store: store13,
		id: "grid13",
		stripeRows: true,
		collapsible:true,
		//iconCls:'icon-agrid',
		//frame:true,
		autoScroll: true,
		enableDragDrop: true,
		//collapsed: true,
		//ddGroup : 'mygrid-dd',
		//ddText : 'Place this row.',
        columns: [
            {header: "Title", dataIndex: "title", sortable: true, width: 175},
            //{header: "Name", dataIndex: "name", sortable: true, width: 175},
            //{header: "Queryable", dataIndex: "queryable", sortable: true, width: 70},
            {id: "description", header: "Description", dataIndex: "abstract"}
        ],
		sm: new Ext.grid.RowSelectionModel({singleSelect:false}),
        autoExpandColumn: "description",
        tbar: [
			"Select a layer to add to the map, double click to preview.",
			'->',
			//{iconCls:'icon-save'},
			//{iconCls:'icon-pdf'},
			//{iconCls:'icon-print'},
			{
            text: "Add Layer",
			iconCls: 'icon-add',
			//displayInfo:true,
			prependButtons: true,
            handler: function() {
                var record = grid13.getSelectionModel().getSelected();
								//alert(record);
                if(record) {
                    var copy = record.copy();
                    //copy.set("layer", record.get("layer"));
                    copy.get("layer").mergeNewParams({
                        format: "image/png",
                        transparent: "true"
                    });
                    mapPanel.layers.add(copy);
                    mapPanel.map.zoomToExtent(
                        OpenLayers.Bounds.fromArray(copy.get("llbbox"))
                    );
                }
            }
        },
		{handler: function() {
			Ext.getCmp("grid13").hide();
			}, iconCls:'icon-delete'},
		  {
            xtype: 'tbspacer'
          },
          		{
            xtype: 'tbspacer'
          },
          		{
            xtype: 'tbspacer'
          },
          		{
            xtype: 'tbspacer'
          },
          		{
            xtype: 'tbspacer'
          }
		],
        autoHeight: true,
        //width: 650,
        listeners: {
            rowdblclick: mapPreview
        }
    });
	Ext.getCmp('WMS').add(grid13);
	Ext.getCmp('WMS').doLayout();
	};

    function mapPreview(grid13, index) {
        var record = grid13.getStore().getAt(index);
        var layer = record.get("layer").clone();


		var border = new OpenLayers.Layer.WMS(
			"Bluemarble",
			"http://maps.opengeo.org/geowebcache/service/wms",
			{
			layers: ["bluemarble"],
			transparent: true,
			}
		);

        var win = new Ext.Window({
            title: "Preview: " + record.get("title"),
            width: 512,
            height: 300,
            layout: "fit",
            items: [{
                xtype: "gx_mappanel",
                layers: [border, layer],
                extent: record.get("llbbox")
            }]
        });
        win.show();
    };




//WMS Store14 = Probabilistic Scenarios, Loss Maps 10%

         // create a new WMS capabilities store
         store14 = new GeoExt.data.WMSCapabilitiesStore({
             url: "data/PEALRM.xml"
         });
         // load the store with records derived from the doc at the above url
         store14.load();

     	function PEALRM() {
         // create a grid to display records from the store
         var grid14 = new Ext.grid.GridPanel({
             title: "Mean loss ratio maps for an investigation interval of 50 years",
             store: store14,
     		id: "grid14",
     		stripeRows: true,
     		collapsible:true,
     		//iconCls:'icon-agrid',
     		//frame:true,
     		autoScroll: true,
     		enableDragDrop: true,
     		//collapsed: true,
     		//ddGroup : 'mygrid-dd',
     		//ddText : 'Place this row.',
             columns: [
                 {header: "Title", dataIndex: "title", sortable: true, width: 175},
                 //{header: "Name", dataIndex: "name", sortable: true, width: 175},
                 //{header: "Queryable", dataIndex: "queryable", sortable: true, width: 70},
                 {id: "description", header: "Description", dataIndex: "abstract"}
             ],
     		sm: new Ext.grid.RowSelectionModel({singleSelect:false}),
             autoExpandColumn: "description",
             tbar: [
     			"Select a featuer to add to the map, double click to preview.",
     			'->',
     			//{iconCls:'icon-save'},
     			//{iconCls:'icon-pdf'},
     			//{iconCls:'icon-print'},
     			{
                 text: "Add Layer",
     			iconCls: 'icon-add',
     			//displayInfo:true,
     			prependButtons: true,
                 handler: function() {
                     var record = grid14.getSelectionModel().getSelected();
     								//alert(record);
                     if(record) {
                         var copy = record.copy();
                         //copy.set("layer", record.get("layer"));
                         copy.get("layer").mergeNewParams({
                             format: "image/png",
                             transparent: "true"
                         });
                         mapPanel.layers.add(copy);
                         mapPanel.map.zoomToExtent(
                             OpenLayers.Bounds.fromArray(copy.get("llbbox"))
                         );
                     }
                 }
             },
     		{handler: function() {
     			Ext.getCmp("grid14").hide();
     			}, iconCls:'icon-delete'},
     		  {
                 xtype: 'tbspacer'
               },
               		{
                 xtype: 'tbspacer'
               },
               		{
                 xtype: 'tbspacer'
               },
               		{
                 xtype: 'tbspacer'
               },
               		{
                 xtype: 'tbspacer'
               }
     		],
             autoHeight: true,
             //width: 650,
             listeners: {
                 rowdblclick: mapPreview
             }
         });
     	Ext.getCmp('WMS').add(grid14);
     	Ext.getCmp('WMS').doLayout();
     	};

         function mapPreview(grid14, index) {
             var record = grid14.getStore().getAt(index);
             var layer = record.get("layer").clone();


     		var border = new OpenLayers.Layer.WMS(
     			"Bluemarble",
     			"http://maps.opengeo.org/geowebcache/service/wms",
     			{
     			layers: ["bluemarble"],
     			transparent: true,
     			}
     		);

             var win = new Ext.Window({
                 title: "Preview: " + record.get("title"),
                 width: 512,
                 height: 300,
                 layout: "fit",
                 items: [{
                     xtype: "gx_mappanel",
                     layers: [border, layer],
                     extent: record.get("llbbox")
                 }]
             });
             win.show();
         };

//My page Home		

 
 // NOTE Portlets definition

var item4a = function(t)
{
	return new Ext.ux.Portlet({
		//tools : t,
		id : "item4a",
		collapsible: false,
		title : "Professional Network",
		html: '<br><p style="font-family:helvetica, Georgia, serif; font-size:12px;"><b>Welcome to the OpenGEM Portal!</b><br><br>Take a look at some pre-calculated GEM maps that will provide you with an insight in earthquake risk on a location chosen by you, by selecting maps from the layer tree on the left and viewing them via the 2D or 3D tabs above.<br><br>If you want to create your own maps, plots or tables of seismic risk- related output you will need to sign up and become a member of the GEM community.<br><br>Members can add their own data related to hazard, exposure, vulnerability, social and /or economic impact. This data can then be added to the OpenGEM calculation engine to run analysis and create new maps, plots or tables of your choice.<br><br>Your data and outputs can be published and shared with other members and might even been selected to be featured on the home page of this platform.<br><br>Sign in here</p>',
	});
}

var item4b = function(t)
{
	return new Ext.ux.Portlet({
		//tools : t,
		id : "item4b",
		collapsible: false,
		title : "Featured Map",
		items: [mapPanel2],
		//html : "<img src=\"images/Map3.png\">"
	});
}

var item4c = function(t)
{
	return new Ext.ux.Portlet({
		//tools : t,
		id : "Members",
		collapsible: false,
		title : "members",
		html : "<img src=\"images/members.png\">"
	});
}



//all portlets

var portlets3 = new Array()

var restoreTools = [ {
				id : "minimize",
				handler : function(event, toolEl, panel, tc) {
					Ext.getCmp("portalTest3").removeAll(true);
					Ext.getCmp("portalTest3").add(allPortlets());
					Ext.getCmp("portalTest3").doLayout();
				}
} ];

var tools3 = [{
        id: "maximize",
				handler : function(event, toolEl, panel, tc) {
					Ext.getCmp("portalTest3").removeAll(true);
					Ext.getCmp("portalTest3").add( {
						columnWidth : 0.99,
							style : "padding:10px 0 10px 10px",
							items : [ portlets[panel.id].call(this, restoreTools) ]
						});
						
						Ext.getCmp("portalTest3").doLayout();
					}
    	},{
        id:'close',
        handler: function(e, target, panel){
            panel.ownerCt.remove(panel, true);
     		}
}];

var allPortlets = function()
{
	return [{
			columnWidth : .20,
      style: "padding:10px 0 10px 10px",
      items:[item4a(tools3)]
  },{
			columnWidth : .57,
      style: "padding:10px 0 10px 10px",
      items:[item4b(tools3)]
  }, 
  {
			columnWidth : .22,
      style: "padding:10px 0 10px 10px",
      items:[item4c(tools3)]
  }
];
}
  

portlets3["item4a"] = item4a;
portlets3["item4b"] = item4b;
portlets3["item4c"] = item4c;

var portalTest3 = new Ext.Panel({
        layout:'border',
        tbar: [
			'->',  
			loginUsernameField("username3"), 
			loginPasswordField("password3")
			],
        items:[{
						id: "portalTest3",
            xtype:'portal',
            region:'center',
            margins:'5 5 5 5',			
            items: allPortlets()
            
            /*
             * Uncomment this block to test handling of the drop event. You could use this
             * to save portlet position state for example. The event arg e is the custom 
             * event defined in Ext.ux.Portal.DropZone.
             */
//            ,listeners: {
//                'drop': function(e){
//                    Ext.Msg.alert('Portlet Dropped', e.panel.title + '<br />Column: ' + 
//                        e.columnIndex + '<br />Position: ' + e.position);
//                }
//            }
        }]
    });

           
//My page HOME END 
            
//My page BASIC		


//my page basic form

 var form_map1 = new Ext.FormPanel({
        labelWidth: 90,
        border:false,
        width: 400,

        items: {
            xtype:'tabpanel',
            activeTab: 0,
            defaults:{autoHeight:true, bodyStyle:'padding:10px'}, 
            items:[{
                title:'Metadata',
                layout:'form',
                defaults: {width: 230},
                defaultType: 'textfield',

                items: [{
                    fieldLabel: 'Author',
                    name: 'author',
                    allowBlank:false,
                    //value: 'Jack'
                },{
                    fieldLabel: 'Description',
                    name: 'description'
                    //value: 'Slocum'
                },{
                    fieldLabel: 'Group',
                    name: 'group'
                    //value: 'Ext JS'
                }, {
                    fieldLabel: 'Title',
                    name: 'title'
                    //vtype:'email'
                },
                {
                    fieldLabel: 'Select location',
                    name: 'location'
                },
                 {
                    fieldLabel: 'Key words',
                    name: 'words'
                },
                {
                    xtype: 'textarea',
					fieldLabel: 'Abstract',
                    name: 'abstract'
                }]
            },{
                title:'Map options',
                layout:'form',
                defaults: {width: 230},
                defaultType: 'textfield',

                items: [{
					xtype: 'combo',
					store: ['Type 1', 'Type 2', 'Type 3' ],
					//plugins: [ Ext.ux.FieldReplicator, Ext.ux.FieldLabeler ],
					fieldLabel: 'Map type',
					name: 'map_type',
					emptyText: "Select a map type...",
				},{
					xtype: 'combo',
					store: ['Type 1', 'Type 2', 'Type 3' ],
					//plugins: [ Ext.ux.FieldReplicator, Ext.ux.FieldLabeler ],
					fieldLabel: 'Data Input',
					name: 'data',
					emptyText: "Select a data Input...",
                },{
					xtype: 'checkbox',
					fieldLabel: 'Output types',
					boxLabel: 'Maps',
					name: 'box_maps',
				}, {
					xtype: 'checkbox',
					fieldLabel: '',
					labelSeparator: '',
					boxLabel: 'Tables',
					name: 'box_tables'
				}, {
					xtype: 'checkbox',
					//checked: true,
					fieldLabel: '',
					labelSeparator: '',
					boxLabel: 'Curves',
					name: 'box_curves'
				},
				{
					xtype: 'checkbox',
					fieldLabel: 'Privacy settings',
					boxLabel: 'Anyone from group can view',
					name: 'anyone_group_view',
					checked: true,
				}, {
					xtype: 'checkbox',
					fieldLabel: '',
					labelSeparator: '',
					boxLabel: 'Anyone from group can edit',
					name: 'anyone_group_edit',
					checked: true,
				}, {
					xtype: 'checkbox',
					fieldLabel: '',
					labelSeparator: '',
					boxLabel: 'Anyone from group can copy',
					name: 'anyone_group_copy',
					checked: true,
				},{
					xtype: 'checkbox',
					fieldLabel: '',
					boxLabel: 'Anyone can view',
					name: 'anyone_view',
					checked: true,
				},{
					xtype: 'checkbox',
					//checked: true,
					fieldLabel: '',
					labelSeparator: '',
					boxLabel: 'Anyone can edit',
					name: 'anyone_edit',
					checked: true,
				}, {
					xtype: 'checkbox',
					//checked: true,
					fieldLabel: '',
					labelSeparator: '',
					boxLabel: 'Anyone can copy',
					name: 'anyone_copy',
					checked: true,
				}]
            }]
        },

/*        buttons: [{*/
/*            text: 'Save'*/
/*        },{*/
/*            text: 'Cancel'*/
/*        }]*/
    });

//form Window				 

    var formMap1 = new Ext.Window({
    	id: "formMap1",
        title: 'Add Data',
        collapsible: true,
        maximizable: true,
        closeAction: "hide",
        width: 750,
        height: 500,
        minWidth: 300,
        minHeight: 200,
        layout: 'fit',
        plain: true,
        bodyStyle: 'padding:5px;',
        buttonAlign: 'center',
        items: [form_map1],
        buttons: [{
            text: 'Send'
        },{
            text: 'Cancel'
        }]
    });
    

		 

		 

//My page BASIC
//my page frames	


  
				 
//my page basic Toolbar
	var toolbar_basic =  new Ext.Toolbar({
		//renderTo: document.body,
		items: [
		{
		xtype: 'tbbutton',
		hideBorders: true,
		text: 'Modify Dashboard',
		iconCls:'icon-alter',
/*		listeners: {*/
/*			click: function() {*/
/*				Ext.getCmp("formExport").show();*/
/*			}*/
/*		}*/
		},
/*		'->',*/
		{
		hideBorders: true,
		iconCls:'icon-search',
		},
		new Ext.form.ComboBox({
        store: store5a,
        displayField:'title',
        typeAhead: false,
        loadingText: 'Searching...',
        width: 150,
        pageSize:10,
        hideTrigger:true,
        //tpl: resultTpl,
        onSelect: function(record){ // override default onSelect to do redirect
            window.location =
                String.format('http://extjs.com/forum/showthread.php?t={0}&p={1}', record.data.topicId, record.id);
        }
    })
		]
	  });
 
  
  
  
 // NOTE Portlets definition

var item3a = function(t)
{
	return new Ext.ux.Portlet({
		tools : t,
		id : "item3a",
		title : "My Profile",
		html : "<img src=\"images/Andrea1.png\">"
	});
}

var item3g = function(t)
{
	return new Ext.ux.Portlet({
		tools : t,
		id : "item3g",
		title : "My Groups",
		html : "<img src=\"images/groups.png\">"
	});
}

var item3h = function(t)
{
	return new Ext.ux.Portlet({
		tools : t,
		id : "item3h",
		title : "My Friends",
		html : "<img src=\"images/friends.png\">"
	});
}

var item3b = function(t)
{
	return new Ext.ux.Portlet({
		tools : t,
		id : "item3b",
		title : "GEM Risk Map",
		tbar: [
			{iconCls:'icon-search',},
			{
                    xtype:'textfield',
                    fieldLabel: 'Model ID',
                    name: 'model',
                    anchor:'95%',
                    value: 'Search location'
                },
                ],
                items: [mapPanel3]
		//html : "<img src=\"images/Map2.png\">"
	});
}
var item3c = function(t)
{
	return new Ext.ux.Portlet({
		tools : t,
		id : "item3c",
		title : "Todays Seismic Risk Fact",
		html : "<p>The biggest earthquakes in history was<br/> on May 22 1960: A magnitude-9.5<br/> earthquake in southern Chile.</p>"
	});
}

var item3d = function(t)
{
	return new Ext.ux.Portlet({
		tools : t,
		id : "item3d",
		title : "Understanding Your Risk",
		html : "<img src=\"images/Color.png\"><br><p>The probability your house will suffer<br/> structural damage in the next 50 years<br/> is comparable to...</p>"
	});
}

var item3e = function(t)
{
	return new Ext.ux.Portlet({
		tools : t,
		id : "item3e",
		title : "RSS Feed: USGS M5+ Earthquakes",
		html : "<img src=\"images/RSS1.png\">"
	});
}

var item3f = function(t)
{
	return new Ext.ux.Portlet({
		tools : t,
		id : "item3f",
		autoScroll: true,
		height: 250,
		title : "My Discussion Threads",
		html : "<img src=\"images/thread.png\">"
	});
}



//all portlets

var portlets2 = new Array()

var restoreTools2 = [ {
				id : "minimize",
				handler : function(event, toolEl, panel, tc) {
					Ext.getCmp("portalTest2").removeAll(true);
					Ext.getCmp("portalTest2").add(allPortlets2());
					Ext.getCmp("portalTest2").doLayout();
				}
} ];

var tools2 = [{
        id: "maximize",
				handler : function(event, toolEl, panel, tc) {
					Ext.getCmp("portalTest2").removeAll(true);
					Ext.getCmp("portalTest2").add( {
						columnWidth : 0.99,
							style : "padding:10px 0 10px 10px",
							items : [ portlets2[panel.id].call(this, restoreTools2) ]
						});
						
						Ext.getCmp("portalTest2").doLayout();
					}
    	},{
        id:'close',
        handler: function(e, target, panel){
            panel.ownerCt.remove(panel, true);
     		}
}];

var allPortlets2 = function()
{
	return [{
			columnWidth : .20,
      style: "padding:10px 0 10px 10px",
      items:[item3a(tools2), item3g(tools2), item3h(tools2)]
  },{
			columnWidth : .57,
      style: "padding:10px 0 10px 10px",
      items:[item3b(tools2), item3f(tools2)]
  }, 
  {
			columnWidth : .22,
      style: "padding:10px 0 10px 10px",
      items:[item3d(tools2), item3c(tools2), item3e(tools2)]
  }
];
}
  

portlets2["item3a"] = item3a;
portlets2["item3b"] = item3b;
portlets2["item3h"] = item3h;
portlets2["item3g"] = item3g;
portlets2["item3c"] = item3c;

var portalTest2 = new Ext.Panel({
        layout:'border',
        tbar: [ 
                    			
                    			//'You are in basic mode',
                    			{
			hideBorders: true,
			iconCls:'icon-search',
			},
			new Ext.form.ComboBox({
			store: store5a,
			displayField:'title',
			typeAhead: false,
			loadingText: 'Searching...',
			width: 120,
			pageSize:10,
			hideTrigger:true,
			//tpl: resultTpl,
			onSelect: function(record){ // override default onSelect to do redirect
				window.location =
					String.format('http://extjs.com/forum/showthread.php?t={0}&p={1}', record.data.topicId, record.id);
				}
			}),
			{
            xtype: 'tbspacer'
          },
          {
            xtype: 'tbspacer'
          },
			{
			xtype: 'tbbutton',
			hideBorders: true,
			text: 'Modify Dashboard',
			iconCls:'icon-alter',
	/*		listeners: {*/
	/*			click: function() {*/
	/*				Ext.getCmp("formExport").show();*/
	/*			}*/
	/*		}*/
			},
			'->',  
			loginUsernameField("username4"), 
			loginPasswordField("password4")
			],
        items:[{
						id: "portalTest2",
            xtype:'portal',
            region:'center',
            margins:'5 5 5 5',			
            items: allPortlets2()
            
            /*
             * Uncomment this block to test handling of the drop event. You could use this
             * to save portlet position state for example. The event arg e is the custom 
             * event defined in Ext.ux.Portal.DropZone.
             */
//            ,listeners: {
//                'drop': function(e){
//                    Ext.Msg.alert('Portlet Dropped', e.panel.title + '<br />Column: ' + 
//                        e.columnIndex + '<br />Position: ' + e.position);
//                }
//            }
        }]
    });

           
//My page BASIC END          
//My page Power		

// my page power temp my data, store and grid2
 var oColModels = new Ext.grid.ColumnModel([
                {header:'ID',dataIndex:'id', width: 25, sortable: true},
                {id: "date", header:' Title',dataIndex:'title', sortable: true},
                {header:' Author',dataIndex:'author', width: 100, sortable: true},
                {header:'Data Type',dataIndex:'Data Type', width: 70, sortable: true},
                {header:'Privacy',dataIndex:'privacy', width: 60, sortable: true},
                {header:' Date Modified',dataIndex:'date', width: 80, sortable: true,},
                {header:'Data Type',dataIndex:'File Type', sortable: true},
                
        ]);
        
        // Defines the data structure  , That is, the database field  
        var aFields = ["id","title","author","Data Type", "privacy", "date", "File Type"];
        
        // A data set  
        var aDatas = [
						["1","European GEM1 Hazard Curves", "Marco Pagani", "Hazard", "Open", "1/05/2010", "ASCII file"],
						["2","Global Population Distribution (LandScan 2008)", "Oak Ridge National Laboratory","Exposure", "Private","1/06/2010", "Binary Raster file"],
						["3","PAGER Global Fatality Model", "Kishor Jaiswal","Vulnerability", "Open", "1/05/2010", "ASCII file"],

				 ];     
        
        // Data storage  
        var oStore = new Ext.data.SimpleStore({
                fields : aFields,
                data : aDatas
        });


//grid for Hazard data (Area) form

         // Defines the data structure  , That is, the database field  
        var FieldsArea = ["id","title","author", "privacy", "date"];
        
        // A data set  
        var DatasAria = [
						["1","Area1", "Marco Pagani", "Open", "1/05/2010"],
						["2","Area2", "Marco Pagani", "Private","1/06/2010"],
						["3","Area3", "Marco Pagani", "Open", "1/05/2010"],

				 ];     
        
        // Data storage  
        var StoreArea = new Ext.data.SimpleStore({ 
                fields : FieldsArea,
                data : DatasAria
        });
        
        var areaGrid = new Ext.grid.EditorGridPanel({
			store: StoreArea,
			columns: [
					{header:'ID', dataIndex:'id', width: 25, sortable: true, editor: new Ext.form.TextField({
				allowBlank: false
				})},
					{id: "date", header:' Title',dataIndex:'title', sortable: true, editor: new Ext.form.TextField({
				allowBlank: false
				})},
					{header:' Author',dataIndex:'author', width: 130, sortable: true, editor: new Ext.form.TextField({
				allowBlank: false
				})},
					{header:'Privacy',dataIndex:'privacy', width: 60, sortable: true, editor: new Ext.form.TextField({
				allowBlank: false
				})},
					{header:' Date Modified',dataIndex:'date', width: 80, sortable: true, editor: new Ext.form.TextField({
				allowBlank: false
				})},
					
			],
			stripeRows: true,
			//autoExpandColumn: 'Title',
			height: 130,
			width: 397,
			buttons: [{
							text: 'Add',
							bodyStyle:'padding:5px 5px 0',
								},{
							text: 'Edit',
							bodyStyle:'padding:5px 5px 0',
								},{
							text: 'Delete',
							bodyStyle:'padding:5px 5px 0',
								 }],
			//title: 'Array Grid',
			// config options for stateful behavior
			//stateful: true,
			//stateId: 'grid'        
    });
    
        
//grid for Hazard data (Area3 mag and depth) form

         // Defines the data structure  , That is, the database field  
        var FieldsArea1 = ["id","mag","depth"];
        
        // A data set  
        var DatasAria1 = [
						["1","6.4", "55"],
						["2","5.8", "38"],
						["3","7.1", "81"],
				 ];     
        
        // Data storage  
        var StoreArea1 = new Ext.data.SimpleStore({ 
                fields : FieldsArea1,
                data : DatasAria1
        });
        
        var areaGrid1 = new Ext.grid.EditorGridPanel({
        store: StoreArea1,
        columns: [
                {header:'ID',dataIndex:'id', width: 25, sortable: true, editor: new Ext.form.TextField({
				allowBlank: false
				})},
                {id: "date", header:' Mag',dataIndex:'mag', width: 65, sortable: true, editor: new Ext.form.TextField({
				allowBlank: false
				})},
                {header:'Depth [km]',dataIndex:'depth', width: 65, sortable: true, editor: new Ext.form.TextField({
				allowBlank: false
				})},               
        ],
        stripeRows: true,
        //autoExpandColumn: 'Title',
        height: 130,
        width: 158,
        buttons: [{
			text: 'Save',
			bodyStyle:'padding:5px 5px 0',
				}]
         
    });

//grid for Hazard data (Area2) form

         // Defines the data structure  , That is, the database field  
        var FieldsArea2 = ["id","mag","rate"];
        
        // A data set  
        var DatasAria2 = [
						["1","6.4", "7.01"],
						["2","5.8", "7.01"],
						["3","6.1", "7.01"],

				 ];     
        
        // Data storage  
        var StoreArea2 = new Ext.data.SimpleStore({ 
                fields : FieldsArea2,
                data : DatasAria2
        });
        
        var areaGrid2 = new Ext.grid.EditorGridPanel({
        store: StoreArea2,
        columns: [
                {header:'ID',dataIndex:'id', width: 25, sortable: true, editor: new Ext.form.TextField({
				allowBlank: false
				})},
                {id: "date", header:' Mag',dataIndex:'mag', width: 65, sortable: true, editor: new Ext.form.TextField({
				allowBlank: false
				})},
                {header:' Rate [event/yr]',dataIndex:'rate', width: 90, sortable: true, editor: new Ext.form.TextField({
				allowBlank: false
				})},
        ],
        stripeRows: true,
        //autoExpandColumn: 'Title',
        height: 130,
        width: 200,
        buttons: [{
			text: 'Save',
			bodyStyle:'padding:5px 5px 0',
				}]
         
    });



//grid for Hazard data (Fault simple) form

         // Defines the data structure  , That is, the database field  
        var FieldsArea3 = ["id","title","author", "privacy", "date"];
        
        // A data set  
        var DatasAria3 = [
						["1","Fault1", "Marco Pagani", "Open", "1/05/2010"],
						["2","Fault2", "Oak Ridge National Laboratory", "Private","1/06/2010"],
						["3","Fault3", "Kishor Jaiswal", "Open", "1/05/2010"],

				 ];     
        
        // Data storage  
        var StoreArea3 = new Ext.data.SimpleStore({ 
                fields : FieldsArea3,
                data : DatasAria3
        });
        
        var areaGrid3 = new Ext.grid.EditorGridPanel({
        store: StoreArea3,
        columns: [
                {header:'ID',dataIndex:'id', width: 25, sortable: true, editor: new Ext.form.TextField({
				allowBlank: false
				})},
                {id: "date", header:' Title',dataIndex:'title', sortable: true, editor: new Ext.form.TextField({
				allowBlank: false
				})},
                {header:' Author',dataIndex:'author', width: 130, sortable: true, editor: new Ext.form.TextField({
				allowBlank: false
				})},
                {header:'Privacy',dataIndex:'privacy', width: 60, sortable: true, editor: new Ext.form.TextField({
				allowBlank: false
				})},
                {header:' Date Modified',dataIndex:'date', width: 80, sortable: true, editor: new Ext.form.TextField({
				allowBlank: false
				})},
                
        ],
        stripeRows: true,
        //autoExpandColumn: 'Title',
        height: 130,
        width: 400,
        buttons: [{
           				text: 'Add',
           				bodyStyle:'padding:5px 5px 0',
        					},{
            			text: 'Edit',
            			bodyStyle:'padding:5px 5px 0',
       				 		},{
            			text: 'Delete',
            			bodyStyle:'padding:5px 5px 0',
       						 }],
        //title: 'Array Grid',
        // config options for stateful behavior
        //stateful: true,
        //stateId: 'grid'        
    });





//grid for Hazard data (Fault simple2) form

         // Defines the data structure  , That is, the database field  
        var FieldsArea4 = ["id","mag","rate"];
        
        // A data set  
        var DatasAria4 = [
						["1","5.5", "7.01"],
						["2","6.3", "7.01"],
						["3","6.1", "7.01"],
				 ];     
        
        // Data storage  
        var StoreArea4 = new Ext.data.SimpleStore({ 
                fields : FieldsArea4,
                data : DatasAria4
        });
        
        var areaGrid4 = new Ext.grid.EditorGridPanel({
        store: StoreArea4,
        columns: [
                {header:'ID',dataIndex:'id', width: 25, sortable: true, editor: new Ext.form.TextField({
				allowBlank: false
				})},
                {id: "date", header:' Mag',dataIndex:'mag', width: 65, sortable: true, editor: new Ext.form.TextField({
				allowBlank: false
				})},
                {header:' Rate [events/yr]',dataIndex:'rate', width: 90, sortable: true, editor: new Ext.form.TextField({
				allowBlank: false
				})},
  
                
        ],
        stripeRows: true,
        //autoExpandColumn: 'Title',
        height: 130,
        width: 200,
        buttons: [{
			text: 'Save',
			bodyStyle:'padding:5px 5px 0',
				}]
         
    });
    
    //grid for Hazard data (Area3 polygon vertex) form

         // Defines the data structure  , That is, the database field  
        var FieldsArea5 = ["id","lat","long"];
        
        // A data set  
        var DatasAria5 = [
						["1","41.013", "143.434"],
						["2","40.123", "142.137"],
				 ];     
        
        // Data storage  
        var StoreArea5 = new Ext.data.SimpleStore({ 
                fields : FieldsArea5,
                data : DatasAria5
        });
        
        var areaGrid5 = new Ext.grid.EditorGridPanel({
        store: StoreArea5,
        columns: [
                {header:'ID',dataIndex:'id', width: 25, sortable: true, editor: new Ext.form.TextField({
				allowBlank: false
				})},
                {id: "date", header:'Lat [DD]',dataIndex:'lat', width: 65, sortable: true, editor: new Ext.form.TextField({
				allowBlank: false
				})},
                {header:'Long [DD]',dataIndex:'long', width: 65, sortable: true, editor: new Ext.form.TextField({
				allowBlank: false
				})},               
        ],
        stripeRows: true,
        //autoExpandColumn: 'Title',
        height: 110,
        width: 158,
        buttons: [{
			text: 'Save',
			bodyStyle:'padding:5px 5px 0',
				}]
         
    });
 
//my page power add hazard data form

    var formAddDataForm = new Ext.FormPanel({
        //labelAlign: 'top',
        hideBorders: true,
        //title: 'Inner Tabs',
        bodyStyle:'padding:5px',
        autoScroll: true,
        width: 900,
        Height: 730,
        items: {
            xtype:'tabpanel',
            activeTab: 0,
            defaults:{autoHeight:true, bodyStyle:'padding:10px'}, 
            items:[
            {
                title:'Earthquake Rupture Forecast',
                layout:'form',
                defaults: { width: 230 },
                defaultType: 'textfield',
                items: [{
									fieldLabel: 'Select the file to upload',
									inputType: "file"
								}],
								buttonAlign: "center",
								buttons: [{
									text: 'Upload'
								}]
            },{
                title:'Event Set(s)',
                layout:'form',
                defaults: { width: 230 },
                defaultType: 'textfield',
                items: [{
									fieldLabel: 'Select the file to upload',
									inputType: "file"
								}],
								buttonAlign: "center",
								buttons: [{
									text: 'Upload'
								}]
            },{
                title:'Shake Map(s)',
                layout:'form',
                defaults: { width: 230 },
                defaultType: 'textfield',
                items: [{
									fieldLabel: 'Select the file to upload',
									inputType: "file"
								}],
								buttonAlign: "center",
								buttons: [{
									text: 'Upload'
								}]
            },{
                title:'Hazard Map(s)',
                layout:'form',
                defaults: { width: 230 },
                defaultType: 'textfield',
                items: [{
									fieldLabel: 'Select the file to upload',
									inputType: "file"
								}],
								buttonAlign: "center",
								buttons: [{
									text: 'Upload'
								}]
            },{
                title:'Hazard Curve(s)',
                layout:'form',
                defaults: { width: 230 },
                defaultType: 'textfield',
                items: [{
									fieldLabel: 'Select the file to upload',
									inputType: "file"
								}],
								buttonAlign: "center",
								buttons: [{
									text: 'Upload'
								}]
            },]
        }


/*        buttons: [{*/
/*            text: 'Save'*/
/*        },{*/
/*            text: 'Cancel'*/
/*        }]*/
    });
    
    
    //my page power add hazard data form

    var formAddDataForm2 = new Ext.FormPanel({
        //labelAlign: 'top',
        hideBorders: true,
        //title: 'Inner Tabs',
        bodyStyle:'padding:5px',
        autoScroll: true,
        width: 900,
        Height: 730, 
            items:[
            {
                //title:'PSHA Input Model',
                layout:'form',
                items: [{
            layout:'column',
            border:false,
            labelAlign: 'top',
            items:[{
                columnWidth:.5,
                layout: 'form',
                border:false,
                items: [{
                    xtype:'textfield',
                    fieldLabel: 'Model ID',
                    name: 'model',
                    anchor:'95%',
                    value: 'mdl00001'
                }, {
                    xtype:'textfield',
                    fieldLabel: 'Input model name',
                    name: 'input',
                    anchor:'95%',
                    value: 'USGS - NSHMP United States'
                }]
            },{
                columnWidth:.5,
                layout: 'form',
                border:false,
                items: [{
                    xtype:'textfield',
                    fieldLabel: 'Author',
                    name: 'author',
                    anchor:'95%',
                    value: 'Unknown'
                },{
                    xtype:'textfield',
                    fieldLabel: 'Title',
                    name: 'title',
                    anchor:'95%',
                    value: 'Example'
                }]
            }]
        },{
            xtype:'tabpanel',
            plain:true,
            activeTab: 0,
            hideBorders: true,
            height:500,
            width:700,
            /*
              By turning off deferred rendering we are guaranteeing that the
              form fields within tabs that are not activated will still be rendered.
              This is often important when creating multi-tabbed forms.
            */
            deferredRender: false,
            defaults:{bodyStyle:'padding:10px'},
            items:[{
                title:'Area',
                layout:'form',
                autoScroll:true,
                hideBorders: true,
                Height: 50,
                //defaults: {width: 230},
                //defaultType: 'textfield',
                items: [areaGrid,
                {
                    fieldLabel: 'ID',
                    xtype: 'textfield',
                    name: 'id5',
                    allowBlank:false,
                    value: 'src0001'
                },{
                    fieldLabel: 'Name',
                    xtype: 'textfield',
                    name: 'name5',
                    value: 'San Andreas'
                },{
                    fieldLabel: 'Description',
                    xtype: 'textfield',
                    name: 'des5',
                    value: 'Very Important'
                },{
                    fieldLabel: 'Ave. hypocentral depth [km]',
                    xtype: 'textfield',
                    name: 'des5',
                    value: '10'
                },{
                    html: '<br><H2>Depth to the top of Rupture</H2><br>',
                },
                areaGrid1,
                {
                html: '<br><img src="images/MapArea.png"><br>',
                },
                {
                html: '<br><H2>Polygon vertex</H2><br>',
                },
                areaGrid5,
                {
                    html: '<br><H2>Magnitude-frequency distribution for focal mechanism</H2><br>',
                },
                 
//third embedded tabs
				
				{
					xtype:'tabpanel',
					plain:true,
					activeTab: 0,
					hideBorders: true,
					height:180,
					/*
					  By turning off deferred rendering we are guaranteeing that the
					  form fields within tabs that are not activated will still be rendered.
					  This is often important when creating multi-tabbed forms.
					*/
					deferredRender: false,
					defaults:{bodyStyle:'padding:10px'},
					items:[{
						title:'One',
						layout:'form',
						defaultType: 'textfield',
 						items: [areaGrid2]
					},           
					 
					{
						cls:'x-plain',
						title:'Two',
						layout:'fit',
						/*items: {*/
		/*                    xtype:'textarea',*/
		/*                    id:'bio2',*/
		/*                    flex: 1,*/
		/*                    width: 695,*/
		/*       				height: 500,*/
		/*                    fieldLabel:'Biography',*/
		/*                    hideLabel: true,*/
		/*                }*/
					},
					{
						cls:'x-plain',
						title:'Three',
						layout:'fit',
						/*items: {*/
		/*                    xtype:'textarea',*/
		/*                    id:'bio2',*/
		/*                    flex: 1,*/
		/*                    width: 695,*/
		/*       				height: 500,*/
		/*                    fieldLabel:'Biography',*/
		/*                    hideLabel: true,*/
		/*                }*/
					},

           ]
        },
        {
                    xtype:'textfield',
                    fieldLabel: 'Width',
                    name: 'model',
                    width: 130,
                    labelWidth: 50,
                    //anchor:'95%',
                    //value: 'mdl00001'
                },{
                    xtype:'textfield',
                    fieldLabel: 'Rake [&deg]',
                    name: 'model',
                    width: 130,
                    labelWidth: 50,
                    //anchor:'95%',
                    //value: 'mdl00001'
                }, 
                {
                    xtype:'textfield',
                    fieldLabel: 'Strike [&deg]',
                    name: 'model',
                    width: 130,
                    labelWidth: 50,
                    //anchor:'95%',
                    //value: 'mdl00001'
                },{
                    xtype:'textfield',
                    fieldLabel: 'Dip [&deg]',
                    name: 'model',
                    width: 130,
                    labelWidth: 50,
                    //anchor:'95%',
                    //value: 'mdl00001'
                },
        

                ]
            },{
                title:'Grid',
                layout:'form',
                defaults: {width: 230},
                defaultType: 'textfield',
               /* items: [{*/
/*                    fieldLabel: 'Home',*/
/*                    name: 'home',*/
/*                    value: '(888) 555-1212'*/
/*                },{*/
/*                    fieldLabel: 'Business',*/
/*                    name: 'business'*/
/*                },{*/
/*                    fieldLabel: 'Mobile',*/
/*                    name: 'mobile'*/
/*                },{*/
/*                    fieldLabel: 'Fax',*/
/*                    name: 'fax'*/
/*                }]*/
            },           
            {
                title:'Fault Simple',
                layout:'form',
                autoScroll:true,
                hideBorders: true,
                Height: 50,
                //defaults: {width: 230},
                //defaultType: 'textfield',
                 items:[{
                //title:'Area',
                layout:'form',
                autoScroll:true,
                hideBorders: true,
                Height: 50,
                //defaults: {width: 230},
                //defaultType: 'textfield',
                items: [areaGrid3,
                {
                    fieldLabel: 'ID',
                    xtype: 'textfield',
                    name: 'id5',
                    allowBlank:false,
                    value: 'src0001'
                },{
                    fieldLabel: 'Name',
                    xtype: 'textfield',
                    name: 'name5',
                    value: 'San Andreas'
                },{
                    fieldLabel: 'Description',
                    xtype: 'textfield',
                    name: 'des5',
                    value: 'Very Important'
                },
                {
                    fieldLabel: 'Rake',
                    xtype: 'textfield',
                    name: 'des5',
                    value: '90'
                },
                {
                    fieldLabel: 'Dip',
                    xtype: 'textfield',
                    name: 'des5',
                    value: '70'
                },
                {
					xtype: 'checkbox',
					//fieldLabel: 'Rupture floating flag',
					boxLabel: 'Rupture floating flag',
					name: 'box_maps',
				}, 
                {
                html: '<br><img src="images/MapArea.png"><br>',
                },{
                    html: '<br><H2>Magnitude-frequency distribution</H2><br>',
                    
                },
                 
//third embedded tabs
				
				{
					xtype:'tabpanel',
					plain:true,
					activeTab: 0,
					hideBorders: true,
					height:360,
					/*
					  By turning off deferred rendering we are guaranteeing that the
					  form fields within tabs that are not activated will still be rendered.
					  This is often important when creating multi-tabbed forms.
					*/
					deferredRender: false,
					defaults:{bodyStyle:'padding:10px'},
					items:[{
						title:'One',
						layout:'form',
						defaultType: 'textfield',
 						items: [areaGrid4]
					},           
					 
					{
						cls:'x-plain',
						title:'Two',
						layout:'fit',
						/*items: {*/
		/*                    xtype:'textarea',*/
		/*                    id:'bio2',*/
		/*                    flex: 1,*/
		/*                    width: 695,*/
		/*       				height: 500,*/
		/*                    fieldLabel:'Biography',*/
		/*                    hideLabel: true,*/
		/*                }*/
					},
					{
						cls:'x-plain',
						title:'Three',
						layout:'fit',
						/*items: {*/
		/*                    xtype:'textarea',*/
		/*                    id:'bio2',*/
		/*                    flex: 1,*/
		/*                    width: 695,*/
		/*       				height: 500,*/
		/*                    fieldLabel:'Biography',*/
		/*                    hideLabel: true,*/
		/*                }*/
					},
           ]
        }

                ]
            },

            ]  
            },
            {
                cls:'x-plain',
                title:'Fault Complex',
                layout:'fit',
                /*items: {*/
/*                    xtype:'textarea',*/
/*                    id:'bio2',*/
/*                    flex: 1,*/
/*                    width: 695,*/
/*       				height: 500,*/
/*                    fieldLabel:'Biography',*/
/*                    hideLabel: true,*/
/*                }*/
            },
            {
                cls:'x-plain',
                title:'Logic Tree',
                layout:'fit',
                /*items: {*/
/*                    xtype:'textarea',*/
/*                    id:'bio2',*/
/*                    flex: 1,*/
/*                    width: 695,*/
/*       				height: 500,*/
/*                    fieldLabel:'Biography',*/
/*                    hideLabel: true,*/
/*                }*/
            },

            
            ] 
        }]
            },
            ]
        


/*        buttons: [{*/
/*            text: 'Save'*/
/*        },{*/
/*            text: 'Cancel'*/
/*        }]*/
    });
    
    




//my page power add data form Window				 

    var formAddData = new Ext.Window({
    	id: "formAddData",
        title: 'Add Hazard Data',
        collapsible: true,
        maximizable: true,
        closeAction: "hide",
        width: 590,
        height: 300,
        minWidth: 300,
        minHeight: 200,
        layout: 'fit',
        plain: true,
        bodyStyle: 'padding:5px;',
        buttonAlign: 'center',
        items: [formAddDataForm],
        buttons: [{
            text: 'Send'
        },{
            text: 'Cancel'
        }]
    });
    
    //my page power add data form Window				 

    var formAddData2 = new Ext.Window({
    	id: "formAddData2",
        title: 'PSHA Input Model',
        collapsible: true,
        maximizable: true,
        closeAction: "hide",
        width: 750,
        height: 600,
        minWidth: 300,
        minHeight: 200,
        layout: 'fit',
        plain: true,
        bodyStyle: 'padding:5px;',
        buttonAlign: 'center',
        items: [formAddDataForm2],
        buttons: [{
            text: 'Send'
        },{
            text: 'Cancel'
        }]
    });

//my page power data form

 var form_data2 = new Ext.FormPanel({
        labelWidth: 90,
        border:false,
        width: 400,

        items: {
            xtype:'tabpanel',
            activeTab: 0,
            defaults:{autoHeight:true, bodyStyle:'padding:10px'}, 
            items:[{
                title:'Metadata',
                layout:'form',
                defaults: {width: 230},
                defaultType: 'textfield',

                items: [{
                    fieldLabel: 'Author',
                    name: 'author',
                    allowBlank:false,
                    //value: 'Jack'
                },{
                    fieldLabel: 'Description',
                    name: 'description'
                    //value: 'Slocum'
                },{
                    fieldLabel: 'Group',
                    name: 'group'
                    //value: 'Ext JS'
                }, {
                    fieldLabel: 'Title',
                    name: 'title'
                    //vtype:'email'
                },
                {
                    fieldLabel: 'Select location',
                    name: 'location'
                },
                 {
                    fieldLabel: 'Key words',
                    name: 'words'
                },
                {
                    xtype: 'textarea',
					fieldLabel: 'Abstract',
                    name: 'abstract'
                }]
            },{
                title:'Map options',
                layout:'form',
                defaults: {width: 230},
                defaultType: 'textfield',

                items: [{
					xtype: 'combo',
					store: ['Type 1', 'Type 2', 'Type 3' ],
					//plugins: [ Ext.ux.FieldReplicator, Ext.ux.FieldLabeler ],
					fieldLabel: 'Map type',
					name: 'map_type',
					emptyText: "Select a map type...",
				},{
					xtype: 'combo',
					store: ['Type 1', 'Type 2', 'Type 3' ],
					//plugins: [ Ext.ux.FieldReplicator, Ext.ux.FieldLabeler ],
					fieldLabel: 'Data Input',
					name: 'data',
					emptyText: "Select a data Input...",
                },{
					xtype: 'checkbox',
					fieldLabel: 'Output types',
					boxLabel: 'Maps',
					name: 'box_maps',
				}, {
					xtype: 'checkbox',
					fieldLabel: '',
					labelSeparator: '',
					boxLabel: 'Tables',
					name: 'box_tables'
				}, {
					xtype: 'checkbox',
					//checked: true,
					fieldLabel: '',
					labelSeparator: '',
					boxLabel: 'Curves',
					name: 'box_curves'
				},
				{
					xtype: 'checkbox',
					fieldLabel: 'Privacy settings',
					boxLabel: 'Anyone from group can view',
					name: 'anyone_group_view',
					checked: true,
				}, {
					xtype: 'checkbox',
					fieldLabel: '',
					labelSeparator: '',
					boxLabel: 'Anyone from group can edit',
					name: 'anyone_group_edit',
					checked: true,
				}, {
					xtype: 'checkbox',
					fieldLabel: '',
					labelSeparator: '',
					boxLabel: 'Anyone from group can copy',
					name: 'anyone_group_copy',
					checked: true,
				},{
					xtype: 'checkbox',
					fieldLabel: '',
					boxLabel: 'Anyone can view',
					name: 'anyone_view',
					checked: true,
				},{
					xtype: 'checkbox',
					//checked: true,
					fieldLabel: '',
					labelSeparator: '',
					boxLabel: 'Anyone can edit',
					name: 'anyone_edit',
					checked: true,
				}, {
					xtype: 'checkbox',
					//checked: true,
					fieldLabel: '',
					labelSeparator: '',
					boxLabel: 'Anyone can copy',
					name: 'anyone_copy',
					checked: true,
				}]
            }]
        },

/*        buttons: [{*/
/*            text: 'Save'*/
/*        },{*/
/*            text: 'Cancel'*/
/*        }]*/
    });



//my page power map form

 var form_map2 = new Ext.Panel({
        labelWidth: 90,
        border:false,
        width: 400,
        hideBorders: true,
        autoScroll: 'true',

        items: {
            xtype:'tabpanel',
            activeTab: 0,
            defaults:{autoHeight:true, bodyStyle:'padding:10px'}, 
            items:[{
                title:'Metadata',
                layout:'form',
                defaults: {width: 230},
                defaultType: 'textfield',

                items: [{
                    fieldLabel: 'Author',
                    name: 'author',
                    allowBlank:false,
                    //value: 'Jack'
                },{
                    fieldLabel: 'Description',
                    name: 'description'
                    //value: 'Slocum'
                },{
                    fieldLabel: 'Group',
                    name: 'group'
                    //value: 'Ext JS'
                }, {
                    fieldLabel: 'Title',
                    name: 'title'
                    //vtype:'email'
                },
                 {
                    fieldLabel: 'Key words',
                    name: 'words'
                },
                {
                    xtype: 'textarea',
					fieldLabel: 'Abstract',
					width: 450,
                    name: 'abstract'
                }]
            },{
                title:'Map Options',
                layout:'form',
		items: [{
		xtype: "fieldset",
		title: "Input Maps",
		autoHeight: true,
		defaults: { labelSeparator: "" },
		items: [{
			xtype: "radio",
			fieldLabel: "&nbsp;",
			boxLabel: "Hazard source zone model map",
			name: "inputmaps",
			inputValue: 1
			},
			{
			xtype: "radio",
			fieldLabel: "&nbsp;",
			boxLabel: "Site conditions map",
			name: "inputmaps",
			inputValue: 2
			},
			{
			xtype: "radio",
			fieldLabel: "&nbsp;",
			boxLabel: "Exposure model map",
			name: "inputmaps",
			inputValue: 3
			}]
			},
			{
		xtype: "fieldset",
		title: "Other Output types",
		autoHeight: true,
		defaults: { labelSeparator: "" },
		items: [{
			xtype: "radio",
			fieldLabel: "&nbsp;",
			boxLabel: "IML map for a given probability of exceedance (i.e. Hazard Map)",
			name: "inputmaps",
			inputValue: 1
			},
			{
			xtype: "radio",
			fieldLabel: "&nbsp;",
			boxLabel: "IML map for a given earthquake rupture (i.e. Shake Map)",
			name: "inputmaps",
			inputValue: 2
			},
			{
			xtype: "radio",
			fieldLabel: "&nbsp;",
			boxLabel: "Probability of exceedance of IML map",
			name: "inputmaps",
			inputValue: 3
			},
			{
			xtype: "radio",
			fieldLabel: "&nbsp;",
			boxLabel: "Probability of occurrence of IML map",
			name: "inputmaps",
			inputValue: 2
			},
			{
			xtype: "radio",
			fieldLabel: "&nbsp;",
			boxLabel: "Loss (ratio) map for a given probability of exceedance",
			name: "inputmaps",
			inputValue: 2
			},
			{
			xtype: "radio",
			fieldLabel: "&nbsp;",
			boxLabel: "Loss (ratio) map for a given earthquake rupture",
			name: "inputmaps",
			inputValue: 2
			},
			{
			xtype: "radio",
			fieldLabel: "&nbsp;",
			boxLabel: "Mean loss (ratio) map",
			name: "inputmaps",
			inputValue: 2
			},
			{
			xtype: "radio",
			fieldLabel: "&nbsp;",
			boxLabel: "Probability of exceedance of loss map",
			name: "inputmaps",
			inputValue: 2
			},
			{
			xtype: "radio",
			fieldLabel: "&nbsp;",
			boxLabel: "Probability of occurrence of loss map",
			name: "inputmaps",
			inputValue: 2
			},]
			},
				
				{
					fieldLabel: 'Output types:',
					xtype: 'checkbox',
					//checked: true,
					//fieldLabel: '',
					labelSeparator: '',
					boxLabel: 'Tables',
				},
				{
					xtype: 'checkbox',
					//checked: true,
					fieldLabel: '',
					labelSeparator: '',
					boxLabel: 'Plots',
				},
				]
            },
            {
                title:'Calculation Options',
                layout:'form',
                defaults: {width: 300},
                labelWidth: 270,
                defaultType: 'textfield',

                items: [
/*					{*/
/*					xtype: 'tbbutton',*/
/*					text: 'Select location',*/
/*					width: 70,*/
/*					iconCls:'icon-search',*/
/*					},*/{
					xtype: 'combo',
					store: ['PSHA Input Model', 'Earthquake Rupture Forecast', 'Event Set(s)', 'Shake Map(s)', 'Hazard Map(s)', 'Hazard Curve(s)'],
					//plugins: [ Ext.ux.FieldReplicator, Ext.ux.FieldLabeler ],
					fieldLabel: 'Select Hazard Data Type',
					name: 'rupture',
					emptyText: "Select Hazard Data Type",
				},{
					xtype: 'combo',
					store: ['European GEM1 Hazard Curves' ],
					//plugins: [ Ext.ux.FieldReplicator, Ext.ux.FieldLabeler ],
					fieldLabel: 'Select Hazard Input Data',
					name: 'rupture',
					emptyText: "Select Hazard Input Data",
				},{
					xtype: 'combo',
					store: ['Global Population Distribution (LandScan 2008)' ],
					//plugins: [ Ext.ux.FieldReplicator, Ext.ux.FieldLabeler ],
					fieldLabel: 'Select Vulnerability Data',
					name: 'rupture',
					emptyText: "Select Vulnerability Data",
				},{
					xtype: 'combo',
					store: ['PAGER Global Fatality Model' ],
					//plugins: [ Ext.ux.FieldReplicator, Ext.ux.FieldLabeler ],
					fieldLabel: 'Select Exposure Data',
					name: 'rupture',
					emptyText: "Select Exposure Data",
				},
                {
					xtype: 'combo',
					store: ['1 year', '10 years', '50 years', '100 years' ],
					//plugins: [ Ext.ux.FieldReplicator, Ext.ux.FieldLabeler ],
					fieldLabel: 'Select time span',
					name: 'IML',
					emptyText: "Select time span",
                },
				]
            }]
        },

/*        buttons: [{*/
/*            text: 'Save'*/
/*        },{*/
/*            text: 'Cancel'*/
/*        }]*/
    });
    

//my page power download tool form

 //my page power download tool form Window				 

//my page power export data form

	var form_export = new Ext.FormPanel({
			labelWidth: 120, // label settings here cascade unless overridden
			//url:'save-form.php',
			//frame:true,
			//title: 'Export Data',
			bodyStyle:'padding:5px 5px 0',
			width: 350,
			defaults: {width: 230},
			defaultType: 'textfield',
	
			items: [{
				xtype:'combo',
				fieldLabel:'Select data type',
				store:['Data', 'Plot','Table', 'Map']
				},{
				xtype:'combo',
				fieldLabel:'Select feature',
				store:['Africa LRM 01', 'Albania LRM 01','Canada LRM 01', 'East Asia LRM 01', 'Australia LRM 01', 'Europe LRM 01']
				},{
				xtype:'combo',
				fieldLabel:'Select export format',
				store:['GeoTiff', 'ArcGrid','Shapefile']
				},
			],
	
/*			buttons: [{*/
/*				text: 'Export'*/
/*			},{*/
/*				text: 'Cancel'*/
/*			}]*/
		});

//my page power export data form Window				 

    var formExport = new Ext.Window({
    	id: "formExport",
        title: 'Export Output',
        collapsible: true,
        maximizable: true,
        closeAction: "hide",
        width: 410,
        height: 190,
        minWidth: 300,
        minHeight: 200,
        layout: 'fit',
        plain: true,
        bodyStyle: 'padding:5px;',
        buttonAlign: 'center',
        items: [form_export],
        buttons: [{
            text: 'Export'
        },{
            text: 'Cancel'
        }]
    });



//My page Power treePlots

	
		 // create drag enabled tree in the west
		 var treePlots = new Ext.tree.TreePanel({
			 root:{
			 	text:'Root', 
			 	ddGroup: 'sourceDrop',
			 	id:'Plots', 
			 	animate:true,
		    	enableDD:true,
		    	enableDrop:true,
		   		dropConfig: {appendOnly:true},
		   		ddGroup: 'DropGroup',
			 	expanded:true,
			 	hideBorders: true,
			 	children:[
			 		{
			 		text:'My hazard plots',
			 		data:'Child 1 additional data',
					children:[
						{
						text:'Plot 1',
						data:'Child 1 additional data',
						children:[{
							text:'Europe',
							item: [Europe],
							leaf:true
								},{
							text:'temp2',
							data:'Some additional data of Child 1 Subchild 2',
							leaf:true,
								}]
								},
						{
						text:'Plot 2',
						data:'Child 2 additional data',
						children:[{
							text:'temp1',
							data:'Some additional data of Child 1 Subchild 1',
							leaf:true
								},{
							text:'temp2',
							data:'Some additional data of Child 1 Subchild 2',
							leaf:true,
								}]
								
						},
						{
						text:'Plot 3',
						data:'Child 2 additional data',
						children:[{
							text:'temp1',
							data:'Some additional data of Child 1 Subchild 1',
							leaf:true
								},{
							text:'temp2',
							data:'Some additional data of Child 1 Subchild 2',
							leaf:true,
								}]
								
						},
					]},
			 		{
			 		text:'My vulnerability plots',
			 		data:'Child 1 additional data',
					children:[
			 		{
			 		text:'Plot 1',
			 		data:'Child 1 additional data',
			 		children:[{
			 			text:'temp1',
			 			data:'Some additional data of Child 1 Subchild 1',
			 			leaf:true
			 				},{
			 			text:'temp2',
			 			data:'Some additional data of Child 1 Subchild 2',
			 			leaf:true,
			 				}]
			 				},
			 		{
			 		text:'Plot 2',
			 		data:'Child 2 additional data',
			 		children:[{
			 			text:'temp1',
			 			data:'Some additional data of Child 1 Subchild 1',
			 			leaf:true
			 				},{
			 			text:'temp2',
			 			data:'Some additional data of Child 1 Subchild 2',
			 			leaf:true,
			 				}]
			 				
			 		},
			 		{
			 		text:'Plot 3',
			 		data:'Child 2 additional data',
			 		children:[{
			 			text:'temp1',
			 			data:'Some additional data of Child 1 Subchild 1',
			 			leaf:true
			 				},{
			 			text:'temp2',
			 			data:'Some additional data of Child 1 Subchild 2',
			 			leaf:true,
			 				}]
			 				
			 		},
			 	]},
			 		{
			 		text:'My temp plots',
			 		data:'Child 1 additional data',
					children:[
			 		{
			 		text:'Hazard plots',
			 		data:'Child 1 additional data',
			 		children:[{
			 			text:'temp1',
			 			data:'Some additional data of Child 1 Subchild 1',
			 			leaf:true
			 				},{
			 			text:'temp2',
			 			data:'Some additional data of Child 1 Subchild 2',
			 			leaf:true,
			 				}]
			 				},
			 		{
			 		text:'vulnerability plots',
			 		data:'Child 2 additional data',
			 		children:[{
			 			text:'temp1',
			 			data:'Some additional data of Child 1 Subchild 1',
			 			leaf:true
			 				},{
			 			text:'temp2',
			 			data:'Some additional data of Child 1 Subchild 2',
			 			leaf:true,
			 				}]
			 				
			 		},
			 		{
			 		text:'Exposure plots',
			 		data:'Child 2 additional data',
			 		children:[{
			 			text:'temp1',
			 			data:'Some additional data of Child 1 Subchild 1',
			 			leaf:true
			 				},{
			 			text:'temp2',
			 			data:'Some additional data of Child 1 Subchild 2',
			 			leaf:true,
			 				}]
			 				
			 		},
			 	]},
			 	
			 	]},
				loader:new Ext.tree.TreeLoader({preloadChildren:true}),
					enableDrag:true,
					ddGroup:'t2div',
					//region:'west',
					//title:'Tree',
					layout:'fit',
					//width:200,
					split:true,
					//collapsible:true,
					autoScroll:true,
					listeners:{
						startdrag:function() {
							var t = Ext.getCmp('target').body.child('div.drop-target');
								if(t) {
									t.applyStyles({'background-color':'#f0f0f0'});
										}
									},
							enddrag:function() {
								var t = Ext.getCmp('target').body.child('div.drop-target');
									if(t) {
										t.applyStyles({'background-color':'white'});
											}
										 }
								}
				 });


				 
//My page Power treeTables

	
		 // create drag enabled tree in the west
		 var treeTables = new Ext.tree.TreePanel({
			 root:{
			 	text:'Root', 
			 	ddGroup: 'sourceDrop',
			 	id:'Tables', 
			 	animate:true,
		    	enableDD:true,
		    	enableDrop:true,
		   		dropConfig: {appendOnly:true},
		   		ddGroup: 'DropGroup',
			 	expanded:true,
			 	hideBorders: true,
			 	children:[
			 		{
			 		text:'My hazard tables',
			 		data:'Child 1 additional data',
					children:[
						{
						text:'Table 1',
						data:'Child 1 additional data',
						children:[{
							text:'Europe',
							item: [Europe],
							leaf:true
								},{
							text:'temp2',
							data:'Some additional data of Child 1 Subchild 2',
							leaf:true,
								}]
								},
						{
						text:'Table 2',
						data:'Child 2 additional data',
						children:[{
							text:'temp1',
							data:'Some additional data of Child 1 Subchild 1',
							leaf:true
								},{
							text:'temp2',
							data:'Some additional data of Child 1 Subchild 2',
							leaf:true,
								}]
								
						},
						{
						text:'Table 3',
						data:'Child 2 additional data',
						children:[{
							text:'temp1',
							data:'Some additional data of Child 1 Subchild 1',
							leaf:true
								},{
							text:'temp2',
							data:'Some additional data of Child 1 Subchild 2',
							leaf:true,
								}]
								
						},
					]},
			 		{
			 		text:'My vulnerability tables',
			 		data:'Child 1 additional data',
					children:[
			 		{
			 		text:'Table 1',
			 		data:'Child 1 additional data',
			 		children:[{
			 			text:'temp1',
			 			data:'Some additional data of Child 1 Subchild 1',
			 			leaf:true
			 				},{
			 			text:'temp2',
			 			data:'Some additional data of Child 1 Subchild 2',
			 			leaf:true,
			 				}]
			 				},
			 		{
			 		text:'Table 2',
			 		data:'Child 2 additional data',
			 		children:[{
			 			text:'temp1',
			 			data:'Some additional data of Child 1 Subchild 1',
			 			leaf:true
			 				},{
			 			text:'temp2',
			 			data:'Some additional data of Child 1 Subchild 2',
			 			leaf:true,
			 				}]
			 				
			 		},
			 		{
			 		text:'Table 3',
			 		data:'Child 2 additional data',
			 		children:[{
			 			text:'temp1',
			 			data:'Some additional data of Child 1 Subchild 1',
			 			leaf:true
			 				},{
			 			text:'temp2',
			 			data:'Some additional data of Child 1 Subchild 2',
			 			leaf:true,
			 				}]
			 				
			 		},
			 	]},
			 		{
			 		text:'My temp tables',
			 		data:'Child 1 additional data',
					children:[
			 		{
			 		text:'Hazard tables',
			 		data:'Child 1 additional data',
			 		children:[{
			 			text:'temp1',
			 			data:'Some additional data of Child 1 Subchild 1',
			 			leaf:true
			 				},{
			 			text:'temp2',
			 			data:'Some additional data of Child 1 Subchild 2',
			 			leaf:true,
			 				}]
			 				},
			 		{
			 		text:'vulnerability tables',
			 		data:'Child 2 additional data',
			 		children:[{
			 			text:'temp1',
			 			data:'Some additional data of Child 1 Subchild 1',
			 			leaf:true
			 				},{
			 			text:'temp2',
			 			data:'Some additional data of Child 1 Subchild 2',
			 			leaf:true,
			 				}]
			 				
			 		},
			 		{
			 		text:'Exposure tables',
			 		data:'Child 2 additional data',
			 		children:[{
			 			text:'temp1',
			 			data:'Some additional data of Child 1 Subchild 1',
			 			leaf:true
			 				},{
			 			text:'temp2',
			 			data:'Some additional data of Child 1 Subchild 2',
			 			leaf:true,
			 				}]
			 				
			 		},
			 	]},
			 	
			 	]},
				loader:new Ext.tree.TreeLoader({preloadChildren:true}),
					enableDrag:true,
					ddGroup:'t2div',
					//region:'west',
					//title:'Tree',
					layout:'fit',
					//width:200,
					split:true,
					//collapsible:true,
					autoScroll:true,
					listeners:{
						startdrag:function() {
							var t = Ext.getCmp('target').body.child('div.drop-target');
								if(t) {
									t.applyStyles({'background-color':'#f0f0f0'});
										}
									},
							enddrag:function() {
								var t = Ext.getCmp('target').body.child('div.drop-target');
									if(t) {
										t.applyStyles({'background-color':'white'});
											}
										 }
								}
				 });



	
//my page power data form Window				 

    var formData2 = new Ext.Window({
    	id: "formData2",
        title: 'Create A Map',
        collapsible: true,
        maximizable: true,
        width: 750,
        height: 500,
        closeAction: "hide",
        minWidth: 300,
        minHeight: 200,
        layout: 'fit',
        plain: true,
        bodyStyle: 'padding:5px;',
        buttonAlign: 'center',
        items: [form_data2],
        buttons: [{
            text: 'Send'
        },{
            text: 'Cancel'
        }]
    });



//my page power map form Window				 

    var formMap2 = new Ext.Window({
    	id: "formMap2",
        title: 'Create A Map',
        collapsible: true,
        maximizable: true,
        closeAction: "hide",
        width: 750,
        height: 530,
        minWidth: 300,
        minHeight: 200,
        layout: 'fit',
        plain: true,
        bodyStyle: 'padding:5px;',
        buttonAlign: 'center',
        items: [form_map2],
        buttons: [{
            text: 'Send'
        },{
            text: 'Cancel'
        }]
    });
    
//my page power search 

        store5b = new GeoExt.data.WMSCapabilitiesStore({
            url: "data/Professional_Network.xml"
		});
		store5b.load();
		
    var search = new Ext.form.ComboBox({
        store: store5b,
        displayField:'title',
        typeAhead: false,
        loadingText: 'Searching...',
        width: 150,
        pageSize:10,
        hideTrigger:true,
        //tpl: resultTpl,
        onSelect: function(record){ // override default onSelect to do redirect
            window.location =
                String.format('http://extjs.com/forum/showthread.php?t={0}&p={1}', record.data.topicId, record.id);
        }
    });
    // apply it to the exsting input element
    //search.applyTo('search');

				 
//my page power Toolbar
	var toolbar_power = new Ext.Toolbar({
		//renderTo: document.body,
		items: [{
		xtype: 'tbbutton',
		hideBorders: true,
		text: 'Modify Dashboard',
		iconCls:'icon-alter',
/*		listeners: {*/
/*			click: function() {*/
/*				Ext.getCmp("formExport").show();*/
/*			}*/
/*		}*/
		},
		{
		xtype: 'tbbutton',
		hideBorders: true,
		text: 'Add Data',
		iconCls:'icon-add',
		menu: [{
			text: 'Add hazard data',
			iconCls:'icon-data',
			listeners: {
				click: function() {
					Ext.getCmp("formAddData").show();
				}
			}
			},{
			text: 'Add vulnerability data',
			iconCls:'icon-data',
			listeners: {
				click: function() {
					//Ext.getCmp("formAddData").show();
				}
			}
			},{
			text: 'Add exposure data',
			iconCls:'icon-data',
			listeners: {
				click: function() {
					//Ext.getCmp("formAddData").show();
				}
			}
			}]
		},
		{
		xtype: 'tbbutton',
		text: 'Create Output',
		iconCls:'icon-make',
		menu: [{
		  text: 'Create plots',
		  iconCls:'icon-node',
		},{
		  text: 'Create tables',
		  iconCls:'icon-agrid',
		},{
		  text: 'Create maps',
		  iconCls:'icon-map',
		  listeners: {
        	click: function() {
            	Ext.getCmp("formMap2").show();
            	// Ext.getCmp('formMap2').doLayout();
        	}
        	}
		}]
		},
		{
		xtype: 'tbbutton',
		hideBorders: true,
		text: 'Export Output',
		iconCls:'icon-export',
		listeners: {
			click: function() {
				Ext.getCmp("formExport").show();
			}
		}
		},
		'->',
		{
		hideBorders: true,
		iconCls:'icon-search',
		},
		new Ext.form.ComboBox({
        store: store5b,
        displayField:'title',
        typeAhead: false,
        loadingText: 'Searching...',
        width: 150,
        pageSize:10,
        hideTrigger:true,
        //tpl: resultTpl,
        onSelect: function(record){ // override default onSelect to do redirect
            window.location =
                String.format('http://extjs.com/forum/showthread.php?t={0}&p={1}', record.data.topicId, record.id);
        }
    })
		]
	  });
 
//my page power (TreeTables)

		var toolbar_map2 = new Ext.Panel({
			//title: 'My Data',
			//html: "&nbsp;",
			//renderTo: document.body,
			enableDragDrop: true,
			layout:'fit',
			hideBorders: true,
			items:[
				new Ext.Panel({
				//title: 'Layers',
				//html: "&nbsp;",
				//renderTo: document.body,
				enableDragDrop: true,
				//id: 'WMS',
				hideBorders: true,
				//items:[toolbar_power()],
				width:500,
				height:600,
				autoScroll: true
				 })
			],
			autoScroll: true
		
		 });
	
//my page power item2a (profile)
/*
		var item2a = new Ext.Panel({
			frame: true,
			items: [{
       		//region: 'north',
       		hideBorders: true,
        	html: '<img src="images/Vitor.png">',
        	border: false,
        	//frame: true,
        	margins: '0 0 5 0'
    		}
			]
		 });

*/

/*//my page power map text*/
/*		var item2b = new Ext.Panel({*/
/*			frame: true,*/
/*			items: [*/
/*				{*/
/*       			//region: 'north',*/
/*       			hideBorders: true,*/
/*        		html: '<H2>My House</H2><br><br><img src="images/Map1.png">',*/
/*        		border: false,*/
/*        		//frame: true,*/
/*        		margins: '0 0 5 0'*/
/*    			}*/
/*			]*/
/*		 });*/
		 
//my page power risk fact	 
/*var item2c = new Ext.Panel({
			frame: true,
			items: [
				{
       			//region: 'north',
        		html: '<p>The biggest earthquakes in history was on May 22 1960: A magnitude-9.5 earthquake in southern Chile.</p>',
        		border: false,
        		hideBorders: true,
        		//frame: true,
        		margins: '0 0 5 0'
    			}
			]
		 });
*/
//my page power understanding your rick 		 
		var item2d = new Ext.Panel({
			frame: true,
			items: [
				{
       			//region: 'north',
        		html: '<br><img src="images/Color.png"><br><br><p>The probability your house will suffer structural damage in the next 50 years is comparable to...</p><br>',
        		border: false,
        		hideBorders: true,
        		//frame: true,
        		margins: '0 0 5 0'
    			}
			]
		 });
		 
//my page RSS feed 		 
		var item2i = new Ext.Panel({
			frame: true,
			items: [
				{
       			//region: 'north',
        		html: '<H2>RSS Feed: USGS M5+ Earthquakes</H2><br><img src="images/RSS1.png"><br><br><p>The probability your house will suffer structural damage in the next 50 years is comparable to...</p><br>',
        		border: false,
        		hideBorders: true,
        		//frame: true,
        		margins: '0 0 5 0'
    			}
			]
		 });

/**/
/*	*/
/*		 */
/*//my page power download tools*/
/*	var item2e = new Ext.Panel({*/
/*		items: [*/
/*			{*/
/*			html: '<H2>Tool Download</H2><br><br><br><p>Selecty a standalone tool to download</p><br>',*/
/*			},*/
/*			{*/
/*			html: '<H2>Tool Download</H2><br><br><br><p>Selecty a standalone tool to download</p><br>',*/
/*			},*/
/*			*/
/*		]*/
/*	});*/

		 
//my page power item2a (profile)
/*
		var item2f = new Ext.Panel({
			frame: true,
			items: [{
       		//region: 'north',
       		hideBorders: true,
        	html: '<img src="images/groups.png">',
        	border: false,
        	//frame: true,
        	margins: '0 0 5 0'
    		}
			]
		 });*/
		 
//my page power item2a (profile)
/*
		var item2g = new Ext.Panel({
			frame: true,
			items: [{
       		//region: 'north',
       		hideBorders: true,
        	html: '<img src="images/friends.png">',
        	border: false,
        	//frame: true,
        	margins: '0 0 5 0'
    		}
			]
		 });
*/
//my page power frames	
	         var myPageB = new Ext.Panel({
                //id:'main-panel',
                baseCls:'x-plain',
                //title: 'test',
                //renderTo: Ext.getBody(),
                layout:'table',
                autoScroll: true,
                layoutConfig: {columns:3},
                // applied to child components
                defaults: {width:200, height: 200, hideBorders: true,},
                items:[/*{*/
/*                    //title:'Item 1a',*/
/*                    items:[item2a],*/
/*                    autoScroll: true,*/
/*                    width:220,*/
/*                    height:610*/
/*                },*/{
                    //title:'Item 1b',
                    items:[toolbar_map2],
                    width:510,
                    height:610
                },{
                    //title:'Item 1c',
                    hideBorders: true,
                    items:[item2d],
                    width:280,
                    height:610
                }]
            });
/*        */
/*	         var myPage2 = new Ext.Panel({*/
/*                //id:'main-panel',*/
/*                baseCls:'x-plain',*/
/*                layout:'fit',*/
/*                //title: 'test',*/
/*                //renderTo: Ext.getBody(),*/
/*                layout:'table',*/
/*                autoScroll: true,*/
/*                layoutConfig: {columns:3},*/
/*                // applied to child components*/
/*                defaults: {hideBorders: true,},*/
/*                items:[{*/
/*                    //title:'My Page',*/
/*                    items:[myPageB],*/
/*                    		tbar: [ */
/*                    			//'You are in power/expert mode',*/
/*                    			//toolbar_power,*/
/*                    			*/
/*								'->',  */
/*								loginForm1, */
/*								loginForm2*/
/*								],*/
/**/
/*                }]*/
/*            });*/
		
//Portal
// portal my features Store
//var grid5a = function(){
	/*var grid5a = new Ext.grid.GridPanel({
			      store: store5,
    		id: "grid5a",
    		stripeRows: true,
    		autoScroll: true,
    		enableDragDrop: true,
    	      columns: [
                {header: "Title", dataIndex: "title", sortable: true, width: 175},
                {id: "description", header: "Description", dataIndex: "abstract"}
            ],
    		sm: new Ext.grid.RowSelectionModel
    		({singleSelect:false}),
            autoExpandColumn: "description",
            tbar: [
    			"Select a featuer to add to the feature panel, double click to preview.",
    			'->',
    			{
                text: "Add Layer",
    			iconCls: 'icon-add',
    			prependButtons: true,
                handler: function() {
                    var record = Ext.getCmp("grid5a").getSelectionModel().getSelected();
    	              if(record) {
                        var copy = record.copy();
                        copy.get("layer").mergeNewParams({
                            format: "image/png",
                            transparent: "true"
                        });
                        mapPanel.layers.add(copy);
                        mapPanel.map.zoomToExtent(
                            OpenLayers.Bounds.fromArray(copy.get("llbbox"))
                        );
                    }
                }
                 }]
                 
});
//};*/
//portal my data Store

	var myData = [['cat1', 'Category 1'], ['cat2', 'Category 2']];
	var myDataStore = new Ext.data.SimpleStore({
		 fields:['catCode', 'catName']
		,data:myData
	});  


var myDataGrid = new Ext.grid.GridPanel({
            //title: "Loss maps for an investigation interval of 50 years for a probability of exceedance of 1%",
            store: myData,
    		id: "myDataGrid",
    		stripeRows: true,
    		//collapsible:true,
    		//iconCls:'icon-agrid',
    		//frame:true,
    		autoScroll: true,
    		enableDragDrop: true,
    		//collapsed: true,
    		//ddGroup : 'mygrid-dd',
    		//ddText : 'Place this row.',
/*            columns: [*/
/*                {header: "Title", dataIndex: "title", sortable: true, width: 175},*/
/*                //{header: "Name", dataIndex: "name", sortable: true, width: 175},*/
/*                //{header: "Queryable", dataIndex: "queryable", sortable: true, width: 70},*/
/*                {id: "description", header: "Description", dataIndex: "abstract"}*/
/*                //{header: "Data modified", dataIndex: "srs", sortable: true, width: 70},*/
/*            ],*/
/*    		sm: new Ext.grid.RowSelectionModel*/
/*    			({singleSelect:false}),*/
/*            autoExpandColumn: "description",*/
            tbar: [
    			"Select an output to add to the feature panel, double click to preview.",
    			'->',
    			//{iconCls:'icon-save'},
    			//{iconCls:'icon-pdf'},
    			//{iconCls:'icon-print'},
    			{
                text: "Add Layer",
    			iconCls: 'icon-add',
    			//displayInfo:true,
    			prependButtons: true,
                handler: function() {
                    var record = myDataGrid.getSelectionModel().getSelected();
    								//alert(record);
                    if(record) {
                        var copy = record.copy();
                        //copy.set("layer", record.get("layer"));
                        copy.get("layer").mergeNewParams({
                            format: "image/png",
                            transparent: "true"
                        });
                        mapPanel.layers.add(copy);
                        mapPanel.map.zoomToExtent(
                            OpenLayers.Bounds.fromArray(copy.get("llbbox"))
                        );
                    }
                }
                 }]
                 
});
//begin portal
    // create some portlet tools using built in Ext tool ids
    /*var tools = [{
        id:'gear',
        handler: function(){
            Ext.Msg.alert('Message', 'The Settings tool was clicked.');
        }
    },{
        id:'close',
        handler: function(e, target, panel){
            panel.ownerCt.remove(panel, true);
        }
    }];*/

 //begin portal
    // create some portlet tools using built in Ext tool ids


var portlets = new Array()

var restoreTools = [ {
				id : "minimize",
				handler : function(event, toolEl, panel, tc) {
					Ext.getCmp("portalTest").removeAll(true);
					Ext.getCmp("portalTest").add(allPortlets());
					Ext.getCmp("portalTest").doLayout();
				}
} ];

var tools = [{
        id: "maximize",
				handler : function(event, toolEl, panel, tc) {
					Ext.getCmp("portalTest").removeAll(true);
					Ext.getCmp("portalTest").add( {
						columnWidth : 0.99,
							style : "padding:10px 0 10px 10px",
							items : [ portlets[panel.id].call(this, restoreTools, 550) ]
						});
						
						Ext.getCmp("portalTest").doLayout();
					}
    	},{
        id:'close',
        handler: function(e, target, panel){
            panel.ownerCt.remove(panel, true);
     		}
}];

// NOTE Portlets definition
var item2a = function(t)
{
	return new Ext.ux.Portlet({
		tools : t,
		id : "item2a",
		title : "My Profile",
		html : "<img src=\"images/Marco.png\">"
	});
}

var item2f = function(t)
{
	return new Ext.ux.Portlet({
		tools : t,
		id : "item2f",
		title : "My Groups",
		html : "<img src=\"images/groups.png\">"
	});
}

var item2g = function(t)
{
	return new Ext.ux.Portlet({
		tools : t,
		id : "item2g",
		title : "My Friends",
		html : "<img src=\"images/friends.png\">"
	});
}

var item2h = function(t, h)
{
	return new Ext.ux.Portlet({
		tools : t,
		id : "item2h",
		autoScroll: true,
		height: h,
		title : "My Discussion Threads",
		html : "<img src=\"images/thread.png\">"
	});
}

/*var toolbar_power_portlet = function(t)*/
/*{*/
/*	return new Ext.ux.Portlet({*/
/*		tools : t,*/
/*		id : "toolbar_power_portlet",*/
/*		title : "My Tools",*/
/*		items: [toolbar_power()]*/
/*	});*/
/*}*/


var grid5a_portlet = function(t, h)
{
	return new Ext.ux.Portlet({
		tools : t,
		layout: "fit",
		height: h,
		id : "grid5a_portlet",
		title : "My Output",
		items: [new Ext.grid.GridPanel({
			store: store5b,
	    id: "grid5a",
	    stripeRows: true,
	    autoScroll: true,
			autoExpandColumn: "description",
	    enableDragDrop: true,
				columns: [
					{header: "Title", dataIndex: "title", sortable: true, width: 175},
					//{id: "Keyword", header: "Date", dataIndex: "Keyword", sortable: true, width: 100},
					{id: "description", header: "Description", dataIndex: "abstract"}
				],
				autoExpandColumn: "description", 
						listeners: { 
					rowdblclick: mapPreview
				}, 
	    tbar: ["Select an output to add to the feature panel, double click to preview.",'->',
	    	{
	    	text: "Add Layer",
	    	iconCls: 'icon-add',
	    	prependButtons: true,
	      handler: function() {
	      	var record = Ext.getCmp("grid5a").getSelectionModel().getSelected();
	    	  if(record) {
	        	var copy = record.copy();
	          copy.get("layer").mergeNewParams({
	          	format: "image/png",
	            transparent: "true"
	         	});
	          
						mapPanel.layers.add(copy);
	          mapPanel.map.zoomToExtent(
	          	OpenLayers.Bounds.fromArray(copy.get("llbbox"))
	          );
	 				}
	      }
	    }]
		})]
		
	});
}

var oGrid_portlet = function(t, h)
{
	return new Ext.ux.Portlet({
		tools : t,
		layout: "fit",
		height: h,
		id : "oGrid_portlet",
		title : "My Input",
		items: [new Ext.grid.GridPanel({
			autoExpandColumn: "date",
			colModel : oColModels,
			store : oStore
    })]
	});
}

/*var item2c = function(t)*/
/*{*/
/*	return new Ext.ux.Portlet({*/
/*		tools : t,*/
/*		id : "item2c",*/
/*		title : "Todays Seismic Risk Fact",*/
/*		html : "<p>The biggest earthquakes in history was<br/> on May 22 1960: A magnitude-9.5<br/> earthquake in southern Chile.</p>"*/
/*	});*/
/*}*/

/*var item2d_portlet = function(t)*/
/*{*/
/*	return new Ext.ux.Portlet({*/
/*		tools : t,*/
/*		id : "item2d_portlet",*/
/*		title : "Understanding Your Risk",*/
/*		html : "<img src=\"images/Color.png\"><br><p>The probability your house will suffer<br/> structural damage in the next 50 years<br/> is comparable to...</p>"*/
/*	});*/
/*}*/

var item2i_portlet = function(t)
{
	return new Ext.ux.Portlet({
		tools : t,
		id : "item2i_portlet",
		title : "RSS Feed: USGS M5+ Earthquakes",
		html : "<img src=\"images/RSS1.png\">"
	});
}

var item2k = function(t)
{
	return new Ext.ux.Portlet({
		tools : t,
		id : "item2k",
		title : "RSS Feeds Bullets",
		html : "<img src=\"images/RSS2.png\">"
	});
}

var allPortlets = function()
{
	return [{
			columnWidth : .20,
      style: "padding:10px 0 10px 10px",
      items:[item2a(tools), item2f(tools), item2g(tools)]
  }, {
			columnWidth : .57,
      style: "padding:10px 0 10px 10px",
      items:[oGrid_portlet(tools, 250),grid5a_portlet(tools, 250), item2h(tools, 250)]
  }, {
			columnWidth : .22,
      style: "padding:10px 0 10px 10px",
      items:[item2j_download(tools), item2i_portlet(tools), item2k(tools)]
  }];
}

var item2j_download = function(t)
{
	return new Ext.ux.Portlet({
		tools : t,
		layout: "fit",
		height: 230,
		id : "item2j_download",
		title : "Download Tools",
		//html : "<img src=\"images/RSS1.png\">"
		items: [new Ext.FormPanel({
				labelWidth: 120, // label settings here cascade unless overridden
				labelAlign: 'top',
				bodyStyle:'padding:5px 5px 0',
				width: 350,
				defaults: {width: 230},
				defaultType: 'textfield',

				items: [{
					xtype:'combo',
					fieldLabel:'Select tool',
					store:['Hazard Curves Load Mode Application', 'GEM PSHA Input Tool', 'GEM Vulnerability Model Tool']
					},{
					xtype:'combo',
					fieldLabel:'Select platform',
					store:['Linux', 'Windows','Mac OS X']
					},{
					xtype:'combo',
					fieldLabel:'Select version',
					store:['version1', 'version2','version3']
					},
				],

				buttons: [{
					text: 'Download'
				}]
			})]
	});
}

portlets["item2a"] = item2a;
portlets["item2k"] = item2k;
portlets["item2f"] = item2f;
portlets["item2g"] = item2g;
portlets["item2j_download"] = item2j_download;
/*portlets["toolbar_power_portlet"] = toolbar_power_portlet;*/
portlets["grid5a_portlet"] = grid5a_portlet;
portlets["oGrid_portlet"] = oGrid_portlet;
portlets["item2h"] = item2h;



var portalTest = new Ext.Panel({
        layout:'border',
        tbar: [ 
			//'You are in power/expert mode',
			{
			hideBorders: true,
			iconCls:'icon-search',
			},
			new Ext.form.ComboBox({
			store: store5b,
			displayField:'title',
			typeAhead: false,
			loadingText: 'Searching...',
			width: 120,
			pageSize:10,
			hideTrigger:true,
			//tpl: resultTpl,
			onSelect: function(record){ // override default onSelect to do redirect
				window.location =
					String.format('http://extjs.com/forum/showthread.php?t={0}&p={1}', record.data.topicId, record.id);
			}
		}),
		{
            xtype: 'tbspacer'
          },
          {
            xtype: 'tbspacer'
          },
		{
			xtype: 'tbbutton',
			hideBorders: true,
			text: 'Modify Dashboard',
			iconCls:'icon-alter',
	/*		listeners: {*/
	/*			click: function() {*/
	/*				Ext.getCmp("formExport").show();*/
	/*			}*/
	/*		}*/
			},
			{
		xtype: 'tbbutton',
		hideBorders: true,
		text: 'Upload Input',
		iconCls:'icon-add',
		menu: [{
			text: 'Add hazard data',
			iconCls:'icon-data',
			listeners: {
				click: function() {
					Ext.getCmp("formAddData").show();
				}
			}
			},{
			text: 'Add vulnerability data',
			iconCls:'icon-data',
			listeners: {
				click: function() {
					//Ext.getCmp("formAddData").show();
				}
			}
			},{
			text: 'Add exposure data',
			iconCls:'icon-data',
			listeners: {
				click: function() {
					//Ext.getCmp("formAddData").show();
						}
					}
				}]
			},
			
		{
		xtype: 'tbbutton',
		hideBorders: true,
		text: 'Create Input',
		iconCls:'icon-input',
		menu: [{
			text: 'GEM PSHA Input Tool',
			iconCls:'icon-edit',
			listeners: {
				click: function() {
					Ext.getCmp("formAddData2").show();
				}
			}
			},{
			text: 'Hazard Curves Load Mode Application',
			iconCls:'icon-edit',
			listeners: {
				click: function() {
					//Ext.getCmp("formAddData").show();
				}
			}
			},{
			text: 'GEM Vulnerability Model Tool',
			iconCls:'icon-edit',
			listeners: {
				click: function() {
					//Ext.getCmp("formAddData").show();
						}
					}
				}]
			},
			{
		xtype: 'tbbutton',
		text: 'Create Output',
		iconCls:'icon-output',
		menu: [{
		  text: 'Create plots',
		  iconCls:'icon-node',
		},{
		  text: 'Create tables',
		  iconCls:'icon-agrid',
		},{
		  text: 'Create maps',
		  iconCls:'icon-map',
		  listeners: {
        	click: function() {
            	Ext.getCmp("formMap2").show();
            	// Ext.getCmp('formMap2').doLayout();
        	}
        	}
		}]
		},
		{
		xtype: 'tbbutton',
		hideBorders: true,
		text: 'Export Output',
		iconCls:'icon-export',
		listeners: {
			click: function() {
				Ext.getCmp("formExport").show();
			}
		}
		},
		
			'->', 
			loginUsernameField("username5"), 
			loginPasswordField("password5")
			],
        items:[{
						id: "portalTest",
            xtype:'portal',
            region:'center',
            margins:'5 5 5 5',			
            items: allPortlets()
            
            /*
             * Uncomment this block to test handling of the drop event. You could use this
             * to save portlet position state for example. The event arg e is the custom 
             * event defined in Ext.ux.Portal.DropZone.
             */
//            ,listeners: {
//                'drop': function(e){
//                    Ext.Msg.alert('Portlet Dropped', e.panel.title + '<br />Column: ' + 
//                        e.columnIndex + '<br />Position: ' + e.position);
//                }
//            }
        }]
    });


		
		
		
		
//click event

		   controls = {
				"single": new OpenLayers.Control.Click({
					handlerOptions: {
						"single": true
					}
				}),
			};

			var props = document.getElementById("props");
			var control;
			for(var key in controls) {
				control = controls[key];
				// only to route output here
				control.key = key;
				map.addControl(control);
			}

			//map.zoomToMaxExtent();
		
		
	   function toggle(key) {
			var control = controls[key];
			if(control.active) {
				control.deactivate();
			} else {
				control.activate();
			}
			var status = document.getElementById(key + "Status");
			status.innerHTML = control.active ? "on" : "off";
			var output = document.getElementById(key + "Output");
			output.value = "";
		}


//side panel
		var item1 = new Ext.Panel({
			title: 'Maps',
			//html: "&nbsp;",
			//renderTo: document.body,
			//cls:"&nbsp;"
			enableDragDrop: true,
			hideBorders: true,
			items:[Tree1],
			autoScroll: true
		});

		var item2 = new Ext.Panel({
			title: 'Plots',
			//html: '&lt;empty panel&gt;',
			//cls:'empty'
			hideBorders: true,
			items:[treePlots],
			autoScroll: true
		});

		var item3 = new Ext.Panel({
			title: 'Tables',
			autoScroll: true,
			hideBorders: true,
			//defaults:{border:false, activeTab:0},
				items:[treeTables]
						
			//html: '<body><td><button id="singleStatus" onclick="toggle("single")">off</button></td><td><textarea class="output" id="singleOutput"></textarea></td></tr><tr></body>'
			//cls:'empty'
			//renderTo: toggle
		});
		


		var accordion = new Ext.Panel({
			collapsible:true,
			title:"File Tree",
			region:'west',
			//margins:'5 0 5 5',
			//split:true,
			showPin: true,
			width: 210,
			layout:'accordion',
			split: true,
			items: [item1, item2, item3]
		});
		
		var item8 = new Ext.Panel({
			title: 'Print/Export',
			//html: '&lt;empty panel&gt;',
			//cls:'empty'
			//items:[formPanel]
		});

		var item9 = new Ext.Panel({
			title: 'Accordion Item 7',
			html: '&lt;empty panel&gt;',
			cls:'empty'
		});

		var item10 = new Ext.Panel({
			title: 'Accordion Item 8',
			html: '&lt;empty panel&gt;',
			cls:'empty'
		});

		var item11 = new Ext.Panel({
			title: 'Accordion Item 9',
			html: '&lt;empty panel&gt;',
			cls:'empty'
		});

		var item12 = new Ext.Panel({
			title: 'Accordion Item 10',
			html: '&lt;empty panel&gt;',
			cls:'empty'
		});

	
		//google earth
		
// Create control panel
		var controlPanel = new Ext.Panel({
			//contentEl: 'westPanel',
			width: 280,
			//border: true,
			collapsible: true,
			margins: '5 5 5 5',
			layout: 'accordion',
			layoutConfig: {
				animate: true
			},
			defaultType: 'panel',
			defaults: {
				bodyStyle: 'padding: 10px'
			}
		});
		
 

		// Build control panel
		earthPanel.on('earthLoaded', function(){

			// Display KMLs
			// Display KMLs
			// Display KMLs
			//earthPanel.fetchKml('http://www.globalquakemodel.org/tools/risk/images/Haiti3.kmz');
			earthPanel.fetchKml('http://www.globalquakemodel.org/tools/risk/data/indonesia.kmz');
			earthPanel.fetchKml('http://www.globalquakemodel.org/tools/risk/data/chile.kmz');
			//earthPanel.fetchKml('http://earthquake.usgs.gov/earthquakes/catalogs/eqs7day-age_src.kmz');
			earthPanel.fetchKml('http://www.globalquakemodel.org/tools/risk/data/Haiti3.kmz');
			//earthPanel.fetchKml('http://www.globalquakemodel.org/tools/risk/data/US_West.kmz');
			
			
			// Add panels
			controlPanel.add(earthPanel.getKmlPanel());
			controlPanel.add(earthPanel.getLocationPanel());
			controlPanel.add(earthPanel.getLayersPanel());
			controlPanel.add(earthPanel.getOptionsPanel());
			controlPanel.doLayout();

		});

		var accordion2 = new Ext.Panel({
			collapsible:true,
			//hideCollapseTool: true,
			collapsed: true,
			title:"3D Globe Controls",
			//title:"&nbsp;",
			region:'east',
			//margins:'5 0 5 5',
			//split:true,
			width: 200,
			layout:'accordion',
			split: true,
			items: [controlPanel]
		});
		
/*		var accordion3 = new Ext.Panel({*/
/*			id: 'WMS',*/
/*			collapsible: false,*/
/*			//hideCollapseTool: true,*/
/*			//collapsed: true,*/
/*			frame: false,*/
/*			//title:"GEM1 Results",*/
/*			//region:'east',*/
/*			//margins:'5 0 5 5',*/
/*			//split:true,*/
/*			autoScroll: true,*/
/*			//layout:'accordion',*/
/*			//split: true,*/
/*			//items: [menubar]*/
/*		});*/
		

		
		var south = new Ext.Panel({
			collapsible:true,
			collapsed: true,
			animate: true,
			//hideCollapseTool: true,
			title:"Log/Info",
			region: 'south',
			layout:'accordion',
			header : true,
			autoScroll: true,
			titleCollapse: true,
			height: 80, 
			split: true,
			//items: [item6]
 
            });
			
		var Layer = new Ext.Panel({
			collapsible:false,
			//title:"Log/Info",
			region: 'center',
			//height: 80, 
			//split: true,
			layout:'fit',
			//items: [mapPanel]
			});
			
			var aSampleChart = new Ext.Panel(
            {
				id: "aSampleChart",
				frame: false,
        border: false,
        listeners: { render: function(component) {
					myData = new Array([0.05, 1.0], [0.08, 0.95], [0.10, 0.90], [0.13, 0.85], [0.15, 0.80], [0.20, 0.75], [0.25, 0.70], [0.35, 0.60], [0.45, 0.50], [0.58, 0.40], [0.65, 0.35], [0.70, 0.32], [0.75, 0.30], [0.98, 0.23], [1.10, 0.20], [1.35, 0.15], [1.35, 0.15], [1.55, 0.12], [1.70, 0.11], [1.85, 0.10], [2.3, 0.09], [3.0, 0.08], [5.0, 0.05], [10.0, 0.0]);
					myChart = new JSChart("aSampleChart", 'line');
					myChart.setDataArray(myData);
					myChart.setAxisNameFontSize(10);
					myChart.setAxisNameX('Human losses');
					myChart.setAxisNameY('Probabiliy of exceedance in 50 years');
					myChart.setAxisNameColor('#787878');
					myChart.setAxisValuesNumberX(6);
					myChart.setAxisValuesNumberY(5);
					myChart.setAxisValuesColor('#38a4d9');
					myChart.setAxisColor('#38a4d9');
					myChart.setLineColor('#C71112');
					myChart.setTitle('Loss Curve (LC)');
					myChart.setTitleColor('#383838');
					myChart.setGraphExtend(true);
					myChart.setGridColor('#38a4d9');
					myChart.setSize(800, 500);
					myChart.setAxisPaddingLeft(140);
					myChart.setAxisPaddingRight(140);
					myChart.setAxisPaddingTop(60);
					myChart.setAxisPaddingBottom(45);
					myChart.setTextPaddingLeft(105);
					myChart.setTextPaddingBottom(12);
					myChart.draw();
				}}
			});	
			
		var center = new Ext.Panel({
			collapsible:false,
			//title:"Log/Info",
			region: 'center',
			animCollapse: true,
			
			border: false,
			//height: 80, 
			//split: true,
			layout:'fit',
			items: [{
				xtype : "tabpanel",
				border: false,
				items : [
				{
					xtype : "panel",
					layout:'fit',
					iconCls:'icon-map',
					title : "Home",
					items:[portalTest3]
				},
				{
					xtype : "panel",
					layout:'fit',
					iconCls:'icon-map',
					title : "My Page (Basic)",
					items:[portalTest2]
				},
				/*{*/
/*					xtype : "panel",*/
/*					layout:'fit',*/
/*					iconCls:'icon-map',*/
/*					title : "My Page Power",*/
/*					items:[myPage2]*/
/*				},*/
								{
					xtype : "panel",
					layout:'fit',
					iconCls:'icon-map',
					title : "My Page (Expert)",
					items:[portalTest]
				},
				{
					xtype : "panel",
					layout:'fit',
					iconCls:'icon-map', 
					title : "Map",
					items:[mapPanel]
				},
				/*{*/
/*					xtype : "panel",*/
/*					iconCls:'icon-data',*/
/*					layout:'fit',*/
/*					title : "Results Layers Store",*/
/*					items:[accordion3]*/
/*				},*/
				{
					xtype : "panel",
					layout:'fit',
					iconCls:'icon-globe',
					title : "3D Globe",
					hideMode: "nosize",
					items:[earthPanel]
				},
				{
					xtype : "panel",
					iconCls:'icon-chart',
					layout:'fit',
					title : "Plot",
					closable:true,
					items:[aSampleChart]
				},
				{
					xtype : "panel",
					iconCls:'icon-agrid',
					layout:'fit',
					title : "Table",
					closable:true, 
					items:[lossGrid]
				},
				],
				activeTab : 0
			}]
			});
		
		
		
			/*var myData = new Array([0.001, 1.0], [0.01, 0.8], [0.10, 0.5], [1.0, 0.2], [10.0, 0.0]);
			var myChart = new JSChart("aSampleChart", 'line');
			myChart.setDataArray(myData);
			myChart.setAxisNameFontSize(10);
			myChart.setAxisNameX('Human losses');
			myChart.setAxisNameY('Probabiliy of exceedance in 50 years');
			myChart.setAxisNameColor('#787878');
			myChart.setAxisValuesNumberX(6);
			myChart.setAxisValuesNumberY(5);
			myChart.setAxisValuesColor('#38a4d9');
			myChart.setAxisColor('#38a4d9');
			myChart.setLineColor('#C71112');
			myChart.setTitle('Loss Curve (LC)');
			myChart.setTitleColor('#383838');
			myChart.setGraphExtend(true);
			myChart.setGridColor('#38a4d9');
			myChart.setSize(800, 600);
			myChart.setAxisPaddingLeft(140);
			myChart.setAxisPaddingRight(140);
			myChart.setAxisPaddingTop(60);
			myChart.setAxisPaddingBottom(45);
			myChart.setTextPaddingLeft(105);
			myChart.setTextPaddingBottom(12);
			//myChart.setBackgroundImage('chart_bg.jpg');
			myChart.draw();*/
		
/*//Simple Form 2 button*/
/*    // Define the Submit button and the action required. This will be enabled if the Load is successful.*/
/*    accordion.addButton({*/
/*        text: 'Submit',*/
/*        //disabled:true,*/
/*        handler: function(){*/
/*            simpleForm2.form.submit({*/
/*                //url:'json-form-submit.cfm', // Coldfusion */
/*                url:'json-form-submit.php', // PHP*/
/*                waitMsg:'Submitting Request...',*/
/*                success: function (form, action) {*/
/*                    Ext.MessageBox.alert('Message', 'Your request has been submitted');*/
/*                },*/
/*                failure:function(form, action) {*/
/*                    Ext.MessageBox.alert('Message', 'Save failed');*/
/*                }*/
/*            });*/
/*        }*/
/*    });*/
		

		
//viewport
        var viewport = new Ext.Viewport({
                layout:'border',
				//renderTo: 'ben',
				items:[
                    accordion, 
					accordion2, 
					center,
					south,
							
					new Ext.BoxComponent({
						region: 'north',
						height: 75, // give north and south regions a height
						autoEl: {
							tag: 'div',
							html: '<div style="background-image: url(\'images/Banner_UP_partb.png\'); background-repeat: repeat-x;"> <img src="images/Banner_UP_parta.png" style="align: left;">  <img src="images/User-Platform_c.png ALIGN=RIGHT></div>'

						}
					}),

				]	
            });
	
});