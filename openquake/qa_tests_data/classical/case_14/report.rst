Classical PSHA QA test with sites_csv
=====================================

============== ===================
checksum32     2,580,379,596      
date           2019-05-03T06:44:08
engine_version 3.5.0-git7a6d15e809
============== ===================

num_sites = 10, num_levels = 13, num_rlzs = 2

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
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
============ ======= =============== ================
smlt_path    weight  gsim_logic_tree num_realizations
============ ======= =============== ================
simple_fault 1.00000 simple(2)       2               
============ ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================================= =========== ============================= =======================
grp_id gsims                                             distances   siteparams                    ruptparams             
====== ================================================= =========== ============================= =======================
0      '[AbrahamsonSilva2008]' '[CampbellBozorgnia2008]' rjb rrup rx vs30 vs30measured z1pt0 z2pt5 dip mag rake width ztor
====== ================================================= =========== ============================= =======================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,'[AbrahamsonSilva2008]': [0]
  0,'[CampbellBozorgnia2008]': [1]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
simple_fault.xml 0      Active Shallow Crust 447          447         
================ ====== ==================== ============ ============

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight
====== ========= ==== ===== ===== ============ ========= ========= ======
0      3         S    0     2     447          4.663E-04 10        1,414 
====== ========= ==== ===== ===== ============ ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    4.663E-04 1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
read_source_models 0.00522 NaN    0.00522 0.00522 1      
preclassical       0.00735 NaN    0.00735 0.00735 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ======================================================== ========
task               sent                                                     received
read_source_models converter=313 B fnames=107 B                             1.49 KB 
preclassical       params=110.64 KB srcs=1.1 KB gsims=296 B srcfilter=218 B 336 B   
================== ======================================================== ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total preclassical       0.00735   0.0       1     
managing sources         0.00579   0.0       1     
total read_source_models 0.00522   0.0       1     
store source_info        0.00263   0.0       1     
aggregate curves         1.462E-04 0.0       1     
======================== ========= ========= ======