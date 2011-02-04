<?xml version="1.0" encoding="utf-8"?>
<!-- 
    this XSLT style sheet updates NRML instance files of type 
    'exposurePortfolio' from version 0.1 to version 0.2 
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


    <!--<xsl:include href="nrml_update_common.xsl"/>-->

    <xsl:output method="xml" indent="yes"/>

    <!-- start main template -->

    <xsl:template match="nrml1:ExposurePortfolio">

        <nrml>
            <xsl:attribute name="gml:id">nrml</xsl:attribute>
            <exposurePortfolio>
                <xsl:attribute name="gml:id">ep</xsl:attribute>
                <xsl:apply-templates select="nrml1:ExposureList"/>
            </exposurePortfolio>
        </nrml>

    </xsl:template>

    <!-- end main template -->

    <xsl:template match="nrml1:ExposureList">

        <!-- fix asset and loss category in order to match new-style enum values -->
        <xsl:variable name="assetCategoryOrig" select="/nrml1:ExposurePortfolio/nrml1:Config/nrml1:ExposureParameters/@AssetType"/>
        <xsl:variable name="assetCategory">
            <xsl:choose>
                <xsl:when test="$assetCategoryOrig = 'Population'">
                    <xsl:text>population</xsl:text>
                </xsl:when>
                <xsl:when test="$assetCategoryOrig = 'Buildings'">
                    <xsl:text>buildings</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$assetCategoryOrig"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:variable name="lossCategoryOrig" select="/nrml1:ExposurePortfolio/nrml1:Config/nrml1:ExposureParameters/@LossType"/>
        <xsl:variable name="lossCategory">
            <xsl:choose>
                <xsl:when test="($lossCategoryOrig = 'People') or ($lossCategoryOrig = 'people')">
                    <xsl:text>fatalities</xsl:text>
                </xsl:when>
                <xsl:when test="($lossCategoryOrig = 'Economical_loss') or ($lossCategoryOrig = 'Economical loss') or 
                    ($lossCategoryOrig = 'economical_loss') or ($lossCategoryOrig = 'economical loss') or
                    ($lossCategoryOrig = 'Economic_loss') or ($lossCategoryOrig = 'Economic loss') or
                    ($lossCategoryOrig = 'economic loss')">
                    <xsl:text>economic_loss</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$lossCategoryOrig"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <!-- fix gml:id of exposureList, if necessary -->
        <xsl:variable name="portfolioID">
            <xsl:call-template name="fix_gml_id">
                <xsl:with-param name="input_id" 
                    select="/nrml1:ExposurePortfolio/nrml1:Config/nrml1:ExposureParameters/@PortfolioID"/>
                <xsl:with-param name="prefix" select="'p'"/>
            </xsl:call-template>
        </xsl:variable>

        <exposureList>

            <xsl:attribute name="gml:id">
                <xsl:value-of select="$portfolioID"/>
            </xsl:attribute>
            <xsl:attribute name="assetCategory">
                <xsl:value-of select="$assetCategory"/>
            </xsl:attribute>
            <xsl:attribute name="lossCategory">
                <xsl:value-of select="$lossCategory"/>
            </xsl:attribute>
            
            <!-- description -->
            <xsl:apply-templates select="/nrml1:ExposurePortfolio/nrml1:Config/nrml1:ExposureParameters/@PortfolioDescription"/>
            <xsl:apply-templates select="nrml1:AssetInstance"/>
        </exposureList>
    </xsl:template>

    <xsl:template match="nrml1:AssetInstance">

        <!-- fix gml:id of assetDefinition, if necessary -->
        <xsl:variable name="assetID">
            <xsl:call-template name="fix_gml_id">
                <xsl:with-param name="input_id" select="./nrml1:AssetID"/>
                <xsl:with-param name="prefix" select="'a'"/>
            </xsl:call-template>
        </xsl:variable>

        <assetDefinition>
            <xsl:attribute name="gml:id">
                <xsl:value-of select="$assetID"/>
            </xsl:attribute>

            <!-- site -->
            <xsl:apply-templates select="./gml_old:pos"/>

            <assetDescription>
                <xsl:value-of select="./@AssetDescription"/>
            </assetDescription>
            <vulnerabilityFunctionReference>
                <xsl:value-of select="./@VulnerabilityFunction"/>
            </vulnerabilityFunctionReference>
            <structureCategory>
                <xsl:value-of select="./nrml1:StructureType"/>
            </structureCategory>
            <assetValue>
                <xsl:value-of select="./nrml1:AssetValue"/>
            </assetValue>
        </assetDefinition>
    </xsl:template>

    <xsl:template match="/nrml1:ExposurePortfolio/nrml1:Config/nrml1:ExposureParameters/@PortfolioDescription">
        <gml:description>
            <xsl:value-of select="."/>
        </gml:description>
    </xsl:template>

    <xsl:template match="gml_old:pos">
        <xsl:variable name="lat" select="substring-before(normalize-space(.), ' ')"/>
        <xsl:variable name="lon" select="substring(normalize-space(.), string-length($lat)+2)"/>
        <site>
            <gml:Point>
                <xsl:attribute name="srsName">epsg:4326</xsl:attribute>
                <gml:pos>
                    <xsl:value-of select="concat($lon, ' ', $lat)"/>
                </gml:pos>
            </gml:Point>
        </site>
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

