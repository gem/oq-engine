Scenario QA Test with AtkinsonBoore2003SInter
=============================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_66944.hdf5 Wed Nov  9 08:14:05 2016
engine_version                                 2.2.0-git54d01f4        
hazardlib_version                              0.22.0-git173c60c       
============================================== ========================

num_sites = 2, sitecol = 785 B

Parameters
----------
============================ =================
calculation_mode             'scenario'       
number_of_logic_tree_samples 0                
maximum_distance             {u'default': 200}
investigation_time           None             
ses_per_logic_tree_path      1                
truncation_level             None             
rupture_mesh_spacing         1.0              
complex_fault_mesh_spacing   1.0              
width_of_mfd_bin             None             
area_source_discretization   None             
random_seed                  3                
master_seed                  0                
============================ =================

Input files
-----------
============= ========================================
Name          File                                    
============= ========================================
job_ini       `job.ini <job.ini>`_                    
rupture_model `rupture_model.xml <rupture_model.xml>`_
============= ========================================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,AtkinsonBoore2003SInter(): ['<0,b_1~b1,w=1.0>']>

Slowest operations
------------------
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
filtering sites         0.007     0.0       1     
reading site collection 2.599E-05 0.0       1     
======================= ========= ========= ======