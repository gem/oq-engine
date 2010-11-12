package org.gem;

import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Type;

import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;

import com.google.gson.JsonDeserializationContext;
import com.google.gson.JsonDeserializer;
import com.google.gson.JsonElement;

public class ScalarIntensityMeasureRelationshipApiDeserializer implements
        JsonDeserializer<ScalarIntensityMeasureRelationshipAPI> {

    ParameterChangeWarningEvent event = null;

    @Override
    public ScalarIntensityMeasureRelationshipAPI deserialize(JsonElement json,
            Type typeOfT, JsonDeserializationContext context) {
        ScalarIntensityMeasureRelationshipAPI ar = null;
        try {
            Class cl = Class.forName(json.getAsString());
            Constructor cstr =
                    cl.getConstructor(new Class[] { ParameterChangeWarningListener.class });
            ar =
                    (ScalarIntensityMeasureRelationshipAPI) cstr
                            .newInstance(ParameterChangeWarningListener(event));
        } catch (ClassNotFoundException e) {
            e.printStackTrace();
        } catch (SecurityException e) {
            e.printStackTrace();
        } catch (NoSuchMethodException e) {
            e.printStackTrace();
        } catch (IllegalArgumentException e) {
            e.printStackTrace();
        } catch (InstantiationException e) {
            e.printStackTrace();
        } catch (IllegalAccessException e) {
            e.printStackTrace();
        } catch (InvocationTargetException e) {
            e.printStackTrace();
        }
        return ar;
    }

    private static ParameterChangeWarningListener
            ParameterChangeWarningListener(ParameterChangeWarningEvent event) {
        return null;
    }

}
