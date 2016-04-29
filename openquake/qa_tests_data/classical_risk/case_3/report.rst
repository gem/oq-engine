Classical PSHA - Loss fractions QA test
=======================================

gem-tstation:/home/michele/ssd/calc_1796.hdf5 updated Fri Apr 29 08:18:13 2016

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
oqlite_version               '0.13.0-git5086754'
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
====== =============== =========== ======================= =================
trt_id gsims           distances   siteparams              ruptparams       
====== =============== =========== ======================= =================
0      ChiouYoungs2008 rx rjb rrup vs30measured vs30 z1pt0 rake dip ztor mag
====== =============== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008: ['<0,b1,b1,w=1.0>']>

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
0            232       AreaSource   40     1         7.291E-04   0.0        2.245    
0            225       AreaSource   13     1         7.179E-04   0.0        0.341    
============ ========= ============ ====== ========= =========== ========== =========

Information about the tasks
---------------------------
======================== ===== ====== ===== ===== =========
measurement              mean  stddev min   max   num_tasks
classical_risk.time_sec  0.557 0.154  0.386 0.779 13       
classical_risk.memory_mb 1.162 0.027  1.152 1.250 13       
classical.time_sec       1.297 1.346  0.346 2.249 2        
classical.memory_mb      2.871 0.044  2.840 2.902 2        
classical.time_sec       1.297 1.346  0.346 2.249 2        
classical.memory_mb      2.871 0.044  2.840 2.902 2        
======================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total classical_risk           7.237     1.250     13    
computing risk                 7.216     0.0       13    
total classical                2.595     2.902     2     
making contexts                1.475     0.0       2,132 
reading composite source model 1.065     0.0       1     
computing poes                 0.474     0.0       1,613 
managing sources               0.040     0.0       1     
filtering sources              0.013     0.0       15    
store source_info              0.007     0.0       1     
reading exposure               0.006     0.0       1     
building hazard                0.002     0.0       13    
save curves_by_trt_gsim        0.002     0.0       1     
aggregate curves               7.679E-04 0.0       2     
save curves_by_rlz             7.520E-04 0.0       1     
building riskinputs            6.421E-04 0.0       1     
combine curves_by_rlz          1.249E-04 0.0       1     
reading site collection        1.001E-05 0.0       1     
============================== ========= ========= ======