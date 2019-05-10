Classical PSHA with non-trivial logic tree (1 source model + 5 (a, b) pairs per source + 3 Mmax per source
==========================================================================================================

============== ===================
checksum32     1,751,642,476      
date           2019-05-10T05:07:54
engine_version 3.5.0-gitbaeb4c1e35
============== ===================

num_sites = 1, num_levels = 3, num_rlzs = 10

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    10                
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
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
============================================= ======= =============== ================
smlt_path                                     weight  gsim_logic_tree num_realizations
============================================= ======= =============== ================
b11_b21_b32_b41_b52_b61_b72_b81_b92_b101_b112 0.10000 trivial(1)      1               
b11_b22_b32_b42_b52_b62_b72_b82_b92_b102_b112 0.10000 trivial(1)      1               
b11_b23_b32_b43_b52_b63_b72_b83_b92_b103_b112 0.10000 trivial(1)      1               
b11_b23_b33_b43_b53_b63_b73_b83_b93_b103_b113 0.10000 trivial(1)      1               
b11_b24_b33_b44_b53_b64_b73_b84_b93_b104_b113 0.10000 trivial(1)      1               
============================================= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================== ========= ========== ==========
grp_id gsims                 distances siteparams ruptparams
====== ===================== ========= ========== ==========
0      '[BooreAtkinson2008]' rjb       vs30       mag rake  
1      '[BooreAtkinson2008]' rjb       vs30       mag rake  
2      '[BooreAtkinson2008]' rjb       vs30       mag rake  
3      '[BooreAtkinson2008]' rjb       vs30       mag rake  
4      '[BooreAtkinson2008]' rjb       vs30       mag rake  
====== ===================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=5, rlzs=10)
  0,'[BooreAtkinson2008]': [0]
  1,'[BooreAtkinson2008]': [1 2 3 4]
  2,'[BooreAtkinson2008]': [5]
  3,'[BooreAtkinson2008]': [6 7 8]
  4,'[BooreAtkinson2008]': [9]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 2,025        2,025       
source_model.xml 1      Active Shallow Crust 2,025        2,025       
source_model.xml 2      Active Shallow Crust 2,025        2,025       
source_model.xml 3      Active Shallow Crust 2,295        2,025       
source_model.xml 4      Active Shallow Crust 2,295        2,025       
================ ====== ==================== ============ ============

============= ======
#TRT models   5     
#eff_ruptures 10,665
#tot_ruptures 10,125
#tot_weight   1,066 
============= ======

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight
====== ========= ==== ===== ===== ============ ========= ========= ======
1      1         A    20    24    375          0.00404   1.00000   37    
1      4         A    32    36    375          0.00403   1.00000   37    
1      2         A    24    28    450          0.00284   1.00000   45    
0      1         A    0     4     375          0.00276   1.00000   37    
0      5         A    16    20    375          0.00274   1.00000   37    
2      3         A    48    52    450          0.00272   1.00000   45    
1      5         A    36    40    375          0.00256   1.00000   37    
3      5         A    76    80    425          0.00251   1.00000   42    
0      2         A    4     8     450          0.00243   1.00000   45    
0      4         A    12    16    375          0.00240   1.00000   37    
4      1         A    80    84    425          0.00236   1.00000   42    
4      2         A    84    88    510          0.00234   1.00000   51    
1      3         A    28    32    450          0.00230   1.00000   45    
0      3         A    8     12    450          0.00224   1.00000   45    
4      3         A    88    92    510          0.00208   1.00000   51    
2      5         A    56    60    375          0.00208   1.00000   37    
2      2         A    44    48    450          0.00205   1.00000   45    
2      4         A    52    56    375          0.00203   1.00000   37    
3      3         A    68    72    510          0.00200   1.00000   51    
3      4         A    72    76    425          0.00196   1.00000   42    
====== ========= ==== ===== ===== ============ ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.05753   25    
==== ========= ======

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
read_source_models 0.03043 0.00323   0.02582 0.03326 5      
preclassical       0.00270 8.068E-04 0.00149 0.00473 25     
================== ======= ========= ======= ======= =======

Data transfer
-------------
================== ============================================================= ========
task               sent                                                          received
read_source_models converter=1.53 KB fnames=535 B                                26.92 KB
preclassical       srcs=47.87 KB params=11.69 KB srcfilter=5.35 KB gsims=3.93 KB 8.4 KB  
================== ============================================================= ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.15215  0.0       5     
total preclassical       0.06760  0.0       25    
managing sources         0.01730  0.0       1     
aggregate curves         0.00373  0.0       25    
store source_info        0.00185  0.0       1     
======================== ======== ========= ======