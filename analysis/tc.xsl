<?xml version="1.0" encoding="ISO-8859-1"?>
<!-- Name: tc.xsl ©2010 -->
<!-- Purpose: displaying CXML data in a tabular form -->
<!-- Usage: insert "<?xml-stylesheet type="text/xsl" href="tc.xsl"?>" after the first line of CXML -->
<!-- Written by Hong Wang  -->

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:template match="/">
  <html>
  <body>
  <h2>
  Cyclone Track: 
  <xsl:value-of select="cxml/header/generatingApplication/model/name"/> from 
  <xsl:value-of select="cxml/header/productionCenter"/>
  </h2>  
  <h5>
  (Stylesheet by <a
 href="mailto:ozweatherman@yahoo.com.au">Hong Wang</a> ©2010)
  </h5>

  <xsl:for-each select="cxml/data">
    <xsl:if test="@type='ensembleForecast'">
        <font color="#aa1511">
        <h3>Ensemble Member: <xsl:value-of select="@member"/></h3> 
        </font>       
    </xsl:if> 

    <xsl:for-each select="disturbance">
        <font color="red"> 
        Basin: <xsl:value-of select="basin"/>   
        </font> 
        <br/>
        <font color="blue"> 
        ID: <xsl:value-of select="@ID"/> - <xsl:value-of select="cycloneName"/>   
        </font> 
        <xsl:variable name="latsign" select="substring(@ID,15,1)"/>
        <xsl:variable name="lonsign" select="substring(@ID,21,1)"/>

    <table border="1">
      <tr bgcolor="#9acd32">
        <th>Hour</th>
        <th>Valid Time</th>
        <th>Latitude</th>
        <th>Longitude</th>
        <th>Min Pressure</th>
        <th>Max Wind</th>
      </tr>
      <xsl:for-each select="fix">
        <tr> 
          <td><xsl:value-of select="concat('+',@hour)"/></td>
          <td><xsl:value-of select="validTime"/></td>
          <td><xsl:value-of select='concat(format-number(latitude,"#.0"),$latsign)'/></td>
          <xsl:choose>
            <xsl:when test="$lonsign='W'">
              <td><xsl:value-of select='concat(format-number(360-longitude,"#.0"),$lonsign)'/></td>
            </xsl:when>
            <xsl:otherwise>
              <td><xsl:value-of select='concat(format-number(longitude,"#.0"),$lonsign)'/></td>
            </xsl:otherwise>
          </xsl:choose>
          <td><xsl:value-of select="concat(cycloneData/minimumPressure/pressure,cycloneData/minimumPressure/pressure/@units)"/></td>        
          <td><xsl:value-of select="concat(cycloneData/maximumWind/speed,cycloneData/maximumWind/speed/@units)"/></td>
        </tr>                                    
      </xsl:for-each>
    </table>
      <br/>
    </xsl:for-each>

  </xsl:for-each>
  </body>
  </html>
</xsl:template>          
</xsl:stylesheet>