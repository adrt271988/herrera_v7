<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:fo="http://www.w3.org/1999/XSL/Format">
	<xsl:variable name="initial_bottom_pos">23</xsl:variable>
	<xsl:variable name="initial_left_pos">1</xsl:variable>
	<xsl:variable name="height_increment">3.7</xsl:variable>
	<xsl:variable name="width_increment">5.1</xsl:variable>
	<xsl:variable name="frame_height">6cm</xsl:variable>
	<xsl:variable name="frame_width">3.6cm</xsl:variable>
	<xsl:variable name="number_columns">4</xsl:variable>
	<xsl:variable name="max_frames">32</xsl:variable>

	<xsl:template match="/">
		<xsl:apply-templates select="lots"/>
	</xsl:template>

	<xsl:template match="lots">
		<document>
			<template leftMargin="2.0cm" rightMargin="2.0cm" topMargin="2.0cm" bottomMargin="2.0cm" title="Codigo" author="Herrera, C.A">
				<pageTemplate id="all">
					<pageGraphics/>
					<xsl:apply-templates select="lot-line" mode="frames"/>
				</pageTemplate>
			</template>

			<story>
				<xsl:apply-templates select="lot-line" mode="story"/>
			</story>
		</document>
	</xsl:template>

	<xsl:template match="lot-line" mode="frames">
		<xsl:if test="position() &lt; $max_frames + 1">
			<frame>
				<xsl:attribute name="width">
					<xsl:value-of select="$frame_width"/>
				</xsl:attribute>
				<xsl:attribute name="height">
					<xsl:value-of select="$frame_height"/>
				</xsl:attribute>
				<xsl:attribute name="x1">
					<xsl:value-of select="$initial_left_pos + ((position()-1) mod $number_columns) * $width_increment"/>
					<xsl:text>cm</xsl:text>
				</xsl:attribute>
				<xsl:attribute name="y1">
					<xsl:value-of select="$initial_bottom_pos - floor((position()-1) div $number_columns) * $height_increment"/>
					<xsl:text>cm</xsl:text>
				</xsl:attribute>
			</frame>
		</xsl:if>
	</xsl:template>

    <xsl:param name="pmaxChars" as="xs:integer" select="80"/>
    <xsl:template match="lot-line" mode="story">
                <para fontName="Helvetica-Bold" alignment="CENTER"><xsl:value-of select="company"/></para>
                <barCode code="Extended93" quiet="0" xdim="20cm" barHeight="30" barWidth="1" bearers="0" height="1.1cm" ratio="3.0"><xsl:value-of select="code" /></barCode>
                <para alignment="CENTER"><xsl:value-of select="code"/></para>
    <nextFrame/>
    </xsl:template>
</xsl:stylesheet>


<!--
<blockTable colWidths="415.0" style="CodBarra"> 
    <tr> 
      <td> 
        <barCode code="i2of5" quiet="0" xdim="20cm" barHeight="30" barWidth="1" bearers="0" height="2cm" ratio="3.0">[[ o.codigo_b ]]</barCode> 
      </td> 
    </tr> 
    <tr> 
        <td><para style="P8">[[ (o.resultado == 'A') and o.codigo_b or removeParentNode('blockTable') ]]</para></td> 
    </tr> 
</blockTable> 

<blockTable colWidths="155.0,260.0" style="CAE"> 
    <tr> 
        <td><para style="P8">[[ (o.resultado == 'A') and 'CAE: '+ o.cae or removeParentNode('blockTable') ]]</para></td> 
        <td><para style="P8">Fecha de Vencimiento: [[ formatLang(o.fecha_vto_cae,date=True) ]]</para></td> 
    </tr> 
</blockTable> 
-->

<!--
Algunos de los parámetros del código de barras: 
- quiet = "0" esto quita espacio muertos a los laterales externos al codigo de barras 
- xdim = especifica el ancho, pero este valor de 20 está supeditado además al ratio 
- barheight = en pixeles la altura del codigo (tambien supeditado al ratio) 
- height = 2cm, espacio total, siendo el barheight mas un espacio muerto arriba del codigo 
- barwidth = ancho en pixeles de cada elemento del codigo 
- bearers = esta puesto a cero. si no lo ponen, aparecen barras negras horizontales (default es un multiplo del barwidth), arriba y abajo del 
  código, como encerrandolo. Dicen que esto mejora la lectura. Se puede variar y es por ejemplo, 1, 2 o 3 el ancho de esas barras 
  horizontales.. 
- ratio: es un valor característico de i2of5 y puede variar entre 2.2 y 3 en este tipo de codigo de barras. 
-->
