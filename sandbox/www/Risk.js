	
	//Google Earth API stuff
        google.load("earth", "1");
        google.load("maps", "2.xx");
		Ext.onReady(function (){

//login form
/*
		var msg = function(title, msg) {
		Ext.Msg.show({
			title: title,
			msg: msg,
			minWidth: 200,
		    modal: true,
			icon: Ext.Msg.INFO,
			buttons: Ext.Msg.OK
		});

	};
		*/	   
	   var loginForm1 = new Ext.form.FormPanel({
				//frame:false,
				width:100, 
				height: 22,				
				labelWidth:.1,         
				defaults: {
						width: 100,
				},
				items: [
						new Ext.form.TextField({
					id:"username",
					emptyText: "username",
					//frame:false,
					//fieldLabel:"Username",
					//allowBlank:false,
					//blankText:"Enter your username"
				})

				],
		});
/*
		var loginWindow = new Ext.Window({
				title: 'Welcome to At-byte',
				layout: 'fit',                 
				height: 140,
				width: 200,                            
				closable: false,
				resizable: false,                              
				draggable: false,
				items: [loginForm]                     

		});
	*/
	   var loginForm2 = new Ext.form.FormPanel({
				//frame:false,
				width:100, 
				height: 22,				
				labelWidth:.1,         
				defaults: {
						width: 100,
				},
				items: [
						new Ext.form.TextField({
					id:"password",
					emptyText: "password",
					//fieldLabel:"password",
					allowBlank:false,
					//blankText:"Enter your password"
				})

				],
		/*		
		buttons: [{
					text: 'Login',                         
					handler: function(){
			if(loginForm.getForm().isValid()){
					loginForm.getForm().submit({
						//url: 'check_login.php',
						//waitMsg: 'Processing Request',
						success: function(loginForm, resp){
							msg('Success', 'Welcome "'+ resp.result.message +'" on the cluster manager');
						}
					});
				}
			}
		}]
			*/	
		});
		

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
		/*	
        buttons: [{
            text: 'Submit',
			handler: function () {
				// when this button clicked, sumbit this form
				simpleForm1.getForm().submit({
					waitMsg: 'Saving...',		// Wait Message
					success: function () {		// When saving data success
						Ext.MessageBox.alert ('Message','Data has been saved');
						// clear the form
						simpleForm1.getForm().reset();
					},
					failure: function () {		// when saving data failed
						Ext.MessageBox.alert ('Message','Saving data failed');
					}
				});
			}
        }
		/*{
            text: 'Cancel',
			handler: function () {
				// when this button clicked, reset this form
				simpleForm1.getForm().reset();
			}
			
        }*/
		/*
		]
*/

			
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
				'->', 
				{iconCls:'icon-save'}, 
				{iconCls:'icon-pdf'}, 
				{iconCls:'icon-kml'}, 
				{iconCls:'icon-print'}, 
				loginForm1, 
				loginForm2
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
		    expanded: true
		    })
        );

		layerRoot.appendChild(new GeoExt.tree.OverlayLayerContainer
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

		var Tree1 = new Ext.tree.TreePanel
		    ({
		    //title: "Map Layers",
		    root: layerRoot,
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
        // load the store with records derived from the doc at the above url
        store5.load();

    	function PELM01() {
        // create a grid to display records from the store 5
        var grid5 = new Ext.grid.GridPanel({
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
			title: 'Layers',
			//html: "&nbsp;",
			//renderTo: document.body,
			//cls:"&nbsp;"
			enableDragDrop: true,
			hideBorders: true,
			items:[Tree1],
			autoScroll: true
		});

		var item2 = new Ext.Panel({
			title: 'Location',
			//html: '&lt;empty panel&gt;',
			//cls:'empty'
			hideBorders: true,
			items:[simpleForm1],
			autoScroll: true
		});

		var item3 = new Ext.Panel({
			title: 'Scenario Risk Results Viewer',
			autoScroll: true,
			hideBorders: true,
			defaults:{border:false, activeTab:0},
				items:[{
					defaults:{layout:'fit', border: false, hideMode:"offsets"},
					//autoScroll: true,
					//resizable:true,
					xtype:'tabpanel',
						items:[{
						title:'Loss Maps',
							items:[simpleForm2],
							autoScroll: true,
							//resizable:true
						},{
						title:'Limit State Maps'
						}]
					}]
						
			//html: '<body><td><button id="singleStatus" onclick="toggle("single")">off</button></td><td><textarea class="output" id="singleOutput"></textarea></td></tr><tr></body>'
			//cls:'empty'
			//renderTo: toggle
		});
		var item4 = new Ext.Panel({
			title: 'Global Risk Results Viewer',
			hideBorders: true,
			autoScroll: true,
			defaults:{border:false, activeTab:0},
				items:[{
					defaults:{layout:'fit', border: false, hideMode:"offsets"},
					//autoScroll: true,
					//resizable:true,
					xtype:'tabpanel',
						items:[{
						title:'Loss Maps',
							items:[simpleForm3],
							autoScroll: true,
							//resizable:true
								},{
								title:'Loss Curves'
								},/*{
								title:'Limit State Maps'
								},{
								title:'Limit State Curves'
								}*/
						]
					}]
						
			//html: '<body><td><button id="singleStatus" onclick="toggle("single")">off</button></td><td><textarea class="output" id="singleOutput"></textarea></td></tr><tr></body>'
			//cls:'empty'
			//renderTo: toggle
		});
		/*
		var item5 = new Ext.Panel({
			title: 'Risk Calculator',
			//html: '&lt;empty panel&gt;',
			//cls:'empty'
			
		});
		*/
/*
		var item6 = new Ext.Panel({
			title: 'Global Risk Calculator',
			//html: '<b>A Global Earthquake Model</b><p>GEM is a public/private partnership initiated and approved by the Global Science Forum of the Organisation for Economic Co-operation and Development (OECD-GSF).</p><p><b>More information at: <a href="http://www.globalquakemodel.org">globalquakemodel.org</a></b></p>'
			//cls: 'item5'
			
		});
*/
		var accordion = new Ext.Panel({
			collapsible:true,
			title:"Risk Panel",
			region:'west',
			//margins:'5 0 5 5',
			//split:true,
			showPin: true,
			width: 305,
			layout:'accordion',
			split: true,
			items: [item1, item2, item3, item4]
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
		
		var accordion3 = new Ext.Panel({
			id: 'WMS',
			collapsible: false,
			//hideCollapseTool: true,
			//collapsed: true,
			frame: false,
			//title:"GEM1 Results",
			//region:'east',
			//margins:'5 0 5 5',
			//split:true,
			autoScroll: true,
			//layout:'accordion',
			//split: true,
			items: [menubar]
		});
		

		
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
				items : [{
					xtype : "panel",
					layout:'fit',
					iconCls:'icon-map',
					title : "Map",
					items:[mapPanel]
				},
				{
					xtype : "panel",
					iconCls:'icon-data',
					layout:'fit',
					title : "Results Layers Store",
					items:[accordion3]
				},
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
		
		
		
//Simple Form 2 button
    // Define the Submit button and the action required. This will be enabled if the Load is successful.
    accordion.addButton({
        text: 'Submit',
        //disabled:true,
        handler: function(){
            simpleForm2.form.submit({
                //url:'json-form-submit.cfm', // Coldfusion 
                url:'json-form-submit.php', // PHP
                waitMsg:'Submitting Request...',
                success: function (form, action) {
                    Ext.MessageBox.alert('Message', 'Your request has been submitted');
                },
                failure:function(form, action) {
                    Ext.MessageBox.alert('Message', 'Save failed');
                }
            });
        }
    });
		

		
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