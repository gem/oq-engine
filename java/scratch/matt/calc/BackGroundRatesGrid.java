package scratch.matt.calc;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.ListIterator;
import java.util.StringTokenizer;

import org.apache.log4j.Logger;
import org.opensha.commons.data.region.SitesInGriddedRegion;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.earthquake.griddedForecast.GriddedHypoMagFreqDistForecast;
import org.opensha.sha.earthquake.griddedForecast.HypoMagFreqDistAtLoc;
import org.opensha.sha.earthquake.rupForecastImpl.PointEqkSource;
import org.opensha.sha.magdist.IncrementalMagFreqDist;

public class BackGroundRatesGrid extends GriddedHypoMagFreqDistForecast  {
	private static Logger logger = Logger.getLogger(BackGroundRatesGrid.class);

	private double minForecastMag, maxForecastMag, deltaForecastMag;
	private double minMagInSourceFile = 2.0;
	private double[] seqIndAtNode;
	// booleans to help decide if sources need to be made
	private boolean deltaSourcesAlreadyMade = false;
	private boolean backgroundSourcesAlreadyMade = false;
	private boolean backgroundRatesFileAlreadyRead = false;
	//private final static String BACKGROUND_RATES_FILE_NAME = "org/opensha/sha/earthquake/rupForecastImpl/step/AllCal96ModelDaily.txt";
	private String bgGridFilename = RegionDefaults.BACKGROUND_RATES_FILE_NAME;

	// misc values
	private static final double RAKE=0.0;
	private static final double DIP=90.0;
	public static final double DEPTH=0;
	private final double GRID_SPACING= 0.1; 
    
	//private Comparator <HypoMagFreqDistAtLoc> locationComparator;

	/**
	 * stores HypoMagFreqDistAtLoc, 
	 * N.B.
	 * it is an assumption that the hypoMagFreqDistAtLoc list contain the same number and order of locations as 
	 * those in the region grid list, but this is not true for california, may be a map should be used to store the 
	 * hypoMagFreqDist
	 */
	private ArrayList<HypoMagFreqDistAtLoc> hypoMagFreqDist;
	//this map will eventually replace the above list, to cope with the location match problem
	private HashMap<String,HypoMagFreqDistAtLoc> hypoMagFreqDistMap;
	
	private ArrayList backGroundSourceList;

	public BackGroundRatesGrid()
	{
	  minForecastMag = RegionDefaults.minForecastMag;
	  maxForecastMag =  RegionDefaults.maxForecastMag;
	  deltaForecastMag = RegionDefaults.deltaForecastMag;

	}

	public BackGroundRatesGrid(double minForecastMag, double maxForecastMag, double deltaForecastMag)
	{
		this.minForecastMag = minForecastMag;
		this.maxForecastMag = maxForecastMag;
		this.deltaForecastMag = deltaForecastMag;
	}

	/**
	 * 
	 * @param fileName
	 */
	public BackGroundRatesGrid(String fileName){	
		//take default values for minForecastMag, maxForecastMag, deltaForecastMag??		
		this();		
		setBgGridFilename(fileName);
		initialize();
	}

	public void initialize(){
//	{   if(locationComparator == null){
//			locationComparator = new Comparator <HypoMagFreqDistAtLoc>  (){
//				public int compare(HypoMagFreqDistAtLoc hyp1, HypoMagFreqDistAtLoc hyp2) {	
//					//Location loc1 = hyp1.getLocation(), loc2 = hyp2.getLocation();
//					if(hyp2.getLocation().getLatitude() == hyp1.getLocation().getLatitude()){
//							return (int)(100*hyp1.getLocation().getLongitude() -100*hyp2.getLocation().getLongitude()) ;//					
//					}
//					return (int)(100*hyp1.getLocation().getLatitude() -100*hyp2.getLocation().getLatitude()) ;//	
//				}		
//			};
//		}
	    //create the region grid
	    createBackGroundRegion();		
		loadBackGroundGridFromFile(bgGridFilename);		
		initSeqIndices();
	}

	/**
	 * //region must be initialised before this can be done
		// set to a dummy value representing the background so that 
		// it can be changed to a sequence index if required later
		// this indicates the sequence that contributes rates at this
		// index.  -1 means no sequence does.
	 */
	public void initSeqIndices()
	{
		if(seqIndAtNode == null)
			seqIndAtNode = new double[getRegion().getNodeCount()];
		logger.info((new StringBuilder()).append("seqIndAtNode ").append(seqIndAtNode.length).toString());
		Arrays.fill(seqIndAtNode, -1D);
	}

	public void setBgGridFilename(String bgGridFilename)
	{
		this.bgGridFilename = bgGridFilename;
	}

	

