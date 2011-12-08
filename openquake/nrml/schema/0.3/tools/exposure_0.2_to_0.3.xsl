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
    <xsl:template match='*'>
        <xsl:element name="{name()}" namespace="{namespace-uri()}">
            <xsl:copy-of select="@*"/>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>

    <xsl:template match="//nrml_02:assetValue">
        <assetValue xmlns="http://openquake.org/xmlns/nrml/0.3">
            <xsl:apply-templates select="node( )"/>
        </assetValue>
    </xsl:template>

    <xsl:template match="//nrml_02:vulnerabilityFunctionReference">
        <taxonomy xmlns="http://openquake.org/xmlns/nrml/0.3">
            <xsl:apply-templates select="@* | node( )"/>
        </taxonomy>
    </xsl:template>

    <xsl:template match="//nrml_02:assetDescription">
        <!-- Effectively replaces assetDescription with nothing. -->
    </xsl:template>

<!--
        <xsl:element name="{name()}" namespace="{namespace-uri()}">
            <xsl:copy-of select="@*"/>
            <xsl:apply-templates/>
        </xsl:element>
-->

<!--
    <xsl:template match="node( ) | @*">
        <xsl:copy>
            <xsl:apply-templates select="@* | node( )"/>
        </xsl:copy>
    </xsl:template>
-->
<!--
    <xsl:template match="//nrml_02:nrml">
        <nrml xmlns="http://openquake.org/xmlns/nrml/0.3">
            <xsl:apply-templates select="@* | node( )"/>
        </nrml>
    </xsl:template>

    <xsl:template match="//nrml_02:exposurePortfolio">
        <exposurePortfolio xmlns="http://openquake.org/xmlns/nrml/0.3">
            <xsl:apply-templates select="@* | node( )"/>
        </exposurePortfolio>
    </xsl:template>

    <xsl:template match="//nrml_02:config">
        <config xmlns="http://openquake.org/xmlns/nrml/0.3">
            <xsl:apply-templates select="@* | node( )"/>
        </config>
    </xsl:template>

    <xsl:template match="//nrml_02:exposureList">
        <exposureList xmlns="http://openquake.org/xmlns/nrml/0.3">
            <xsl:apply-templates select="@* | node( )"/>
        </exposureList>
    </xsl:template>

    <xsl:template match="//nrml_02:assetDefinition">
        <assetDefinition xmlns="http://openquake.org/xmlns/nrml/0.3">
            <xsl:apply-templates select="@* | node( )"/>
        </assetDefinition>
    </xsl:template>

    <xsl:template match="//nrml_02:assetDefinition">
        <assetDefinition xmlns="http://openquake.org/xmlns/nrml/0.3">
            <xsl:apply-templates select="@* | node( )"/>
        </assetDefinition>
    </xsl:template>

    <xsl:template match="//nrml_02:site">
        <site xmlns="http://openquake.org/xmlns/nrml/0.3">
            <xsl:apply-templates select="@* | node( )"/>
        </site>
    </xsl:template>

    <xsl:template match="//nrml_02:structureCategory">
        <structureCategory xmlns="http://openquake.org/xmlns/nrml/0.3">
            <xsl:apply-templates select="@* | node( )"/>
        </structureCategory>
    </xsl:template>
-->

</xsl:stylesheet>
