Ucerf test
==========

gem-tstation:/home/michele/ssd/calc_19618.hdf5 updated Wed May 25 08:32:46 2016

num_sites = 1588, sitecol = 72.04 KB

Parameters
----------
============================ ===================
calculation_mode             'ucerf_event_based'
number_of_logic_tree_samples 0                  
maximum_distance             {'default': 200.0} 
investigation_time           10000.0            
ses_per_logic_tree_path      1                  
truncation_level             None               
rupture_mesh_spacing         1.0                
complex_fault_mesh_spacing   1.0                
width_of_mfd_bin             1.0                
area_source_discretization   None               
random_seed                  1066               
master_seed                  0                  
oqlite_version               '0.13.0-git1cc9966'
============================ ===================

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
ltbr0003  0.050  `ltbr0003 <ltbr0003>`_ trivial(0)      0/0             
ltbr0037  0.006  `ltbr0037 <ltbr0037>`_ trivial(0)      0/0             
ltbr0038  0.006  `ltbr0038 <ltbr0038>`_ trivial(0)      0/0             
ltbr0039  0.050  `ltbr0039 <ltbr0039>`_ trivial(0)      0/0             
ltbr0541  0.019  `ltbr0541 <ltbr0541>`_ trivial(0)      0/0             
ltbr0542  0.019  `ltbr0542 <ltbr0542>`_ trivial(0)      0/0             
ltbr0543  0.150  `ltbr0543 <ltbr0543>`_ trivial(0)      0/0             
ltbr0577  0.019  `ltbr0577 <ltbr0577>`_ trivial(0)      0/0             
ltbr0578  0.019  `ltbr0578 <ltbr0578>`_ trivial(0)      0/0             
ltbr0579  0.150  `ltbr0579 <ltbr0579>`_ trivial(0)      0/0             
ltbr0721  0.006  `ltbr0721 <ltbr0721>`_ trivial(0)      0/0             
ltbr0722  0.006  `ltbr0722 <ltbr0722>`_ trivial(0)      0/0             
ltbr0723  0.050  `ltbr0723 <ltbr0723>`_ trivial(0)      0/0             
ltbr0757  0.006  `ltbr0757 <ltbr0757>`_ trivial(0)      0/0             
ltbr0758  0.006  `ltbr0758 <ltbr0758>`_ trivial(0)      0/0             
ltbr0759  0.050  `ltbr0759 <ltbr0759>`_ trivial(0)      0/0             
ltbr1261  0.019  `ltbr1261 <ltbr1261>`_ trivial(0)      0/0             
ltbr1262  0.019  `ltbr1262 <ltbr1262>`_ trivial(0)      0/0             
ltbr1263  0.150  `ltbr1263 <ltbr1263>`_ trivial(0)      0/0             
ltbr1297  0.019  `ltbr1297 <ltbr1297>`_ trivial(0)      0/0             
ltbr1298  0.019  `ltbr1298 <ltbr1298>`_ trivial(0)      0/0             
ltbr1299  0.150  `ltbr1299 <ltbr1299>`_ trivial(0)      0/0             
========= ====== ====================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =============== ========= ========== ==========
trt_id gsims           distances siteparams ruptparams
====== =============== ========= ========== ==========
0      BooreEtAl2014() rjb       vs30       rake mag  
1      BooreEtAl2014() rjb       vs30       rake mag  
====== =============== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,BooreEtAl2014(): ['<0,ltbr0001,BSSA14,w=0.5>']
  1,BooreEtAl2014(): ['<1,ltbr0002,BSSA14,w=0.5>']>

Number of ruptures per tectonic region type
-------------------------------------------
============ ====== ==================== =========== ============ ======
source_model trt_id trt                  num_sources eff_ruptures weight
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
======== ==============
hostname 'gem-tstation'
======== ==============

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            ltbr0542  UcerfBranch  1.000  0         0.0         0.0        4.531    
1            ltbr0037  UcerfBranch  1.000  0         0.0         0.0        4.422    
0            ltbr0757  UcerfBranch  1.000  0         0.0         0.0        4.460    
1            ltbr0039  UcerfBranch  1.000  0         0.0         0.0        4.479    
0            ltbr0003  UcerfBranch  1.000  0         0.0         0.0        4.546    
1            ltbr1298  UcerfBranch  1.000  0         0.0         0.0        4.432    
0            ltbr1297  UcerfBranch  1.000  0         0.0         0.0        4.559    
1            ltbr0543  UcerfBranch  1.000  0         0.0         0.0        4.491    
0            ltbr0758  UcerfBranch  1.000  0         0.0         0.0        4.575    
1            ltbr0759  UcerfBranch  1.000  0         0.0         0.0        4.472    
0            ltbr0577  UcerfBranch  1.000  0         0.0         0.0        4.622    
1            ltbr0578  UcerfBranch  1.000  0         0.0         0.0        4.437    
0            ltbr0579  UcerfBranch  1.000  0         0.0         0.0        4.527    
1            ltbr0721  UcerfBranch  1.000  0         0.0         0.0        4.520    
0            ltbr1299  UcerfBranch  1.000  0         0.0         0.0        4.589    
1            ltbr0541  UcerfBranch  1.000  0         0.0         0.0        4.497    
0            ltbr0723  UcerfBranch  1.000  0         0.0         0.0        4.576    
1            ltbr0722  UcerfBranch  1.000  0         0.0         0.0        4.516    
0            ltbr0001  UcerfBranch  1.000  0         0.0         0.0        4.529    
1            ltbr0002  UcerfBranch  1.000  0         0.0         0.0        4.547    
============ ========= ============ ====== ========= =========== ========== =========

Computation times by source typology
------------------------------------
============ =========== ========== ========= ======
source_class filter_time split_time calc_time counts
============ =========== ========== ========= ======
UcerfBranch  0.0         0.0        106       24    
============ =========== ========== ========= ======

Information about the tasks
---------------------------
================================= ===== ====== ===== ===== =========
measurement                       mean  stddev min   max   num_tasks
compute_ruptures.time_sec         8.916 0.280  8.289 9.093 12       
compute_ruptures.memory_mb        58    24     6.086 69    12       
compute_gmfs_and_curves.time_sec  0.729 0.361  0.069 1.414 22       
compute_gmfs_and_curves.memory_mb 0.042 0.107  -0.25 0.234 22       
================================= ===== ====== ===== ===== =========

Slowest operations
------------------
============================= ======== ========= ======
operation                     time_sec memory_mb counts
============================= ======== ========= ======
total compute_ruptures        106      69        12    
sampling ruptures             46       0.0       24    
saving ruptures               31       0.0       1     
update_background_site_filter 23       0.0       24    
total compute_gmfs_and_curves 16       0.234     22    
make contexts                 8.460    0.0       5,626 
compute poes                  7.470    0.0       5,626 
saving gmfs                   0.018    0.0       22    
============================= ======== ========= ======