# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import StringIO
import tempfile
import shutil
import numpy
from nose.plugins.attrib import attr
from numpy.testing import assert_almost_equal

from openquake.engine import export
from openquake.engine.db import models
from qa_tests import _utils as qa_utils


class ScenarioHazardCase1TestCase(qa_utils.BaseQATestCase):
    EXPECTED_XML = '''<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <gmfSet>
    <gmf IMT="PGA">
      <node gmv="0.0754214232865" lon="0.0" lat="0.2"/>
      <node gmv="0.174205566494" lon="0.0" lat="0.1"/>
      <node gmv="0.571052978176" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.113794677187" lon="0.0" lat="0.2"/>
      <node gmv="0.307433263306" lon="0.0" lat="0.1"/>
      <node gmv="0.31901451305" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.136747257501" lon="0.0" lat="0.2"/>
      <node gmv="0.139236102857" lon="0.0" lat="0.1"/>
      <node gmv="0.50749803082" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.0793634497327" lon="0.0" lat="0.2"/>
      <node gmv="0.224789924488" lon="0.0" lat="0.1"/>
      <node gmv="0.341463070589" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.13142854714" lon="0.0" lat="0.2"/>
      <node gmv="0.297932212796" lon="0.0" lat="0.1"/>
      <node gmv="0.689401720228" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.17900992414" lon="0.0" lat="0.2"/>
      <node gmv="0.248138371012" lon="0.0" lat="0.1"/>
      <node gmv="0.402892807305" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.159154498696" lon="0.0" lat="0.1"/>
      <node gmv="0.172363626591" lon="0.0" lat="0.2"/>
      <node gmv="0.34574713546" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.078876732828" lon="0.0" lat="0.2"/>
      <node gmv="0.256750201819" lon="0.0" lat="0.1"/>
      <node gmv="0.385456864048" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.0984913845316" lon="0.0" lat="0.2"/>
      <node gmv="0.216724670292" lon="0.0" lat="0.1"/>
      <node gmv="0.436496521162" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.107722517114" lon="0.0" lat="0.2"/>
      <node gmv="0.229041584857" lon="0.0" lat="0.1"/>
      <node gmv="0.60431799809" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.134700395447" lon="0.0" lat="0.2"/>
      <node gmv="0.187666725846" lon="0.0" lat="0.1"/>
      <node gmv="0.545404092642" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.223037434618" lon="0.0" lat="0.2"/>
      <node gmv="0.358438673529" lon="0.0" lat="0.1"/>
      <node gmv="0.390048950754" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.183069364059" lon="0.0" lat="0.2"/>
      <node gmv="0.320075456515" lon="0.0" lat="0.1"/>
      <node gmv="0.534099158209" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.172509182174" lon="0.0" lat="0.2"/>
      <node gmv="0.301915188679" lon="0.0" lat="0.1"/>
      <node gmv="0.584323147097" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.211944183198" lon="0.0" lat="0.2"/>
      <node gmv="0.226948120526" lon="0.0" lat="0.1"/>
      <node gmv="0.411070205042" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.125417934918" lon="0.0" lat="0.2"/>
      <node gmv="0.160650455098" lon="0.0" lat="0.1"/>
      <node gmv="0.58163909402" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.153548990412" lon="0.0" lat="0.2"/>
      <node gmv="0.199492088682" lon="0.0" lat="0.1"/>
      <node gmv="0.36138575839" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.107247314519" lon="0.0" lat="0.2"/>
      <node gmv="0.225821271602" lon="0.0" lat="0.1"/>
      <node gmv="0.454306873644" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.128992616668" lon="0.0" lat="0.1"/>
      <node gmv="0.183712415554" lon="0.0" lat="0.2"/>
      <node gmv="0.513015244614" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.113545300108" lon="0.0" lat="0.2"/>
      <node gmv="0.264266885356" lon="0.0" lat="0.1"/>
      <node gmv="0.751304210776" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.107574858309" lon="0.0" lat="0.2"/>
      <node gmv="0.194027425043" lon="0.0" lat="0.1"/>
      <node gmv="0.546611479685" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.199801488474" lon="0.0" lat="0.2"/>
      <node gmv="0.320225183373" lon="0.0" lat="0.1"/>
      <node gmv="0.909364004079" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.113552692898" lon="0.0" lat="0.2"/>
      <node gmv="0.280824171473" lon="0.0" lat="0.1"/>
      <node gmv="0.328101891734" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.0896893964435" lon="0.0" lat="0.2"/>
      <node gmv="0.211382033667" lon="0.0" lat="0.1"/>
      <node gmv="0.729287180439" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.117007115328" lon="0.0" lat="0.2"/>
      <node gmv="0.177747153663" lon="0.0" lat="0.1"/>
      <node gmv="0.455041436436" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.183669988835" lon="0.0" lat="0.2"/>
      <node gmv="0.225310032097" lon="0.0" lat="0.1"/>
      <node gmv="0.558626410484" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.10230880631" lon="0.0" lat="0.2"/>
      <node gmv="0.199583194306" lon="0.0" lat="0.1"/>
      <node gmv="0.34741553262" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.177047034567" lon="0.0" lat="0.1"/>
      <node gmv="0.188483248601" lon="0.0" lat="0.2"/>
      <node gmv="0.664702971826" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.229585538356" lon="0.0" lat="0.2"/>
      <node gmv="0.331280512828" lon="0.0" lat="0.1"/>
      <node gmv="0.523553783941" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.168401433938" lon="0.0" lat="0.1"/>
      <node gmv="0.190492186177" lon="0.0" lat="0.2"/>
      <node gmv="0.792776927792" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.126095942905" lon="0.0" lat="0.2"/>
      <node gmv="0.329429984271" lon="0.0" lat="0.1"/>
      <node gmv="0.340846417688" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.211670978613" lon="0.0" lat="0.2"/>
      <node gmv="0.373249500419" lon="0.0" lat="0.1"/>
      <node gmv="0.608748550301" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.153667937849" lon="0.0" lat="0.2"/>
      <node gmv="0.178133099246" lon="0.0" lat="0.1"/>
      <node gmv="0.42340545289" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.258487477666" lon="0.0" lat="0.1"/>
      <node gmv="0.275779385087" lon="0.0" lat="0.2"/>
      <node gmv="0.39936445174" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.149597791698" lon="0.0" lat="0.2"/>
      <node gmv="0.321899020278" lon="0.0" lat="0.1"/>
      <node gmv="0.640238669583" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.142906593737" lon="0.0" lat="0.2"/>
      <node gmv="0.403776624931" lon="0.0" lat="0.1"/>
      <node gmv="0.910182491748" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.163977518867" lon="0.0" lat="0.2"/>
      <node gmv="0.22856630889" lon="0.0" lat="0.1"/>
      <node gmv="0.705336267029" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.116994344274" lon="0.0" lat="0.2"/>
      <node gmv="0.2102506549" lon="0.0" lat="0.1"/>
      <node gmv="0.789241762826" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.0910582267813" lon="0.0" lat="0.2"/>
      <node gmv="0.162404448522" lon="0.0" lat="0.1"/>
      <node gmv="0.353969825025" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.166973060899" lon="0.0" lat="0.2"/>
      <node gmv="0.218084288956" lon="0.0" lat="0.1"/>
      <node gmv="0.420314640959" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.0912606469481" lon="0.0" lat="0.2"/>
      <node gmv="0.117269732653" lon="0.0" lat="0.1"/>
      <node gmv="0.536880110493" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.216506169205" lon="0.0" lat="0.2"/>
      <node gmv="0.269087665793" lon="0.0" lat="0.1"/>
      <node gmv="0.431280563581" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.178018478947" lon="0.0" lat="0.2"/>
      <node gmv="0.35657319476" lon="0.0" lat="0.1"/>
      <node gmv="0.40079865569" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.185497341792" lon="0.0" lat="0.2"/>
      <node gmv="0.189652078739" lon="0.0" lat="0.1"/>
      <node gmv="0.318918592954" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.198158326039" lon="0.0" lat="0.1"/>
      <node gmv="0.217080064505" lon="0.0" lat="0.2"/>
      <node gmv="0.574203179624" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.181069584387" lon="0.0" lat="0.2"/>
      <node gmv="0.276790770382" lon="0.0" lat="0.1"/>
      <node gmv="0.420990766578" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.243171010578" lon="0.0" lat="0.2"/>
      <node gmv="0.307655507634" lon="0.0" lat="0.1"/>
      <node gmv="0.427946622129" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.147559766096" lon="0.0" lat="0.2"/>
      <node gmv="0.312365227457" lon="0.0" lat="0.1"/>
      <node gmv="0.617352365707" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.19668784189" lon="0.0" lat="0.2"/>
      <node gmv="0.401516758003" lon="0.0" lat="0.1"/>
      <node gmv="0.648547600384" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.165133087218" lon="0.0" lat="0.2"/>
      <node gmv="0.312187678928" lon="0.0" lat="0.0"/>
      <node gmv="0.333075264964" lon="0.0" lat="0.1"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.163284731392" lon="0.0" lat="0.2"/>
      <node gmv="0.218338287434" lon="0.0" lat="0.1"/>
      <node gmv="0.489415477822" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.147285586685" lon="0.0" lat="0.1"/>
      <node gmv="0.202314153692" lon="0.0" lat="0.2"/>
      <node gmv="0.408640084499" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.143574111044" lon="0.0" lat="0.1"/>
      <node gmv="0.175976500682" lon="0.0" lat="0.2"/>
      <node gmv="0.457762661454" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.077944611109" lon="0.0" lat="0.2"/>
      <node gmv="0.185005307119" lon="0.0" lat="0.1"/>
      <node gmv="0.549674782597" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.238067134882" lon="0.0" lat="0.2"/>
      <node gmv="0.34779588487" lon="0.0" lat="0.1"/>
      <node gmv="0.615519798328" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.210267165914" lon="0.0" lat="0.2"/>
      <node gmv="0.210327983845" lon="0.0" lat="0.1"/>
      <node gmv="0.31696965769" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.105585804693" lon="0.0" lat="0.2"/>
      <node gmv="0.289257595313" lon="0.0" lat="0.1"/>
      <node gmv="0.473101807868" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.169857547513" lon="0.0" lat="0.1"/>
      <node gmv="0.212089882965" lon="0.0" lat="0.2"/>
      <node gmv="0.782597308647" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.0939485814401" lon="0.0" lat="0.2"/>
      <node gmv="0.122576245568" lon="0.0" lat="0.1"/>
      <node gmv="0.480213590232" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.156630116422" lon="0.0" lat="0.2"/>
      <node gmv="0.220764100998" lon="0.0" lat="0.1"/>
      <node gmv="0.288078642967" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.18427037612" lon="0.0" lat="0.2"/>
      <node gmv="0.328656830632" lon="0.0" lat="0.1"/>
      <node gmv="0.376375820739" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.158598306326" lon="0.0" lat="0.2"/>
      <node gmv="0.270935342372" lon="0.0" lat="0.1"/>
      <node gmv="0.943565415254" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.144633541691" lon="0.0" lat="0.2"/>
      <node gmv="0.181107662907" lon="0.0" lat="0.1"/>
      <node gmv="0.278698726761" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.104033014799" lon="0.0" lat="0.2"/>
      <node gmv="0.149012794807" lon="0.0" lat="0.1"/>
      <node gmv="0.622462699694" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.178898908243" lon="0.0" lat="0.2"/>
      <node gmv="0.259309232345" lon="0.0" lat="0.1"/>
      <node gmv="0.67634747561" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.0808667234369" lon="0.0" lat="0.2"/>
      <node gmv="0.115777617591" lon="0.0" lat="0.1"/>
      <node gmv="0.322009917804" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.104679774138" lon="0.0" lat="0.2"/>
      <node gmv="0.344085522538" lon="0.0" lat="0.1"/>
      <node gmv="0.629865280751" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.154098304963" lon="0.0" lat="0.2"/>
      <node gmv="0.27376803421" lon="0.0" lat="0.1"/>
      <node gmv="0.657242649098" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.129038971176" lon="0.0" lat="0.2"/>
      <node gmv="0.287034464714" lon="0.0" lat="0.1"/>
      <node gmv="0.487356406472" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.12659953685" lon="0.0" lat="0.2"/>
      <node gmv="0.271477902407" lon="0.0" lat="0.1"/>
      <node gmv="0.48977711306" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.231486008359" lon="0.0" lat="0.1"/>
      <node gmv="0.251403582918" lon="0.0" lat="0.2"/>
      <node gmv="0.631583862372" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.090113210691" lon="0.0" lat="0.2"/>
      <node gmv="0.248251553688" lon="0.0" lat="0.1"/>
      <node gmv="0.40877866669" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.1200947147" lon="0.0" lat="0.2"/>
      <node gmv="0.195545341733" lon="0.0" lat="0.1"/>
      <node gmv="0.655941688042" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.161332259537" lon="0.0" lat="0.1"/>
      <node gmv="0.195699861457" lon="0.0" lat="0.2"/>
      <node gmv="0.474152447123" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.120129696618" lon="0.0" lat="0.2"/>
      <node gmv="0.220728537367" lon="0.0" lat="0.1"/>
      <node gmv="0.517339991087" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.195474839598" lon="0.0" lat="0.2"/>
      <node gmv="0.30459048674" lon="0.0" lat="0.1"/>
      <node gmv="0.494221605674" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.111504209517" lon="0.0" lat="0.2"/>
      <node gmv="0.214428987431" lon="0.0" lat="0.1"/>
      <node gmv="0.412559150392" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.0933706204411" lon="0.0" lat="0.2"/>
      <node gmv="0.175563143271" lon="0.0" lat="0.1"/>
      <node gmv="0.372968497772" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.134205046365" lon="0.0" lat="0.2"/>
      <node gmv="0.18596443214" lon="0.0" lat="0.1"/>
      <node gmv="0.594418244041" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.175619468555" lon="0.0" lat="0.2"/>
      <node gmv="0.24039546615" lon="0.0" lat="0.1"/>
      <node gmv="0.362183687433" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.215052233106" lon="0.0" lat="0.2"/>
      <node gmv="0.306784733906" lon="0.0" lat="0.1"/>
      <node gmv="0.368775820563" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.222573033224" lon="0.0" lat="0.2"/>
      <node gmv="0.350253185667" lon="0.0" lat="0.1"/>
      <node gmv="0.627234932328" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.144862598883" lon="0.0" lat="0.2"/>
      <node gmv="0.254082276882" lon="0.0" lat="0.1"/>
      <node gmv="0.874040807667" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.120927688255" lon="0.0" lat="0.2"/>
      <node gmv="0.145977222337" lon="0.0" lat="0.1"/>
      <node gmv="0.658142420734" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.158739296837" lon="0.0" lat="0.2"/>
      <node gmv="0.217198552928" lon="0.0" lat="0.1"/>
      <node gmv="0.47647215814" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.146030901205" lon="0.0" lat="0.2"/>
      <node gmv="0.184016598392" lon="0.0" lat="0.1"/>
      <node gmv="0.463412553325" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.162423857338" lon="0.0" lat="0.2"/>
      <node gmv="0.248688721564" lon="0.0" lat="0.1"/>
      <node gmv="0.588799740325" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.131644897816" lon="0.0" lat="0.2"/>
      <node gmv="0.146761917776" lon="0.0" lat="0.1"/>
      <node gmv="0.560552218045" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.155005165228" lon="0.0" lat="0.2"/>
      <node gmv="0.274947360839" lon="0.0" lat="0.1"/>
      <node gmv="0.557724720217" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.0970590191549" lon="0.0" lat="0.2"/>
      <node gmv="0.298362641451" lon="0.0" lat="0.1"/>
      <node gmv="0.336263468167" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.0916710373484" lon="0.0" lat="0.2"/>
      <node gmv="0.184530870838" lon="0.0" lat="0.1"/>
      <node gmv="0.480619316931" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.120589829545" lon="0.0" lat="0.2"/>
      <node gmv="0.143854198621" lon="0.0" lat="0.1"/>
      <node gmv="0.247707391799" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.0805498344305" lon="0.0" lat="0.2"/>
      <node gmv="0.135399141837" lon="0.0" lat="0.1"/>
      <node gmv="0.472343816643" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.168343170835" lon="0.0" lat="0.2"/>
      <node gmv="0.217465901127" lon="0.0" lat="0.1"/>
      <node gmv="0.69140476041" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.17041987712" lon="0.0" lat="0.2"/>
      <node gmv="0.372407771403" lon="0.0" lat="0.1"/>
      <node gmv="0.533657428476" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.0868211073182" lon="0.0" lat="0.2"/>
      <node gmv="0.210929318199" lon="0.0" lat="0.1"/>
      <node gmv="0.266205234746" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.127269184128" lon="0.0" lat="0.2"/>
      <node gmv="0.187655094535" lon="0.0" lat="0.1"/>
      <node gmv="0.804399320667" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.094510614726" lon="0.0" lat="0.2"/>
      <node gmv="0.187784170424" lon="0.0" lat="0.1"/>
      <node gmv="0.779152839885" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.140933416377" lon="0.0" lat="0.2"/>
      <node gmv="0.175272384138" lon="0.0" lat="0.1"/>
      <node gmv="0.231692028424" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.0781761127866" lon="0.0" lat="0.2"/>
      <node gmv="0.159770977097" lon="0.0" lat="0.1"/>
      <node gmv="0.26846302019" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.168111025114" lon="0.0" lat="0.2"/>
      <node gmv="0.25003733281" lon="0.0" lat="0.1"/>
      <node gmv="0.88284032146" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node gmv="0.110061790281" lon="0.0" lat="0.2"/>
      <node gmv="0.193161622895" lon="0.0" lat="0.1"/>
      <node gmv="0.557887121305" lon="0.0" lat="0.0"/>
    </gmf>
  </gmfSet>
</nrml>
'''

    @attr('qa', 'hazard', 'scenario')
    def test(self):
        cfg = os.path.join(os.path.dirname(__file__), 'job.ini')
        job = self.run_hazard(cfg)
        [output] = export.core.get_outputs(job.id)

        actual = map(numpy.median, models.get_gmvs_per_site(output, 'PGA'))
        expected_medians = [0.48155582, 0.21123045, 0.14484586]

        assert_almost_equal(actual, expected_medians, decimal=2)

    @attr('qa', 'hazard', 'scenario')
    def test_export(self):
        result_dir = tempfile.mkdtemp()

        try:
            cfg = os.path.join(os.path.dirname(__file__), 'job.ini')
            job = self.run_hazard(cfg)
            [output] = export.core.get_outputs(job.id)
            exported_file = export.hazard.export(
                output.id, result_dir)
            self.assert_xml_equal(
                StringIO.StringIO(self.EXPECTED_XML), exported_file)
        finally:
            shutil.rmtree(result_dir)
