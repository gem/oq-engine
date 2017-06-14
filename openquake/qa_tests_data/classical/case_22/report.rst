Classical PSHA using Alaska 2007 active shallow crust grid model
================================================================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_29228.hdf5 Wed Jun 14 10:04:20 2017
engine_version                                   2.5.0-gite200a20        
================================================ ========================

num_sites = 21, num_imts = 6

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
======================= ======================================================================================================================================================
Name                    File                                                                                                                                                  
======================= ======================================================================================================================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                                                                                                          
job_ini                 `job.ini <job.ini>`_                                                                                                                                  
sites                   `sites.csv <sites.csv>`_                                                                                                                              
source                  `Alaska_asc_grid_NSHMP2007.xml
                    extra_source_model.xml <Alaska_asc_grid_NSHMP2007.xml
                    extra_source_model.xml>`_
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_                                                                                          
======================= ======================================================================================================================================================

Composite source model
----------------------
========================= ====== ====================================================================================================================================================== =============== ================
smlt_path                 weight source_model_file                                                                                                                                      gsim_logic_tree num_realizations
========================= ====== ====================================================================================================================================================== =============== ================
Alaska_asc_grid_NSHMP2007 1.000  `Alaska_asc_grid_NSHMP2007.xml
                    extra_source_model.xml <Alaska_asc_grid_NSHMP2007.xml
                    extra_source_model.xml>`_ simple(4)       4/4             
========================= ====== ====================================================================================================================================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ==================================================================================================== ========= ========== ============
grp_id gsims                                                                                                distances siteparams ruptparams  
====== ==================================================================================================== ========= ========== ============
0      AbrahamsonSilva1997() BooreEtAl1997GeometricMean() CampbellBozorgnia2003NSHMP2007() SadighEtAl1997() rjb rrup  vs30       dip mag rake
1      AbrahamsonSilva1997() BooreEtAl1997GeometricMean() CampbellBozorgnia2003NSHMP2007() SadighEtAl1997() rjb rrup  vs30       dip mag rake
====== ==================================================================================================== ========= ========== ============

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=4)
  0,AbrahamsonSilva1997(): ['<0,Alaska_asc_grid_NSHMP2007~Abrahamson_Silva_1997,w=0.25>']
  0,BooreEtAl1997GeometricMean(): ['<1,Alaska_asc_grid_NSHMP2007~Boore_et_al_1997,w=0.25>']
  0,CampbellBozorgnia2003NSHMP2007(): ['<2,Alaska_asc_grid_NSHMP2007~Campbell_Bozorgnia_2003,w=0.25>']
  0,SadighEtAl1997(): ['<3,Alaska_asc_grid_NSHMP2007~Sadigh_et_al_1997,w=0.25>']
  1,AbrahamsonSilva1997(): ['<0,Alaska_asc_grid_NSHMP2007~Abrahamson_Silva_1997,w=0.25>']
  1,BooreEtAl1997GeometricMean(): ['<1,Alaska_asc_grid_NSHMP2007~Boore_et_al_1997,w=0.25>']
  1,CampbellBozorgnia2003NSHMP2007(): ['<2,Alaska_asc_grid_NSHMP2007~Campbell_Bozorgnia_2003,w=0.25>']
  1,SadighEtAl1997(): ['<3,Alaska_asc_grid_NSHMP2007~Sadigh_et_al_1997,w=0.25>']>

Number of ruptures per tectonic region type
-------------------------------------------
======================================================================== ====== ==================== =========== ============ ============
source_model                                                             grp_id trt                  num_sources eff_ruptures tot_ruptures
======================================================================== ====== ==================== =========== ============ ============
Alaska_asc_grid_NSHMP2007.xml
                    extra_source_model.xml 0      Active Shallow Crust 1           160          160         
Alaska_asc_grid_NSHMP2007.xml
                    extra_source_model.xml 1      Active Shallow Crust 1           1104         1,104       
======================================================================== ====== ==================== =========== ============ ============

============= =====
#TRT models   2    
#sources      2    
#eff_ruptures 1,264
#tot_ruptures 1,264
#tot_weight   0    
============= =====

Informational data
------------------
============================== =============================================================================
count_eff_ruptures.received    tot 1.14 KB, max_per_task 585 B                                              
count_eff_ruptures.sent        sources 6.08 KB, param 3.62 KB, srcfilter 2.43 KB, gsims 706 B, monitor 626 B
hazard.input_weight            126                                                                          
hazard.n_imts                  6 B                                                                          
hazard.n_levels                114 B                                                                        
hazard.n_realizations          4 B                                                                          
hazard.n_sites                 21 B                                                                         
hazard.n_sources               2 B                                                                          
hazard.output_weight           2,394                                                                        
hostname                       tstation.gem.lan                                                             
require_epsilons               0 B                                                                          
============================== =============================================================================

Slowest sources
---------------
====== ========= ================ ============ ========= ========= =========
grp_id source_id source_class     num_ruptures calc_time num_sites num_split
====== ========= ================ ============ ========= ========= =========
1      mps-0     MultiPointSource 1,104        6.175E-05 21        1        
0      mps-0     MultiPointSource 160          6.127E-05 21        1        
====== ========= ================ ============ ========= ========= =========

Computation times by source typology
------------------------------------
================ ========= ======
source_class     calc_time counts
================ ========= ======
MultiPointSource 1.230E-04 2     
================ ========= ======

Information about the tasks
---------------------------
================== ===== ========= ===== ===== =========
operation-duration mean  stddev    min   max   num_tasks
count_eff_ruptures 0.001 3.422E-05 0.001 0.001 2        
================== ===== ========= ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
store source_info              0.004     0.0       1     
reading composite source model 0.004     0.0       1     
total count_eff_ruptures       0.002     0.023     2     
managing sources               0.002     0.0       1     
prefiltering source model      0.002     0.0       1     
reading site collection        2.496E-04 0.0       1     
aggregate curves               4.601E-05 0.0       2     
saving probability maps        3.099E-05 0.0       1     
============================== ========= ========= ======