	/**
	 * Setting the Relm Region to the region for the STEP code.
	 */
	private void createBackGroundRegion(){
		/**
		 * creates locationlist of california boundary.
		 * @return
		 */
		/*LocationList locList = new LocationList();
	   locList.addLocation(new Location(41.998016,-124.210136));
	   locList.addLocation(new Location(41.995640,-123.820290));
	   locList.addLocation(new Location(41.997173,-123.726974));
	   locList.addLocation(new Location(41.995300,-123.655823));
	   locList.addLocation(new Location(42.000000,-123.623375));
	   locList.addLocation(new Location(42.001015,-123.516739));
	   locList.addLocation(new Location(42.001801,-123.433601));
	   locList.addLocation(new Location(41.999264,-123.346390));
	   locList.addLocation(new Location(42.004002,-123.229599));
	   locList.addLocation(new Location(42.009399,-123.144798));
	   locList.addLocation(new Location(42.003201,-123.044106));
	   locList.addLocation(new Location(42.002750,-122.892815));
	   locList.addLocation(new Location(42.005001,-122.633598));
	   locList.addLocation(new Location(42.009655,-122.377068));
	   locList.addLocation(new Location(42.007900,-122.288399));
	   locList.addLocation(new Location(41.997303,-121.446503));
	   locList.addLocation(new Location(41.997692,-121.250000));
	   locList.addLocation(new Location(41.993443,-121.034210));
	   locList.addLocation(new Location(41.993900,-120.878403));
	   locList.addLocation(new Location(41.993053,-120.293373));
	   locList.addLocation(new Location(41.994652,-119.998116));
	   locList.addLocation(new Location(41.184078,-119.998817));
	   locList.addLocation(new Location(40.500000,-119.994888));
	   locList.addLocation(new Location(40.000000,-119.996246));
	   locList.addLocation(new Location(39.722511,-120.000290));
	   locList.addLocation(new Location(39.445206,-120.002090));
	   locList.addLocation(new Location(39.316444,-120.004295));
	   locList.addLocation(new Location(39.165684,-120.003441));
	   locList.addLocation(new Location(39.112782,-120.002411));
	   locList.addLocation(new Location(39.067585,-120.001450));
	   locList.addLocation(new Location(38.999668,-120.000000));
	   locList.addLocation(new Location(38.933414,-119.903305));
	   locList.addLocation(new Location(38.713306,-119.584435));
	   locList.addLocation(new Location(38.620056,-119.449615));
	   locList.addLocation(new Location(38.609127,-119.434067));
	   locList.addLocation(new Location(38.534882,-119.327408));
	   locList.addLocation(new Location(38.414833,-119.155991));
	   locList.addLocation(new Location(37.896290,-118.427193));
	   locList.addLocation(new Location(37.465000,-117.831802));
	   locList.addLocation(new Location(36.971176,-117.165108));
	   locList.addLocation(new Location(36.004211,-115.897507));
	   locList.addLocation(new Location(35.809021,-115.646362));
	   locList.addLocation(new Location(35.002083,-114.632217));
	   locList.addLocation(new Location(34.986149,-114.628220));
	   locList.addLocation(new Location(34.965149,-114.634438));
	   locList.addLocation(new Location(34.943039,-114.628967));
	   locList.addLocation(new Location(34.924606,-114.632454));
	   locList.addLocation(new Location(34.907261,-114.630081));
	   locList.addLocation(new Location(34.889103,-114.635925));
	   locList.addLocation(new Location(34.869968,-114.632256));
	   locList.addLocation(new Location(34.859737,-114.623146));
	   locList.addLocation(new Location(34.847355,-114.599854));
	   locList.addLocation(new Location(34.835667,-114.586044));
	   locList.addLocation(new Location(34.815296,-114.575653));
	   locList.addLocation(new Location(34.794289,-114.570213));
	   locList.addLocation(new Location(34.766869,-114.551888));
	   locList.addLocation(new Location(34.750816,-114.528824));
	   locList.addLocation(new Location(34.736740,-114.515823));
	   locList.addLocation(new Location(34.725697,-114.491226));
	   locList.addLocation(new Location(34.716621,-114.486710));
	   locList.addLocation(new Location(34.712208,-114.470192));
	   locList.addLocation(new Location(34.691196,-114.464455));
	   locList.addLocation(new Location(34.666828,-114.449715));
	   locList.addLocation(new Location(34.657104,-114.457191));
	   locList.addLocation(new Location(34.642525,-114.440674));
	   locList.addLocation(new Location(34.621449,-114.437943));
	   locList.addLocation(new Location(34.610443,-114.423409));
	   locList.addLocation(new Location(34.600834,-114.424545));
	   locList.addLocation(new Location(34.596066,-114.436012));
	   locList.addLocation(new Location(34.580700,-114.421593));
	   locList.addLocation(new Location(34.569630,-114.404442));
	   locList.addLocation(new Location(34.529713,-114.380051));
	   locList.addLocation(new Location(34.507275,-114.377335));
	   locList.addLocation(new Location(34.495747,-114.381569));
	   locList.addLocation(new Location(34.476028,-114.380913));
	   locList.addLocation(new Location(34.457901,-114.385910));
	   locList.addLocation(new Location(34.446926,-114.372925));
	   locList.addLocation(new Location(34.450905,-114.336685));
	   locList.addLocation(new Location(34.446640,-114.330978));
	   locList.addLocation(new Location(34.437843,-114.325928));
	   locList.addLocation(new Location(34.426796,-114.300232));
	   locList.addLocation(new Location(34.419510,-114.292610));
	   locList.addLocation(new Location(34.409771,-114.290367));
	   locList.addLocation(new Location(34.405327,-114.286018));
	   locList.addLocation(new Location(34.400360,-114.262131));
	   locList.addLocation(new Location(34.376648,-114.233490));
	   locList.addLocation(new Location(34.365906,-114.225327));
	   locList.addLocation(new Location(34.361359,-114.198692));
	   locList.addLocation(new Location(34.349293,-114.176125));
	   locList.addLocation(new Location(34.339500,-114.168022));
	   locList.addLocation(new Location(34.317848,-114.156425));
	   locList.addLocation(new Location(34.303215,-114.137505));
	   locList.addLocation(new Location(34.274364,-114.135887));
	   locList.addLocation(new Location(34.262714,-114.130432));
	   locList.addLocation(new Location(34.258450,-114.132484));
	   locList.addLocation(new Location(34.259686,-114.163864));
	   locList.addLocation(new Location(34.253338,-114.163086));
	   locList.addLocation(new Location(34.250000,-114.165344));
	   locList.addLocation(new Location(34.247288,-114.173813));
	   locList.addLocation(new Location(34.239956,-114.177269));
	   locList.addLocation(new Location(34.211525,-114.210976));
	   locList.addLocation(new Location(34.203629,-114.224419));
	   locList.addLocation(new Location(34.193878,-114.224159));
	   locList.addLocation(new Location(34.186913,-114.228935));
	   locList.addLocation(new Location(34.183216,-114.239929));
	   locList.addLocation(new Location(34.172825,-114.256248));
	   locList.addLocation(new Location(34.170162,-114.267677));
	   locList.addLocation(new Location(34.172134,-114.274483));
	   locList.addLocation(new Location(34.170517,-114.286514));
	   locList.addLocation(new Location(34.138618,-114.319992));
	   locList.addLocation(new Location(34.134022,-114.335327));
	   locList.addLocation(new Location(34.133102,-114.352249));
	   locList.addLocation(new Location(34.118561,-114.365738));
	   locList.addLocation(new Location(34.115971,-114.378448));
	   locList.addLocation(new Location(34.110069,-114.389778));
	   locList.addLocation(new Location(34.111637,-114.400818));
	   locList.addLocation(new Location(34.110016,-114.410896));
	   locList.addLocation(new Location(34.103451,-114.419708));
	   locList.addLocation(new Location(34.088394,-114.432594));
	   locList.addLocation(new Location(34.079712,-114.434639));
	   locList.addLocation(new Location(34.057877,-114.438553));
	   locList.addLocation(new Location(34.037769,-114.434158));
	   locList.addLocation(new Location(34.022591,-114.437477));
	   locList.addLocation(new Location(34.012562,-114.449417));
	   locList.addLocation(new Location(34.010971,-114.465080));
	   locList.addLocation(new Location(34.005177,-114.466522));
	   locList.addLocation(new Location(34.000000,-114.458397));
	   locList.addLocation(new Location(33.995541,-114.457840));
	   locList.addLocation(new Location(33.992859,-114.467140));
	   locList.addLocation(new Location(33.961773,-114.499100));
	   locList.addLocation(new Location(33.957508,-114.507881));
	   locList.addLocation(new Location(33.958088,-114.515076));
	   locList.addLocation(new Location(33.954647,-114.522339));
	   locList.addLocation(new Location(33.934635,-114.534691));
	   locList.addLocation(new Location(33.925076,-114.532906));
	   locList.addLocation(new Location(33.917500,-114.517647));
	   locList.addLocation(new Location(33.911076,-114.510719));
	   locList.addLocation(new Location(33.903790,-114.507126));
	   locList.addLocation(new Location(33.900623,-114.507919));
	   locList.addLocation(new Location(33.897942,-114.512924));
	   locList.addLocation(new Location(33.901569,-114.523499));
	   locList.addLocation(new Location(33.900215,-114.525078));
	   locList.addLocation(new Location(33.892563,-114.521973));
	   locList.addLocation(new Location(33.876053,-114.503006));
	   locList.addLocation(new Location(33.866432,-114.502625));
	   locList.addLocation(new Location(33.858620,-114.513885));
	   locList.addLocation(new Location(33.859985,-114.524879));
	   locList.addLocation(new Location(33.855419,-114.529816));
	   locList.addLocation(new Location(33.825363,-114.519180));
	   locList.addLocation(new Location(33.818958,-114.521927));
	   locList.addLocation(new Location(33.814945,-114.527267));
	   locList.addLocation(new Location(33.760445,-114.504074));
	   locList.addLocation(new Location(33.750980,-114.503693));
	   locList.addLocation(new Location(33.734192,-114.511559));
	   locList.addLocation(new Location(33.719135,-114.495773));
	   locList.addLocation(new Location(33.707901,-114.493408));
	   locList.addLocation(new Location(33.698433,-114.494926));
	   locList.addLocation(new Location(33.685856,-114.523170));
	   locList.addLocation(new Location(33.675087,-114.530739));
	   locList.addLocation(new Location(33.666801,-114.529480));
	   locList.addLocation(new Location(33.660156,-114.513275));
	   locList.addLocation(new Location(33.655903,-114.517555));
	   locList.addLocation(new Location(33.654442,-114.529793));
	   locList.addLocation(new Location(33.651634,-114.532410));
	   locList.addLocation(new Location(33.634678,-114.523018));
	   locList.addLocation(new Location(33.630238,-114.525581));
	   locList.addLocation(new Location(33.628189,-114.530251));
	   locList.addLocation(new Location(33.623886,-114.530426));
	   locList.addLocation(new Location(33.612518,-114.521057));
	   locList.addLocation(new Location(33.606628,-114.528397));
	   locList.addLocation(new Location(33.591389,-114.539833));
	   locList.addLocation(new Location(33.580593,-114.539513));
	   locList.addLocation(new Location(33.570934,-114.536003));
	   locList.addLocation(new Location(33.552204,-114.523819));
	   locList.addLocation(new Location(33.531796,-114.558113));
	   locList.addLocation(new Location(33.516712,-114.560173));
	   locList.addLocation(new Location(33.509193,-114.568741));
	   locList.addLocation(new Location(33.506439,-114.579681));
	   locList.addLocation(new Location(33.498650,-114.591583));
	   locList.addLocation(new Location(33.481369,-114.600914));
	   locList.addLocation(new Location(33.456535,-114.622131));
	   locList.addLocation(new Location(33.447529,-114.621498));
	   locList.addLocation(new Location(33.433525,-114.626335));
	   locList.addLocation(new Location(33.422699,-114.634392));
	   locList.addLocation(new Location(33.413605,-114.648750));
	   locList.addLocation(new Location(33.413010,-114.657593));
	   locList.addLocation(new Location(33.418270,-114.673111));
	   locList.addLocation(new Location(33.417915,-114.687157));
	   locList.addLocation(new Location(33.415096,-114.694862));
	   locList.addLocation(new Location(33.408360,-114.700943));
	   locList.addLocation(new Location(33.407864,-114.719269));
	   locList.addLocation(new Location(33.404026,-114.724747));
	   locList.addLocation(new Location(33.382511,-114.706520));
	   locList.addLocation(new Location(33.376598,-114.706558));
	   locList.addLocation(new Location(33.361118,-114.698265));
	   locList.addLocation(new Location(33.352413,-114.697250));
	   locList.addLocation(new Location(33.336983,-114.700142));
	   locList.addLocation(new Location(33.323391,-114.707169));
	   locList.addLocation(new Location(33.312077,-114.722832));
	   locList.addLocation(new Location(33.302402,-114.730431));
	   locList.addLocation(new Location(33.286949,-114.720879));
	   locList.addLocation(new Location(33.279755,-114.693657));
	   locList.addLocation(new Location(33.273544,-114.679718));
	   locList.addLocation(new Location(33.258465,-114.671295));
	   locList.addLocation(new Location(33.246395,-114.688751));
	   locList.addLocation(new Location(33.223087,-114.672836));
	   locList.addLocation(new Location(33.203415,-114.677963));
	   locList.addLocation(new Location(33.185455,-114.674568));
	   locList.addLocation(new Location(33.169682,-114.679459));
	   locList.addLocation(new Location(33.159485,-114.678566));
	   locList.addLocation(new Location(33.142159,-114.686287));
	   locList.addLocation(new Location(33.131172,-114.696037));
	   locList.addLocation(new Location(33.105297,-114.705383));
	   locList.addLocation(new Location(33.091064,-114.707031));
	   locList.addLocation(new Location(33.087013,-114.703934));
	   locList.addLocation(new Location(33.084000,-114.688232));
	   locList.addLocation(new Location(33.070930,-114.686203));
	   locList.addLocation(new Location(33.057133,-114.673508));
	   locList.addLocation(new Location(33.041859,-114.672874));
	   locList.addLocation(new Location(33.032631,-114.661530));
	   locList.addLocation(new Location(33.033787,-114.657043));
	   locList.addLocation(new Location(33.048862,-114.645195));
	   locList.addLocation(new Location(33.045254,-114.638771));
	   locList.addLocation(new Location(33.031013,-114.627502));
	   locList.addLocation(new Location(33.027164,-114.617996));
	   locList.addLocation(new Location(33.026192,-114.588989));
	   locList.addLocation(new Location(33.028191,-114.583977));
	   locList.addLocation(new Location(33.035336,-114.577507));
	   locList.addLocation(new Location(33.036587,-114.570869));
	   locList.addLocation(new Location(33.032356,-114.530296));
	   locList.addLocation(new Location(33.027576,-114.515671));
	   locList.addLocation(new Location(33.019669,-114.507179));
	   locList.addLocation(new Location(33.007519,-114.500450));
	   locList.addLocation(new Location(32.971741,-114.492157));
	   locList.addLocation(new Location(32.969906,-114.487839));
	   locList.addLocation(new Location(32.975136,-114.475754));
	   locList.addLocation(new Location(32.971611,-114.467827));
	   locList.addLocation(new Location(32.955219,-114.467278));
	   locList.addLocation(new Location(32.937889,-114.479439));
	   locList.addLocation(new Location(32.933640,-114.480003));
	   locList.addLocation(new Location(32.923588,-114.475853));
	   locList.addLocation(new Location(32.912399,-114.463196));
	   locList.addLocation(new Location(32.905758,-114.462112));
	   locList.addLocation(new Location(32.845112,-114.468193));
	   locList.addLocation(new Location(32.823189,-114.493408));
	   locList.addLocation(new Location(32.816376,-114.509430));
	   locList.addLocation(new Location(32.795433,-114.528847));
	   locList.addLocation(new Location(32.776878,-114.531647));
	   locList.addLocation(new Location(32.757050,-114.526070));
	   locList.addLocation(new Location(32.756905,-114.538315));
	   locList.addLocation(new Location(32.749767,-114.538437));
	   locList.addLocation(new Location(32.749508,-114.563667));
	   locList.addLocation(new Location(32.742252,-114.563728));
	   locList.addLocation(new Location(32.742275,-114.580956));
	   locList.addLocation(new Location(32.734901,-114.581001));
	   locList.addLocation(new Location(32.734463,-114.614304));
	   locList.addLocation(new Location(32.728401,-114.614799));
	   locList.addLocation(new Location(32.728168,-114.616875));
	   locList.addLocation(new Location(32.737545,-114.687737));
	   locList.addLocation(new Location(32.745586,-114.700790));
	   locList.addLocation(new Location(32.730343,-114.713737));
	   locList.addLocation(new Location(32.718716,-114.718849));
	   locList.addLocation(new Location(32.618530,-116.105339));
	   locList.addLocation(new Location(32.556618,-116.860207));
	   locList.addLocation(new Location(32.541580,-117.035583));
	   locList.addLocation(new Location(32.541248,-117.039993));
	   locList.addLocation(new Location(32.541199,-117.041107));
	   locList.addLocation(new Location(32.540909,-117.044525));
	   locList.addLocation(new Location(32.534878,-117.124184));
	   locList.addLocation(new Location(32.554695,-117.128761));
	   locList.addLocation(new Location(32.561050,-117.133545));
	   locList.addLocation(new Location(32.614277,-117.134529));
	   locList.addLocation(new Location(32.629059,-117.140442));
	   locList.addLocation(new Location(32.669594,-117.165260));
	   locList.addLocation(new Location(32.683914,-117.182610));
	   locList.addLocation(new Location(32.689896,-117.199661));
	   locList.addLocation(new Location(32.686897,-117.218689));
	   locList.addLocation(new Location(32.677952,-117.230225));
	   locList.addLocation(new Location(32.668484,-117.235054));
	   locList.addLocation(new Location(32.664539,-117.241959));
	   locList.addLocation(new Location(32.666508,-117.245903));
	   locList.addLocation(new Location(32.714806,-117.256744));
	   locList.addLocation(new Location(32.755215,-117.252800));
	   locList.addLocation(new Location(32.792667,-117.255760));
	   locList.addLocation(new Location(32.821251,-117.278427));
	   locList.addLocation(new Location(32.834061,-117.281387));
	   locList.addLocation(new Location(32.849831,-117.278427));
	   locList.addLocation(new Location(32.852428,-117.261810));
	   locList.addLocation(new Location(32.866589,-117.251816));
	   locList.addLocation(new Location(32.885315,-117.251816));
	   locList.addLocation(new Location(32.939522,-117.260689));
	   locList.addLocation(new Location(33.000629,-117.277443));
	   locList.addLocation(new Location(33.056808,-117.302078));
	   locList.addLocation(new Location(33.091305,-117.313904));
	   locList.addLocation(new Location(33.156353,-117.354317));
	   locList.addLocation(new Location(33.271667,-117.448936));
	   locList.addLocation(new Location(33.327847,-117.499199));
	   locList.addLocation(new Location(33.365299,-117.548477));
	   locList.addLocation(new Location(33.378109,-117.571144));
	   locList.addLocation(new Location(33.386600,-117.595001));
	   locList.addLocation(new Location(33.387623,-117.595627));
	   locList.addLocation(new Location(33.406288,-117.607025));
	   locList.addLocation(new Location(33.430500,-117.630798));
	   locList.addLocation(new Location(33.440701,-117.644707));
	   locList.addLocation(new Location(33.461342,-117.682671));
	   locList.addLocation(new Location(33.459400,-117.691002));
	   locList.addLocation(new Location(33.460499,-117.714294));
	   locList.addLocation(new Location(33.483398,-117.725601));
	   locList.addLocation(new Location(33.484978,-117.732986));
	   locList.addLocation(new Location(33.488998,-117.737297));
	   locList.addLocation(new Location(33.494202,-117.737907));
	   locList.addLocation(new Location(33.541500,-117.783997));
	   locList.addLocation(new Location(33.551102,-117.807701));
	   locList.addLocation(new Location(33.573502,-117.839401));
	   locList.addLocation(new Location(33.592354,-117.878807));
	   locList.addLocation(new Location(33.605663,-117.927055));
	   locList.addLocation(new Location(33.619972,-117.940033));
	   locList.addLocation(new Location(33.655243,-118.002258));
	   locList.addLocation(new Location(33.728779,-118.088776));
	   locList.addLocation(new Location(33.733109,-118.100090));
	   locList.addLocation(new Location(33.742897,-118.116257));
	   locList.addLocation(new Location(33.752468,-118.132072));
	   locList.addLocation(new Location(33.757969,-118.147308));
	   locList.addLocation(new Location(33.763046,-118.180321));
	   locList.addLocation(new Location(33.752468,-118.222214));
	   locList.addLocation(new Location(33.751198,-118.235748));
	   locList.addLocation(new Location(33.747387,-118.245064));
	   locList.addLocation(new Location(33.739349,-118.253952));
	   locList.addLocation(new Location(33.713955,-118.271729));
	   locList.addLocation(new Location(33.707184,-118.280617));
	   locList.addLocation(new Location(33.703800,-118.292885));
	   locList.addLocation(new Location(33.707607,-118.295425));
	   locList.addLocation(new Location(33.727501,-118.350861));
	   locList.addLocation(new Location(33.736385,-118.359329));
	   locList.addLocation(new Location(33.736385,-118.374138));
	   locList.addLocation(new Location(33.740616,-118.378792));
	   locList.addLocation(new Location(33.740196,-118.385559));
	   locList.addLocation(new Location(33.735115,-118.395294));
	   locList.addLocation(new Location(33.740616,-118.410103));
	   locList.addLocation(new Location(33.774700,-118.427505));
	   locList.addLocation(new Location(33.800201,-118.404106));
	   locList.addLocation(new Location(33.803501,-118.393997));
	   locList.addLocation(new Location(33.815399,-118.390602));
	   locList.addLocation(new Location(33.838402,-118.390305));
	   locList.addLocation(new Location(33.843201,-118.399002));
	   locList.addLocation(new Location(33.861500,-118.401604));
	   locList.addLocation(new Location(33.876801,-118.408295));
	   locList.addLocation(new Location(33.940300,-118.441505));
	   locList.addLocation(new Location(33.987499,-118.475700));
	   locList.addLocation(new Location(34.009499,-118.496506));
	   locList.addLocation(new Location(34.027500,-118.518600));
	   locList.addLocation(new Location(34.037121,-118.539230));
	   locList.addLocation(new Location(34.037502,-118.647682));
	   locList.addLocation(new Location(34.031055,-118.680466));
	   locList.addLocation(new Location(34.029663,-118.704323));
	   locList.addLocation(new Location(34.032112,-118.743744));
	   locList.addLocation(new Location(34.025330,-118.758705));
	   locList.addLocation(new Location(34.019539,-118.786179));
	   locList.addLocation(new Location(34.006767,-118.794334));
	   locList.addLocation(new Location(34.000065,-118.806465));
	   locList.addLocation(new Location(34.008209,-118.814110));
	   locList.addLocation(new Location(34.032928,-118.849792));
	   locList.addLocation(new Location(34.042866,-118.935982));
	   locList.addLocation(new Location(34.045830,-118.943748));
	   locList.addLocation(new Location(34.065361,-118.995010));
	   locList.addLocation(new Location(34.064571,-119.003716));
	   locList.addLocation(new Location(34.082764,-119.036934));
	   locList.addLocation(new Location(34.082764,-119.051971));
	   locList.addLocation(new Location(34.097004,-119.087563));
	   locList.addLocation(new Location(34.098583,-119.099434));
	   locList.addLocation(new Location(34.093842,-119.109711));
	   locList.addLocation(new Location(34.100166,-119.127907));
	   locList.addLocation(new Location(34.134972,-119.183281));
	   locList.addLocation(new Location(34.142883,-119.201469));
	   locList.addLocation(new Location(34.145256,-119.214127));
	   locList.addLocation(new Location(34.166615,-119.229950));
	   locList.addLocation(new Location(34.196674,-119.247353));
	   locList.addLocation(new Location(34.229900,-119.264755));
	   locList.addLocation(new Location(34.267075,-119.278992));
	   locList.addLocation(new Location(34.274197,-119.292442));
	   locList.addLocation(new Location(34.271030,-119.301933));
	   locList.addLocation(new Location(34.288437,-119.335953));
	   locList.addLocation(new Location(34.306629,-119.351768));
	   locList.addLocation(new Location(34.318497,-119.370750));
	   locList.addLocation(new Location(34.315331,-119.388954));
	   locList.addLocation(new Location(34.330360,-119.398438));
	   locList.addLocation(new Location(34.348557,-119.422966));
	   locList.addLocation(new Location(34.354885,-119.441956));
	   locList.addLocation(new Location(34.373867,-119.458557));
	   locList.addLocation(new Location(34.376240,-119.470421));
	   locList.addLocation(new Location(34.373199,-119.475700));
	   locList.addLocation(new Location(34.412327,-119.579712));
	   locList.addLocation(new Location(34.419418,-119.612328));
	   locList.addLocation(new Location(34.415165,-119.643532));
	   locList.addLocation(new Location(34.413750,-119.677559));
	   locList.addLocation(new Location(34.402405,-119.690331));
	   locList.addLocation(new Location(34.395313,-119.704506));
	   locList.addLocation(new Location(34.395313,-119.731445));
	   locList.addLocation(new Location(34.415165,-119.782501));
	   locList.addLocation(new Location(34.413750,-119.836395));
	   locList.addLocation(new Location(34.403820,-119.840637));
	   locList.addLocation(new Location(34.406654,-119.874680));
	   locList.addLocation(new Location(34.433601,-119.928566));
	   locList.addLocation(new Location(34.432182,-119.952675));
	   locList.addLocation(new Location(34.446365,-119.973946));
	   locList.addLocation(new Location(34.456291,-119.995216));
	   locList.addLocation(new Location(34.459129,-120.090225));
	   locList.addLocation(new Location(34.471889,-120.141281));
	   locList.addLocation(new Location(34.471889,-120.220688));
	   locList.addLocation(new Location(34.461964,-120.334137));
	   locList.addLocation(new Location(34.450615,-120.419228));
	   locList.addLocation(new Location(34.440693,-120.451843));
	   locList.addLocation(new Location(34.447781,-120.470268));
	   locList.addLocation(new Location(34.473309,-120.475945));
	   locList.addLocation(new Location(34.490322,-120.491547));
	   locList.addLocation(new Location(34.522942,-120.509979));
	   locList.addLocation(new Location(34.539955,-120.553947));
	   locList.addLocation(new Location(34.555557,-120.580887));
	   locList.addLocation(new Location(34.551300,-120.614922));
	   locList.addLocation(new Location(34.559811,-120.636192));
	   locList.addLocation(new Location(34.576828,-120.646118));
	   locList.addLocation(new Location(34.599518,-120.641861));
	   locList.addLocation(new Location(34.663334,-120.610664));
	   locList.addLocation(new Location(34.694527,-120.600739));
	   locList.addLocation(new Location(34.710129,-120.603577));
	   locList.addLocation(new Location(34.737072,-120.626266));
	   locList.addLocation(new Location(34.755508,-120.637611));
	   locList.addLocation(new Location(34.795212,-120.620590));
	   locList.addLocation(new Location(34.844845,-120.607826));
	   locList.addLocation(new Location(34.863281,-120.613503));
	   locList.addLocation(new Location(34.877460,-120.637611));
	   locList.addLocation(new Location(34.897316,-120.656036));
	   locList.addLocation(new Location(34.901569,-120.670227));
	   locList.addLocation(new Location(34.931347,-120.664551));
	   locList.addLocation(new Location(34.974957,-120.648796));
	   locList.addLocation(new Location(35.002094,-120.638985));
	   locList.addLocation(new Location(35.044647,-120.630943));
	   locList.addLocation(new Location(35.071907,-120.628662));
	   locList.addLocation(new Location(35.109520,-120.631088));
	   locList.addLocation(new Location(35.126534,-120.636131));
	   locList.addLocation(new Location(35.146652,-120.649719));
	   locList.addLocation(new Location(35.151440,-120.665283));
	   locList.addLocation(new Location(35.168201,-120.696419));
	   locList.addLocation(new Location(35.171791,-120.717957));
	   locList.addLocation(new Location(35.180172,-120.737122));
	   locList.addLocation(new Location(35.176579,-120.751488));
	   locList.addLocation(new Location(35.157425,-120.751488));
	   locList.addLocation(new Location(35.159821,-120.765846));
	   locList.addLocation(new Location(35.180172,-120.800575));
	   locList.addLocation(new Location(35.205315,-120.854446));
	   locList.addLocation(new Location(35.220879,-120.872406));
	   locList.addLocation(new Location(35.242432,-120.891563));
	   locList.addLocation(new Location(35.256798,-120.897552));
	   locList.addLocation(new Location(35.274757,-120.892761));
	   locList.addLocation(new Location(35.299900,-120.877197));
	   locList.addLocation(new Location(35.328632,-120.866425));
	   locList.addLocation(new Location(35.342999,-120.864021));
	   locList.addLocation(new Location(35.376526,-120.864021));
	   locList.addLocation(new Location(35.399273,-120.867615));
	   locList.addLocation(new Location(35.423218,-120.879593));
	   locList.addLocation(new Location(35.445171,-120.902290));
	   locList.addLocation(new Location(35.448357,-120.905930));
	   locList.addLocation(new Location(35.447159,-120.949036));
	   locList.addLocation(new Location(35.456738,-120.978958));
	   locList.addLocation(new Location(35.459133,-121.004105));
	   locList.addLocation(new Location(35.547729,-121.102280));
	   locList.addLocation(new Location(35.580055,-121.120239));
	   locList.addLocation(new Location(35.627945,-121.160942));
	   locList.addLocation(new Location(35.638721,-121.175308));
	   locList.addLocation(new Location(35.636326,-121.194466));
	   locList.addLocation(new Location(35.639915,-121.206444));
	   locList.addLocation(new Location(35.650692,-121.224403));
	   locList.addLocation(new Location(35.654285,-121.248344));
	   locList.addLocation(new Location(35.665058,-121.284264));
	   locList.addLocation(new Location(35.681820,-121.287857));
	   locList.addLocation(new Location(35.708160,-121.311798));
	   locList.addLocation(new Location(35.745277,-121.318985));
	   locList.addLocation(new Location(35.756050,-121.324966));
	   locList.addLocation(new Location(35.774010,-121.324966));
	   locList.addLocation(new Location(35.796112,-121.348228));
	   locList.addLocation(new Location(35.802612,-121.355080));
	   locList.addLocation(new Location(35.819481,-121.382179));
	   locList.addLocation(new Location(35.856285,-121.414894));
	   locList.addLocation(new Location(35.870087,-121.445053));
	   locList.addLocation(new Location(35.886955,-121.464478));
	   locList.addLocation(new Location(35.909451,-121.466019));
	   locList.addLocation(new Location(35.913029,-121.471634));
	   locList.addLocation(new Location(35.968746,-121.484413));
	   locList.addLocation(new Location(35.999420,-121.501801));
	   locList.addLocation(new Location(36.006069,-121.509979));
	   locList.addLocation(new Location(36.018337,-121.546272));
	   locList.addLocation(new Location(36.018845,-121.566208));
	   locList.addLocation(new Location(36.023449,-121.571831));
	   locList.addLocation(new Location(36.040318,-121.581032));
	   locList.addLocation(new Location(36.047985,-121.590233));
	   locList.addLocation(new Location(36.063831,-121.591766));
	   locList.addLocation(new Location(36.070477,-121.604546));
	   locList.addLocation(new Location(36.084278,-121.617325));
	   locList.addLocation(new Location(36.098080,-121.620903));
	   locList.addLocation(new Location(36.111374,-121.628067));
	   locList.addLocation(new Location(36.140511,-121.654640));
	   locList.addLocation(new Location(36.192139,-121.713943));
	   locList.addLocation(new Location(36.232231,-121.790871));
	   locList.addLocation(new Location(36.234306,-121.812355));
	   locList.addLocation(new Location(36.246086,-121.827591));
	   locList.addLocation(new Location(36.273804,-121.848381));
	   locList.addLocation(new Location(36.293209,-121.880951));
	   locList.addLocation(new Location(36.301525,-121.887184));
	   locList.addLocation(new Location(36.301525,-121.898270));
	   locList.addLocation(new Location(36.306374,-121.901733));
	   locList.addLocation(new Location(36.312607,-121.894806));
	   locList.addLocation(new Location(36.341019,-121.892731));
	   locList.addLocation(new Location(36.354183,-121.905197));
	   locList.addLocation(new Location(36.433872,-121.918365));
	   locList.addLocation(new Location(36.452579,-121.929459));
	   locList.addLocation(new Location(36.489304,-121.945389));
	   locList.addLocation(new Location(36.505932,-121.943314));
	   locList.addLocation(new Location(36.516327,-121.953018));
	   locList.addLocation(new Location(36.522564,-121.953018));
	   locList.addLocation(new Location(36.523254,-121.928757));
	   locList.addLocation(new Location(36.528107,-121.925293));
	   locList.addLocation(new Location(36.550282,-121.928757));
	   locList.addLocation(new Location(36.558598,-121.932220));
	   locList.addLocation(new Location(36.562752,-121.937073));
	   locList.addLocation(new Location(36.565525,-121.945389));
	   locList.addLocation(new Location(36.560677,-121.952316));
	   locList.addLocation(new Location(36.568989,-121.970337));
	   locList.addLocation(new Location(36.582848,-121.973106));
	   locList.addLocation(new Location(36.609871,-121.956482));
	   locList.addLocation(new Location(36.615417,-121.944695));
	   locList.addLocation(new Location(36.636894,-121.934303));
	   locList.addLocation(new Location(36.636894,-121.928062));
	   locList.addLocation(new Location(36.620960,-121.903816));
	   locList.addLocation(new Location(36.603638,-121.889961));
	   locList.addLocation(new Location(36.600861,-121.881638));
	   locList.addLocation(new Location(36.607101,-121.865013));
	   locList.addLocation(new Location(36.623035,-121.847687));
	   locList.addLocation(new Location(36.645905,-121.829674));
	   locList.addLocation(new Location(36.670849,-121.817894));
	   locList.addLocation(new Location(36.699261,-121.810272));
	   locList.addLocation(new Location(36.726284,-121.804726));
	   locList.addLocation(new Location(36.751228,-121.804031));
	   locList.addLocation(new Location(36.805969,-121.788094));
	   locList.addLocation(new Location(36.850853,-121.808922));
	   locList.addLocation(new Location(36.934399,-121.863998));
	   locList.addLocation(new Location(36.950199,-121.879105));
	   locList.addLocation(new Location(36.968800,-121.904495));
	   locList.addLocation(new Location(36.977299,-121.928001));
	   locList.addLocation(new Location(36.977402,-121.938896));
	   locList.addLocation(new Location(36.971500,-121.950600));
	   locList.addLocation(new Location(36.954498,-121.972496));
	   locList.addLocation(new Location(36.960503,-121.984589));
	   locList.addLocation(new Location(36.962200,-122.022301));
	   locList.addLocation(new Location(36.950298,-122.025101));
	   locList.addLocation(new Location(36.950500,-122.075203));
	   locList.addLocation(new Location(36.956001,-122.104897));
	   locList.addLocation(new Location(36.966301,-122.127899));
	   locList.addLocation(new Location(36.976501,-122.142105));
	   locList.addLocation(new Location(36.976200,-122.152107));
	   locList.addLocation(new Location(37.012501,-122.198601));
	   locList.addLocation(new Location(37.014000,-122.205101));
	   locList.addLocation(new Location(37.025200,-122.221893));
	   locList.addLocation(new Location(37.080032,-122.266998));
	   locList.addLocation(new Location(37.098099,-122.280602));
	   locList.addLocation(new Location(37.106895,-122.292175));
	   locList.addLocation(new Location(37.115276,-122.303207));
	   locList.addLocation(new Location(37.118214,-122.312820));
	   locList.addLocation(new Location(37.112522,-122.328499));
	   locList.addLocation(new Location(37.117706,-122.336182));
	   locList.addLocation(new Location(37.120953,-122.338318));
	   locList.addLocation(new Location(37.134327,-122.336143));
	   locList.addLocation(new Location(37.140453,-122.341919));
	   locList.addLocation(new Location(37.149403,-122.358902));
	   locList.addLocation(new Location(37.158573,-122.359810));
	   locList.addLocation(new Location(37.172215,-122.365799));
	   locList.addLocation(new Location(37.181091,-122.378441));
	   locList.addLocation(new Location(37.183361,-122.385628));
	   locList.addLocation(new Location(37.181786,-122.393867));
	   locList.addLocation(new Location(37.196167,-122.403870));
	   locList.addLocation(new Location(37.220665,-122.406609));
	   locList.addLocation(new Location(37.240974,-122.417603));
	   locList.addLocation(new Location(37.279797,-122.408447));
	   locList.addLocation(new Location(37.350693,-122.399971));
	   locList.addLocation(new Location(37.412346,-122.430023));
	   locList.addLocation(new Location(37.433922,-122.443130));
	   locList.addLocation(new Location(37.465515,-122.446205));
	   locList.addLocation(new Location(37.480156,-122.450829));
	   locList.addLocation(new Location(37.500191,-122.471642));
	   locList.addLocation(new Location(37.499424,-122.481659));
	   locList.addLocation(new Location(37.496342,-122.490128));
	   locList.addLocation(new Location(37.493256,-122.491669));
	   locList.addLocation(new Location(37.495567,-122.498611));
	   locList.addLocation(new Location(37.524853,-122.517876));
	   locList.addLocation(new Location(37.537952,-122.519417));
	   locList.addLocation(new Location(37.594208,-122.517105));
	   locList.addLocation(new Location(37.598061,-122.511711));
	   locList.addLocation(new Location(37.597294,-122.504776));
	   locList.addLocation(new Location(37.605766,-122.498611));
	   locList.addLocation(new Location(37.643528,-122.492439));
	   locList.addLocation(new Location(37.707222,-122.502487));
	   locList.addLocation(new Location(37.780823,-122.514114));
	   locList.addLocation(new Location(37.788078,-122.504524));
	   locList.addLocation(new Location(37.788078,-122.491302));
	   locList.addLocation(new Location(37.790417,-122.485077));
	   locList.addLocation(new Location(37.810631,-122.477303));
	   locList.addLocation(new Location(37.804672,-122.463051));
	   locList.addLocation(new Location(37.811413,-122.418983));
	   locList.addLocation(new Location(37.810890,-122.405502));
	   locList.addLocation(new Location(37.805969,-122.397987));
	   locList.addLocation(new Location(37.791973,-122.386063));
	   locList.addLocation(new Location(37.751793,-122.378799));
	   locList.addLocation(new Location(37.732609,-122.365318));
	   locList.addLocation(new Location(37.730015,-122.356247));
	   locList.addLocation(new Location(37.715759,-122.362473));
	   locList.addLocation(new Location(37.718094,-122.372581));
	   locList.addLocation(new Location(37.710056,-122.380875));
	   locList.addLocation(new Location(37.708401,-122.391602));
	   locList.addLocation(new Location(37.707813,-122.391502));
	   locList.addLocation(new Location(37.685425,-122.387779));
	   locList.addLocation(new Location(37.677593,-122.379578));
	   locList.addLocation(new Location(37.655228,-122.374352));
	   locList.addLocation(new Location(37.647400,-122.378456));
	   locList.addLocation(new Location(37.635098,-122.379578));
	   locList.addLocation(new Location(37.619812,-122.363167));
	   locList.addLocation(new Location(37.615341,-122.353477));
	   locList.addLocation(new Location(37.597446,-122.363922));
	   locList.addLocation(new Location(37.591484,-122.359444));
	   locList.addLocation(new Location(37.591106,-122.313965));
	   locList.addLocation(new Location(37.579182,-122.310242));
	   locList.addLocation(new Location(37.576199,-122.300171));
	   locList.addLocation(new Location(37.572472,-122.262894));
	   locList.addLocation(new Location(37.567623,-122.252831));
	   locList.addLocation(new Location(37.557186,-122.243134));
	   locList.addLocation(new Location(37.541531,-122.215927));
	   locList.addLocation(new Location(37.536682,-122.195427));
	   locList.addLocation(new Location(37.521770,-122.191322));
	   locList.addLocation(new Location(37.509472,-122.174545));
	   locList.addLocation(new Location(37.500523,-122.154793));
	   locList.addLocation(new Location(37.507607,-122.138763));
	   locList.addLocation(new Location(37.505001,-122.130562));
	   locList.addLocation(new Location(37.508755,-122.117516));
	   locList.addLocation(new Location(37.510765,-122.110535));
	   locList.addLocation(new Location(37.529510,-122.110535));
	   locList.addLocation(new Location(37.580826,-122.144089));
	   locList.addLocation(new Location(37.607956,-122.145073));
	   locList.addLocation(new Location(37.627693,-122.151489));
	   locList.addLocation(new Location(37.651863,-122.155434));
	   locList.addLocation(new Location(37.672092,-122.165794));
	   locList.addLocation(new Location(37.686401,-122.179611));
	   locList.addLocation(new Location(37.693802,-122.193909));
	   locList.addLocation(new Location(37.699226,-122.213158));
	   locList.addLocation(new Location(37.718468,-122.240288));
	   locList.addLocation(new Location(37.763363,-122.274338));
	   locList.addLocation(new Location(37.779644,-122.319229));
	   locList.addLocation(new Location(37.797409,-122.331070));
	   locList.addLocation(new Location(37.812698,-122.320709));
	   locList.addLocation(new Location(37.828487,-122.300484));
	   locList.addLocation(new Location(37.835888,-122.297028));
	   locList.addLocation(new Location(37.897400,-122.311905));
	   locList.addLocation(new Location(37.897423,-122.311928));
	   locList.addLocation(new Location(37.904430,-122.319359));
	   locList.addLocation(new Location(37.908569,-122.328392));
	   locList.addLocation(new Location(37.907440,-122.349449));
	   locList.addLocation(new Location(37.908943,-122.358849));
	   locList.addLocation(new Location(37.904430,-122.362610));
	   locList.addLocation(new Location(37.904430,-122.369751));
	   locList.addLocation(new Location(37.909321,-122.388931));
	   locList.addLocation(new Location(37.915710,-122.387421));
	   locList.addLocation(new Location(37.921726,-122.389679));
	   locList.addLocation(new Location(37.931881,-122.408478));
	   locList.addLocation(new Location(37.960835,-122.428413));
	   locList.addLocation(new Location(37.965347,-122.428413));
	   locList.addLocation(new Location(37.963093,-122.414505));
	   locList.addLocation(new Location(37.960083,-122.410362));
	   locList.addLocation(new Location(37.958958,-122.398331));
	   locList.addLocation(new Location(37.962341,-122.392311));
	   locList.addLocation(new Location(37.976257,-122.382538));
	   locList.addLocation(new Location(37.975124,-122.372009));
	   locList.addLocation(new Location(37.977760,-122.367874));
	   locList.addLocation(new Location(37.988663,-122.361855));
	   locList.addLocation(new Location(38.007088,-122.368248));
	   locList.addLocation(new Location(38.012730,-122.366371));
	   locList.addLocation(new Location(38.002953,-122.335915));
	   locList.addLocation(new Location(38.003704,-122.326508));
	   locList.addLocation(new Location(38.011223,-122.315224));
	   locList.addLocation(new Location(38.011600,-122.306198));
	   locList.addLocation(new Location(38.021755,-122.287025));
	   locList.addLocation(new Location(38.039429,-122.272736));
	   locList.addLocation(new Location(38.043564,-122.263710));
	   locList.addLocation(new Location(38.052589,-122.261833));
	   locList.addLocation(new Location(38.060097,-122.264854));
	   locList.addLocation(new Location(38.068577,-122.268272));
	   locList.addLocation(new Location(38.100300,-122.294502));
	   locList.addLocation(new Location(38.113392,-122.310509));
	   locList.addLocation(new Location(38.136002,-122.352402));
	   locList.addLocation(new Location(38.151489,-122.398232));
	   locList.addLocation(new Location(38.149067,-122.401733));
	   locList.addLocation(new Location(38.147873,-122.403458));
	   locList.addLocation(new Location(38.136593,-122.409821));
	   locList.addLocation(new Location(38.127777,-122.421486));
	   locList.addLocation(new Location(38.112923,-122.487366));
	   locList.addLocation(new Location(38.108936,-122.487808));
	   locList.addLocation(new Location(38.104469,-122.488304));
	   locList.addLocation(new Location(38.071556,-122.482323));
	   locList.addLocation(new Location(38.064903,-122.487640));
	   locList.addLocation(new Location(38.039639,-122.495949));
	   locList.addLocation(new Location(38.029999,-122.498611));
	   locList.addLocation(new Location(38.021687,-122.496941));
	   locList.addLocation(new Location(38.015373,-122.494286));
	   locList.addLocation(new Location(38.003735,-122.465370));
	   locList.addLocation(new Location(37.997089,-122.455727));
	   locList.addLocation(new Location(37.984787,-122.446083));
	   locList.addLocation(new Location(37.979469,-122.456055));
	   locList.addLocation(new Location(37.974480,-122.474342));
	   locList.addLocation(new Location(37.964840,-122.488968));
	   locList.addLocation(new Location(37.948883,-122.484978));
	   locList.addLocation(new Location(37.941898,-122.477997));
	   locList.addLocation(new Location(37.936581,-122.486641));
	   locList.addLocation(new Location(37.938576,-122.496613));
	   locList.addLocation(new Location(37.935253,-122.502930));
	   locList.addLocation(new Location(37.926277,-122.499275));
	   locList.addLocation(new Location(37.916637,-122.479324));
	   locList.addLocation(new Location(37.901344,-122.467361));
	   locList.addLocation(new Location(37.897018,-122.460373));
	   locList.addLocation(new Location(37.894028,-122.447746));
	   locList.addLocation(new Location(37.882061,-122.436440));
	   locList.addLocation(new Location(37.879398,-122.437111));
	   locList.addLocation(new Location(37.871426,-122.450737));
	   locList.addLocation(new Location(37.864109,-122.456718));
	   locList.addLocation(new Location(37.856464,-122.477333));
	   locList.addLocation(new Location(37.847488,-122.478325));
	   locList.addLocation(new Location(37.836517,-122.470352));
	   locList.addLocation(new Location(37.832401,-122.471199));
	   locList.addLocation(new Location(37.830654,-122.476997));
	   locList.addLocation(new Location(37.830502,-122.477501));
	   locList.addLocation(new Location(37.825802,-122.476997));
	   locList.addLocation(new Location(37.825802,-122.490295));
	   locList.addLocation(new Location(37.824661,-122.491898));
	   locList.addLocation(new Location(37.822613,-122.494766));
	   locList.addLocation(new Location(37.819801,-122.498703));
	   locList.addLocation(new Location(37.824036,-122.509605));
	   locList.addLocation(new Location(37.824501,-122.510803));
	   locList.addLocation(new Location(37.824554,-122.512367));
	   locList.addLocation(new Location(37.824902,-122.522507));
	   locList.addLocation(new Location(37.815201,-122.526398));
	   locList.addLocation(new Location(37.844498,-122.557205));
	   locList.addLocation(new Location(37.861691,-122.586967));
	   locList.addLocation(new Location(37.874260,-122.600861));
	   locList.addLocation(new Location(37.875584,-122.616074));
	   locList.addLocation(new Location(37.880211,-122.625992));
	   locList.addLocation(new Location(37.887489,-122.629303));
	   locList.addLocation(new Location(37.902039,-122.649811));
	   locList.addLocation(new Location(37.906010,-122.665016));
	   locList.addLocation(new Location(37.905350,-122.680229));
	   locList.addLocation(new Location(37.900715,-122.692139));
	   locList.addLocation(new Location(37.892120,-122.701401));
	   locList.addLocation(new Location(37.903362,-122.726540));
	   locList.addLocation(new Location(37.913948,-122.729179));
	   locList.addLocation(new Location(37.925194,-122.736458));
	   locList.addLocation(new Location(37.937096,-122.764893));
	   locList.addLocation(new Location(37.947681,-122.781433));
	   locList.addLocation(new Location(37.974796,-122.795319));
	   locList.addLocation(new Location(37.995964,-122.818474));
	   locList.addLocation(new Location(38.014484,-122.851547));
	   locList.addLocation(new Location(38.021759,-122.869400));
	   locList.addLocation(new Location(38.027054,-122.890572));
	   locList.addLocation(new Location(38.027714,-122.925621));
	   locList.addLocation(new Location(38.031021,-122.940834));
	   locList.addLocation(new Location(38.027714,-122.959351));
	   locList.addLocation(new Location(38.009853,-122.980522));
	   locList.addLocation(new Location(37.991333,-122.973251));
	   locList.addLocation(new Location(37.993980,-123.023514));
	   locList.addLocation(new Location(38.000591,-123.019547));
	   locList.addLocation(new Location(38.006550,-123.008301));
	   locList.addLocation(new Location(38.107082,-122.961334));
	   locList.addLocation(new Location(38.149418,-122.948112));
	   locList.addLocation(new Location(38.169254,-122.951416));
	   locList.addLocation(new Location(38.180500,-122.959351));
	   locList.addLocation(new Location(38.183147,-122.966629));
	   locList.addLocation(new Location(38.195717,-122.964645));
	   locList.addLocation(new Location(38.240032,-122.994408));
	   locList.addLocation(new Location(38.236725,-122.971268));
	   locList.addLocation(new Location(38.250610,-122.966629));
	   locList.addLocation(new Location(38.263180,-122.973907));
	   locList.addLocation(new Location(38.273102,-122.985153));
	   locList.addLocation(new Location(38.295795,-123.001617));
	   locList.addLocation(new Location(38.311279,-123.025490));
	   locList.addLocation(new Location(38.313133,-123.036598));
	   locList.addLocation(new Location(38.312019,-123.045853));
	   locList.addLocation(new Location(38.307575,-123.051407));
	   locList.addLocation(new Location(38.302391,-123.050674));
	   locList.addLocation(new Location(38.298687,-123.053635));
	   locList.addLocation(new Location(38.299801,-123.060295));
	   locList.addLocation(new Location(38.322762,-123.076591));
	   locList.addLocation(new Location(38.324612,-123.071777));
	   locList.addLocation(new Location(38.331276,-123.068817));
	   locList.addLocation(new Location(38.353497,-123.066589));
	   locList.addLocation(new Location(38.363865,-123.068817));
	   locList.addLocation(new Location(38.373123,-123.076225));
	   locList.addLocation(new Location(38.389050,-123.083633));
	   locList.addLocation(new Location(38.393120,-123.089188));
	   locList.addLocation(new Location(38.392754,-123.095116));
	   locList.addLocation(new Location(38.399788,-123.094742));
	   locList.addLocation(new Location(38.410156,-123.098816));
	   locList.addLocation(new Location(38.417191,-123.104736));
	   locList.addLocation(new Location(38.422009,-123.113258));
	   locList.addLocation(new Location(38.451263,-123.128075));
	   locList.addLocation(new Location(38.456078,-123.140663));
	   locList.addLocation(new Location(38.481998,-123.180290));
	   locList.addLocation(new Location(38.491627,-123.199173));
	   locList.addLocation(new Location(38.509037,-123.248055));
	   locList.addLocation(new Location(38.531998,-123.276199));
	   locList.addLocation(new Location(38.546898,-123.302742));
	   locList.addLocation(new Location(38.555786,-123.309616));
	   locList.addLocation(new Location(38.563873,-123.332657));
	   locList.addLocation(new Location(38.586510,-123.341141));
	   locList.addLocation(new Location(38.596207,-123.348824));
	   locList.addLocation(new Location(38.597015,-123.357315));
	   locList.addLocation(new Location(38.607124,-123.370247));
	   locList.addLocation(new Location(38.649158,-123.401779));
	   locList.addLocation(new Location(38.662090,-123.408646));
	   locList.addLocation(new Location(38.681900,-123.431686));
	   locList.addLocation(new Location(38.693619,-123.438148));
	   locList.addLocation(new Location(38.706959,-123.452705));
	   locList.addLocation(new Location(38.717064,-123.459579));
	   locList.addLocation(new Location(38.727173,-123.483017));
	   locList.addLocation(new Location(38.738083,-123.497566));
	   locList.addLocation(new Location(38.741718,-123.512924));
	   locList.addLocation(new Location(38.749401,-123.523438));
	   locList.addLocation(new Location(38.759399,-123.530769));
	   locList.addLocation(new Location(38.768497,-123.532417));
	   locList.addLocation(new Location(38.768513,-123.532440));
	   locList.addLocation(new Location(38.800957,-123.579605));
	   locList.addLocation(new Location(38.820381,-123.603081));
	   locList.addLocation(new Location(38.842236,-123.644363));
	   locList.addLocation(new Location(38.874611,-123.663795));
	   locList.addLocation(new Location(38.909416,-123.708305));
	   locList.addLocation(new Location(38.916698,-123.724495));
	   locList.addLocation(new Location(38.937744,-123.730164));
	   locList.addLocation(new Location(38.954742,-123.741486));
	   locList.addLocation(new Location(38.953934,-123.730965));
	   locList.addLocation(new Location(38.966885,-123.717209));
	   locList.addLocation(new Location(38.991165,-123.701836));
	   locList.addLocation(new Location(39.019497,-123.690498));
	   locList.addLocation(new Location(39.045395,-123.690498));
	   locList.addLocation(new Location(39.125523,-123.718018));
	   locList.addLocation(new Location(39.156284,-123.735016));
	   locList.addLocation(new Location(39.194324,-123.769005));
	   locList.addLocation(new Location(39.233177,-123.778717));
	   locList.addLocation(new Location(39.270409,-123.796532));
	   locList.addLocation(new Location(39.349728,-123.824051));
	   locList.addLocation(new Location(39.375629,-123.820816));
	   locList.addLocation(new Location(39.407196,-123.820816));
	   locList.addLocation(new Location(39.448475,-123.814339));
	   locList.addLocation(new Location(39.478424,-123.803009));
	   locList.addLocation(new Location(39.522804,-123.775398));
	   locList.addLocation(new Location(39.556709,-123.765633));
	   locList.addLocation(new Location(39.596355,-123.785744));
	   locList.addLocation(new Location(39.605553,-123.786896));
	   locList.addLocation(new Location(39.610725,-123.781151));
	   locList.addLocation(new Location(39.690601,-123.793793));
	   locList.addLocation(new Location(39.711285,-123.809303));
	   locList.addLocation(new Location(39.721058,-123.828850));
	   locList.addLocation(new Location(39.750935,-123.837463));
	   locList.addLocation(new Location(39.775070,-123.836891));
	   locList.addLocation(new Location(39.824490,-123.846657));
	   locList.addLocation(new Location(39.833107,-123.851830));
	   locList.addLocation(new Location(39.846325,-123.884583));
	   locList.addLocation(new Location(39.859543,-123.903542));
	   locList.addLocation(new Location(39.908386,-123.928253));
	   locList.addLocation(new Location(39.921028,-123.952393));
	   locList.addLocation(new Location(39.954361,-123.974220));
	   locList.addLocation(new Location(40.001411,-124.022087));
	   locList.addLocation(new Location(40.002712,-124.023590));
	   locList.addLocation(new Location(40.017509,-124.040665));
	   locList.addLocation(new Location(40.022488,-124.058090));
	   locList.addLocation(new Location(40.018753,-124.069298));
	   locList.addLocation(new Location(40.027470,-124.079254));
	   locList.addLocation(new Location(40.062328,-124.078011));
	   locList.addLocation(new Location(40.076023,-124.085480));
	   locList.addLocation(new Location(40.098434,-124.106651));
	   locList.addLocation(new Location(40.115864,-124.137779));
	   locList.addLocation(new Location(40.129559,-124.185089));
	   locList.addLocation(new Location(40.166912,-124.226173));
	   locList.addLocation(new Location(40.222939,-124.318306));
	   locList.addLocation(new Location(40.256557,-124.361877));
	   locList.addLocation(new Location(40.281456,-124.359390));
	   locList.addLocation(new Location(40.313828,-124.348183));
	   locList.addLocation(new Location(40.392269,-124.370598));
	   locList.addLocation(new Location(40.404716,-124.388031));
	   locList.addLocation(new Location(40.438335,-124.407951));
	   locList.addLocation(new Location(40.508057,-124.386787));
	   locList.addLocation(new Location(40.531712,-124.370598));
	   locList.addLocation(new Location(40.600189,-124.335739));
	   locList.addLocation(new Location(40.641277,-124.312080));
	   locList.addLocation(new Location(40.815582,-124.193802));
	   locList.addLocation(new Location(40.867874,-124.161430));
	   locList.addLocation(new Location(40.913944,-124.141510));
	   locList.addLocation(new Location(41.004833,-124.114120));
	   locList.addLocation(new Location(41.028488,-124.112869));
	   locList.addLocation(new Location(41.047165,-124.129059));
	   locList.addLocation(new Location(41.049652,-124.147736));
	   locList.addLocation(new Location(41.069572,-124.158936));
	   locList.addLocation(new Location(41.141788,-124.160187));
	   locList.addLocation(new Location(41.148010,-124.140266));
	   locList.addLocation(new Location(41.189880,-124.121498));
	   locList.addLocation(new Location(41.276043,-124.094467));
	   locList.addLocation(new Location(41.395813,-124.068031));
	   locList.addLocation(new Location(41.427952,-124.062897));
	   locList.addLocation(new Location(41.464897,-124.064018));
	   locList.addLocation(new Location(41.465057,-124.064072));
	   locList.addLocation(new Location(41.513237,-124.080048));
	   locList.addLocation(new Location(41.546124,-124.080048));
	   locList.addLocation(new Location(41.552841,-124.091019));
	   locList.addLocation(new Location(41.571232,-124.099495));
	   locList.addLocation(new Location(41.579365,-124.100563));
	   locList.addLocation(new Location(41.586437,-124.097023));
	   locList.addLocation(new Location(41.594570,-124.103745));
	   locList.addLocation(new Location(41.601997,-124.100204));
	   locList.addLocation(new Location(41.616138,-124.112587));
	   locList.addLocation(new Location(41.645493,-124.124252));
	   locList.addLocation(new Location(41.656456,-124.133446));
	   locList.addLocation(new Location(41.712685,-124.143707));
	   locList.addLocation(new Location(41.728947,-124.153252));
	   locList.addLocation(new Location(41.739204,-124.163155));
	   locList.addLocation(new Location(41.743095,-124.170578));
	   locList.addLocation(new Location(41.750168,-124.191803));
	   locList.addLocation(new Location(41.744865,-124.199577));
	   locList.addLocation(new Location(41.751579,-124.212303));
	   locList.addLocation(new Location(41.769974,-124.238121));
	   locList.addLocation(new Location(41.771385,-124.247673));
	   locList.addLocation(new Location(41.783180,-124.254799));
	   locList.addLocation(new Location(41.792465,-124.243835));
	   locList.addLocation(new Location(41.818844,-124.229477));
	   locList.addLocation(new Location(41.846596,-124.218399));
	   locList.addLocation(new Location(41.888355,-124.207245));
	   locList.addLocation(new Location(41.935848,-124.201988));
	   locList.addLocation(new Location(41.950851,-124.209038));
	   locList.addLocation(new Location(41.958057,-124.205978));
	   locList.addLocation(new Location(41.983608,-124.203751));
	   locList.addLocation(new Location(41.998016,-124.210136));
	   
	    public static double searchLatMin = searchLatMin_NZ;
  public static double searchLatMax = searchLatMax_NZ;
  public static double searchLongMin = searchLongMin_NZ;
  public static double searchLongMax = searchLongMax_NZ;
  
	   */

		SitesInGriddedRegion sites;
//		try {	
			//set the grid precision first
//			SitesInGriddedRectangularRegion.setGridPrecision(RegionDefaults.gridPrecision);
//			GriddedRegion eggr = 
//				new GriddedRegion(
//						RegionDefaults.searchLatMin,
//						RegionDefaults.searchLatMax,
//						RegionDefaults.searchLongMin,
//						RegionDefaults.searchLongMax,
//						RegionDefaults.gridSpacing);
			GriddedRegion eggr = 
				new GriddedRegion(
						new Location(RegionDefaults.searchLatMin,RegionDefaults.searchLongMin),
						new Location(RegionDefaults.searchLatMax,RegionDefaults.searchLongMax),
						RegionDefaults.gridSpacing, new Location(0,0));
			
			sites = new  SitesInGriddedRegion(eggr);
			this.setBackGroundRegion(sites.getRegion());
			
//		} catch (RegionConstraintException e) {
//			// TODO Auto-generated catch block
//			e.printStackTrace();
//		}

		/*locList.addLocation(new Location(42.009655,-124.407951));
		   locList.addLocation(new Location(42.2,-114.130432));
		   locList.addLocation(new Location(32.534878,-124.407951));
		   locList.addLocation(new Location(32.534878,-114.130432));*/

	}

