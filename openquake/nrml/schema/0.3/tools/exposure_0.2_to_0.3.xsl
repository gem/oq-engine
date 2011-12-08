<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:nrml_02="http://openquake.org/xmlns/nrml/0.2"
                xmlns:nrml="http://openquake.org/xmlns/nrml/0.3"
                exclude-result-prefixes="nrml_02 nrml">

    <xsl:output method="xml" indent="yes"/>

    <!-- Update all nrml elements in the nrml 0.2 namespace
         to the nrml0.3 namespace. -->
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

    <!-- Copy assetValue elements, update the namespace, and don't include any attributes.
         This is used to drop the 'unit' attribute, which is obsolete. -->
    <xsl:template match="//nrml_02:assetValue">
        <xsl:element name="assetValue" namespace="http://openquake.org/xmlns/nrml/0.3">
            <xsl:copy-of select="*"/>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>

    <!-- Rename 'vulnerabilityFunctionReference' to 'taxonomy'. -->
    <xsl:template match="//nrml_02:vulnerabilityFunctionReference">
        <xsl:element name="taxonomy" namespace="http://openquake.org/xmlns/nrml/0.3">
            <xsl:copy-of select="@*"/>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>

    <!-- Delete all assetDescription elements. -->
    <xsl:template match="//nrml_02:assetDescription"/>

    <!-- Copy comments. -->
    <xsl:template match="comment()">
        <xsl:copy/>
    </xsl:template>

</xsl:stylesheet>
