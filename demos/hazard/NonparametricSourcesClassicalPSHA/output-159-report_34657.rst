Classical PSHA with Non-parametric sources
==========================================

============== ===================
checksum32     1_077_220_430      
date           2020-02-14T10:49:01
engine_version 3.9.0-git64012a67b1
============== ===================

num_sites = 168, num_levels = 150, num_rlzs = 3

Parameters
----------
=============================== =================================================
calculation_mode                'classical'                                      
number_of_logic_tree_samples    0                                                
maximum_distance                {'default': 300.0, 'Subduction IntraSlab': 300.0}
investigation_time              1.0                                              
ses_per_logic_tree_path         1                                                
truncation_level                3.0                                              
rupture_mesh_spacing            5.0                                              
complex_fault_mesh_spacing      5.0                                              
width_of_mfd_bin                0.1                                              
area_source_discretization      None                                             
pointsource_distance            {'default': {}}                                  
ground_motion_correlation_model None                                             
minimum_intensity               {}                                               
random_seed                     23                                               
master_seed                     0                                                
ses_seed                        42                                               
=============================== =================================================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job-2019_np.ini <job-2019_np.ini>`_                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 simple(3)       3               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ==================================================================================== ========== ============ ==============
grp_id gsims                                                                                distances  siteparams   ruptparams    
====== ==================================================================================== ========== ============ ==============
0      '[AbrahamsonEtAl2015SSlab]' '[MontalvaEtAl2017SSlab]' '[ZhaoEtAl2006SSlabNSHMP2014]' rhypo rrup backarc vs30 hypo_depth mag
1      '[AbrahamsonEtAl2015SSlab]' '[MontalvaEtAl2017SSlab]' '[ZhaoEtAl2006SSlabNSHMP2014]' rhypo rrup backarc vs30 hypo_depth mag
2      '[AbrahamsonEtAl2015SSlab]' '[MontalvaEtAl2017SSlab]' '[ZhaoEtAl2006SSlabNSHMP2014]' rhypo rrup backarc vs30 hypo_depth mag
3      '[AbrahamsonEtAl2015SSlab]' '[MontalvaEtAl2017SSlab]' '[ZhaoEtAl2006SSlabNSHMP2014]' rhypo rrup backarc vs30 hypo_depth mag
4      '[AbrahamsonEtAl2015SSlab]' '[MontalvaEtAl2017SSlab]' '[ZhaoEtAl2006SSlabNSHMP2014]' rhypo rrup backarc vs30 hypo_depth mag
====== ==================================================================================== ========== ============ ==============

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=45, rlzs=3)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      153       631          631         
1      154       510          510         
2      155       431          431         
3      156       353          353         
4      157       282          282         
====== ========= ============ ============

Slowest sources
---------------
=============== ====== ==== ============ ========= ========= ============
source_id       grp_id code num_ruptures calc_time num_sites eff_ruptures
=============== ====== ==== ============ ========= ========= ============
src_col50_7pt05 0      N    631          4.80994   153       631         
src_col50_7pt15 1      N    510          3.99582   154       510         
src_col50_7pt25 2      N    431          3.47050   155       431         
src_col50_7pt35 3      N    353          2.87483   156       353         
src_col50_7pt45 4      N    282          2.36206   157       282         
=============== ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
N    17       
==== =========

Information about the tasks
---------------------------
====================== ======= ======= ======= ======= =======
operation-duration     mean    stddev  min     max     outputs
SourceReader           0.70333 0.08648 0.59828 0.81754 5      
build_hazard           0.02752 0.00408 0.02065 0.03268 24     
classical_split_filter 3.55430 0.96911 2.39933 4.88228 5      
====================== ======= ======= ======= ======= =======

Data transfer
-------------
====================== ============================================ =========
task                   sent                                         received 
SourceReader           apply_unc=6.56 KB ltmodel=1.2 KB fname=345 B 5.83 MB  
classical_split_filter srcs=4.7 MB params=10.55 KB gsims=2.08 KB    2.94 MB  
build_hazard           pgetter=12.98 KB hstats=1.52 KB N=336 B      229.73 KB
====================== ============================================ =========

Slowest operations
------------------
============================ ========= ========= ======
calc_34657                   time_sec  memory_mb counts
============================ ========= ========= ======
total classical_split_filter 17        32        5     
ClassicalCalculator.run      9.87013   29        1     
get_poes                     6.48093   0.0       2_207 
total SourceReader           3.51666   11        5     
computing mean_std           3.00722   0.0       2_207 
composing pnes               2.94267   0.0       2_207 
composite source model       2.08962   24        1     
total build_hazard           0.66060   3.35547   24    
make_contexts                0.62446   0.0       2_207 
read PoEs                    0.44657   3.28516   24    
splitting/filtering sources  0.22179   2.63672   5     
iter_ruptures                0.17400   0.0       2_207 
compute stats                0.13111   0.0       168   
saving statistics            0.08268   0.10156   24    
combine pmaps                0.06426   0.0       168   
saving probability maps      0.05638   0.00781   1     
store source_info            0.00833   6.34766   1     
aggregate curves             8.433E-04 0.00781   5     
============================ ========= ========= ======