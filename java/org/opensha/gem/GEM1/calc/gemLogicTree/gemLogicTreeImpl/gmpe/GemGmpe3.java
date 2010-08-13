package org.opensha.gem.GEM1.calc.gemLogicTree.gemLogicTreeImpl.gmpe;

import java.util.HashMap;


import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.gem.GEM1.calc.gemLogicTree.GemLogicTree;
import org.opensha.gem.GEM1.calc.gemLogicTree.GemLogicTreeBranch;
import org.opensha.gem.GEM1.calc.gemLogicTree.GemLogicTreeBranchingLevel;
import org.opensha.gem.GEM1.scratch.AtkBoo_2006_AttenRel;
import org.opensha.gem.GEM1.scratch.ZhaoEtAl_2006_AttenRel;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.CY_2008_AttenRel;
import org.opensha.sha.util.TectonicRegionType;

public class GemGmpe3 {
	
    // logic tree for GMPE
    private GemLogicTree<HashMap<TectonicRegionType,ScalarIntensityMeasureRelationshipAPI>> gmpeLT =
    	new GemLogicTree<HashMap<TectonicRegionType,ScalarIntensityMeasureRelationshipAPI>>();
    
    public GemGmpe3(){
    	
        ParameterChangeWarningEvent event = null;
	
	    // SHALLOW ACTIVE
		// Boore and Atkinson 2008
	    AttenuationRelationship ar1 = null;
//	    ar1 = new BA_2008_AttenRel(ParameterChangeWarningListener(event));
	    ar1 = new CY_2008_AttenRel(ParameterChangeWarningListener(event));
	    // set defaults parameters
	    ar1.setParamDefaults();
	    
	    // SUBDUCTION INTERFACE AND INTRASLAB
	    AttenuationRelationship ar3 = null;
	    ar3 = new ZhaoEtAl_2006_AttenRel(ParameterChangeWarningListener(event));
	    ar3.setParamDefaults();
	    
	    // STABLE SHALLOW
	    AttenuationRelationship ar4 = null;
	    ar4 = new AtkBoo_2006_AttenRel(ParameterChangeWarningListener(event));
	    ar4.setParamDefaults();
	    
	    // HashMap containing relationship between attenuation relationship and tectonic region type
	    HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> map1 = 
	    	      new HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>();
	    map1.put(TectonicRegionType.ACTIVE_SHALLOW,ar1);
	    map1.put(TectonicRegionType.STABLE_SHALLOW,ar4);
	    map1.put(TectonicRegionType.SUBDUCTION_SLAB, ar3);
	    map1.put(TectonicRegionType.SUBDUCTION_INTERFACE, ar3);
	    
	    // logic tree for GMPE
	    // 1st branching level
	    // 0 means apply to all previous branching levels
		GemLogicTreeBranchingLevel braLev1gmpe = new GemLogicTreeBranchingLevel(1,"gmpe",0);
		// create branch(s)
		GemLogicTreeBranch bra1gmpe = new GemLogicTreeBranch(1,"B&A2008_ZHAO2006_A&B2006",1.0);
		// add to branching level
		braLev1gmpe.addTreeBranch(bra1gmpe);
		// add branching level to logic tree
		gmpeLT.addBranchingLevel(braLev1gmpe);
	    // add end branch mapping
	    gmpeLT.addEBMapping("1", map1);
	
}

// return the logic tree
public GemLogicTree<HashMap<TectonicRegionType,ScalarIntensityMeasureRelationshipAPI>> getGemLogicTree(){
	return gmpeLT;
}

/**
 * 
 * @param event
 * @return
 */
private static ParameterChangeWarningListener ParameterChangeWarningListener(
		ParameterChangeWarningEvent event) {
	return null;
}


}
