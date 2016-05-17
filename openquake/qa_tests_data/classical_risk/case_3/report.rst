Classical PSHA - Loss fractions QA test
=======================================

gem-tstation:/home/michele/ssd/calc_16293.hdf5 updated Mon May 16 14:18:57 2016

num_sites = 13, sitecol = 1.26 KB

Parameters
----------
============================ ===================
calculation_mode             'classical_risk'   
number_of_logic_tree_samples 1                  
maximum_distance             {'default': 200.0} 
investigation_time           50.0               
ses_per_logic_tree_path      1                  
truncation_level             3.0                
rupture_mesh_spacing         5.0                
complex_fault_mesh_spacing   5.0                
width_of_mfd_bin             0.2                
area_source_discretization   10.0               
random_seed                  23                 
master_seed                  0                  
avg_losses                   False              
sites_per_tile               1000               
oqlite_version               '0.13.0-git16c052c'
============================ ===================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                  `job.ini <job.ini>`_                                        
source                   `source_model.xml <source_model.xml>`_                      
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
======================== ============================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1        1.000  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================= =========== ======================= =================
trt_id gsims             distances   siteparams              ruptparams       
====== ================= =========== ======================= =================
0      ChiouYoungs2008() rx rjb rrup vs30measured vs30 z1pt0 rake dip ztor mag
====== ================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): ['<0,b1,b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     trt_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 2           1,613        53    
================ ====== ==================== =========== ============ ======

Informational data
------------------
================ ==============
hostname         'gem-tstation'
require_epsilons True          
================ ==============

Exposure model
--------------
=========== ==
#assets     13
#taxonomies 4 
=========== ==

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
A        1.000 0.0    1   1   4         4         
DS       1.000 0.0    1   1   2         2         
UFB      1.000 0.0    1   1   2         2         
W        1.000 0.0    1   1   5         5         
*ALL*    1.000 0.0    1   1   13        13        
======== ===== ====== === === ========= ==========

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            232       AreaSource   40     1         6.590E-04   0.0        2.115    
0            225       AreaSource   13     1         6.859E-04   0.0        0.328    
============ ========= ============ ====== ========= =========== ========== =========

Computation times by source typology
------------------------------------
============ =========== ========== ========= ======
source_class filter_time split_time calc_time counts
============ =========== ========== ========= ======
AreaSource   0.001       0.0        2.443     2     
============ =========== ========== ========= ======

Information about the tasks
---------------------------
======================== ===== ====== ===== ===== =========
measurement              mean  stddev min   max   num_tasks
classical_risk.time_sec  0.402 0.037  0.323 0.465 13       
classical_risk.memory_mb 0.659 0.509  0.0   1.117 13       
classical.time_sec       1.226 1.263  0.332 2.119 2        
classical.memory_mb      2.428 0.367  2.168 2.688 2        
classical.time_sec       1.226 1.263  0.332 2.119 2        
classical.memory_mb      2.428 0.367  2.168 2.688 2        
======================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total classical_risk           5.225     1.117     13    
computing riskmodel            5.206     0.0       13    
total classical                2.451     2.688     2     
making contexts                1.522     0.0       2,132 
reading composite source model 1.185     0.0       1     
computing poes                 0.314     0.0       1,613 
managing sources               0.047     0.0       1     
reading exposure               0.040     0.0       1     
filtering sources              0.030     0.0       15    
store source_info              0.010     0.0       1     
save curves_by_trt_gsim        0.003     0.0       1     
building hazard                0.002     0.0       13    
save curves_by_rlz             0.002     0.0       1     
building riskinputs            9.871E-04 0.0       1     
aggregate curves               9.379E-04 0.0       2     
combine curves_by_rlz          1.831E-04 0.0       1     
reading site collection        3.409E-05 0.0       1     
============================== ========= ========= ======