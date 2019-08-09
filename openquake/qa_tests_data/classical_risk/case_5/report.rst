Hazard Calculation for end-to-end hazard+risk
=============================================

============== ===================
checksum32     2,783,587,006      
date           2019-07-30T15:04:00
engine_version 3.7.0-git3b3dff46da
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
========= ====== ==== ============ ========= ========= ====== ======
source_id grp_id code num_ruptures calc_time num_sites weight speed 
========= ====== ==== ============ ========= ========= ====== ======
A         0      P    23           0.00164   1.00000   23     14,009
B         1      P    23           0.00141   1.00000   23     16,268
========= ====== ==== ============ ========= ========= ====== ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    0.00306   2     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
preclassical       0.00185 1.404E-04 0.00175 0.00194 2      
read_source_models 0.00105 NaN       0.00105 0.00105 1      
================== ======= ========= ======= ======= =======

Data transfer
-------------
================== ======================================================= ========
task               sent                                                    received
preclassical       srcs=2.32 KB params=1.77 KB gsims=658 B srcfilter=440 B 684 B   
read_source_models converter=314 B fnames=104 B                            1.96 KB 
================== ======================================================= ========

Slowest operations
------------------
======================== ========= ========= ======
calc_15510               time_sec  memory_mb counts
======================== ========= ========= ======
total preclassical       0.00369   0.0       2     
store source_info        0.00198   0.0       1     
managing sources         0.00121   0.0       1     
total read_source_models 0.00105   0.0       1     
aggregate curves         2.804E-04 0.0       2     
======================== ========= ========= ======