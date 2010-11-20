package org.gem;

import java.lang.reflect.Type;

import org.opensha.sha.util.TectonicRegionType;

import com.google.gson.JsonDeserializationContext;
import com.google.gson.JsonDeserializer;
import com.google.gson.JsonElement;
import com.google.gson.JsonParseException;

public class TectonicRegionTypeDeserializer implements
        JsonDeserializer<TectonicRegionType> {

    @Override
    public TectonicRegionType deserialize(JsonElement arg0, Type arg1,
            JsonDeserializationContext arg2) throws JsonParseException {
        return TectonicRegionType.getTypeForName(arg0.getAsString());
    }

}
