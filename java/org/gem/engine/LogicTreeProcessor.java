package org.gem.engine;

import java.util.Properties;

import org.apache.commons.configuration.Configuration;
import org.apache.commons.configuration.ConfigurationConverter;
import org.gem.engine.hazard.redis.Cache;
import org.opensha.commons.data.TimeSpan;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.GEM1ERF;

import com.google.gson.Gson;

public class LogicTreeProcessor {
    /**
     * WARNING, this file is deprecated in favor of python implementation!
     * See openquake/input/logictree.py
     */

    private final Configuration config;

    private static enum ConfigItems {
        SOURCE_MODEL_LOGIC_TREE_FILE,
        GMPE_LOGIC_TREE_FILE,
        OUTPUT_DIR,
        SUBDUCTION_FAULT_SURFACE_DISCRETIZATION,
        MAXIMUM_DISTANCE,
        SUBDUCTION_FAULT_MAGNITUDE_SCALING_RELATIONSHIP,
        SUBDUCTION_RUPTURE_FLOATING_TYPE,
        INTENSITY_MEASURE_TYPE,
        FAULT_MAGNITUDE_SCALING_SIGMA,
        INCLUDE_GRID_SOURCES,
        PERIOD,
        INCLUDE_SUBDUCTION_FAULT_SOURCE,
        WIDTH_OF_MFD_BIN,
        MINIMUM_MAGNITUDE,
        SUBDUCTION_FAULT_MAGNITUDE_SCALING_SIGMA,
        DAMPING,
        NUMBER_OF_LOGIC_TREE_SAMPLES,
        NUMBER_OF_SEISMICITY_HISTORIES,
        AREA_SOURCE_MAGNITUDE_SCALING_RELATIONSHIP,
        INVESTIGATION_TIME,
        TREAT_GRID_SOURCE_AS,
        INCLUDE_AREA_SOURCES,
        FAULT_MAGNITUDE_SCALING_RELATIONSHIP,
        SUBDUCTION_RUPTURE_ASPECT_RATIO,
        TREAT_AREA_SOURCE_AS,
        REFERENCE_VS30_VALUE,
        REFERENCE_DEPTH_TO_2PT5KM_PER_SEC_PARAM,
        REGION_VERTEX,
        REGION_GRID_SPACING,
        CALCULATION_MODE,
        FAULT_SURFACE_DISCRETIZATION,
        COMPONENT,
        RUPTURE_ASPECT_RATIO,
        NUMBER_OF_PROCESSORS,
        INTENSITY_MEASURE_LEVELS,
        TRUNCATION_LEVEL,
        GMPE_TRUNCATION_TYPE,
        AREA_SOURCE_DISCRETIZATION,
        GRID_SOURCE_MAGNITUDE_SCALING_RELATIONSHIP,
        STANDARD_DEVIATION_TYPE,
        INCLUDE_FAULT_SOURCE,
        SUBDUCTION_FAULT_RUPTURE_OFFSET,
        FAULT_RUPTURE_OFFSET,
        RUPTURE_FLOATING_TYPE,
        SOURCE_MODEL_LT_RANDOM_SEED,
        GMPE_LT_RANDOM_SEED,
        SADIGH_SITE_TYPE,
        REGION,
        GROUND_MOTION_CORRELATION,
    } // enum

    /**
     * Create LogicTreeProcessor by loading a job configuration from the
     * available KVS. The configuration file is serialized as JSON.
     *
     * @param cache
     *            - KVS connection
     * @param key
     *            - key used to retrieve the job config from the KVS
     */
    public LogicTreeProcessor(Cache cache, String key) {
        Properties properties =
                new Gson().fromJson((String) cache.get(key), Properties.class);

        config = ConfigurationConverter.getConfiguration(properties);
    }

