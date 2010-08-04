package scratch.kevin;

import org.opensha.sha.imr.attenRelImpl.SadighEtAl_1997_AttenRel;
import org.opensha.sha.imr.param.EqkRuptureParams.FaultTypeParam;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceRupParameter;

public class SadighTest {

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		SadighEtAl_1997_AttenRel imr = new SadighEtAl_1997_AttenRel(null);
		imr.setParamDefaults();
		
		imr.getParameter(DistanceRupParameter.NAME).setValue(new Double(10.0));
		imr.getParameter(MagParam.NAME).setValue(new Double(6.5));
		imr.getParameter(FaultTypeParam.NAME).setValue("Reverse");
		imr.getParameter(SadighEtAl_1997_AttenRel.SITE_TYPE_NAME).setValue("Deep-Soil");
		imr.getParameter(StdDevTypeParam.NAME).setValue("Total");
		
		imr.setIntensityMeasure(SA_Param.NAME);
		SA_Param.setPeriodInSA_Param(imr.getIntensityMeasure(), 0.075);
		
		System.out.println(imr.getAllParamMetadata().replaceAll("; ", ";\n"));
		
		double mean = Math.exp(imr.getMean());
		System.out.println("Mean: " + mean);
		double stdDev = Math.exp(imr.getStdDev());
		System.out.println("Std Dev: " + stdDev);
	}

}
