package org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData;

import org.opensha.sha.util.TectonicRegionType;

public abstract class GEMSourceData {

    protected String id;
    protected String name;
    protected TectonicRegionType tectReg;

    /**
     * 
     * @return
     */
    public TectonicRegionType getTectReg() {
        return tectReg;
    }

    /**
     * 
     * @return
     */
    public void setTectReg(TectonicRegionType tectReg) {
        this.tectReg = tectReg;
    }

    /**
	 * 
	 */
    public String getID() {
        return this.id;
    }

    /**
     * 
     * @return
     */
    public String getName() {
        return this.name;
    }

    public void setName(String name) {
        this.name = name;
    }

}
