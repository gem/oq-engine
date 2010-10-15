package org.opensha.gem.GEM1.scratch;

import java.util.HashMap;

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.DoubleDiscreteConstraint;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.PropagationEffect;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.EqkRuptureParams.StressDropParam;
// import org.opensha.sha.imr.param.EqkRuptureParams.StressDropParam;

import org.opensha.sha.imr.param.IntensityMeasureParams.DampingParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGV_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceRupParameter;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;

/**
 * <b>Title:</b> AtkBoo_2006_AttenRel
 * <p>
 * 
 * <b>Description:</b> This implements the Attenuation Relationship published by
 * Atkinson & Boore (2006,
 * "Earthquake ground-motion prediction equations for Eastern North America",
 * BSSA, 96(2): 2181-2205).
 * 
 * @author Marco M. Pagani
 * @created December, 2009
 * 
 */

public class AtkBoo_2006_AttenRel extends AttenuationRelationship implements
        ScalarIntensityMeasureRelationshipAPI, NamedObjectAPI,
        ParameterChangeListener {

    //
    private static boolean D = false;

    public final static String SHORT_NAME = "AtkBoo06";

    // Warning constraints:
    protected final static Double MAG_WARN_MIN = new Double(3.5);
    protected final static Double MAG_WARN_MAX = new Double(8.0);
    protected final static Double DISTANCE_RUP_WARN_MIN = new Double(0.0);
    protected final static Double DISTANCE_RUP_WARN_MAX = new Double(200.0); // TODO
                                                                             // check
                                                                             // this
    protected final static Double VS30_WARN_MIN = new Double(0.0);
    protected final static Double VS30_WARN_MAX = new Double(2500.0);
    protected final static Double STRESS_DROP_MIN = new Double(35.0);
    protected final static Double STRESS_DROP_MAX = new Double(560.0);

    private transient ParameterChangeWarningListener warningListener = null;
    private static final long serialVersionUID = 1L;

    // // This is the original vector from the BSSA paper
    // double[] period = {
    // 0.010,0.011,0.025,0.031,0.040,0.050,0.063,0.079,0.100,0.125,
    // 0.158,0.200,0.251,0.315,0.397,0.500,0.629,0.794,1.000,1.250,
    // 1.590,2.000,2.500,3.130,4.000,5.000};

    double[] period = { -1.000, +0.010, +0.025, +0.031, +0.040, +0.050, +0.063,
            +0.079, +0.100, +0.125, +0.158, +0.200, +0.251, +0.315, +0.397,
            +0.500, +0.629, +0.794, +1.000, +1.250, +1.590, +2.000, +2.500,
            +3.125, +4.000, +5.000 };

    // Coefficients for bedrock with Vs=2000 m/s:
    // PGV, PGA, Sa ...
    // Tested parameters for: PGA, 0.125, 1.59,
    // double[] c1 = {-1.44,9.07e-1,1.52,1.44,1.26,1.11,0.911,0.691,0.480,0.214,
    // -0.146,-0.615,-1.12,-1.72,-2.44,-3.22,-3.92,-4.60,-5.27,-5.72,
    // -6.04,-6.18,-6.17,-6.04,-5.79,-5.41};
    // double[] c2 = {0.991,0.983,0.960,0.959,0.968,0.972,0.980,0.997,1.02,1.05,
    // 1.12,1.23,1.34,1.48,1.65,1.83,1.99,2.13,2.26,2.32,
    // 2.34,2.30,2.21,2.08,1.92,1.71};
    // double[] c3 =
    // {-5.85e-2,-6.60e-2,-0.0635,-0.0628,-0.0623,-0.0620,-0.0621,-0.0628,-0.0640,-0.0666,
    // -0.0714,-7.89e-2,-0.0872,-0.0974,-0.108,-0.120,-0.131,-0.141,-0.148,-0.151,
    // -0.150,-0.144,-0.135,-0.122,-0.107,-0.0901};
    // double[] c4 =
    // {-2.70,-2.70,-2.81,-2.71,-2.58,-2.47,-2.36,-2.26,-2.20,-2.15,
    // -2.12,-2.09,-2.08,-2.08,-2.05,-2.02,-2.05,-2.06,-2.07,-2.10,
    // -2.16,-2.22,-2.30,-2.37,-2.44,-2.54};
    // double[] c5 =
    // {2.16e-1,1.59e-1,0.146,0.140,0.132,0.128,0.126,0.125,0.127,0.130,
    // 0.130,1.31e-1,0.135,0.138,0.136,0.134,0.142,0.147,0.150,0.157,
    // 0.166,0.177,0.190,0.2,0.211,0.227};
    // double[] c6 =
    // {-2.44,-2.80,-3.65,-3.73,-3.64,-3.39,-2.97,-2.49,-2.01,-1.61,
    // -1.30,-1.12e0,-0.971,-0.889,-0.843,-0.813,-0.782,-0.797,-0.813,-0.820,
    // -0.870,-0.937,-0.986,-1.07,-1.16,-1.27};
    // double[] c7 =
    // {2.66e-1,2.12e-1,0.236,0.234,0.228,0.214,0.191,0.164,0.133,0.105,
    // 0.0831,6.79e-2,0.0563,0.0487,0.0448,0.0444,0.0430,0.0435,0.0467,0.0519,
    // 0.0605,0.0707,0.0786,0.0895,0.102,0.116};
    // double[] c8 =
    // {8.48e-2,-3.01e-1,-0.654,-0.543,-0.351,-0.139,0.107,0.214,0.337,0.427,
    // 0.562,6.06e-1,0.614,0.610,0.739,0.884,0.788,0.775,0.826,0.856,
    // 0.921,0.952,0.968,1.0,1.01,0.979};
    // double[] c9 =
    // {-6.93e-2,-6.53e-2,-0.0550,-0.0645,-0.0813,-0.0984,-0.117,-0.121,-0.127,-0.130,
    // -0.144,-1.46e-1,-0.143,-0.139,-0.156,-0.175,-0.159,-0.156,-0.162,-0.166,-0.173,-0.177,
    // -0.177,-0.180,-0.182,-0.177};
    // double[] c10 =
    // {-3.73e-4,-4.48e-4,-4.85e-5,-3.23e-5,-1.23e-4,-3.17e-4,-5.79e-4,-8.47e-4,-1.05e-3,-1.15e-3,
    // -1.18e-3,-1.13e-3,-1.06e-3,-9.54e-4,-8.51e-4,-7.70e-4,-6.95e-4,-5.79e-4,-4.86e-4,-4.33e-4,
    // -3.75e-4,-3.22e-4,-2.82e-4,-2.31e-4,-2.01e-4,-1.76e-4};

    // Coefficients ground motion calculation on hard rock [max of ten values
    // per line] - from the table
    // 'AB05eqn_Rcd.par' received from David Boore on 2010.10.15
    double[] c1 = { -1.442e+00, +9.069e-01, +1.522e+00, +1.436e+00, +1.264e+00,
            +1.105e+00, +9.109e-01, +6.906e-01, +4.797e-01, +2.144e-01,
            -1.455e-01, -6.153e-01, -1.121e+00, -1.721e+00, -2.437e+00,
            -3.216e+00, -3.917e+00, -4.604e+00, -5.272e+00, -5.724e+00,
            -6.043e+00, -6.183e+00, -6.169e+00, -6.038e+00, -5.791e+00,
            -5.408e+00 };
    double[] c2 = { +9.909e-01, +9.830e-01, +9.597e-01, +9.592e-01, +9.680e-01,
            +9.719e-01, +9.802e-01, +9.974e-01, +1.017e+00, +1.054e+00,
            +1.123e+00, +1.227e+00, +1.342e+00, +1.483e+00, +1.649e+00,
            +1.826e+00, +1.987e+00, +2.132e+00, +2.264e+00, +2.324e+00,
            +2.342e+00, +2.302e+00, +2.211e+00, +2.080e+00, +1.916e+00,
            +1.714e+00 };
    double[] c3 = { -5.848e-02, -6.595e-02, -6.351e-02, -6.276e-02, -6.232e-02,
            -6.197e-02, -6.208e-02, -6.276e-02, -6.404e-02, -6.664e-02,
            -7.143e-02, -7.886e-02, -8.722e-02, -9.739e-02, -1.084e-01,
            -1.201e-01, -1.314e-01, -1.406e-01, -1.483e-01, -1.505e-01,
            -1.496e-01, -1.442e-01, -1.348e-01, -1.221e-01, -1.071e-01,
            -9.012e-02 };
    double[] c4 = { -2.701e+00, -2.698e+00, -2.813e+00, -2.714e+00, -2.581e+00,
            -2.466e+00, -2.360e+00, -2.262e+00, -2.201e+00, -2.154e+00,
            -2.116e+00, -2.087e+00, -2.082e+00, -2.080e+00, -2.051e+00,
            -2.018e+00, -2.045e+00, -2.062e+00, -2.069e+00, -2.104e+00,
            -2.157e+00, -2.223e+00, -2.299e+00, -2.367e+00, -2.441e+00,
            -2.537e+00 };
    double[] c5 = { +2.155e-01, +1.594e-01, +1.458e-01, +1.400e-01, +1.317e-01,
            +1.276e-01, +1.263e-01, +1.246e-01, +1.270e-01, +1.295e-01,
            +1.302e-01, +1.312e-01, +1.349e-01, +1.382e-01, +1.363e-01,
            +1.344e-01, +1.419e-01, +1.468e-01, +1.497e-01, +1.565e-01,
            +1.662e-01, +1.770e-01, +1.898e-01, +2.002e-01, +2.113e-01,
            +2.267e-01 };
    double[] c6 = { -2.436e+00, -2.795e+00, -3.654e+00, -3.728e+00, -3.644e+00,
            -3.390e+00, -2.972e+00, -2.487e+00, -2.007e+00, -1.608e+00,
            -1.303e+00, -1.120e+00, -9.714e-01, -8.893e-01, -8.426e-01,
            -8.134e-01, -7.818e-01, -7.974e-01, -8.132e-01, -8.202e-01,
            -8.704e-01, -9.370e-01, -9.860e-01, -1.073e+00, -1.162e+00,
            -1.268e+00 };
    double[] c7 = { +2.659e-01, +2.120e-01, +2.362e-01, +2.343e-01, +2.276e-01,
            +2.144e-01, +1.910e-01, +1.636e-01, +1.326e-01, +1.046e-01,
            +8.311e-02, +6.788e-02, +5.628e-02, +4.869e-02, +4.483e-02,
            +4.437e-02, +4.297e-02, +4.345e-02, +4.666e-02, +5.186e-02,
            +6.047e-02, +7.067e-02, +7.860e-02, +8.950e-02, +1.018e-01,
            +1.162e-01 };
    double[] c8 = { +8.479e-02, -3.011e-01, -6.544e-01, -5.430e-01, -3.506e-01,
            -1.391e-01, +1.069e-01, +2.139e-01, +3.371e-01, +4.273e-01,
            +5.617e-01, +6.055e-01, +6.140e-01, +6.101e-01, +7.386e-01,
            +8.839e-01, +7.878e-01, +7.748e-01, +8.262e-01, +8.563e-01,
            +9.207e-01, +9.518e-01, +9.683e-01, +1.002e+00, +1.012e+00,
            +9.792e-01 };
    double[] c9 = { -6.927e-02, -6.532e-02, -5.500e-02, -6.448e-02, -8.126e-02,
            -9.839e-02, -1.173e-01, -1.207e-01, -1.266e-01, -1.303e-01,
            -1.438e-01, -1.459e-01, -1.432e-01, -1.389e-01, -1.557e-01,
            -1.751e-01, -1.590e-01, -1.558e-01, -1.622e-01, -1.661e-01,
            -1.734e-01, -1.768e-01, -1.765e-01, -1.803e-01, -1.824e-01,
            -1.767e-01 };
    double[] c10 = { -3.734e-04, -4.484e-04, -4.848e-05, -3.230e-05,
            -1.225e-04, -3.167e-04, -5.786e-04, -8.469e-04, -1.047e-03,
            -1.153e-03, -1.182e-03, -1.125e-03, -1.055e-03, -9.538e-04,
            -8.509e-04, -7.704e-04, -6.948e-04, -5.790e-04, -4.862e-04,
            -4.329e-04, -3.748e-04, -3.220e-04, -2.823e-04, -2.306e-04,
            -2.010e-04, -1.757e-04 };

    // // Coefficients for bedrock with Vs=760 m/s
    // double[] c1s = {
    // -1.66e0,5.23e-1,1.05e0,1.19e0,1.26e0,1.21e0,1.11e0,9.67e-1,7.82e-1,5.36e-1,
    // 1.19e-1,-3.06e-1,-8.76e-1,-1.56e0,-2.28e0,-3.01e0,-3.75e0,-4.45e0,-5.06e0,-5.49e0,
    // -5.75e0,-5.85e0,-5.80e0,-5.59e0,-5.26e0,-4.85e0};
    // double[] c2s = {
    // 1.05e0,9.69e-1,9.03e-1,8.88e-1,8.79e-1,8.83e-1,8.88e-1,9.03e-1,9.24e-1,9.65e-1,
    // 1.06e0,1.16e0,1.29e0,1.46e0,1.63e0,1.80e0,1.97e0,2.12e0,2.23e0,2.29e0,2.29e0,
    // 2.29e0,2.23e0,2.13e0,1.97e0,1.79e0,1.58e0};
    // double[] c3s = {
    // -6.04e-2,-6.20e-2,-5.77e-2,-5.64e-2,-5.52e-2,-5.44e-2,-5.39e-2,-5.48e-2,-5.56e-2,-5.84e-2,
    // -6.47e-2,-7.21e-2,-8.19e-2,-9.31e-2,-1.05e-1,-1.18e-1,-1.29e-1,-1.39e-1,-1.45e-1,-1.48e-1,
    // -1.45e-1,-1.39e-1,-1.28e-1,-1.14e-1,-9.79e-2,-8,07e-2};
    // double[] c4s = {
    // -2.50e0,-2.44e0,-2.57e0,-2.58e0,-2.54e0,-2.44e0,-2.33e0,-2.25e0,-2.17e0,-2.11e0,
    // -2.05e0,-2.04e0,-2.01e0,-1.98e0,-1.97e0,-1.98e0,-2.00e0,-2.01e0,-2.03e0,-2.08e0,
    // -2.13e0,-2.20e0,-2.26e0,-2.33e0,-2.44e0,-2.53e0};
    // double[] c5s = {
    // 1.84e-1,1.47e-1,1.48e-1,1.45e-1,1.39e-1,1.30e-1,1.23e-1,1.22e-1,1.19e-1,1.21e-1,
    // 1.19e-1,1.22e-1,1.23e-1,1.21e-1,1.23e-1,1.27e-1,1.31e-1,1.36e-1,1.41e-1,1.50e-1,
    // 1.58e-1,1.69e-1,1.79e-1,1.91e-1,2.07e-1,2.22e-1};
    // double[] c6s = {
    // -2.30e0,-2.34e0,-2.65e0,-2.84e0,-2.99e-0,-3.04e-0,-2.88e0,-2.53e0,-2.10e0,-1.67e0,
    // -1.36e0,-1.15e0,-1.03e0,-9.47e-1,-8.88e-1,-8.47e-1,-8.42e-1,-8.58e-1,-8.74e-1,-9.00e-1,
    // -9.57e-1,-1.04e0,-1.12e0,-1.20e0,-1.31e0,-1.43e0};
    // double[] c7s = {
    // 2.50e-1,1.91e-1,2.07e-1,2.12e-1,2.16e-1,2.13e-1,2.01e-1,1.78e-1,1.48e-1,1.16e-1,
    // 9.16e-2,7.38e-2,6.34e-2,5.58e-2,5.03e-2,4.70e-2,4.82e-2,4.98e-2,5.41e-2,5.79e-2,
    // 6.76e-2,8.00e-2,9.54e-2,1.10e-1,1.21e-1,1.36e-1};
    // double[] c8s = {
    // 1.27e-1,-8.70e-2,-4.08e-1,-4.37e-1,-3.91e-1,-2.10e-1,-3.19e-1,1.0e-1,2.85e-1,3.43e-1,
    // 5.16e-1, 5.08e-1, 5.81e-1, 6.50e-1, 6.84e-1, 6.67e-1,
    // 6.77e-1,7.08e-1,7.92e-1,8.21e-1,
    // 8.67e-1,8.67e-1,8.91e-1, 8.45e-1, 7.34e-1, 6.34e-1};
    // double[] c9s = {
    // -8.70e-2,-8.29e-2,-5.77e-2,-5.87e-2,-6.75e-2,-9.00e-2,-1.07e-2,-1.15e-2,-1.32e-2,-1.32e-2,
    // -1.50e-1,-1.43e-1,-1.49e-1,-1.56e-1,-1.58e-1,-1.55e-1,-1.56e-1,-1.59e-1,-1.70e-1,-1.72e-1,
    // -1.79e-1,-1.79e-1,-1.80e-1,-1.72e-1,-1.56e-1,-1.41e-1};
    // double[] c10s = {
    // -4.27e-4,-6.30e-4,-5.15e-4,-4.33e-4,-3.88e-4,-4.15e-4,-5.48e-4,-7.72e-4,-9.90e-4,-1.13e-3,
    // -1.18e-3,-1.14e-3,-1.05e-3,-9.55e-4,-8.59e-4,-7.68e-4,-6.76e-4,-5.75e-4,-4.89e-4,-4.07e-4,
    // -3.43e-4,-2.86e-4,-2.60e-4,-2.45e-4,-1.96e-4,-1.61e-4};

    double[] c1s = { -1.662e+00, +5.233e-01, +1.052e+00, +1.191e+00,
            +1.261e+00, +1.209e+00, +1.109e+00, +9.667e-01, +7.818e-01,
            +5.356e-01, +1.194e-01, -3.056e-01, -8.756e-01, -1.560e+00,
            -2.281e+00, -3.007e+00, -3.748e+00, -4.446e+00, -5.058e+00,
            -5.489e+00, -5.754e+00, -5.853e+00, -5.800e+00, -5.590e+00,
            -5.256e+00, -4.852e+00 };
    double[] c2s = { +1.050e+00, +9.686e-01, +9.030e-01, +8.884e-01,
            +8.789e-01, +8.830e-01, +8.875e-01, +9.033e-01, +9.235e-01,
            +9.647e-01, +1.057e+00, +1.156e+00, +1.293e+00, +1.455e+00,
            +1.629e+00, +1.803e+00, +1.973e+00, +2.119e+00, +2.233e+00,
            +2.289e+00, +2.287e+00, +2.233e+00, +2.126e+00, +1.972e+00,
            +1.787e+00, +1.580e+00 };
    double[] c3s = { -6.035e-02, -6.196e-02, -5.768e-02, -5.642e-02,
            -5.515e-02, -5.441e-02, -5.386e-02, -5.476e-02, -5.555e-02,
            -5.835e-02, -6.473e-02, -7.211e-02, -8.193e-02, -9.312e-02,
            -1.054e-01, -1.178e-01, -1.294e-01, -1.387e-01, -1.454e-01,
            -1.476e-01, -1.450e-01, -1.385e-01, -1.278e-01, -1.136e-01,
            -9.785e-02, -8.066e-02 };
    double[] c4s = { -2.496e+00, -2.439e+00, -2.571e+00, -2.577e+00,
            -2.536e+00, -2.440e+00, -2.334e+00, -2.249e+00, -2.165e+00,
            -2.110e+00, -2.054e+00, -2.038e+00, -2.014e+00, -1.977e+00,
            -1.967e+00, -1.982e+00, -1.997e+00, -2.009e+00, -2.030e+00,
            -2.081e+00, -2.131e+00, -2.195e+00, -2.257e+00, -2.331e+00,
            -2.435e+00, -2.530e+00 };
    double[] c5s = { +1.840e-01, +1.465e-01, +1.483e-01, +1.451e-01,
            +1.388e-01, +1.295e-01, +1.229e-01, +1.215e-01, +1.191e-01,
            +1.205e-01, +1.190e-01, +1.220e-01, +1.226e-01, +1.209e-01,
            +1.227e-01, +1.274e-01, +1.313e-01, +1.356e-01, +1.408e-01,
            +1.501e-01, +1.582e-01, +1.688e-01, +1.790e-01, +1.908e-01,
            +2.068e-01, +2.216e-01 };
    double[] c6s = { -2.301e+00, -2.335e+00, -2.652e+00, -2.840e+00,
            -2.994e+00, -3.035e+00, -2.881e+00, -2.530e+00, -2.097e+00,
            -1.672e+00, -1.355e+00, -1.147e+00, -1.027e+00, -9.466e-01,
            -8.880e-01, -8.466e-01, -8.417e-01, -8.576e-01, -8.744e-01,
            -9.000e-01, -9.568e-01, -1.037e+00, -1.123e+00, -1.204e+00,
            -1.307e+00, -1.426e+00 };
    double[] c7s = { +2.500e-01, +1.912e-01, +2.065e-01, +2.121e-01,
            +2.158e-01, +2.133e-01, +2.007e-01, +1.775e-01, +1.483e-01,
            +1.156e-01, +9.160e-02, +7.375e-02, +6.341e-02, +5.576e-02,
            +5.033e-02, +4.698e-02, +4.820e-02, +4.976e-02, +5.412e-02,
            +5.794e-02, +6.762e-02, +8.002e-02, +9.539e-02, +1.099e-01,
            +1.210e-01, +1.361e-01 };
    double[] c8s = { +1.268e-01, -8.695e-02, -4.084e-01, -4.370e-01,
            -3.908e-01, -2.098e-01, -3.189e-02, +1.001e-01, +2.847e-01,
            +3.433e-01, +5.164e-01, +5.082e-01, +5.808e-01, +6.499e-01,
            +6.839e-01, +6.670e-01, +6.772e-01, +7.084e-01, +7.922e-01,
            +8.208e-01, +8.670e-01, +8.666e-01, +8.911e-01, +8.449e-01,
            +7.340e-01, +6.340e-01 };
    double[] c9s = { -8.704e-02, -8.285e-02, -5.769e-02, -5.866e-02,
            -6.746e-02, -8.997e-02, -1.069e-01, -1.147e-01, -1.319e-01,
            -1.322e-01, -1.503e-01, -1.430e-01, -1.491e-01, -1.558e-01,
            -1.582e-01, -1.546e-01, -1.557e-01, -1.589e-01, -1.697e-01,
            -1.719e-01, -1.789e-01, -1.790e-01, -1.797e-01, -1.723e-01,
            -1.560e-01, -1.413e-01 };
    double[] c10s = { -4.266e-04, -6.304e-04, -5.122e-04, -4.329e-04,
            -3.881e-04, -4.145e-04, -5.483e-04, -7.724e-04, -9.897e-04,
            -1.130e-03, -1.178e-03, -1.140e-03, -1.053e-03, -9.552e-04,
            -8.587e-04, -7.676e-04, -6.763e-04, -5.751e-04, -4.886e-04,
            -4.070e-04, -3.429e-04, -2.860e-04, -2.601e-04, -2.452e-04,
            -1.959e-04, -1.608e-04 };

    // // Coefficients for soil response [max of ten values per line]
    // double[] frequencySoil = {
    // 1000.0,1001.00,40.0,32.0,25.0,20.0,15.9,12.6,10.0,8.00,
    // 6.00,5.00,4.00,3.20,2.50,2.00,1.60,1.30,1.00,0.63,
    // 0.50,0.32,0.25,0.20};
    // double[] periodSoil = {};
    // double[] blin =
    // {-0.361,-0.600,-0.330,-0.322,-0.314,-0.286,-0.249,-0.232,-0.250,-0.260,
    // -0.280,-0.306,-0.390,-0.445,-0.500,-0.600,-0.670,-0.690,-0.700,-0.726,
    // -0.730,-0.740,-0.745,-0.752};
    // double[] b1 =
    // {-0.641,-0.495,-0.624,-0.618,-0.609,-0.643,-0.642,-0.637,-0.595,-0.560,
    // -0.528,-0.521,-0.518,-0.513,-0.508,-0.495,-0.480,-0.465,-0.440,-0.395,
    // -0.375,-0.330,-0.310,-0.300};
    // double[] b2 =
    // {-0.060,-0.144,-0.115,-0.108,-0.105,-0.105,-0.105,-0.117,-0.132,-0.140,
    // -0.185,-0.185,-0.160,-0.130,-0.095,-0.060,-0.031,-0.002,0.0,0.0,
    // 0.0,0.0,0.0,0.0};

    // Coefficients from the code David Boore sent on 2010.02.15
    double[] frequencySoil;
    double[] periodSoil = { 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.075, 0.09,
            0.10, 0.12, 0.15, 0.17, 0.20, 0.24, 0.30, 0.36, 0.40, 0.46, 0.50,
            0.60, 0.75, 0.85, 1.00, 1.50, 2.00, 3.00, 4.00, 5.00, 7.50, 10.0 };
    double[] blin = { -0.36, -0.34, -0.33, -0.31, -0.29, -0.25, -0.23, -0.23,
            -0.250, -0.26, -0.28, -0.29, -0.31, -0.38, -0.44, -0.48, -0.50,
            -0.55, -0.600, -0.66, -0.69, -0.69, -0.70, -0.72, -0.73, -0.74,
            -0.75, -0.75, -0.692, -0.650 };
    double[] b1 = { -0.64, -0.63, -0.62, -0.61, -0.64, -0.64, -0.64, -0.640,
            -0.600, -0.560, -0.53, -0.53, -0.52, -0.52, -0.52, -0.51, -0.51,
            -0.500, -0.500, -0.490, -0.47, -0.46, -0.44, -0.40, -0.38, -0.34,
            -0.31, -0.291, -0.247, -0.215 };
    double[] b2 = { -0.14, -0.12, -0.11, -0.11, -0.11, -0.11, -0.11, -0.12,
            -0.13, -0.14, -0.18, -0.19, -0.19, -0.16, -0.14, -0.11, -0.10,
            -0.08, -0.06, -0.03, -0.00, -0.00, -0.00, -0.00, -0.00, -0.00,
            -0.00, -0.00, -0.00, -0.00 };

    // Coefficients for stress drop adjustment [max of ten values per line] -
    // from the BSSA paper
    // double[] delta = {0.11,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,
    // 0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15,
    // 0.15,0.15,0.15,0.15};
    // double[] m1 = {2.00,0.50,0.0,0.0,0.0,0.0,0.17,0.34,0.50,1.15,
    // 1.85,2.50,2.90,3.30,3.65,4.00,4.17,4.34,4.50,4.67,4.84,5.00,
    // 5.25,5.50,5.75,6.00};
    // double[] mh = {5.50,5.50,5.00,5.00,5.00,5.00,5.17,5.34,5.50,5.67,
    // 5.84,6.00,6.12,6.25,6.37,6.50,6.70,6.95,7.20,7.45,7.70,8.00,
    // 8.12,8.25,8.37,8.50};

    // Coefficients for stress drop adjustment [max of ten values per line] -
    // from the table
    // 'ab06_table_7.txt' received from David Boore on 2010.10.15 -
    double[] periodStressDrop = { -1.000, +0.010, +0.025, +0.031, +0.040,
            +0.050, +0.063, +0.079, +0.100, +0.125, +0.158, +0.199, +0.251,
            +0.315, +0.397, +0.500, +0.629, +0.794, +1.000, +1.250, +1.587,
            +2.000, +2.500, +3.125, +4.000, +5.000 };

    double[] delta = { +1.100e-01, +1.500e-01, +1.500e-01, +1.500e-01,
            +1.500e-01, +1.500e-01, +1.500e-01, +1.500e-01, +1.500e-01,
            +1.500e-01, +1.500e-01, +1.500e-01, +1.500e-01, +1.500e-01,
            +1.500e-01, +1.500e-01, +1.500e-01, +1.500e-01, +1.500e-01,
            +1.500e-01, +1.500e-01, +1.500e-01, +1.500e-01, +1.500e-01,
            +1.500e-01, +1.500e-01 };
    double[] m1 = { +2.000e+00, +5.000e-01, +0.000e+00, +0.000e+00, +0.000e+00,
            +0.000e+00, +1.700e-01, +3.400e-01, +5.000e-01, +1.150e+00,
            +1.850e+00, +2.500e+00, +2.900e+00, +3.300e+00, +3.650e+00,
            +4.000e+00, +4.170e+00, +4.340e+00, +4.500e+00, +4.670e+00,
            +4.840e+00, +5.000e+00, +5.250e+00, +5.500e+00, +5.750e+00,
            +6.000e+00 };
    double[] mh = { +5.500e+00, +5.500e+00, +5.000e+00, +5.000e+00, +5.000e+00,
            +5.000e+00, +5.170e+00, +5.340e+00, +5.500e+00, +5.670e+00,
            +5.840e+00, +6.000e+00, +6.120e+00, +6.250e+00, +6.370e+00,
            +6.500e+00, +6.700e+00, +6.950e+00, +7.200e+00, +7.450e+00,
            +7.700e+00, +8.000e+00, +8.120e+00, +8.250e+00, +8.370e+00,
            +8.500e+00 };

    // General variables
    private HashMap<Double, Integer> indexFromPer;
    private HashMap<Double, Integer> indexFromPerSoil;
    private HashMap<Double, Integer> indexFromPerStressDrop;

    private StressDropParam stressDropParam = null;
    private int iper; // Period index
    private double vs30, rrup, mag, stressDrop;
    private String stdDevType, fltType;
    private boolean parameterChange;
    // log() to ln() conversion factor
    private double log2ln = 2.302585;

    /**
     * 
     * @param warningListener
     */
    public AtkBoo_2006_AttenRel(ParameterChangeWarningListener warningListener) {
        super();

        // Warning listener
        this.warningListener = warningListener;
        initSupportedIntensityMeasureParams();

        // Create an Hash map that links the period with its index
        this.indexFromPer = new HashMap<Double, Integer>();
        for (int i = 2; i < period.length; i++) {
            indexFromPer.put(new Double(period[i]), new Integer(i));
        }

        // Calculate period from frequency
        if (this.periodSoil.length < 1) {
            this.periodSoil = new double[frequencySoil.length];
            for (int i = 2; i < frequencySoil.length; i++) {
                this.periodSoil[i] = 1. / frequencySoil[i];
            }
        }

        // Create an Hash map that links the period with its index
        this.indexFromPerSoil = new HashMap<Double, Integer>();
        for (int i = 2; i < periodSoil.length; i++) {
            indexFromPerSoil.put(new Double(periodSoil[i]), new Integer(i));
        }

        // Create an Hash map that links the period with its index
        this.indexFromPerStressDrop = new HashMap<Double, Integer>();
        for (int i = 2; i < periodStressDrop.length; i++) {
            indexFromPerStressDrop.put(new Double(periodStressDrop[i]),
                    new Integer(i));
        }

        // Initialize earthquake Rupture parameters (e.g. magnitude)
        initEqkRuptureParams();
        // Initialize Propagation Effect Parameters (e.g. source-site distance)
        initPropagationEffectParams();
        // Initialize site parameters (e.g. vs30)
        initSiteParams();
        // Initialize other parameters (e.g. stress drop)
        initOtherParams();
        // Initialize the independent parameters list
        initIndependentParamList();
        // Initialize the parameter change listeners
        initParameterEventListeners();
    }

    /**
     * This initializes the parameter characterizing the earthquake rupture such
     * as the magnitude and the stress drop.
     */
    protected void initEqkRuptureParams() {
        // Instantiate the parameters
        magParam = new MagParam(MAG_WARN_MIN, MAG_WARN_MAX);
        stressDropParam = new StressDropParam(STRESS_DROP_MIN, STRESS_DROP_MAX);
        // Clear the list
        eqkRuptureParams.clear();
        // Add the parameters to the list
        eqkRuptureParams.addParameter(magParam);
        eqkRuptureParams.addParameter(stressDropParam);
    }

    /**
     * This initializes the parameters characterizing the propagation path such
     * as the source to site distance.
     */
    protected void initPropagationEffectParams() {
        // Instantiate the parameter describing the source to site distance
        distanceRupParam = new DistanceRupParameter(0.0);
        distanceRupParam.addParameterChangeWarningListener(warningListener);
        DoubleConstraint warn =
                new DoubleConstraint(DISTANCE_RUP_WARN_MIN,
                        DISTANCE_RUP_WARN_MAX);
        warn.setNonEditable();
        distanceRupParam.setWarningConstraint(warn);
        distanceRupParam.setNonEditable();
        // Update the propagationEffect parameter
        propagationEffectParams.addParameter(distanceRupParam);
    }

    /**
     * This sets the propagation term parameters.
     */
    public void setPropagationEffect(PropagationEffect propEffect)
            throws InvalidRangeException, ParameterException {
        this.site = propEffect.getSite();
        this.eqkRupture = propEffect.getEqkRupture();
        vs30Param.setValueIgnoreWarning((Double) site.getParameter(
                Vs30_Param.NAME).getValue());
        magParam.setValueIgnoreWarning(new Double(eqkRupture.getMag()));
        propEffect.setParamValue(distanceRupParam);
    }

    /**
	 * 
	 */
    protected void initSiteParams() {
        vs30Param = new Vs30_Param(VS30_WARN_MIN, VS30_WARN_MAX);
        siteParams.clear();
        siteParams.addParameter(vs30Param);
    }

    /**
	 * 
	 */
    protected void initOtherParams() {

        //
        super.initOtherParams();

        // Ground motion component
        StringConstraint constraint = new StringConstraint();
        constraint.addString(ComponentParam.COMPONENT_GMRotI50);
        componentParam =
                new ComponentParam(constraint,
                        ComponentParam.COMPONENT_GMRotI50);

        // Add the parameter to the list
        otherParams.addParameter(componentParam);

        // Standard deviation
        StringConstraint stdDevTypeConstraint = new StringConstraint();
        stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
        stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_NONE);
        stdDevTypeConstraint.setNonEditable();
        stdDevTypeParam = new StdDevTypeParam(stdDevTypeConstraint);

        // Add the parameter to the list
        otherParams.addParameter(stdDevTypeParam);
    }

    /**
	 * 
	 */
    protected void initIndependentParamList() {
        // Parameters that the mean depends upon
        meanIndependentParams.clear();
        meanIndependentParams.addParameter(distanceRupParam);
        meanIndependentParams.addParameter(stressDropParam);
        meanIndependentParams.addParameter(vs30Param);
        meanIndependentParams.addParameter(magParam);
        // meanIndependentParams.addParameter(componentParam); // TODO check
        // this

        // Parameters that the stdDev depends upon
        stdDevIndependentParams.clear();
        stdDevIndependentParams.addParameter(stdDevTypeParam);

        // Parameters that the exceed. probability depends upon
        exceedProbIndependentParams.clear();
        exceedProbIndependentParams.addParameterList(meanIndependentParams);
        exceedProbIndependentParams.addParameter(stdDevTypeParam);
        exceedProbIndependentParams.addParameter(sigmaTruncTypeParam);
        exceedProbIndependentParams.addParameter(sigmaTruncLevelParam);

        // Parameters that the IML at exceed. prob. depends upon
        imlAtExceedProbIndependentParams
                .addParameterList(exceedProbIndependentParams);
        imlAtExceedProbIndependentParams.addParameter(exceedProbParam);
    }

    /**
     * This initializes the supported IMT parameters.
     */
    protected void initSupportedIntensityMeasureParams() {

        // Create a list of supported ground motion parameters and relative
        // periods. Note that the
        // first two periods are PGV and PGA
        DoubleDiscreteConstraint periodConstraint =
                new DoubleDiscreteConstraint();
        for (int i = 2; i < period.length; i++) {
            periodConstraint.addDouble(new Double(period[i]));
        }
        periodConstraint.setNonEditable();

        // Period and damping parameters
        saPeriodParam = new PeriodParam(periodConstraint);
        saDampingParam = new DampingParam();
        saParam = new SA_Param(saPeriodParam, saDampingParam);
        saParam.setNonEditable();

        // Create PGA param
        pgaParam = new PGA_Param();
        pgaParam.setNonEditable();

        // Create PGV param
        pgvParam = new PGV_Param();
        pgvParam.setNonEditable();

        // Warning listeners
        saParam.addParameterChangeWarningListener(warningListener);
        pgaParam.addParameterChangeWarningListener(warningListener);
        pgvParam.addParameterChangeWarningListener(warningListener);

        // Finally, create the list of supported IM Parameters
        supportedIMParams.clear();
        supportedIMParams.addParameter(saParam);
        supportedIMParams.addParameter(pgaParam);
        supportedIMParams.addParameter(pgvParam);
    }

    /**
     * This sets the earthquake rupture parameters.
     * 
     * @param eqkRup
     */
    public void setEqkRupture(EqkRupture eqkRup) {

        magParam.setValueIgnoreWarning(new Double(eqkRup.getMag()));
        this.eqkRupture = eqkRup;

        // Updates the propagation effect parameters (in case the source-site
        // distance changed)
        setPropagationEffectParams();
    }

    /**
     * This sets the earthquake rupture parameters.
     * 
     * @param eqkRup
     *            Earthquake rupture
     * @param stressDrop
     *            Value of static stress drop [in bars -- note: 1 bar = 100 kPa]
     */
    public void setEqkRupture(EqkRupture eqkRup, double stressDrop) {

        magParam.setValueIgnoreWarning(new Double(eqkRup.getMag()));
        this.eqkRupture = eqkRup;

        stressDropParam.setValueIgnoreWarning(stressDrop);
        this.stressDrop = stressDrop;

        // Updates the propagation effect parameters (in case the source-site
        // distance changed)
        setPropagationEffectParams();
    }

    /**
     * This sets the site parameters such as the Vs30 value
     * 
     * @param site
     */
    public void setSite(Site site) {
        vs30Param.setValue((Double) site.getParameter(Vs30_Param.NAME)
                .getValue());
        this.site = site;
        setPropagationEffectParams();
    }

    /**
     * This set the propagation parameter i.e. the source to site distance using
     * the Site
     * 
     */
    protected void setPropagationEffectParams() {
        if ((this.site != null) && (this.eqkRupture != null)) {
            distanceRupParam.setValue(eqkRupture, site);
        }
    }

    /**
     * This sets the coefficient index. This index is used to get from the
     * arrays initialized at the beginning of this class the parameters
     * necessary to calculate the
     * 
     * @throws ParameterException
     */
    protected void setCoeffIndex() throws ParameterException {
        //
        if (im == null) {
            throw new ParameterException(C + ": updateCoefficients():"
                    + "The Intensity Measure"
                    + " Parameter has not been set yet, unable to process");
        }
        //
        if (im.getName().equalsIgnoreCase(PGV_Param.NAME)) {
            iper = 0;
        } else if (im.getName().equalsIgnoreCase(PGA_Param.NAME)) {
            iper = 1;
        } else {
            // Note: this gives the index of the period contained in the period
            // array populated at
            // the beginning of this class.
            iper =
                    ((Integer) indexFromPer.get(saPeriodParam.getValue()))
                            .intValue();
        }
        parameterChange = true;
        intensityMeasureChanged = false;
    }

    /**
     * This returns the mean ground motion value given Earthquake Rupture and
     * Site
     */
    public double getMean() {
        if (rrup > USER_MAX_DISTANCE)
            return VERY_SMALL_MEAN;
        if (intensityMeasureChanged) {
            setCoeffIndex();
        }
        ;
        return getMean(iper, vs30, rrup, mag, stressDrop);
    }

    /**
     * This computes the mean ln(gm)
     * 
     * @param iper
     * @param vs30
     * @param rrup
     * @param mag
     * @return
     */
    public double getMean(int iper, double vs30, double rrup, double mag,
            double stressDrop) {
        //
        double gm;
        double lnGm, logGm;
        double tmp;
        double f0, f1, f2;

        final double R0 = 10.0; // distance in km
        final double R1 = 70.0; // distance in km
        final double R2 = 140.0; // distance in km

        // This is to avoid rrup == 0 distances
        if (rrup < 1e-3) {
            System.out.println(iper + " " + vs30 + " " + rrup + " " + mag + " "
                    + stressDrop);
            rrup = 1;
        }

        if (D)
            System.out.println("");
        if (D) {
            System.out.printf("Period index ..... : %d\n", iper);
            System.out.printf("Vs30 ............. : %6.2f\n", vs30);
            System.out.printf("R Rup ............ : %6.2f\n", rrup);
            System.out.printf("Mag .............. : %6.2f\n", mag);
            System.out.printf("Stress Drop ...... : %6.2f\n", stressDrop);
        }

        // Correction factors
        f0 = Math.log10(R0 / rrup);
        tmp = 0.0;
        if (tmp > f0)
            f0 = tmp;
        f1 = Math.log10(R1);
        tmp = Math.log10(rrup);
        if (tmp < f1)
            f1 = tmp;
        f2 = Math.log10(rrup / R2);
        tmp = 0.0;
        if (tmp > f2)
            f2 = tmp;

        // Initialize the site term correction factor
        double SiteFactor = 0;

        // Stress Drop Correction
        double StressDropFactor = 0.0;
        double scalingFactor = 0.0;

        if (stressDrop > 140.01 || stressDrop < 139.99) {
            double[] coefSD = getStressDropParameters(period[iper]);
            scalingFactor = coefSD[0] + 0.05; // This is the first term
            double t2 = mag - coefSD[1];
            if (t2 < 0.0)
                t2 = 0.0;
            double t3 = 0.05 + coefSD[0] * (t2 / (coefSD[2] - coefSD[1]));
            if (scalingFactor > t3)
                scalingFactor = t3;
            StressDropFactor =
                    scalingFactor
                            * (Math.log10(stressDrop / 140.0) / Math.log10(2.0));
        }

        // System.out.printf("%f %f %f %f %f %f %f %f %f %f  ",
        // c1s[iper],c2s[iper],c3s[iper],c4s[iper],c5s[iper],c6s[iper],c7s[iper],c8s[iper],
        // c9s[iper],c10s[iper]);

        if (vs30 >= 2000) {

            // This is the log10(GM)? on a reference bedrock with Vs30 = 2000
            // m/s
            logGm =
                    c1[iper] + c2[iper] * mag + c3[iper] * mag * mag
                            + (c4[iper] + c5[iper] * mag) * f1
                            + (c6[iper] + c7[iper] * mag) * f2
                            + (c8[iper] + c9[iper] * mag) * f0 + c10[iper]
                            * rrup;
            logGm += StressDropFactor;

        } else {

            double vref = 760;
            double v1 = 180;
            double v2 = 300;
            double bnl;
            double pgaBC, logPgaBC;
            int ipga = 2;

            // This is the log10(PSA) [cm/s2 or cm/s]
            logGm =
                    c1s[iper] + c2s[iper] * mag + c3s[iper] * mag * mag
                            + (c4s[iper] + c5s[iper] * mag) * f1
                            + (c6s[iper] + c7s[iper] * mag) * f2
                            + (c8s[iper] + c9s[iper] * mag) * f0 + c10s[iper]
                            * rrup;
            logGm += StressDropFactor;

            // This is the log10(PGA) [cm/s2] on a reference site with Vs30 =
            // 760 m/s - This is
            // used to compute the
            logPgaBC =
                    c1s[ipga] + c2s[ipga] * mag + c3s[ipga] * mag * mag
                            + (c4s[ipga] + c5s[ipga] * mag) * f1
                            + (c6s[ipga] + c7s[ipga] * mag) * f2
                            + (c8s[ipga] + c9s[ipga] * mag) * f0 + c10s[ipga]
                            * rrup;
            logPgaBC += StressDropFactor;
            pgaBC = Math.pow(10, logPgaBC);

            // Compute the bnl coefficient
            double[] coef = getSoilParameters(period[iper]);

            if (vs30 <= v1) {
                bnl = coef[1];
            } else if (vs30 <= v2) {
                bnl =
                        (coef[1] - coef[2]) * Math.log(vs30 / v2)
                                / Math.log(v1 / v2) + coef[2];
            } else if (vs30 <= vref) {
                bnl = coef[2] * Math.log(vs30 / vref) / Math.log(v2 / vref);
                // Debug
                if (D)
                    System.out
                            .printf("  b2: %.3f vs30: %.2f v2: %.2f vref: %.2f bnl: %.3f\n",
                                    coef[2], vs30, v2, vref, bnl);
            } else {
                bnl = 0.0;
            }

            // Compute the amplification factor
            double linfa = 0.0;
            double nlinfa = 0.0;
            if (D)
                System.out.printf("  pgaBC: %.3f \n", pgaBC);
            if (pgaBC <= 60) {
                linfa = Math.exp(coef[0] * Math.log(vs30 / vref));
                nlinfa = Math.exp(bnl * Math.log(60.0 / 100.0));
                SiteFactor =
                        Math.log10(Math.exp(coef[0] * Math.log(vs30 / vref)
                                + bnl * Math.log(60.0 / 100.0)));
            } else {
                linfa = Math.exp(coef[0] * Math.log(vs30 / vref));
                nlinfa = Math.exp(bnl * Math.log(pgaBC / 100.0));
                SiteFactor =
                        Math.log10(Math.exp(coef[0] * Math.log(vs30 / vref)
                                + bnl * Math.log(pgaBC / 100.0)));
            }

            if (D)
                System.out.printf(
                        "  Amplification factors: lin %.3f nlin %.3f \n",
                        linfa, nlinfa);

        }

        // Compute the final value of ground motion
        logGm += SiteFactor;

        return Math.log(Math.exp(logGm * log2ln) / 981);
    }

    /**
	 * 
	 */
    public double getStdDev() {
        if (intensityMeasureChanged) {
            setCoeffIndex();
        }
        return getStdDev(iper);
    }

    /**
     * 
     * @param iper
     * @return
     */
    public double getStdDev(double iper) {
        if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_TOTAL)) {
            return 0.30 * log2ln;
        } else {
            return Double.NaN;
        }
    }

    public String getShortName() {
        return SHORT_NAME;
    }

    /**
     * This sets the defaults parameters
     */
    public void setParamDefaults() {

        vs30Param.setValueAsDefault();
        magParam.setValueAsDefault();
        distanceRupParam.setValueAsDefault();
        saParam.setValueAsDefault();
        saPeriodParam.setValueAsDefault();
        saDampingParam.setValueAsDefault();
        pgaParam.setValueAsDefault();
        pgvParam.setValueAsDefault();
        // Standard deviation
        stdDevTypeParam.setValueAsDefault();
        // Stress Drop Parameter
        stressDropParam.setValueAsDefault();
        // GM component
        // componentParam.setValueAsDefault();

        // Set parameters
        vs30 = ((Double) vs30Param.getValue()).doubleValue();
        rrup = ((Double) distanceRupParam.getValue()).doubleValue();
        mag = ((Double) magParam.getValue()).doubleValue();
        stdDevType = (String) stdDevTypeParam.getValue();
        stressDrop = ((Double) stressDropParam.getValue());
    }

    /**
     * This updates the value of a changed parameter
     */
    public void parameterChange(ParameterChangeEvent e) {
        String pName = e.getParameterName();
        Object val = e.getNewValue();
        parameterChange = true;
        if (pName.equals(DistanceRupParameter.NAME)) {
            rrup = ((Double) val).doubleValue();
        } else if (pName.equals(Vs30_Param.NAME)) {
            vs30 = ((Double) val).doubleValue();
        } else if (pName.equals(magParam.NAME)) {
            mag = ((Double) val).doubleValue();
        } else if (pName.equals(StdDevTypeParam.NAME)) {
            stdDevType = (String) val;
        } else if (pName.equals(StressDropParam.NAME)) {
            stressDrop = (Double) val;
        } else if (pName.equals(PeriodParam.NAME)) {
            intensityMeasureChanged = true;
        }
    }

    /**
     * Allows to reset the change listeners on the parameters
     */
    public void resetParameterEventListeners() {
        distanceRupParam.removeParameterChangeListener(this);
        vs30Param.removeParameterChangeListener(this);
        magParam.removeParameterChangeListener(this);
        stdDevTypeParam.removeParameterChangeListener(this);
        saPeriodParam.removeParameterChangeListener(this);
        this.initParameterEventListeners();
    }

    /**
     * Adds the parameter change listeners. This allows to listen to when-ever
     * the parameter is changed.
     */
    protected void initParameterEventListeners() {
        distanceRupParam.addParameterChangeListener(this);
        vs30Param.addParameterChangeListener(this);
        magParam.addParameterChangeListener(this);
        stdDevTypeParam.addParameterChangeListener(this);
        saPeriodParam.addParameterChangeListener(this);
        stressDropParam.addParameterChangeListener(this);
    }

    /**
     * This method computes the blin, b1 and b2 soil response coefficients. The
     * values of the period (i.e frequency) provided by Atkinson and Boore do
     * not correspond to the ones available for computing the GM on hard rock or
     * BC soil conditions (vs30=760m/s) - see also Tables 6 and 9 of Atkinson
     * and Boore (2006) for a comprehensive list of periods. For the missing
     * periods, we calculate the values using a simple interpolation procedure.
     * 
     * 2010.02.02 - Checked the computed coefficients: values are in agreement
     * with the numbers contained in Table 8 of Atkinson and Boore (2006).
     * 
     * @param period
     * @return
     */
    protected double[] getSoilParameters(Double period) {
        double[] coef = new double[3];
        if (indexFromPerSoil.containsKey(period)) {
            // int idx = indexFromPerSoil.get(period);
            int idx = ((Integer) indexFromPerSoil.get(period)).intValue();
            coef[0] = blin[idx];
            coef[1] = b1[idx];
            coef[2] = b2[idx];
        } else {
            ArbitrarilyDiscretizedFunc fun_blin =
                    new ArbitrarilyDiscretizedFunc();
            ArbitrarilyDiscretizedFunc fun_b1 =
                    new ArbitrarilyDiscretizedFunc();
            ArbitrarilyDiscretizedFunc fun_b2 =
                    new ArbitrarilyDiscretizedFunc();
            for (int i = 0; i < periodSoil.length; i++) {
                fun_blin.set(periodSoil[i], blin[i]);
                fun_b1.set(periodSoil[i], b1[i]);
                fun_b2.set(periodSoil[i], b2[i]);
            }
            coef[0] = fun_blin.getInterpolatedY(period);
            coef[1] = fun_b1.getInterpolatedY(period);
            coef[2] = fun_b2.getInterpolatedY(period);
            if (D)
                System.out
                        .printf("  soil coeff interpolated T=%6.2f blin: %.3f b1:%.3f b2:%.3f\n",
                                period, coef[0], coef[1], coef[2]);
        }
        return coef;
    }

    /**
     * 
     * @param period
     * @return
     */
    protected double[] getStressDropParameters(Double T) {
        double[] coef = new double[3];
        if (indexFromPerStressDrop.containsKey(T)) {
            int idx = indexFromPerStressDrop.get(T);
            coef[0] = delta[idx];
            coef[1] = m1[idx];
            coef[2] = mh[idx];
        } else {
            ArbitrarilyDiscretizedFunc fun_m1 =
                    new ArbitrarilyDiscretizedFunc();
            ArbitrarilyDiscretizedFunc fun_mh =
                    new ArbitrarilyDiscretizedFunc();
            for (int i = 0; i < period.length; i++) {
                fun_m1.set(period[i], m1[i]);
                fun_mh.set(period[i], mh[i]);
            }
            if (T == 0.010) {
                coef[0] = 0.11;
            } else {
                coef[0] = delta[1];
            }
            coef[1] = fun_m1.getInterpolatedY(T);
            coef[2] = fun_mh.getInterpolatedY(T);
        }
        return coef;
    }

}