	/**
	 * I am not sure how the background grid will be loaded but this may be
	 * needed
	 * 
	 * Discusion: to make sure that the order of the <code> hypoMagFreqDist</code>
	 * are the same as the regions grid list, two approaches could be used
	 * 1. sort the list by location
	 * 2. search the index of the location from the region's grid list
	 * 3. is hashmap an option?
	 * 
	 * the second method is safer but less efficient
	 * if the input file is garanteed to contain the same locations as the 
	 * regions grid, the 1st method can be used
	 * 
	 *
	 */
	public void loadBackGroundGridFromFile(String fileName){
		// Debug
		ArrayList<String> backgroundRateFileLines = null;
		//read background rates file if needed
		if(!backgroundRatesFileAlreadyRead){
			try {
				System.out.println("loadBackGroundGridFromFile fileName " + fileName);
				backgroundRateFileLines = FileUtils.loadJarFile( fileName );
			} catch(Exception e) {

				throw new RuntimeException("Background file could not be loaded");
			}
			backgroundRatesFileAlreadyRead = true;
		}
		
		//SitesInGriddedRectangularRegion region = (SitesInGriddedRectangularRegion)this.getEvenlyGriddedGeographicRegion();
        	
		//HypoMagFreqDistAtLoc [] hypoMagFreqDistArray = new HypoMagFreqDistAtLoc[region.getNumGridLocs()];
		hypoMagFreqDist = new ArrayList <HypoMagFreqDistAtLoc>();
		hypoMagFreqDistMap = new HashMap<String, HypoMagFreqDistAtLoc>();
		double lat, lon;

		IncrementalMagFreqDist magFreqDist;
		PointEqkSource ptSource;

		// Get iterator over input-file lines
		ListIterator it = backgroundRateFileLines.listIterator();

		StringTokenizer st;

		int forecastMagStart = getForecastMagStart();
		logger.info(" forecastMagStart " + forecastMagStart);
		
		while( it.hasNext() ) {
			// get next line
			String line = it.next().toString();
			//logger.info(" loadBackGroundGridFromFile line=" + line);
			st = new StringTokenizer(line);

			// skip the event ID
			st.nextToken();

			// get lat and lon
			lon =  Double.parseDouble(st.nextToken());
			lat =  Double.parseDouble(st.nextToken());

			//logger.info(" loadBackGroundGridFromFile lat=" + lat + " lon=" + lon);
			
			int numForecastMags = 1 + (int) ( (maxForecastMag - minForecastMag) / this.deltaForecastMag);
			magFreqDist = new IncrementalMagFreqDist(minForecastMag, maxForecastMag, numForecastMags);

			//??? skip the mag=2, 2.1, ... 3.9 -- numForecastMags=20?, is it necessarily 3.9?, is it dependent on minForecastMag?
			for(int j=0; j < forecastMagStart; j++) st.nextToken();
			
			//get the forecast rates
			for(int i = 0;i < numForecastMags; i++) {
				if(st.hasMoreTokens()){
					double rate = Double.parseDouble(st.nextToken());
					magFreqDist.set(i,rate);
				}
			}
			Location loc = new Location(lat,lon,DEPTH);
			// method 2, search for the location index 
			// make sure the hypoMagFreqList has the same order as the region grid location list
			//int index = region.getGridIndex(loc, RegionDefaults.gridPrecision);
			//logger.info(" index " + index);			
			hypoMagFreqDist.add( new HypoMagFreqDistAtLoc(magFreqDist,loc));
			//store in the map for quick search
			hypoMagFreqDistMap.put(getKey4Location(loc),  new HypoMagFreqDistAtLoc(magFreqDist,loc));
			//hypoMagFreqDistArray[index] = new HypoMagFreqDistAtLoc(magFreqDist,loc);
		}
		//convert to list
		//hypoMagFreqDist = new ArrayList <HypoMagFreqDistAtLoc>(Arrays.asList(hypoMagFreqDistArray));
		
		//method 1. sort the collection instead of using an array
		//Collections.sort(hypoMagFreqDist, locationComparator );//sort location by value
		backgroundSourcesAlreadyMade = true;
	}
	
