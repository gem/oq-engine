Classical Hazard QA Test, Case 25, topographic surface1 (Mt Etna)
=================================================================

============== ===================
checksum32     240_735_792        
date           2020-03-13T11:22:02
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 6, num_levels = 3, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                0.1               
area_source_discretization      1.0               
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
sites                   `sites.csv <sites.csv>`_                                    
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        1.00000 1               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ======================= ========= ========== ==========
grp_id gsims                   distances siteparams ruptparams
====== ======================= ========= ========== ==========
0      '[TusaLanger2016Rhypo]' rhypo     vs30       mag       
====== ======================= ========= ========== ==========

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.27273   440          440         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      A    440          0.00367   0.27273   440         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.00367  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.01153 NaN    0.01153 0.01153 1      
read_source_model  0.00829 NaN    0.00829 0.00829 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================= ========================================= ========
task              sent                                      received
read_source_model                                           2.3 KB  
preclassical      srcs=2.17 KB params=638 B srcfilter=223 B 358 B   
================= ========================================= ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66973                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.01708   0.0       1     
total preclassical          0.01153   1.83594   1     
total read_source_model     0.00829   0.0       1     
splitting/filtering sources 0.00722   0.0       1     
store source_info           0.00199   0.0       1     
aggregate curves            4.098E-04 0.0       1     
=========================== ========= ========= ======