PEB QA test 2
=============

Datastore /home/michele/ssd/calc_10518.hdf5 last updated Tue Apr 19 05:56:40 2016 on gem-tstation

num_sites = 3, sitecol = 831 B

Parameters
----------
============================ ===================
calculation_mode             'event_based'      
number_of_logic_tree_samples 0                  
maximum_distance             {'default': 100.0} 
investigation_time           50.0               
ses_per_logic_tree_path      20                 
truncation_level             3.0                
rupture_mesh_spacing         5.0                
complex_fault_mesh_spacing   5.0                
width_of_mfd_bin             0.3                
area_source_discretization   10.0               
random_seed                  23                 
master_seed                  0                  
oqlite_version               '0.13.0-git7c9cf8e'
============================ ===================

Input files
-----------
======================== ==============================================================
Name                     File                                                          
======================== ==============================================================
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                  
job_ini                  `job_haz.ini <job_haz.ini>`_                                  
source                   `source_model.xml <source_model.xml>`_                        
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_  
structural_vulnerability `vulnerability_model_stco.xml <vulnerability_model_stco.xml>`_
======================== ==============================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1        1.000  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =============== =========== ======================= =================
trt_id gsims           distances   siteparams              ruptparams       
====== =============== =========== ======================= =================
0      ChiouYoungs2008 rx rjb rrup vs30measured vs30 z1pt0 rake dip ztor mag
====== =============== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008: ['<0,b1,b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     trt_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 3           8            0.450 
================ ====== ==================== =========== ============ ======

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
0            2         PointSource  0.150  1         7.415E-05   0.0        0.007    
0            1         PointSource  0.150  1         1.030E-04   0.0        0.006    
0            3         PointSource  0.150  1         7.892E-05   0.0        0.006    
============ ========= ============ ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_gmfs_and_curves  0.034     0.195     8     
total compute_ruptures         0.020     0.289     1     
compute poes                   0.018     0.0       8     
make contexts                  0.011     0.0       8     
saving gmfs                    0.006     0.0       8     
store source_info              0.005     0.0       1     
reading composite source model 0.004     0.0       1     
filtering ruptures             0.004     0.0       8     
saving ruptures                0.003     0.0       1     
managing sources               0.002     0.0       1     
aggregate curves               5.698E-04 0.0       1     
filtering sources              2.561E-04 0.0       3     
reading site collection        3.004E-05 0.0       1     
============================== ========= ========= ======