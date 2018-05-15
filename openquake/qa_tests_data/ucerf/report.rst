Ucerf test
==========

============== ===================
checksum32     2,080,369,829      
date           2018-05-15T04:12:41
engine_version 3.1.0-git0acbc11   
============== ===================

num_sites = 155, num_levels = 6

Parameters
----------
=============================== ==================
calculation_mode                'ucerf_rupture'   
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              200.0             
ses_per_logic_tree_path         1                 
truncation_level                None              
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                1.0               
area_source_discretization      None              
ground_motion_correlation_model None              
minimum_intensity               {'default': 0.1}  
random_seed                     1066              
master_seed                     0                 
ses_seed                        1066              
=============================== ==================

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
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
ltbr0001  0.00625 simple(2)       2/2             
ltbr0002  0.00625 simple(2)       2/2             
ltbr0003  0.05000 simple(2)       2/2             
ltbr0037  0.00625 simple(2)       2/2             
ltbr0038  0.00625 simple(2)       2/2             
ltbr0039  0.05000 simple(2)       2/2             
ltbr0541  0.01875 simple(2)       2/2             
ltbr0542  0.01875 simple(2)       2/2             
ltbr0543  0.15000 simple(2)       2/2             
ltbr0577  0.01875 simple(2)       2/2             
ltbr0578  0.01875 simple(2)       2/2             
ltbr0579  0.15000 simple(2)       2/2             
ltbr0721  0.00625 simple(2)       2/2             
ltbr0722  0.00625 simple(2)       2/2             
ltbr0723  0.05000 simple(2)       2/2             
ltbr0757  0.00625 simple(2)       2/2             
ltbr0758  0.00625 simple(2)       2/2             
ltbr0759  0.05000 simple(2)       2/2             
ltbr1261  0.01875 simple(2)       2/2             
ltbr1262  0.01875 simple(2)       2/2             
ltbr1263  0.15000 simple(2)       2/2             
ltbr1297  0.01875 simple(2)       2/2             
ltbr1298  0.01875 simple(2)       2/2             
ltbr1299  0.15000 simple(2)       2/2             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== =========== ======================= =======================
grp_id gsims                                 distances   siteparams              ruptparams             
====== ===================================== =========== ======================= =======================
0      AbrahamsonSilva2008() BooreEtAl2014() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
1      AbrahamsonSilva2008() BooreEtAl2014() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
2      AbrahamsonSilva2008() BooreEtAl2014() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
3      AbrahamsonSilva2008() BooreEtAl2014() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
4      AbrahamsonSilva2008() BooreEtAl2014() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
5      AbrahamsonSilva2008() BooreEtAl2014() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
6      AbrahamsonSilva2008() BooreEtAl2014() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
7      AbrahamsonSilva2008() BooreEtAl2014() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
8      AbrahamsonSilva2008() BooreEtAl2014() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
9      AbrahamsonSilva2008() BooreEtAl2014() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
10     AbrahamsonSilva2008() BooreEtAl2014() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
11     AbrahamsonSilva2008() BooreEtAl2014() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
12     AbrahamsonSilva2008() BooreEtAl2014() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
13     AbrahamsonSilva2008() BooreEtAl2014() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
14     AbrahamsonSilva2008() BooreEtAl2014() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
15     AbrahamsonSilva2008() BooreEtAl2014() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
16     AbrahamsonSilva2008() BooreEtAl2014() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
17     AbrahamsonSilva2008() BooreEtAl2014() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
18     AbrahamsonSilva2008() BooreEtAl2014() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
19     AbrahamsonSilva2008() BooreEtAl2014() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
20     AbrahamsonSilva2008() BooreEtAl2014() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
21     AbrahamsonSilva2008() BooreEtAl2014() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
22     AbrahamsonSilva2008() BooreEtAl2014() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
23     AbrahamsonSilva2008() BooreEtAl2014() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake width ztor
====== ===================================== =========== ======================= =======================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=48, rlzs=48)
  0,AbrahamsonSilva2008(): [0]
  0,BooreEtAl2014(): [1]
  1,AbrahamsonSilva2008(): [2]
  1,BooreEtAl2014(): [3]
  2,AbrahamsonSilva2008(): [4]
  2,BooreEtAl2014(): [5]
  3,AbrahamsonSilva2008(): [6]
  3,BooreEtAl2014(): [7]
  4,AbrahamsonSilva2008(): [8]
  4,BooreEtAl2014(): [9]
  5,AbrahamsonSilva2008(): [10]
  5,BooreEtAl2014(): [11]
  6,AbrahamsonSilva2008(): [12]
  6,BooreEtAl2014(): [13]
  7,AbrahamsonSilva2008(): [14]
  7,BooreEtAl2014(): [15]
  8,AbrahamsonSilva2008(): [16]
  8,BooreEtAl2014(): [17]
  9,AbrahamsonSilva2008(): [18]
  9,BooreEtAl2014(): [19]
  10,AbrahamsonSilva2008(): [20]
  10,BooreEtAl2014(): [21]
  11,AbrahamsonSilva2008(): [22]
  11,BooreEtAl2014(): [23]
  12,AbrahamsonSilva2008(): [24]
  12,BooreEtAl2014(): [25]
  13,AbrahamsonSilva2008(): [26]
  13,BooreEtAl2014(): [27]
  14,AbrahamsonSilva2008(): [28]
  14,BooreEtAl2014(): [29]
  15,AbrahamsonSilva2008(): [30]
  15,BooreEtAl2014(): [31]
  16,AbrahamsonSilva2008(): [32]
  16,BooreEtAl2014(): [33]
  17,AbrahamsonSilva2008(): [34]
  17,BooreEtAl2014(): [35]
  18,AbrahamsonSilva2008(): [36]
  18,BooreEtAl2014(): [37]
  19,AbrahamsonSilva2008(): [38]
  19,BooreEtAl2014(): [39]
  20,AbrahamsonSilva2008(): [40]
  20,BooreEtAl2014(): [41]
  21,AbrahamsonSilva2008(): [42]
  21,BooreEtAl2014(): [43]
  22,AbrahamsonSilva2008(): [44]
  22,BooreEtAl2014(): [45]
  23,AbrahamsonSilva2008(): [46]
  23,BooreEtAl2014(): [47]>

Slowest operations
------------------
======================= ======== ========= ======
operation               time_sec memory_mb counts
======================= ======== ========= ======
reading site collection 0.00106  0.0       1     
======================= ======== ========= ======