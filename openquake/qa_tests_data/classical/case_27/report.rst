Mutex sources for Nankai, Japan, case_27
========================================

=============================================== ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_7931.hdf5 Thu Apr 27 11:11:45 2017
engine_version                                  2.4.0-git53d28d9        
hazardlib_version                               0.24.0-gita2352cf       
=============================================== ========================

num_sites = 1, sitecol = 809 B

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
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1        1.000  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ======================== ========= ========== ==============
grp_id gsims                    distances siteparams ruptparams    
====== ======================== ========= ========== ==============
0      SiMidorikawa1999SInter() rrup                 mag hypo_depth
====== ======================== ========= ========== ==============

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,SiMidorikawa1999SInter(): ['<0,b1~b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Subduction Interface 15          14           19          
================ ====== ==================== =========== ============ ============

Informational data
------------------
============================== ========================================================================
count_eff_ruptures.received    max_per_task 1.07 KB, tot 1.07 KB                                       
count_eff_ruptures.sent        sources 1.08 MB, monitor 867 B, srcfilter 684 B, gsims 106 B, param 65 B
hazard.input_weight            19                                                                      
hazard.n_imts                  1 B                                                                     
hazard.n_levels                6 B                                                                     
hazard.n_realizations          1 B                                                                     
hazard.n_sites                 1 B                                                                     
hazard.n_sources               15 B                                                                    
hazard.output_weight           6.000                                                                   
hostname                       tstation.gem.lan                                                        
require_epsilons               0 B                                                                     
============================== ========================================================================

Slowest sources
---------------
====== ========= ========================== ============ ========= ========= =========
grp_id source_id source_class               num_ruptures calc_time num_sites num_split
====== ========= ========================== ============ ========= ========= =========
0      case_09   NonParametricSeismicSource 1            0.0       1         0        
0      case_02   NonParametricSeismicSource 1            0.0       1         0        
0      case_07   NonParametricSeismicSource 1            0.0       1         0        
0      case_06   NonParametricSeismicSource 1            0.0       1         0        
0      case_11   NonParametricSeismicSource 1            0.0       1         0        
0      case_15   NonParametricSeismicSource 2            0.0       1         0        
0      case_01   NonParametricSeismicSource 1            0.0       1         0        
0      case_12   NonParametricSeismicSource 2            0.0       1         0        
0      case_03   NonParametricSeismicSource 1            0.0       1         0        
0      case_08   NonParametricSeismicSource 1            0.0       1         0        
0      case_13   NonParametricSeismicSource 2            0.0       1         0        
0      case_14   NonParametricSeismicSource 2            0.0       1         0        
0      case_04   NonParametricSeismicSource 1            0.0       1         0        
0      case_05   NonParametricSeismicSource 1            0.0       1         0        
0      case_10   NonParametricSeismicSource 1            0.0       1         0        
====== ========= ========================== ============ ========= ========= =========

Computation times by source typology
------------------------------------
========================== ========= ======
source_class               calc_time counts
========================== ========= ======
NonParametricSeismicSource 0.0       15    
========================== ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.177 NaN    0.177 0.177 1        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
reading composite source model   0.363     0.0       1     
total count_eff_ruptures         0.177     7.047     1     
filtering composite source model 0.013     0.0       1     
managing sources                 0.002     0.0       1     
store source_info                0.001     0.0       1     
reading site collection          5.937E-05 0.0       1     
saving probability maps          4.840E-05 0.0       1     
aggregate curves                 4.721E-05 0.0       1     
================================ ========= ========= ======