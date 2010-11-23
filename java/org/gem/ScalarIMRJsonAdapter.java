package org.gem;

import java.lang.reflect.Type;

import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;

import com.google.gson.JsonElement;
import com.google.gson.JsonPrimitive;
import com.google.gson.JsonSerializationContext;
import com.google.gson.JsonSerializer;

public class ScalarIMRJsonAdapter implements
        JsonSerializer<ScalarIntensityMeasureRelationshipAPI> {

    @Override
    public JsonElement serialize(ScalarIntensityMeasureRelationshipAPI src,
            Type typeOfSrc, JsonSerializationContext context) {
        return new JsonPrimitive(src.getClass().getCanonicalName());
    }

}
