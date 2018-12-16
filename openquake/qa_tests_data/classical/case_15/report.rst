Classical PSHA with GMPE logic tree with multiple tectonic region types
=======================================================================

============== ===================
checksum32     17,280,623         
date           2018-12-13T12:58:02
engine_version 3.3.0-git68d7d11268
============== ===================

num_sites = 3, num_levels = 17

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
============== ======= =============== ================
smlt_path      weight  gsim_logic_tree num_realizations
============== ======= =============== ================
SM1            0.50000 complex(2,2)    4/4             
SM2_a3b1       0.25000 complex(2,2)    2/2             
SM2_a3pt2b0pt8 0.25000 complex(2,2)    2/2             
============== ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =========================================== ========= ========== =================
grp_id gsims                                       distances siteparams ruptparams       
====== =========================================== ========= ========== =================
0      BooreAtkinson2008() CampbellBozorgnia2008() rjb rrup  vs30 z2pt5 dip mag rake ztor
1      Campbell2003() ToroEtAl2002()               rjb rrup             mag              
2      BooreAtkinson2008() CampbellBozorgnia2008() rjb rrup  vs30 z2pt5 dip mag rake ztor
3      BooreAtkinson2008() CampbellBozorgnia2008() rjb rrup  vs30 z2pt5 dip mag rake ztor
====== =========================================== ========= ========== =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=8)
  0,BooreAtkinson2008(): [0 1]
  0,CampbellBozorgnia2008(): [2 3]
  1,Campbell2003(): [0 2]
  1,ToroEtAl2002(): [1 3]
  2,BooreAtkinson2008(): [4]
  2,CampbellBozorgnia2008(): [5]
  3,BooreAtkinson2008(): [6]
  3,CampbellBozorgnia2008(): [7]>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ======================== ============ ============
source_model       grp_id trt                      eff_ruptures tot_ruptures
================== ====== ======================== ============ ============
source_model_1.xml 0      Active Shallow Crust     15           15          
source_model_1.xml 1      Stable Continental Crust 15           15          
source_model_2.xml 2      Active Shallow Crust     240          240         
source_model_2.xml 3      Active Shallow Crust     240          240         
================== ====== ======================== ============ ============

============= ===
#TRT models   4  
#eff_ruptures 510
#tot_ruptures 510
#tot_weight   88 
============= ===

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
0      1         P    0     1     15           0.0       3.314E-05  0.0       1         0.0   
1      2         P    1     2     15           0.0       1.431E-05  0.0       1         0.0   
2      1         A    0     4     240          0.0       0.10170    0.0       16        0.0   
3      1         A    0     4     240          0.0       0.07745    0.0       16        0.0   
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.0       2     
P    0.0       2     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.00868 0.00573 0.00206 0.01205 3      
split_filter       0.02011 NaN     0.02011 0.02011 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ====================================== ========
task               sent                                   received
read_source_models converter=1.14 KB fnames=327 B         6.6 KB  
split_filter       srcs=3.42 KB srcfilter=253 B seed=14 B 9.33 KB 
================== ====================================== ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.02603  0.0       3     
total split_filter       0.02011  0.0       1     
======================== ======== ========= ======