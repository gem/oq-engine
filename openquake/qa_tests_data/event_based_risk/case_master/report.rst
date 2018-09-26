event based risk
================

============== ===================
checksum32     571,516,522        
date           2018-09-25T14:28:24
engine_version 3.3.0-git8ffb37de56
============== ===================

num_sites = 7, num_levels = 46

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         10                
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model 'JB2009'          
minimum_intensity               {}                
random_seed                     24                
master_seed                     0                 
ses_seed                        42                
avg_losses                      True              
=============================== ==================

Input files
-----------
=================================== ================================================================================
Name                                File                                                                            
=================================== ================================================================================
business_interruption_vulnerability `downtime_vulnerability_model.xml <downtime_vulnerability_model.xml>`_          
contents_vulnerability              `contents_vulnerability_model.xml <contents_vulnerability_model.xml>`_          
exposure                            `exposure_model.xml <exposure_model.xml>`_                                      
gsim_logic_tree                     `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                                    
job_ini                             `job.ini <job.ini>`_                                                            
nonstructural_vulnerability         `nonstructural_vulnerability_model.xml <nonstructural_vulnerability_model.xml>`_
occupants_vulnerability             `occupants_vulnerability_model.xml <occupants_vulnerability_model.xml>`_        
source                              `6.05.hdf5 <6.05.hdf5>`_                                                        
source                              `source_model_1.xml <source_model_1.xml>`_                                      
source                              `source_model_2.xml <source_model_2.xml>`_                                      
source_model_logic_tree             `source_model_logic_tree.xml <source_model_logic_tree.xml>`_                    
structural_vulnerability            `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_      
=================================== ================================================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        0.25000 complex(2,2,1)  4/4             
b2        0.25000 complex(2,2,1)  4/4             
b3        0.50000 complex(2,2,1)  1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== =========== ======================= =================
grp_id gsims                                 distances   siteparams              ruptparams       
====== ===================================== =========== ======================= =================
0      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      AkkarBommer2010() ChiouYoungs2008()   rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
3      AkkarBommer2010() ChiouYoungs2008()   rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
4      MontalvaEtAl2016SSlab()               rhypo rrup  backarc vs30            hypo_depth mag   
====== ===================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=9, rlzs=9)
  0,BooreAtkinson2008(): [0 1]
  0,ChiouYoungs2008(): [2 3]
  1,AkkarBommer2010(): [0 2]
  1,ChiouYoungs2008(): [1 3]
  2,BooreAtkinson2008(): [4 5]
  2,ChiouYoungs2008(): [6 7]
  3,AkkarBommer2010(): [4 6]
  3,ChiouYoungs2008(): [5 7]
  4,MontalvaEtAl2016SSlab(): [8]>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== ============ ============
source_model       grp_id trt                  eff_ruptures tot_ruptures
================== ====== ==================== ============ ============
source_model_1.xml 0      Active Shallow Crust 482          482         
source_model_1.xml 1      Stable Shallow Crust 4            4           
source_model_2.xml 2      Active Shallow Crust 482          482         
source_model_2.xml 3      Stable Shallow Crust 1            1           
6.05.hdf5          4      Deep Seismicity      2            2           
================== ====== ==================== ============ ============

============= ===
#TRT models   5  
#eff_ruptures 971
#tot_ruptures 971
#tot_weight   0  
============= ===

Estimated data transfer for the avglosses
-----------------------------------------
7 asset(s) x 9 realization(s) x 5 loss type(s) x 2 losses x 8 bytes x 60 tasks = 295.31 KB

Exposure model
--------------
=============== ========
#assets         7       
#taxonomies     3       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
tax1     1.00000 0.0    1   1   4         4         
tax2     1.00000 0.0    1   1   2         2         
tax3     1.00000 NaN    1   1   1         1         
*ALL*    1.00000 0.0    1   1   7         7         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight 
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
0      1         S    0     2     482          0.25616   0.00559    105       15        0.0    
1      2         S    2     4     4            0.02190   1.884E-05  7.00000   1         9.00000
2      1         S    0     2     482          0.21190   0.00457    105       15        1.00000
3      2         X    2     398   1            2.816E-04 5.960E-06  7.00000   1         0.0    
4      buc06pt05 N    0     24    2            0.00128   7.153E-05  14        2         1.00000
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
N    0.00128   1     
S    0.48996   3     
X    2.816E-04 1     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
read_source_models 0.01221 0.00529 0.00739 0.01786 3        
split_filter       0.04204 NaN     0.04204 0.04204 1        
build_ruptures     0.01935 0.01002 0.00277 0.03899 31       
compute_gmfs       0.03481 0.02429 0.01506 0.06193 3        
================== ======= ======= ======= ======= =========

Data transfer
-------------
================== ================================================================================================= ========
task               sent                                                                                              received
read_source_models monitor=1.08 KB converter=957 B fnames=576 B                                                      16.3 KB 
split_filter       srcs=17.88 KB monitor=381 B srcfilter=220 B sample_factor=21 B seed=14 B                          26.49 KB
build_ruptures     srcs=54.8 KB param=19.38 KB monitor=11.59 KB srcfilter=6.66 KB                                    68.49 KB
compute_gmfs       param=17.02 KB sources_or_ruptures=13.71 KB rlzs_by_gsim=1.12 KB monitor=1.01 KB src_filter=660 B 57.41 KB
================== ================================================================================================= ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total build_ruptures     0.59990   0.0       31    
total compute_gmfs       0.10442   0.25391   3     
building hazard          0.07452   0.06250   3     
updating source_info     0.05210   0.0       1     
total split_filter       0.04204   0.0       1     
total read_source_models 0.03664   0.22266   3     
making contexts          0.01865   0.0       6     
building riskinputs      0.01751   0.0       1     
building hazard curves   0.01660   0.0       63    
saving ruptures          0.00818   0.0       3     
saving gmfs              0.00796   0.0       3     
building ruptures        0.00778   0.0       3     
store source_info        0.00684   0.0       1     
managing sources         0.00453   0.0       1     
saving gmf_data/indices  0.00439   0.0       1     
aggregating hcurves      0.00427   0.0       3     
GmfGetter.init           0.00252   0.21094   3     
setting event years      0.00163   0.0       1     
reading exposure         7.741E-04 0.0       1     
======================== ========= ========= ======