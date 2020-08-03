Classical PSHA QA test with sites_csv
=====================================

============== ===================
checksum32     1_067_610_621      
date           2020-03-13T11:22:54
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 10, num_levels = 13, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    1                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
pointsource_distance            {'default': 0}    
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
========================= ============================================================
Name                      File                                                        
========================= ============================================================
gsim_logic_tree           `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                   `job.ini <job.ini>`_                                        
reqv:active shallow crust `lookup_asc.hdf5 <lookup_asc.hdf5>`_                        
sites                     `qa_sites.csv <qa_sites.csv>`_                              
source_model_logic_tree   `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
========================= ============================================================

Composite source model
----------------------
============ ======= ================
smlt_path    weight  num_realizations
============ ======= ================
simple_fault 1.00000 1               
============ ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================================= =========== ============================= =======================
grp_id gsims                                             distances   siteparams                    ruptparams             
====== ================================================= =========== ============================= =======================
0      '[AbrahamsonSilva2008]' '[CampbellBozorgnia2008]' rjb rrup rx vs30 vs30measured z1pt0 z2pt5 dip mag rake width ztor
====== ================================================= =========== ============================= =======================

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.33557   447          447         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
3         0      S    447          0.03329   0.33557   447         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    0.03329  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.03455 NaN    0.03455 0.03455 1      
read_source_model  0.00408 NaN    0.00408 0.00408 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================= ============================================= ========
task              sent                                          received
read_source_model                                               1.46 KB 
preclassical      params=110.67 KB srcs=1.37 KB srcfilter=223 B 370 B   
================= ============================================= ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66998                  time_sec  memory_mb counts
=========================== ========= ========= ======
total preclassical          0.03455   0.0       1     
composite source model      0.01540   0.0       1     
total read_source_model     0.00408   0.0       1     
store source_info           0.00246   0.0       1     
splitting/filtering sources 5.054E-04 0.0       1     
aggregate curves            2.706E-04 0.0       1     
=========================== ========= ========= ======