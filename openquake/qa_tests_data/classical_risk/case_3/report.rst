Classical PSHA - Loss fractions QA test
=======================================

============== ===================
checksum32     177_006_542        
date           2020-01-16T05:30:35
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 12, num_levels = 19, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'classical_risk'  
number_of_logic_tree_samples    1                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.2               
area_source_discretization      10.0              
pointsource_distance            None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
avg_losses                      True              
=============================== ==================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                  `job.ini <job.ini>`_                                        
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
======================== ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1)      1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== =========== ======================= =================
grp_id gsims               distances   siteparams              ruptparams       
====== =================== =========== ======================= =================
0      '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== =================== =========== ======================= =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      3.56913   33_831       1_613       
====== ========= ============ ============

Exposure model
--------------
=========== ==
#assets     13
#taxonomies 4 
=========== ==

======== ======= ======= === === ========= ==========
taxonomy mean    stddev  min max num_sites num_assets
W        1.00000 0.0     1   1   5         5         
A        1.00000 0.0     1   1   4         4         
DS       2.00000 NaN     2   2   1         2         
UFB      1.00000 0.0     1   1   2         2         
*ALL*    1.08333 0.28868 1   2   12        13        
======== ======= ======= === === ========= ==========

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
232       0      A    1_612        1.94330   3.57072   1_612       
225       0      A    520          0.15081   1.00000   1.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    2.09411  
==== =========

Information about the tasks
---------------------------
====================== ======= ======= ======= ======= =======
operation-duration     mean    stddev  min     max     outputs
SourceReader           0.98020 NaN     0.98020 0.98020 1      
build_hazard           0.00631 0.00197 0.00292 0.00877 12     
classical_split_filter 0.26262 0.51047 0.03246 2.00157 14     
====================== ======= ======= ======= ======= =======

Data transfer
-------------
====================== =============================================== ========
task                   sent                                            received
SourceReader                                                           16.38 KB
classical_split_filter srcs=28.52 KB params=10.84 KB srcfilter=3.05 KB 3.39 KB 
build_hazard           pgetter=5.78 KB hstats=780 B N=60 B             4.89 KB 
====================== =============================================== ========

Slowest operations
------------------
============================ ========= ========= ======
calc_43191                   time_sec  memory_mb counts
============================ ========= ========= ======
total classical_split_filter 3.67661   0.30469   14    
ClassicalCalculator.run      3.14681   1.59766   1     
splitting/filtering sources  1.57324   0.30469   14    
composite source model       0.99300   1.08984   1     
total SourceReader           0.98020   0.0       1     
make_contexts                0.96601   0.0       1_846 
iter_ruptures                0.66812   0.0       142   
computing mean_std           0.23476   0.0       1_613 
get_poes                     0.15729   0.0       1_613 
total build_hazard           0.07570   1.13672   12    
read PoEs                    0.06453   1.13672   12    
composing pnes               0.03641   0.0       1_613 
building riskinputs          0.02977   0.0       1     
saving statistics            0.00595   0.0       12    
store source_info            0.00244   0.0       1     
saving probability maps      0.00190   0.0       1     
compute stats                0.00144   0.0       9     
combine pmaps                7.813E-04 0.0       12    
reading exposure             4.954E-04 0.0       1     
aggregate curves             4.478E-04 0.0       2     
============================ ========= ========= ======