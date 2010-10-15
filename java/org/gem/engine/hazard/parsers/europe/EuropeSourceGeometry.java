package org.gem.engine.hazard.parsers.europe;

import org.opensha.commons.geo.LocationList;

public class EuropeSourceGeometry {

    LocationList vertexes;
    String id;

    public EuropeSourceGeometry() {
    }

    public EuropeSourceGeometry(LocationList vertexes, String id) {
        this.vertexes = vertexes;
        this.id = id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public void setVertexes(LocationList vertexes) {
        this.vertexes = vertexes;
    }

    public LocationList getVertexes() {
        return this.vertexes;
    }

    public String getId() {
        return this.id;
    }

}
