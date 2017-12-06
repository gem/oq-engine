Mutex sources for Nankai, Japan, case_27
========================================

============== ===================
checksum32     426,920,066        
date           2017-12-06T11:20:15
engine_version 2.9.0-gite55e76e   
============== ===================

num_sites = 1, num_imts = 1

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                None              
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                1.0               
area_source_discretization      None              
ground_motion_correlation_model None              
random_seed                     1066              
master_seed                     0                 
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== =============== ================
smlt_path weight gsim_logic_tree num_realizations
========= ====== =============== ================
b1        1.000  trivial(1)      1/1             
========= ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ======================== ========= ========== ==============
grp_id gsims                    distances siteparams ruptparams    
====== ======================== ========= ========== ==============
0      SiMidorikawa1999SInter() rrup                 hypo_depth mag
====== ======================== ========= ========== ==============

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,SiMidorikawa1999SInter(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Subduction Interface 19           19          
================ ====== ==================== ============ ============

Informational data
------------------
======================= =========================================================================
count_ruptures.received max_per_task 1.04 KB, tot 1.04 KB                                        
count_ruptures.sent     sources 1.08 MB, srcfilter 684 B, param 434 B, monitor 319 B, gsims 106 B
hazard.input_weight     19.0                                                                     
hazard.n_imts           1                                                                        
hazard.n_levels         6                                                                        
hazard.n_realizations   1                                                                        
hazard.n_sites          1                                                                        
hazard.n_sources        15                                                                       
hazard.output_weight    6.0                                                                      
hostname                tstation.gem.lan                                                         
require_epsilons        False                                                                    
======================= =========================================================================

Slowest sources
---------------
========= ========================== ============ ========= ========= =========
source_id source_class               num_ruptures calc_time num_sites num_split
========= ========================== ============ ========= ========= =========
case_01   NonParametricSeismicSource 1            0.003     1         1        
case_02   NonParametricSeismicSource 1            0.002     1         1        
case_03   NonParametricSeismicSource 1            0.002     1         1        
case_04   NonParametricSeismicSource 1            0.002     1         1        
case_05   NonParametricSeismicSource 1            0.002     1         1        
case_12   NonParametricSeismicSource 2            0.002     1         1        
case_13   NonParametricSeismicSource 2            0.002     1         1        
case_08   NonParametricSeismicSource 1            0.002     1         1        
case_07   NonParametricSeismicSource 1            0.002     1         1        
case_10   NonParametricSeismicSource 1            0.002     1         1        
case_14   NonParametricSeismicSource 2            0.002     1         1        
case_09   NonParametricSeismicSource 1            0.002     1         1        
case_06   NonParametricSeismicSource 1            0.002     1         1        
case_11   NonParametricSeismicSource 1            0.002     1         1        
case_15   NonParametricSeismicSource 2            0.002     1         1        
========= ========================== ============ ========= ========= =========

Computation times by source typology
------------------------------------
========================== ========= ======
source_class               calc_time counts
========================== ========= ======
NonParametricSeismicSource 0.034     15    
========================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.036 NaN    0.036 0.036 1        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.293     0.0       1     
total count_ruptures           0.036     0.199     1     
managing sources               0.016     0.0       1     
store source_info              0.004     0.0       1     
reading site collection        4.196E-05 0.0       1     
saving probability maps        3.600E-05 0.0       1     
aggregate curves               3.028E-05 0.0       1     
============================== ========= ========= ======