	/**
	 * get the HypoMagFreqDistAtLoc by location
	 * @param loc
	 * @return
	 */
	public HypoMagFreqDistAtLoc getHypoMagFreqDistAtLocation(Location loc){
		return this.hypoMagFreqDistMap.get(getKey4Location(loc));		
	}

	/**
	 * retujrn a key to identify a location
	 * @param loc
	 * @return
	 */
	public String getKey4Location(Location loc) {		
		return Math.round(loc.getLatitude()/RegionDefaults.gridPrecision) + "_" + Math.round(loc.getLongitude()/RegionDefaults.gridPrecision);
	}

	/**
	 * get the index of the minForecastMag in the Bg grid rate source file 
	 * 
	 * @return
	 */
	public int getForecastMagStart()
	{
		double diff = minForecastMag - minMagInSourceFile;
		if(diff <= 0.0D){
			return 0;
		}else{
			return (int)Math.round(diff / deltaForecastMag);
		}
	}

	public void setBackGroundRegion(GriddedRegion backGroundRegion){
		setRegion(backGroundRegion);
//		this.region = backGroundRegion;
	}

	/**
	 * setMinForecastMag
	 */
	public void setMinForecastMag(double minMag) {
		this.minForecastMag = minMag;
	}

	/**
	 * setMaxForecastMag
	 */
	public void setMaxForecastMag(double maxMag) {
		this.maxForecastMag = maxMag;
	}

