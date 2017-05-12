Classical PSHA using Alaska 2007 active shallow crust grid model
================================================================

=============================================== ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_7602.hdf5 Wed Apr 26 15:54:59 2017
engine_version                                  2.4.0-git9336bd0        
hazardlib_version                               0.24.0-gita895d4c       
=============================================== ========================

num_sites = 21, sitecol = 1.84 KB

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            4.0               
complex_fault_mesh_spacing      4.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     23                
master_seed                     0                 
=============================== ==================

Input files
-----------
======================= ================================================================
Name                    File                                                            
======================= ================================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                    
job_ini                 `job.ini <job.ini>`_                                            
sites                   `sites.csv <sites.csv>`_                                        
source                  `Alaska_asc_grid_NSHMP2007.xml <Alaska_asc_grid_NSHMP2007.xml>`_
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_    
======================= ================================================================

Composite source model
----------------------
========================= ====== ================================================================ =============== ================
smlt_path                 weight source_model_file                                                gsim_logic_tree num_realizations
========================= ====== ================================================================ =============== ================
Alaska_asc_grid_NSHMP2007 1.000  `Alaska_asc_grid_NSHMP2007.xml <Alaska_asc_grid_NSHMP2007.xml>`_ simple(4)       4/4             
========================= ====== ================================================================ =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ==================================================================================================== ========= ========== ============
grp_id gsims                                                                                                distances siteparams ruptparams  
====== ==================================================================================================== ========= ========== ============
0      AbrahamsonSilva1997() BooreEtAl1997GeometricMean() CampbellBozorgnia2003NSHMP2007() SadighEtAl1997() rjb rrup  vs30       dip rake mag
====== ==================================================================================================== ========= ========== ============

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=4)
  0,AbrahamsonSilva1997(): ['<0,Alaska_asc_grid_NSHMP2007~Abrahamson_Silva_1997,w=0.25>']
  0,BooreEtAl1997GeometricMean(): ['<1,Alaska_asc_grid_NSHMP2007~Boore_et_al_1997,w=0.25>']
  0,CampbellBozorgnia2003NSHMP2007(): ['<2,Alaska_asc_grid_NSHMP2007~Campbell_Bozorgnia_2003,w=0.25>']
  0,SadighEtAl1997(): ['<3,Alaska_asc_grid_NSHMP2007~Sadigh_et_al_1997,w=0.25>']>

Number of ruptures per tectonic region type
-------------------------------------------
============================= ====== ==================== =========== ============ ============
source_model                  grp_id trt                  num_sources eff_ruptures tot_ruptures
============================= ====== ==================== =========== ============ ============
Alaska_asc_grid_NSHMP2007.xml 0      Active Shallow Crust 4           195          368         
============================= ====== ==================== =========== ============ ============

Informational data
------------------
============================== ============================================================================
count_eff_ruptures.received    tot 2.27 KB, max_per_task 2.27 KB                                           
count_eff_ruptures.sent        sources 5.24 KB, monitor 2.05 KB, srcfilter 1.21 KB, gsims 353 B, param 65 B
hazard.input_weight            36                                                                          
hazard.n_imts                  6 B                                                                         
hazard.n_levels                114 B                                                                       
hazard.n_realizations          4 B                                                                         
hazard.n_sites                 21 B                                                                        
hazard.n_sources               4 B                                                                         
hazard.output_weight           9,576                                                                       
hostname                       tstation.gem.lan                                                            
require_epsilons               0 B                                                                         
============================== ============================================================================

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
0      6736      PointSource  92           0.0       1         0        
0      70088     PointSource  92           0.0       1         0        
0      98979     PointSource  92           0.0       1         0        
0      8878      PointSource  92           0.0       2         0        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.0       4     
============ ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.147 NaN    0.147 0.147 1        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total count_eff_ruptures         0.147     0.0       1     
reading composite source model   0.011     0.0       1     
filtering composite source model 0.010     0.0       1     
store source_info                6.618E-04 0.0       1     
reading site collection          2.356E-04 0.0       1     
managing sources                 1.159E-04 0.0       1     
saving probability maps          5.865E-05 0.0       1     
aggregate curves                 1.740E-05 0.0       1     
================================ ========= ========= ======