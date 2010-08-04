package scratch.matt.calc;

public class CalcAIC_Weights {
	
	//private double genAIC, seqAIC, spaAIC;
    private static double genWeight, seqWeight, spaWeight;
	
	//public CalcAIC_Weights(){
	//}
	
	
	public static void calcWeights(double genAIC, double seqAIC, double spaAIC){
		double[] eDi = new double[3];
		double minAIC = genAIC;
		if (seqAIC < minAIC)
			minAIC = seqAIC;
		if (spaAIC < minAIC)
			minAIC = spaAIC;
		
		eDi[0] = Math.exp(-0.5*(genAIC - minAIC));
		eDi[1] = Math.exp(-0.5*(seqAIC - minAIC));
		eDi[2] = Math.exp(-0.5*(spaAIC - minAIC));
		
		double sum_eDi = eDi[0] + eDi[1] + eDi[2];
		genWeight = eDi[0]/sum_eDi;
		seqWeight = eDi[1]/sum_eDi;
		spaWeight = eDi[2]/sum_eDi;
	}
	
	public static double getGenWeight(){
		return genWeight;
	}
	
	public static double getSeqWeight(){
		return seqWeight;
	}
	
	public static double getSpaWeight(){
		return spaWeight;
	}

}
