Hazard Calculation for end-to-end hazard+risk
=============================================

============== ===================
checksum32     2,783,587,006      
date           2019-09-24T15:20:45
engine_version 3.7.0-git749bb363b3
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

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 23           23          
source_model.xml 1      Subduction Interface 23           23          
================ ====== ==================== ============ ============

============= ==
#TRT models   2 
#eff_ruptures 46
#tot_ruptures 46
============= ==

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed  
========= ====== ==== ============ ========= ========= ============ =======
A         0      P    23           1.955E-04 1.00000   23           117,645
B         1      P    23           1.779E-04 1.00000   23           129,315
========= ====== ==== ============ ========= ========= ============ =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    3.734E-04 2     
==== ========= ======

Information about the tasks
---------------------------
================== ========= ========= ========= ========= =======
operation-duration mean      stddev    min       max       outputs
preclassical       5.999E-04 2.192E-05 5.844E-04 6.154E-04 2      
read_source_models 0.00150   NaN       0.00150   0.00150   1      
================== ========= ========= ========= ========= =======

Data transfer
-------------
================== ============================================= ========
task               sent                                          received
preclassical       srcs=2.34 KB params=1.77 KB srcfilter=1.26 KB 684 B   
read_source_models converter=314 B fnames=111 B                  1.97 KB 
================== ============================================= ========

Slowest operations
------------------
======================== ========= ========= ======
calc_1702                time_sec  memory_mb counts
======================== ========= ========= ======
store source_info        0.00191   0.0       1     
total read_source_models 0.00150   0.03906   1     
total preclassical       0.00120   0.16016   2     
aggregate curves         7.725E-04 0.0       2     
managing sources         3.774E-04 0.00391   1     
======================== ========= ========= ======