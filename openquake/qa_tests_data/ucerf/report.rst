Ucerf test
==========

gem-tstation:/home/michele/ssd/calc_22543.hdf5 updated Tue May 31 15:36:57 2016

num_sites = 1588, sitecol = 72.04 KB

Parameters
----------
============================ ===============================
calculation_mode             'ucerf_event_based'            
number_of_logic_tree_samples 0                              
maximum_distance             {'Active Shallow Crust': 200.0}
investigation_time           10000.0                        
ses_per_logic_tree_path      1                              
truncation_level             None                           
rupture_mesh_spacing         1.0                            
complex_fault_mesh_spacing   1.0                            
width_of_mfd_bin             1.0                            
area_source_discretization   None                           
random_seed                  1066                           
master_seed                  0                              
engine_version               '2.0.0-git4fb4450'             
============================ ===============================

Input files
-----------
======================= ====================================================================
Name                    File                                                                
======================= ====================================================================
gsim_logic_tree         `gmpe_logic_tree_ucerf_mean.xml <gmpe_logic_tree_ucerf_mean.xml>`_  
job_ini                 `job.ini <job.ini>`_                                                
sites                   `bay_area.csv <bay_area.csv>`_                                      
source_model            `dummy_ucerf_bg_source_redux.xml <dummy_ucerf_bg_source_redux.xml>`_
source_model_logic_tree `dummy_ucerf_smlt_redux.xml <dummy_ucerf_smlt_redux.xml>`_          
======================= ====================================================================

Composite source model
----------------------
========= ====== ====================== =============== ================
smlt_path weight source_model_file      gsim_logic_tree num_realizations
========= ====== ====================== =============== ================
ltbr0001  0.006  `ltbr0001 <ltbr0001>`_ trivial(1)      1/1             
ltbr0002  0.006  `ltbr0002 <ltbr0002>`_ trivial(1)      1/1             
ltbr0003  0.050  `ltbr0003 <ltbr0003>`_ trivial(1)      0/0             
ltbr0037  0.006  `ltbr0037 <ltbr0037>`_ trivial(1)      0/0             
ltbr0038  0.006  `ltbr0038 <ltbr0038>`_ trivial(1)      0/0             
ltbr0039  0.050  `ltbr0039 <ltbr0039>`_ trivial(1)      0/0             
ltbr0541  0.019  `ltbr0541 <ltbr0541>`_ trivial(1)      0/0             
ltbr0542  0.019  `ltbr0542 <ltbr0542>`_ trivial(1)      0/0             
ltbr0543  0.150  `ltbr0543 <ltbr0543>`_ trivial(1)      0/0             
ltbr0577  0.019  `ltbr0577 <ltbr0577>`_ trivial(1)      0/0             
ltbr0578  0.019  `ltbr0578 <ltbr0578>`_ trivial(1)      0/0             
ltbr0579  0.150  `ltbr0579 <ltbr0579>`_ trivial(1)      0/0             
ltbr0721  0.006  `ltbr0721 <ltbr0721>`_ trivial(1)      0/0             
ltbr0722  0.006  `ltbr0722 <ltbr0722>`_ trivial(1)      0/0             
ltbr0723  0.050  `ltbr0723 <ltbr0723>`_ trivial(1)      0/0             
ltbr0757  0.006  `ltbr0757 <ltbr0757>`_ trivial(1)      0/0             
ltbr0758  0.006  `ltbr0758 <ltbr0758>`_ trivial(1)      0/0             
ltbr0759  0.050  `ltbr0759 <ltbr0759>`_ trivial(1)      0/0             
ltbr1261  0.019  `ltbr1261 <ltbr1261>`_ trivial(1)      0/0             
ltbr1262  0.019  `ltbr1262 <ltbr1262>`_ trivial(1)      0/0             
ltbr1263  0.150  `ltbr1263 <ltbr1263>`_ trivial(1)      0/0             
ltbr1297  0.019  `ltbr1297 <ltbr1297>`_ trivial(1)      0/0             
ltbr1298  0.019  `ltbr1298 <ltbr1298>`_ trivial(1)      0/0             
ltbr1299  0.150  `ltbr1299 <ltbr1299>`_ trivial(1)      0/0             
========= ====== ====================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =============== ========= ========== ==========
grp_id gsims           distances siteparams ruptparams
====== =============== ========= ========== ==========
0      BooreEtAl2014() rjb       vs30       rake mag  
1      BooreEtAl2014() rjb       vs30       rake mag  
====== =============== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,BooreEtAl2014(): ['<0,ltbr0001~BSSA14,w=0.5>']
  1,BooreEtAl2014(): ['<1,ltbr0002~BSSA14,w=0.5>']>

