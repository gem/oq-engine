package org.gem.engine;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.param.IntensityMeasureParams.DampingParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;

public class GmpeLogicTreeData {
    /**
     * WARNING, this file is deprecated in favor of python implementation!
     * See openquake/input/logictree.py
     */

    private static Log logger = LogFactory.getLog(GmpeLogicTreeData.class);

    /**
     * Set GMPE parameters
     */
    public static void setGmpeParams(String component, String intensityMeasureType,
            double period, double damping, String truncType, double truncLevel,
            String stdType, double vs30, AttenuationRelationship ar) {
        String gmpeName = ar.getClass().getCanonicalName();

        ar.setComponentParameter(component, intensityMeasureType);
        
        if (ar.getSupportedIntensityMeasuresList().containsParameter(
                intensityMeasureType)) {
            ar.setIntensityMeasure(intensityMeasureType);
        } else {
            String msg =
                    "The chosen intensity measure type: "
                            + intensityMeasureType + " is not supported by "
                            + gmpeName + "\n"
                            + "The supported types are the following:\n"
                            + ar.getSupportedIntensityMeasuresList().toString()
                            + "\n" + "Check your input file!\n"
                            + "Execution stopped.";
            logger.error(msg);
            throw new IllegalArgumentException(msg);
        }
        if (intensityMeasureType.equalsIgnoreCase(SA_Param.NAME)) {
            if (ar.getParameter(PeriodParam.NAME).isAllowed(period)) {
                ar.getParameter(PeriodParam.NAME).setValue(period);
            } else {
                String msg =
                        "The chosen period: "
                                + period
                                + " is not supported by "
                                + gmpeName
                                + "\n"
                                + "The allowed values are the following:\n"
                                + ar.getParameter(PeriodParam.NAME)
                                        .getConstraint() + "\n"
                                + "Check your input file\n"
                                + "Execution stopped.";
                logger.error(msg);
                new IllegalArgumentException(msg);
            }
            if (ar.getParameter(DampingParam.NAME).isAllowed(damping)) {
                ar.getParameter(DampingParam.NAME).setValue(damping);
            } else {
                String msg =
                        "The chosen damping: "
                                + damping
                                + " is not supported by "
                                + gmpeName
                                + "\n"
                                + "The allowed values are the following:\n"
                                + ar.getParameter(DampingParam.NAME)
                                        .getConstraint() + "\n"
                                + "Check your input file\n"
                                + "Execution stopped.";
                logger.error(msg);
                throw new IllegalArgumentException(msg);
            }
        }
        if (ar.getParameter(SigmaTruncTypeParam.NAME).isAllowed(truncType)) {
            ar.getParameter(SigmaTruncTypeParam.NAME).setValue(truncType);
        } else {
            String msg =
                    "The chosen truncation type: "
                            + truncType
                            + " is not supported.\n"
                            + "The allowed values are the following:\n"
                            + ar.getParameter(SigmaTruncTypeParam.NAME)
                                    .getConstraint() + "\n"
                            + "Check your input file\n" + "Execution stopped.";
            logger.error(msg);
            throw new IllegalArgumentException(msg);
        }
        if (ar.getParameter(SigmaTruncLevelParam.NAME).isAllowed(truncLevel)) {
            ar.getParameter(SigmaTruncLevelParam.NAME).setValue(truncLevel);
        } else {
            String msg =
                    "The chosen truncation level: "
                            + truncLevel
                            + " is not supported.\n"
                            + "The allowed values are the following: \n"
                            + ar.getParameter(SigmaTruncLevelParam.NAME)
                                    .getConstraint() + "\n"
                            + "Check your input file\n" + "Execution stopped.";
            logger.error(msg);
            throw new IllegalArgumentException(msg);
        }
        if (ar.getParameter(StdDevTypeParam.NAME).isAllowed(stdType)) {
            ar.getParameter(StdDevTypeParam.NAME).setValue(stdType);
        } else {
            String msg =
                    "The chosen standard deviation type: "
                            + stdType
                            + " is not supported by "
                            + gmpeName
                            + "\n"
                            + "The allowed values are the following: \n"
                            + ar.getParameter(StdDevTypeParam.NAME)
                                    .getConstraint() + "\n"
                            + "Check your input file\n" + "Execution stopped.";
            logger.error(msg);
            new IllegalArgumentException(msg);
        }
    }

}
