Event Based QA Test, Case 12
============================

gem-tstation:/home/michele/ssd/calc_22619.hdf5 updated Tue May 31 15:39:11 2016

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ============================================================
calculation_mode             'event_based'                                               
number_of_logic_tree_samples 0                                                           
maximum_distance             {'stable continental': 200.0, 'active shallow crust': 200.0}
investigation_time           1.0                                                         
ses_per_logic_tree_path      3500                                                        
truncation_level             2.0                                                         
rupture_mesh_spacing         1.0                                                         
complex_fault_mesh_spacing   1.0                                                         
width_of_mfd_bin             1.0                                                         
area_source_discretization   10.0                                                        
random_seed                  1066                                                        
master_seed                  0                                                           
engine_version               '2.0.0-git4fb4450'                                          
============================ ============================================================

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
b1        1.000  `source_model.xml <source_model.xml>`_ trivial(1,1)    1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== ========= ========== ==========
grp_id gsims               distances siteparams ruptparams
====== =================== ========= ========== ==========
0      SadighEtAl1997()    rrup      vs30       rake mag  
1      BooreAtkinson2008() rjb       vs30       rake mag  
====== =================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=1)
  0,SadighEtAl1997(): ['<0,b1~b1_b2,w=1.0>']
  1,BooreAtkinson2008(): ['<0,b1~b1_b2,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     grp_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 1           1            0.025 
source_model.xml 1      Stable Continental   1           1            0.025 
================ ====== ==================== =========== ============ ======

=============== =====
#TRT models     2    
#sources        2    
#eff_ruptures   2    
filtered_weight 0.050
=============== =====

Informational data
------------------
======== ============
hostname gem-tstation
======== ============

Specific information for event based
------------------------------------
======================== =====
Total number of ruptures 2    
Total number of events   6,906
Rupture multiplicity     3,453
======================== =====

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
src_group_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            1         PointSource  0.025  1         2.789E-05   0.0        0.069    
1            2         PointSource  0.025  1         1.311E-05   0.0        0.064    
============ ========= ============ ====== ========= =========== ========== =========

Computation times by source typology
------------------------------------
============ =========== ========== ========= ======
source_class filter_time split_time calc_time counts
============ =========== ========== ========= ======
PointSource  4.101E-05   0.0        0.132     2     
============ =========== ========== ========= ======

Information about the tasks
---------------------------
================================= ====== ====== =========== =========== =========
measurement                       mean   stddev min         max         num_tasks
compute_ruptures.time_sec         0.067  0.004  0.064       0.069       2        
compute_ruptures.memory_mb        -0.375 0.094  -0.44140625 -0.30859375 2        
compute_gmfs_and_curves.time_sec  0.045  0.002  0.044       0.047       2        
compute_gmfs_and_curves.memory_mb 0.0    0.0    0.0         0.0         2        
================================= ====== ====== =========== =========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         0.134     0.0       2     
total compute_gmfs_and_curves  0.091     0.0       2     
saving ruptures                0.081     0.0       1     
compute poes                   0.068     0.0       2     
bulding hazard curves          0.016     0.0       2     
store source_info              0.011     0.0       1     
reading composite source model 0.006     0.0       1     
aggregate curves               0.003     0.0       4     
aggregating hcurves            0.003     0.0       2     
managing sources               0.003     0.0       1     
saving gmfs                    0.002     0.0       2     
make contexts                  0.002     0.0       2     
filtering ruptures             0.001     0.0       2     
filtering sources              4.101E-05 0.0       2     
reading site collection        3.505E-05 0.0       1     
============================== ========= ========= ======