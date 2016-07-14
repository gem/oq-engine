Event-based PSHA with logic tree sampling
=========================================

gem-tstation:/home/michele/ssd/calc_22616.hdf5 updated Tue May 31 15:38:48 2016

num_sites = 3, sitecol = 831 B

Parameters
----------
============================ ===============================
calculation_mode             'event_based'                  
number_of_logic_tree_samples 10                             
maximum_distance             {'Active Shallow Crust': 200.0}
investigation_time           50.0                           
ses_per_logic_tree_path      40                             
truncation_level             3.0                            
rupture_mesh_spacing         2.0                            
complex_fault_mesh_spacing   2.0                            
width_of_mfd_bin             0.2                            
area_source_discretization   20.0                           
random_seed                  23                             
master_seed                  0                              
engine_version               '2.0.0-git4fb4450'             
============================ ===============================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model1.xml <source_model1.xml>`_                    
source                  `source_model2.xml <source_model2.xml>`_                    
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ======================================== =============== ================
smlt_path weight source_model_file                        gsim_logic_tree num_realizations
========= ====== ======================================== =============== ================
b11       0.100  `source_model1.xml <source_model1.xml>`_ simple(3)       7/3             
b12       0.100  `source_model2.xml <source_model2.xml>`_ simple(3)       3/3             
========= ====== ======================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ============================================================= =========== ============================= =================
grp_id gsims                                                         distances   siteparams                    ruptparams       
====== ============================================================= =========== ============================= =================
0      BooreAtkinson2008() CampbellBozorgnia2008() ChiouYoungs2008() rx rjb rrup z2pt5 vs30measured vs30 z1pt0 ztor mag rake dip
1      BooreAtkinson2008() CampbellBozorgnia2008()                   rjb rrup    z2pt5 vs30                    ztor mag rake dip
====== ============================================================= =========== ============================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=5, rlzs=10)
  0,BooreAtkinson2008(): ['<3,b11~BA,w=0.1>', '<5,b11~BA,w=0.1>']
  0,CampbellBozorgnia2008(): ['<4,b11~CB,w=0.1>', '<6,b11~CB,w=0.1>']
  0,ChiouYoungs2008(): ['<0,b11~CY,w=0.1>', '<1,b11~CY,w=0.1>', '<2,b11~CY,w=0.1>']
  1,BooreAtkinson2008(): ['<8,b12~BA,w=0.1>', '<9,b12~BA,w=0.1>']
  1,CampbellBozorgnia2008(): ['<7,b12~CB,w=0.1>']>

Number of ruptures per tectonic region type
-------------------------------------------
================= ====== ==================== =========== ============ ======
source_model      grp_id trt                  num_sources eff_ruptures weight
================= ====== ==================== =========== ============ ======
source_model1.xml 0      Active Shallow Crust 1           2120         61    
source_model2.xml 1      Active Shallow Crust 1           478          61    
================= ====== ==================== =========== ============ ======

=============== =====
#TRT models     2    
#sources        2    
#eff_ruptures   2,598
filtered_weight 122  
=============== =====

Informational data
------------------
======== ============
hostname gem-tstation
======== ============

Specific information for event based
------------------------------------
======================== ======
Total number of ruptures 2,598 
Total number of events   14,308
Rupture multiplicity     5.507 
======================== ======

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
src_group_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            1         AreaSource   61     307       0.001       0.058      2.363    
1            1         AreaSource   61     307       0.001       0.064      1.143    
============ ========= ============ ====== ========= =========== ========== =========

Computation times by source typology
------------------------------------
============ =========== ========== ========= ======
source_class filter_time split_time calc_time counts
============ =========== ========== ========= ======
AreaSource   0.003       0.122      3.506     2     
============ =========== ========== ========= ======

Information about the tasks
---------------------------
================================= ================ ====== ===== ===== =========
measurement                       mean             stddev min   max   num_tasks
compute_ruptures.time_sec         0.093            0.044  0.004 0.190 38       
compute_ruptures.memory_mb        0.0              0.0    0.0   0.0   38       
compute_gmfs_and_curves.time_sec  1.048            0.385  0.561 1.924 21       
compute_gmfs_and_curves.memory_mb -0.0119047619048 0.055  -0.25 0.0   21       
================================= ================ ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_gmfs_and_curves  22        0.0       21    
compute poes                   20        0.0       2,598 
total compute_ruptures         3.520     0.0       38    
saving ruptures                1.771     0.0       1     
make contexts                  1.396     0.0       2,598 
filtering ruptures             0.706     0.0       2,598 
managing sources               0.196     0.0       1     
aggregating hcurves            0.125     0.0       143   
splitting sources              0.122     0.0       2     
reading composite source model 0.112     0.0       1     
bulding hazard curves          0.105     0.0       21    
aggregate curves               0.018     0.0       181   
store source_info              0.008     0.0       1     
filtering sources              0.003     0.0       2     
reading site collection        3.695E-05 0.0       1     
============================== ========= ========= ======