    /**
     * Set the GEM1ERF params given the parameters defined in
     *
     * @param erf
     *            : erf for which parameters have to be set
     * @param calcConfig
     *            : calculator configuration obejct containing parameters for
     *            the ERF
     */
    public void setGEM1ERFParams(GEM1ERF erf) {
        // set minimum magnitude
        /*
         * xxr: TODO: !!!type safety!!! apache's Configuration interface handles
         * a similar problem this way: Instead of defining one single method
         * like public void setParameter(String key, Object value) {...} there
         * is one method per type defined: setString(), setDouble(), setInt(),
         * ...
         */
        erf.setParameter(GEM1ERF.MIN_MAG_NAME, config
                .getDouble(ConfigItems.MINIMUM_MAGNITUDE.name()));
        // set time span
        TimeSpan timeSpan = new TimeSpan(TimeSpan.NONE, TimeSpan.YEARS);
        timeSpan.setDuration(config.getDouble(ConfigItems.INVESTIGATION_TIME
                .name()));
        erf.setTimeSpan(timeSpan);

        // params for area source
        // set inclusion of area sources in the calculation
        erf.setParameter(GEM1ERF.INCLUDE_AREA_SRC_PARAM_NAME, config
                .getBoolean(ConfigItems.INCLUDE_AREA_SOURCES.name()));
        // set rupture type ("area source rupture model /
        // area_source_rupture_model / AreaSourceRuptureModel)
        erf.setParameter(GEM1ERF.AREA_SRC_RUP_TYPE_NAME, config
                .getString(ConfigItems.TREAT_AREA_SOURCE_AS.name()));
        // set area discretization
        erf.setParameter(GEM1ERF.AREA_SRC_DISCR_PARAM_NAME, config
                .getDouble(ConfigItems.AREA_SOURCE_DISCRETIZATION.name()));
        // set mag-scaling relationship
        erf
                .setParameter(
                        GEM1ERF.AREA_SRC_MAG_SCALING_REL_PARAM_NAME,
                        config
                                .getString(ConfigItems.AREA_SOURCE_MAGNITUDE_SCALING_RELATIONSHIP
                                        .name()));
        // params for grid source
        // inclusion of grid sources in the calculation
        erf.setParameter(GEM1ERF.INCLUDE_GRIDDED_SEIS_PARAM_NAME, config
                .getBoolean(ConfigItems.INCLUDE_GRID_SOURCES.name()));
        // rupture model
        erf.setParameter(GEM1ERF.GRIDDED_SEIS_RUP_TYPE_NAME, config
                .getString(ConfigItems.TREAT_GRID_SOURCE_AS.name()));
        // mag-scaling relationship
        erf
                .setParameter(
                        GEM1ERF.GRIDDED_SEIS_MAG_SCALING_REL_PARAM_NAME,
                        config
                                .getString(ConfigItems.AREA_SOURCE_MAGNITUDE_SCALING_RELATIONSHIP
                                        .name()));

        // params for fault source
        // inclusion of fault sources in the calculation
        erf.setParameter(GEM1ERF.INCLUDE_FAULT_SOURCES_PARAM_NAME, config
                .getBoolean(ConfigItems.INCLUDE_FAULT_SOURCE.name()));
        // rupture offset
        erf.setParameter(GEM1ERF.FAULT_RUP_OFFSET_PARAM_NAME, config
                .getDouble(ConfigItems.FAULT_RUPTURE_OFFSET.name()));
        // surface discretization
        erf.setParameter(GEM1ERF.FAULT_DISCR_PARAM_NAME, config
                .getDouble(ConfigItems.FAULT_SURFACE_DISCRETIZATION.name()));
        // mag-scaling relationship
        erf.setParameter(GEM1ERF.FAULT_MAG_SCALING_REL_PARAM_NAME, config
                .getString(ConfigItems.FAULT_MAGNITUDE_SCALING_RELATIONSHIP
                        .name()));

        // mag-scaling sigma
        erf.setParameter(GEM1ERF.FAULT_SCALING_SIGMA_PARAM_NAME, config
                .getDouble(ConfigItems.FAULT_MAGNITUDE_SCALING_SIGMA.name()));
        // rupture aspect ratio
        erf.setParameter(GEM1ERF.FAULT_RUP_ASPECT_RATIO_PARAM_NAME, config
                .getDouble(ConfigItems.RUPTURE_ASPECT_RATIO.name()));
        // rupture floating type
        erf.setParameter(GEM1ERF.FAULT_FLOATER_TYPE_PARAM_NAME, config
                .getString(ConfigItems.RUPTURE_FLOATING_TYPE.name()));

        // params for subduction fault
        // inclusion of fault sources in the calculation
        erf
                .setParameter(
                        GEM1ERF.INCLUDE_SUBDUCTION_SOURCES_PARAM_NAME,
                        config
                                .getBoolean(ConfigItems.INCLUDE_SUBDUCTION_FAULT_SOURCE
                                        .name()));
        // rupture offset
        erf.setParameter(GEM1ERF.SUB_RUP_OFFSET_PARAM_NAME, config
                .getDouble(ConfigItems.SUBDUCTION_FAULT_RUPTURE_OFFSET.name()));
        // surface discretization
        erf.setParameter(GEM1ERF.SUB_DISCR_PARAM_NAME, config
                .getDouble(ConfigItems.SUBDUCTION_FAULT_SURFACE_DISCRETIZATION
                        .name()));
        // mag-scaling relationship
        erf
                .setParameter(
                        GEM1ERF.SUB_MAG_SCALING_REL_PARAM_NAME,
                        config
                                .getString(ConfigItems.SUBDUCTION_FAULT_MAGNITUDE_SCALING_RELATIONSHIP
                                        .name()));
        // mag-scaling sigma
        erf.setParameter(GEM1ERF.SUB_SCALING_SIGMA_PARAM_NAME, config
                .getDouble(ConfigItems.SUBDUCTION_FAULT_MAGNITUDE_SCALING_SIGMA
                        .name()));
        // rupture aspect ratio
        erf.setParameter(GEM1ERF.SUB_RUP_ASPECT_RATIO_PARAM_NAME, config
                .getDouble(ConfigItems.SUBDUCTION_RUPTURE_ASPECT_RATIO.name()));
        // rupture floating type
        erf
                .setParameter(GEM1ERF.SUB_FLOATER_TYPE_PARAM_NAME, config
                        .getString(ConfigItems.SUBDUCTION_RUPTURE_FLOATING_TYPE
                                .name()));

        // update
        erf.updateForecast();
    } // setGEM1ERFParams()

}