	/**
	 * setDeltaForecastMag
	 */
	public void setDeltaForecastMag(double deltaMag) {
		this.deltaForecastMag = deltaMag;
	}

	/**
	 * setSeqIndAtNode
	 * @param ithLocation
	 * @param seqInd
	 * seqIndAtNode[] contains the index of the STEP_CombineForecast
	 * that contributes rates to this node if applicable.  if = -1, the rates
	 * come from the background.  
	 */
	public void setSeqIndAtNode(int ithLocation, int seqInd){
		seqIndAtNode[ithLocation] = seqInd;
	}

	public HypoMagFreqDistAtLoc getHypoMagFreqDistAtLoc(int ithLocation){

		return (HypoMagFreqDistAtLoc)hypoMagFreqDist.get(ithLocation);
	}
	

	public ArrayList<HypoMagFreqDistAtLoc> getMagDistList(){
		return hypoMagFreqDist;
	}


	/**
	 * setMagFreqDistAtLoc
	 * @param locDist
	 * @param ithLocation
	 * set the (gridded) IncrementalMagFreqDist at this location 
	 */

	public void setMagFreqDistAtLoc(IncrementalMagFreqDist locDist, int ithLocation){
		/**
		 * changed Nitin's original definition here as hypoMagFreqDist needs a Location
		 * and this was passing an IncrementalMagFreqDist
		 */
		/**
		GutenbergRichterMagFreqDist tgrd = new GutenbergRichterMagFreqDist(4,8,.1);
		if (locDist.getClass().isInstance(tgrd)){
	        System.out.println("is GRDdist" + ithLocation);
		}
		 **/

		HypoMagFreqDistAtLoc tmpFreqDistAtLoc = (HypoMagFreqDistAtLoc)this.hypoMagFreqDist.get(ithLocation);	
		Location tmpLoc = tmpFreqDistAtLoc.getLocation();
		HypoMagFreqDistAtLoc newFreqDistAtLoc = new HypoMagFreqDistAtLoc(locDist,tmpLoc);

		//hypoMagFreqDist.set(ithLocation, locDist);
		hypoMagFreqDist.set(ithLocation, newFreqDistAtLoc);
	}
	
