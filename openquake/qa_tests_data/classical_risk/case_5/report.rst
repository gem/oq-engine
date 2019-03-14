Hazard Calculation for end-to-end hazard+risk
=============================================

============== ===================
checksum32     2,783,587,006      
date           2019-03-14T01:44:53
engine_version 3.4.0-gita06742ffe6
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

  <RlzsAssoc(size=5, rlzs=4)
  0,'[AkkarBommer2010]': [0 1 2 3]
  1,'[AtkinsonBoore2003SInter]': [1]
  1,'[LinLee2008SInter]': [3]
  1,'[YoungsEtAl1997SInter]': [2]
  1,'[ZhaoEtAl2006SInter]': [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 23           23          
source_model.xml 1      Subduction Interface 23           23          
================ ====== ==================== ============ ============

============= =======
#TRT models   2      
#eff_ruptures 46     
#tot_ruptures 46     
#tot_weight   4.60000
============= =======

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight 
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
1      B         P    1     2     23           0.0       2.027E-05  1.00000   1         2.30000
0      A         P    0     1     23           0.0       2.074E-05  1.00000   1         2.30000
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    0.0       2     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
read_source_models 0.00146 NaN       0.00146 0.00146 1      
split_filter       0.00262 2.192E-05 0.00260 0.00263 2      
================== ======= ========= ======= ======= =======

Data transfer
-------------
================== ======================================= ========
task               sent                                    received
read_source_models converter=313 B fnames=111 B            1.97 KB 
split_filter       srcs=2.29 KB srcfilter=506 B dummy=28 B 2.49 KB 
================== ======================================= ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total split_filter       0.00523  1.42969   2     
total read_source_models 0.00146  0.07812   1     
======================== ======== ========= ======