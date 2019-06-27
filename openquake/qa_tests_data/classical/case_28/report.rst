North Africa PSHA
=================

============== ===================
checksum32     3,672,594,697      
date           2019-06-24T15:34:20
engine_version 3.6.0-git4b6205639c
============== ===================

num_sites = 2, num_levels = 133, num_rlzs = 8

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
random_seed                     19                
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
============================= ======= =============== ================
smlt_path                     weight  gsim_logic_tree num_realizations
============================= ======= =============== ================
smoothed_model_m_m0.2_b_e0.0  0.50000 simple(0,4,0)   4               
smoothed_model_m_m0.2_b_m0.05 0.50000 simple(0,4,0)   4               
============================= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ============================================================================================== =========== ======================= =================
grp_id gsims                                                                                          distances   siteparams              ruptparams       
====== ============================================================================================== =========== ======================= =================
0      '[AkkarEtAlRjb2014]' '[AtkinsonBoore2006Modified2011]' '[ChiouYoungs2014]' '[PezeshkEtAl2011]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      '[AkkarEtAlRjb2014]' '[AtkinsonBoore2006Modified2011]' '[ChiouYoungs2014]' '[PezeshkEtAl2011]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ============================================================================================== =========== ======================= =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=32, rlzs=8)>

Number of ruptures per tectonic region type
-------------------------------------------
=============== ====== =============== ============ ============
source_model    grp_id trt             eff_ruptures tot_ruptures
=============== ====== =============== ============ ============
GridSources.xml 0      Tectonic_type_b 260          260         
GridSources.xml 1      Tectonic_type_b 260          260         
=============== ====== =============== ============ ============

============= ===
#TRT models   2  
#eff_ruptures 520
#tot_ruptures 520
#tot_weight   520
============= ===

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========= ====== =============
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight checksum     
====== ========= ==== ===== ===== ============ ========= ========= ====== =============
0      21        M    0     2     260          0.00329   1.00000   260    1,650,391,507
1      21        M    2     4     260          0.0       0.0       0.0    1,650,391,507
====== ========= ==== ===== ===== ============ ========= ========= ====== =============

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
M    0.00329   2     
==== ========= ======

Duplicated sources
------------------
Found 1 source(s) with the same ID and 1 true duplicate(s): ['21']

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.00380 NaN     0.00380 0.00380 1      
read_source_models 0.00198 0.00101 0.00127 0.00269 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ======================================================= ========
task               sent                                                    received
preclassical       params=1.91 KB srcs=1.56 KB gsims=632 B srcfilter=220 B 350 B   
read_source_models converter=626 B fnames=212 B                            3.9 KB  
================== ======================================================= ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.00396   0.0       2     
total preclassical       0.00380   0.0       1     
managing sources         0.00315   0.0       1     
store source_info        0.00184   0.0       1     
aggregate curves         1.686E-04 0.0       1     
======================== ========= ========= ======