	/**
	 * setMagFreqDistAtLoc
	 * @param locDist
	 * @param ithLocation
	 * set the (gridded) IncrementalMagFreqDist at this location 
	 */

	public void setMagFreqDistAtLocation(IncrementalMagFreqDist locDist, Location loc){	
		HypoMagFreqDistAtLoc newFreqDistAtLoc = new HypoMagFreqDistAtLoc(locDist,loc);
		this.hypoMagFreqDistMap.put(this.getKey4Location(loc), newFreqDistAtLoc);
	}
	

	public double[] getSeqIndAtNode() {
		return seqIndAtNode;
	}

	public boolean isBackgroundSourcesAlreadyMade() {
		return backgroundSourcesAlreadyMade;
	}

	public boolean isBackgroundRatesFileAlreadyRead() {
		return backgroundRatesFileAlreadyRead;
	}

	public ArrayList getBackGroundSourceList() {
		return backGroundSourceList;
	}

	public ArrayList getHypoMagFreqDist() {
		return hypoMagFreqDist;
	}

	/**
	 * check two locations equal to each other
	 * @param loc1
	 * @param loc2
	 * @param precision
	 * @return
	 */
	public boolean checkLocaionEquals(Location loc1, Location loc2, double precision) {
	  if ((Math.round(loc1.getLatitude()/precision)) != (Math.round(loc2.getLatitude()/precision))) return false;
   	  if ((Math.round(loc1.getLongitude()/precision)) != (Math.round(loc2.getLongitude()/precision))) return false;
   	  if ((Math.round(loc1.getDepth()/precision)) != (Math.round(loc2.getDepth()/precision))) return false; 
      
   	  return true;
		
	}

	public HashMap<String, HypoMagFreqDistAtLoc> getMagDistMap() {
		// TODO Auto-generated method stub
		return this.hypoMagFreqDistMap;
	}

}
