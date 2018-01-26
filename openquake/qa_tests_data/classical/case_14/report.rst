Classical PSHA QA test with sites_csv
=====================================

============== ===================
checksum32     762,001,888        
date           2018-01-11T04:54:44
engine_version 2.9.0-git3c583c4   
============== ===================

num_sites = 10, num_imts = 1

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     23                
master_seed                     0                 
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
sites                   `qa_sites.csv <qa_sites.csv>`_                              
source                  `simple_fault.xml <simple_fault.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
============ ====== =============== ================
smlt_path    weight gsim_logic_tree num_realizations
============ ====== =============== ================
simple_fault 1.000  simple(2)       2/2             
============ ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ============================================= =========== ============================= =======================
grp_id gsims                                         distances   siteparams                    ruptparams             
====== ============================================= =========== ============================= =======================
0      AbrahamsonSilva2008() CampbellBozorgnia2008() rjb rrup rx vs30 vs30measured z1pt0 z2pt5 dip mag rake width ztor
====== ============================================= =========== ============================= =======================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,AbrahamsonSilva2008(): [0]
  0,CampbellBozorgnia2008(): [1]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
simple_fault.xml 0      Active Shallow Crust 447          447         
================ ====== ==================== ============ ============

Informational data
------------------
======================= ===================================================================================
count_ruptures.received tot 7 KB, max_per_task 682 B                                                       
count_ruptures.sent     srcfilter 14.19 KB, sources 12.91 KB, param 5.86 KB, monitor 3.74 KB, gsims 2.29 KB
hazard.input_weight     447.0                                                                              
hazard.n_imts           1                                                                                  
hazard.n_levels         13                                                                                 
hazard.n_realizations   2                                                                                  
hazard.n_sites          10                                                                                 
hazard.n_sources        1                                                                                  
hazard.output_weight    130.0                                                                              
hostname                tstation.gem.lan                                                                   
require_epsilons        False                                                                              
======================= ===================================================================================

Slowest sources
---------------
========= ================= ============ ========= ========= =========
source_id source_class      num_ruptures calc_time num_sites num_split
========= ================= ============ ========= ========= =========
3         SimpleFaultSource 447          0.047     10        15       
========= ================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 0.047     1     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.005 0.003  0.002 0.014 12       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.072     0.0       1     
total count_ruptures           0.056     0.0       12    
reading composite source model 0.007     0.0       1     
store source_info              0.005     0.0       1     
aggregate curves               2.511E-04 0.0       12    
reading site collection        2.153E-04 0.0       1     
saving probability maps        4.530E-05 0.0       1     
============================== ========= ========= ======