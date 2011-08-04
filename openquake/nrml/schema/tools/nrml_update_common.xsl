<?xml version="1.0" encoding="utf-8"?>
<!-- 
    this XSLT style sheet contains common patterns for updates of
    NRML instance files from version 0.1 to version 0.2 
-->
      
<xsl:stylesheet version="1.0" 
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:xs="http://www.w3.org/2001/XMLSchema"
                xmlns:gml="http://www.opengis.net/gml"
                xmlns:gml_old="http://www.opengis.net/gml/profile/sfgml/1.0"
                xmlns:qml="http://quakeml.org/xmlns/quakeml/1.1"
                xmlns:nrml1="http://openquake.org/xmlns/nrml/0.1"
                xmlns:nrml="http://openquake.org/xmlns/nrml/0.2"
                xmlns="http://openquake.org/xmlns/nrml/0.2"
                exclude-result-prefixes="xsl xs nrml1 nrml qml gml_old">

    <xsl:output method="xml" indent="yes"/>

    <xsl:template name="fix_asset_category">
        <xsl:param name="assetCategory"/>
        <xsl:choose>
            <xsl:when test="$assetCategory = 'Population'">
                <xsl:text>population</xsl:text>
            </xsl:when>
            <xsl:when test="$assetCategory = 'Buildings'">
                <xsl:text>buildings</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$assetCategory"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template name="fix_loss_category">
        <xsl:param name="lossCategory"/>
        <xsl:choose>
            <xsl:when test="($lossCategory = 'People') or ($lossCategory = 'people')">
                <xsl:text>fatalities</xsl:text>
            </xsl:when>
            <xsl:when test="($lossCategory = 'Economical_loss') or ($lossCategory = 'Economical loss') or 
                ($lossCategory = 'economical_loss') or ($lossCategory = 'economical loss') or
                ($lossCategory = 'Economic_loss') or ($lossCategory = 'Economic loss') or
                ($lossCategory = 'economic loss')">
                <xsl:text>economic_loss</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$lossCategory"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template name="fix_gml_id">
        <xsl:param name="input_id"/>
        <xsl:param name="prefix"/>
        <xsl:choose>
            <xsl:when test="translate(substring($input_id, 1, 1), '0123456789', '') = ''">
                <!-- first char is numeric, apply prefix -->
                <xsl:value-of select="concat($prefix, $input_id)"/>
            </xsl:when>
            <xsl:otherwise>
                <!-- first char is non-numeric, take original value -->
                <xsl:value-of select="$input_id"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

</xsl:stylesheet>

