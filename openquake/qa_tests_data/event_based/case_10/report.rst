Event Based Bogota
==================

============== ===================
checksum32     3_397_551_075      
date           2020-03-13T11:21:00
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 5, num_levels = 4, num_rlzs = 100

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    100               
maximum_distance                {'default': 100.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.2               
area_source_discretization      10.0              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     113               
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================== ==================================================================
Name                     File                                                              
======================== ==================================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                        
gsim_logic_tree          `logic_tree_gmpe_simplified.xml <logic_tree_gmpe_simplified.xml>`_
job_ini                  `job.ini <job.ini>`_                                              
site_model               `site_model_bog.xml <site_model_bog.xml>`_                        
source_model_logic_tree  `logic_tree_source_model.xml <logic_tree_source_model.xml>`_      
structural_vulnerability `vulnerability_model_bog.xml <vulnerability_model_bog.xml>`_      
======================== ==================================================================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        1.00000 100             
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ============================================================================ ========= ============ ==============
grp_id gsims                                                                        distances siteparams   ruptparams    
====== ============================================================================ ========= ============ ==============
0      '[AkkarCagnan2010]' '[AkkarEtAlRhyp2014]' '[BindiEtAl2014Rjb]'               rhypo rjb vs30         mag rake      
1      '[AbrahamsonEtAl2015SInter]' '[YoungsEtAl1997SInter]' '[ZhaoEtAl2006SInter]' rrup      backarc vs30 hypo_depth mag
====== ============================================================================ ========= ============ ==============

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.07417   7_860        7_860       
1      NaN       5_370        0.0         
====== ========= ============ ============

Exposure model
--------------
=========== =
#assets     5
#taxonomies 4
=========== =

===================== ======= ====== === === ========= ==========
taxonomy              mean    stddev min max num_sites num_assets
MCF/LWAL+DUC/HBET:3,6 1.00000 0.0    1   1   2         2         
MUR/HBET:4,5          1.00000 NaN    1   1   1         1         
CR/LDUAL+DUC          1.00000 NaN    1   1   1         1         
CR/LFINF+DUC          1.00000 NaN    1   1   1         1         
*ALL*                 1.00000 0.0    1   1   5         5         
===================== ======= ====== === === ========= ==========

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
CC_02_147 0      P    108          0.00186   0.04630   108         
CC_02_62  0      P    108          0.00182   0.04630   108         
CC_57_18  0      P    15           0.00181   0.33333   15          
CC_66_83  0      P    30           0.00178   0.16667   30          
CC_03_56  0      P    108          0.00176   0.04630   108         
CC_67_167 0      P    63           1.190E-04 0.03175   63          
CC_57_415 0      P    15           1.185E-04 0.33333   15          
CC_03_57  0      P    108          1.109E-04 0.04630   108         
CC_02_148 0      P    108          1.085E-04 0.04630   108         
CC_02_63  0      P    108          1.075E-04 0.04630   108         
CC_67_168 0      P    63           1.073E-04 0.04762   63          
CC_03_3   0      P    108          1.066E-04 0.04630   108         
CC_03_159 0      P    108          1.020E-04 0.01852   108         
CC_03_58  0      P    108          1.016E-04 0.04630   108         
CC_05_88  0      P    60           1.006E-04 0.08333   60          
CC_57_19  0      P    15           9.871E-05 0.33333   15          
CC_57_32  0      P    15           9.751E-05 0.26667   15          
CC_03_85  0      P    108          9.584E-05 0.04630   108         
CC_03_75  0      P    108          9.513E-05 0.04630   108         
CC_02_149 0      P    108          9.489E-05 0.04630   108         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
C    0.0      
P    0.01929  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       3.09436 7.56741 0.00336 18      6      
read_source_model  0.29895 0.35139 0.05048 0.54742 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= ========================================== ========
task              sent                                       received
read_source_model converter=664 B fname=221 B srcfilter=8 B  68.1 KB 
preclassical      srcs=74.88 KB params=4.99 KB gsims=2.91 KB 6.58 KB 
================= ========================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66931                  time_sec  memory_mb counts
=========================== ========= ========= ======
total preclassical          18        20        6     
splitting/filtering sources 17        17        6     
composite source model      0.62207   0.04688   1     
total read_source_model     0.59791   1.35547   2     
store source_info           0.00262   0.0       1     
aggregate curves            0.00172   0.0       5     
reading exposure            5.119E-04 0.0       1     
=========================== ========= ========= ======