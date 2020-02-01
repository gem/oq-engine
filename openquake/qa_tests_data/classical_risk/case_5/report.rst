Hazard Calculation for end-to-end hazard+risk
=============================================

============== ===================
checksum32     1_526_146_286      
date           2020-01-16T05:30:29
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 1, num_levels = 50, num_rlzs = 4

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 300.0}
investigation_time              15.0              
ses_per_logic_tree_path         1                 
truncation_level                4.0               
rupture_mesh_spacing            20.0              
complex_fault_mesh_spacing      20.0              
width_of_mfd_bin                0.2               
area_source_discretization      10.0              
pointsource_distance            None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     1024              
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job_h.ini <job_h.ini>`_                                    
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 simple(1,4)     4               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================================================================================ ========== ========== ==============
grp_id gsims                                                                                            distances  siteparams ruptparams    
====== ================================================================================================ ========== ========== ==============
0      '[AkkarBommer2010]'                                                                              rjb        vs30       mag rake      
1      '[AtkinsonBoore2003SInter]' '[LinLee2008SInter]' '[YoungsEtAl1997SInter]' '[ZhaoEtAl2006SInter]' rhypo rrup vs30       hypo_depth mag
====== ================================================================================================ ========== ========== ==============

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=17, rlzs=4)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.04348   23           23          
1      0.04348   23           23          
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
B         1      P    23           0.00173   0.04348   23          
A         0      P    23           0.00162   0.04348   23          
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    0.00335  
==== =========

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
SourceReader       0.00372 NaN       0.00372 0.00372 1      
preclassical       0.00231 3.591E-05 0.00229 0.00234 2      
================== ======= ========= ======= ======= =======

Data transfer
-------------
============ ======================================= ========
task         sent                                    received
SourceReader                                         2.79 KB 
preclassical srcs=2.31 KB params=2.05 KB gsims=658 B 732 B   
============ ======================================= ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_43188                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.06725   1.53906   1     
total preclassical          0.00462   1.72266   2     
total SourceReader          0.00372   0.25781   1     
store source_info           0.00222   0.0       1     
aggregate curves            7.513E-04 0.0       2     
splitting/filtering sources 3.626E-04 0.23828   2     
=========================== ========= ========= ======