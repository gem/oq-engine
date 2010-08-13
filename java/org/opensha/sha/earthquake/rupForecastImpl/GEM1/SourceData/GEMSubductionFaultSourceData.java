package org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData;

import java.io.Serializable;

import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

public class GEMSubductionFaultSourceData extends GEMSourceData implements Serializable {
	
	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;
	
	private FaultTrace topTrace;
	private FaultTrace bottomTrace;
	private double rake;
	private IncrementalMagFreqDist mfd;	
	private boolean floatRuptureFlag;

	
	// constructor.  TectonicRegionType defaults to SUBDUCTION_INTERFACE here.
	public GEMSubductionFaultSourceData(FaultTrace TopTrace, FaultTrace BottomTrace, 
			double rake, IncrementalMagFreqDist mfd, boolean floatRuptureFlag){
		
		this.topTrace = TopTrace;
		this.bottomTrace = BottomTrace;
		this.rake = rake;
		this.mfd = mfd;
		this.floatRuptureFlag = floatRuptureFlag;
		this.tectReg = TectonicRegionType.SUBDUCTION_INTERFACE;
		
	}
	
	// constructor.  TectonicRegionType defaults to SUBDUCTION_INTERFACE here.
	public GEMSubductionFaultSourceData(String id, String name, TectonicRegionType tectReg,
			FaultTrace TopTrace, FaultTrace BottomTrace, 
			double rake, IncrementalMagFreqDist mfd, boolean floatRuptureFlag){
		this.id = id;
		this.name = name;
		this.tectReg = tectReg;
		this.topTrace = TopTrace;
		this.bottomTrace = BottomTrace;
		this.rake = rake;
		this.mfd = mfd;
		this.floatRuptureFlag = floatRuptureFlag;
		
	}

	public FaultTrace getTopTrace() {
		return topTrace;
	}

	public FaultTrace getBottomTrace() {
		return bottomTrace;
	}

	public double getRake() {
		return rake;
	}

	public IncrementalMagFreqDist getMfd() {
		return mfd;
	}
	
	public boolean getFloatRuptureFlag() {
		return floatRuptureFlag;
	}



}