Number of ruptures per tectonic region type
-------------------------------------------
============ ====== ==================== =========== ============ ======
source_model grp_id trt                  num_sources eff_ruptures weight
============ ====== ==================== =========== ============ ======
ltbr0001     0      Active Shallow Crust 12          33646        12    
ltbr0002     1      Active Shallow Crust 12          33686        12    
============ ====== ==================== =========== ============ ======

=============== ======
#TRT models     2     
#sources        24    
#eff_ruptures   67,332
filtered_weight 24    
=============== ======

Informational data
------------------
======== ============
hostname gem-tstation
======== ============

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
src_group_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            ltbr0723  type         1.000  1         0.0         0.0        4.328    
1            ltbr0722  type         1.000  1         0.0         0.0        4.417    
0            ltbr0542  type         1.000  1         0.0         0.0        4.395    
1            ltbr0037  type         1.000  1         0.0         0.0        4.372    
0            ltbr0757  type         1.000  1         0.0         0.0        4.368    
1            ltbr0039  type         1.000  1         0.0         0.0        4.388    
0            ltbr1299  type         1.000  1         0.0         0.0        4.425    
1            ltbr0541  type         1.000  1         0.0         0.0        4.377    
0            ltbr0758  type         1.000  1         0.0         0.0        4.523    
1            ltbr0759  type         1.000  1         0.0         0.0        4.364    
0            ltbr0577  type         1.000  1         0.0         0.0        4.525    
1            ltbr0578  type         1.000  1         0.0         0.0        4.409    
0            ltbr0579  type         1.000  1         0.0         0.0        4.474    
1            ltbr0721  type         1.000  1         0.0         0.0        4.464    
0            ltbr0003  type         1.000  1         0.0         0.0        4.553    
1            ltbr1298  type         1.000  1         0.0         0.0        4.401    
0            ltbr0001  type         1.000  1         0.0         0.0        4.527    
1            ltbr0002  type         1.000  1         0.0         0.0        4.440    
0            ltbr1297  type         1.000  1         0.0         0.0        4.558    
1            ltbr0543  type         1.000  1         0.0         0.0        4.486    
============ ========= ============ ====== ========= =========== ========== =========

Computation times by source typology
------------------------------------
============ =========== ========== ========= ======
source_class filter_time split_time calc_time counts
============ =========== ========== ========= ======
type         0.0         0.0        105       24    
============ =========== ========== ========= ======

Information about the tasks
---------------------------
================================= ===== ====== ========== ===== =========
measurement                       mean  stddev min        max   num_tasks
compute_ruptures.time_sec         8.811 0.190  8.443      9.046 12       
compute_ruptures.memory_mb        55    33     -33.109375 69    12       
compute_gmfs_and_curves.time_sec  0.713 0.365  0.091      1.390 22       
compute_gmfs_and_curves.memory_mb 0.067 0.105  0.0        0.254 22       
================================= ===== ====== ========== ===== =========

Slowest operations
------------------
============================= ======== ========= ======
operation                     time_sec memory_mb counts
============================= ======== ========= ======
total compute_ruptures        105      69        12    
sampling ruptures             46       0.0       24    
saving ruptures               33       0.0       1     
update_background_site_filter 22       0.0       24    
total compute_gmfs_and_curves 15       0.254     22    
make contexts                 8.343    0.0       5,626 
compute poes                  7.233    0.0       5,626 
saving gmfs                   0.016    0.0       22    
============================= ======== ========= ======