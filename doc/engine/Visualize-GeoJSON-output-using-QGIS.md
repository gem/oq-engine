When you wish to visualize a GeoJson file, one option is to use QGIS to view and thematically represent the data. Here we describe how to do this.

### Get QGIS:
QGIS ( download at: http://www.qgis.org/ ) Quantum GIS (QGIS) is a user friendly Open Source Geographic Information System (GIS) licensed under the GNU General Public License available for all common operating systems. Download and install on your computer.

### Add the layer:
Add the GeoJSON layer to QGIS by opening QGIS and dragging & dropping the file into QGIS.
You should now see dots (assuming that your GeoJSON is point data) in the map viewport that represent your data. 

### View the layer in a geographic context (optional)
To get an idea of where this data is in the world you can add an OpenStreetMap map to your map viewport. From the main menu click on **Plugins** - **Fetch Python Plugins** and then search for OpenLayers plugin and select **install**. Now add a base map to your map viewport by clicking **Plugins** - **OpenLayers Plugin** and select the base map you prefer.

### Thematically represent your data
From the layers panel right click on the GeoJSON layer and select properties. From the **Style tab**, select the pull down labeled Single Symbol and select **Categorized**. Make sure to select the appropriate attribute from which the thematic map will be based by selected the **Column** pull and selecting the column that contains the value you wish to map. Next click on **Classify**, and then click **OK**.
Obviously there are many different ways in which one can represent the data in QGIS, the above is just a basic introduction.