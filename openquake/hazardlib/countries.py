import re
from openquake.baselib import general

# these are in one-to-one correspondence with the file mosaic.gpkg
MODELS = sorted('''
ALS ARB AUS CND CCA CEA CHN EUR GLD HAW IDN IND JPN KOR MEX MIE NAF NEA NWA
NZL OAT OIN OPA PAC PHL PNG SAM SEA SSA TEM USA WAF ZAF PAN PAR'''.split())

ALIASES = dict(TWN='TEM')  # manage change of name

REGIONS = """\
Africa
Caribbean_Central_America
Central_Asia
East_Asia
Europe
Middle_East
North_America
North_Asia
Oceania
South_America
South_Asia
Southeast_Asia
""".split()

MODEL_REGION = """\
NAF,Africa
OAT,Africa
SSA,Africa
WAF,Africa
ZAF,Africa
CCA,Caribbean_Central_America
CEA,Central_Asia
CHN,East_Asia
JPA,East_Asia
KOR,East_Asia
TEM,East_Asia
EUR,Europe
ARB,Middle_East
MIE,Middle_East
ALS,North_America
CND,North_America
HAW,North_America
MEX,North_America
USA,North_America
NEA,North_Asia
NWA,North_Asia
AUS,Oceania
NZL,Oceania
OPA,Oceania
PAC,Oceania
PNG,Oceania
SAM,South_America
IND,South_Asia
MIE,South_Asia
OIN,South_Asia
IDN,Southeast_Asia
PHL,Southeast_Asia
SEA,Southeast_Asia
"""

