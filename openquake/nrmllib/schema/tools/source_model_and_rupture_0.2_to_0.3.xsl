<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:nrml_02="http://openquake.org/xmlns/nrml/0.2"
                xmlns:nrml="http://openquake.org/xmlns/nrml/0.3"
                xmlns:qml="http://quakeml.org/xmlns/quakeml/1.1"
                exclude-result-prefixes="nrml_02 nrml qml">

    <xsl:output method="xml" indent="yes"/>

    <!-- Update all nrml elements in the nrml 0.2 namespace
         to the nrml 0.3 namespace. -->
    <xsl:template match='*[namespace-uri() = "http://openquake.org/xmlns/nrml/0.2"]'>
        <xsl:element name="{name()}" namespace="http://openquake.org/xmlns/nrml/0.3">
            <xsl:copy-of select="@*"/>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>

    <!-- If an element is in any other namespace, copy it and don't change anything.
         This properly handles elements in the gml namespace. -->
    <xsl:template match="*">
        <xsl:element name="{name()}" namespace="{namespace-uri()}">
            <xsl:copy-of select="@*"/>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>

    <!-- Replaces a focal mechanism (containing strike, dip, and rake) with
         more primitive elements: <strike>, <dip>, and <rake>.

         This also helps remove our dependency on QuakeML. -->
    <xsl:template match="//nrml_02:focalMechanism">
        <strike xmlns="http://openquake.org/xmlns/nrml/0.3">
            <xsl:value-of select="./qml:nodalPlanes/qml:nodalPlane1/qml:strike/qml:value"/>
        </strike>

        <dip xmlns="http://openquake.org/xmlns/nrml/0.3">
            <xsl:value-of select="./qml:nodalPlanes/qml:nodalPlane1/qml:dip/qml:value"/>
        </dip>

        <rake xmlns="http://openquake.org/xmlns/nrml/0.3">
            <xsl:value-of select="./qml:nodalPlanes/qml:nodalPlane1/qml:rake/qml:value"/>
        </rake>
    </xsl:template>

    <!-- Copy comments. -->
    <xsl:template match="comment()">
        <xsl:copy/>
    </xsl:template>


</xsl:stylesheet>