# nearly lexicographic order, but with longest names first, to avoid fake
# matches in the regular expression below; Guinea_Bissau must go before
# Guinea, Dominican_Republic before Dominica and Nigeria before Niger
COUNTRY_CODE = """\
Afghanistan,AFG
Albania,ALB
Algeria,DZA
American_Samoa,ASM
Andorra,AND
Angola,AGO
Anguilla,AIA
Antigua_and_Barbuda,ATG
Argentina,ARG
Armenia,ARM
Aruba,ABW
Australia,AUS
Austria,AUT
Azerbaijan,AZE
Bahamas,BHS
Bahrain,BHR
Bangladesh,BGD
Barbados,BRB
Belarus,BLR
Belgium,BEL
Belize,BLZ
Benin,BEN
Bermuda,BMU
Bhutan,BTN
Bolivia,BOL
Bonaire_Sint_Eustatius_and_Saba,BES
Bosnia_and_Herzegovina,BIH
Botswana,BWA
Brazil,BRA
British_Virgin_Islands,VGB
Brunei,BRN
Bulgaria,BGR
Burkina_Faso,BFA
Burundi,BDI
Cambodia,KHM
Cameroon,CMR
Canada,CAN
Cabo_Verde,CPV
Cayman_Islands,CYM
Central_African_Republic,CAF
Chad,TCD
Chile,CHL
China,CHN
Colombia,COL
Comoros,COM
Congo,COG
Cook_Islands,COK
Costa_Rica,CRI
Ivory_Coast,CIV
Croatia,HRV
Cuba,CUB
Curacao,CUW
Cyprus,CYP
Czechia,CZE
Democratic_Republic_of_the_Congo,COD
Denmark,DNK
Djibouti,DJI
Dominican_Republic,DOM
Dominica,DMA
Ecuador,ECU
Egypt,EGY
El_Salvador,SLV
Equatorial_Guinea,GNQ
Eritrea,ERI
Estonia,EST
Eswatini,SWZ
Ethiopia,ETH
Falkland_Islands_(Malvinas),FLK
Faroe_Islands,FRO
Fiji,FJI
Finland,FIN
France,FRA
French_Guiana,GUF
French_Polynesia,PYF
Gabon,GAB
Gambia,GMB
Georgia,GEO
Germany,DEU
Ghana,GHA
Gibraltar,GIB
Greece,GRC
Greenland,GRL
Grenada,GRD
Guadeloupe,GLP
Guam,GUM
Guatemala,GTM
Guinea_Bissau,GNB
Guinea,GIN
Guyana,GUY
Haiti,HTI
Holy_See,VAT
Honduras,HND
Hong_Kong,HKG
Hungary,HUN
Iceland,ISL
India,IND
Indonesia,IDN
Iran,IRN
Iraq,IRQ
Ireland,IRL
Isle_of_Man,IMN
Israel,ISR
Italy,ITA
Jamaica,JAM
Japan,JPN
Jordan,JOR
Kazakhstan,KAZ
Kenya,KEN
Kiribati,KIR
Kosovo,XKX
Kuwait,KWT
Kyrgyzstan,KGZ
Laos,LAO
Latvia,LVA
Lebanon,LBN
Lesotho,LSO
Liberia,LBR
Libya,LBY
Liechtenstein,LIE
Lithuania,LTU
Luxembourg,LUX
Macao,MAC
Macedonia,MKD
Madagascar,MDG
Malawi,MWI
Malaysia,MYS
Maldives,MDV
Mali,MLI
Malta,MLT
Marshall_Islands,MHL
Martinique,MTQ
Mauritania,MRT
Mauritius,MUS
Mayotte,MYT
Mexico,MEX
Micronesia,FSM
Moldova,MDA
Monaco,MCO
Mongolia,MNG
Montenegro,MNE
Montserrat,MSR
Morocco,MAR
Mozambique,MOZ
Myanmar,MMR
Namibia,NAM
Nauru,NRU
Nepal,NPL
Netherlands,NLD
New_Caledonia,NCL
New_Zealand,NZL
Nicaragua,NIC
Nigeria,NGA
Niger,NER
Niue,NIU
North_Korea,PRK
North_Macedonia,MKD
Northern_Mariana_Islands,MNP
Norway,NOR
Oman,OMN
Pakistan,PAK
Palau,PLW
Palestine,PSE
Panama,PAN
Papua_New_Guinea,PNG
Paraguay,PRY
Peru,PER
Philippines,PHL
Poland,POL
Portugal,PRT
Puerto_Rico,PRI
Qatar,QAT
Reunion,REU
Romania,ROU
Russia,RUS
Rwanda,RWA
Saint_Helena,SHN
Saint_Kitts_and_Nevis,KNA
Saint_Lucia,LCA
Saint_Pierre_and_Miquelon,SPM
Saint_Vincent_and_the_Grenadines,VCT
Samoa,WSM
San_Marino,SMR
Sao_Tome_and_Principe,STP
Saudi_Arabia,SAU
Senegal,SEN
Serbia,SRB
Seychelles,SYC
Sierra_Leone,SLE
Singapore,SGP
Sint_Maarten,SXM
Slovakia,SVK
Slovenia,SVN
Solomon_Islands,SLB
Somalia,SOM
South_Africa,ZAF
South_Korea,KOR
South_Sudan,SSD
Spain,ESP
Sri_Lanka,LKA
Sudan,SDN
Suriname,SUR
Sweden,SWE
Switzerland,CHE
Syria,SYR
Taiwan,TEM
Tajikistan,TJK
Tanzania,TZA
Thailand,THA
Timor_Leste,TLS
Togo,TGO
Tokelau,TKL
Tonga,TON
Trinidad_and_Tobago,TTO
Tunisia,TUN
Turkiye,TUR
Turkmenistan,TKM
Turks_and_Caicos_Islands,TCA
Tuvalu,TUV
Uganda,UGA
Ukraine,UKR
United_Arab_Emirates,ARE
United_Kingdom,GBR
United_States,USA
US_Virgin_Islands,VIR
Uruguay,URY
Uzbekistan,UZB
Vanuatu,VUT
Venezuela,VEN
Vietnam,VNM
Wallis_and_Futuna_Islands,WLF
Western_Sahara,ESH
Yemen,YEM
Zambia,ZMB
Zimbabwe,ZWE
"""

models_by_region = general.AccumDict(accum=[])
for line in MODEL_REGION.splitlines():
    model, region = line.split(',')
    models_by_region[region].append(model)

country2code = dict(line.split(',') for line in COUNTRY_CODE.splitlines())
code2country = {v: k for k, v in country2code.items()}

COUNTRIES = list(country2code)
REGEX = '|'.join('(%s)' % country.replace('(', r'\(').replace(')', r'\)')
                 for country in country2code)


def get_country_code(longname):
    """
    :returns: the code of the country contained in `longname`, or a ValueError

    >>> for country, code in country2code.items():
    ...     assert get_country_code('Exp_' + country) == code, (country, code)
    """
    mo = re.search(REGEX, longname, re.I)
    if mo is None:
        raise ValueError('Could not find a valid country in %s' % longname)
    return country2code[COUNTRIES[mo.lastindex - 1]]
