Classical Hazard QA Test, Case 21
=================================

============== ===================
checksum32     2,852,175,627      
date           2019-10-01T06:08:43
engine_version 3.8.0-gite0871b5c35
============== ===================

num_sites = 1, num_levels = 4, num_rlzs = 27

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                1.0               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     106               
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
====================== ======= =============== ================
smlt_path              weight  gsim_logic_tree num_realizations
====================== ======= =============== ================
b1_mfd1_high_dip_dip30 0.01320 trivial(1)      1               
b1_mfd1_high_dip_dip45 0.03960 trivial(1)      1               
b1_mfd1_high_dip_dip60 0.01320 trivial(1)      1               
b1_mfd1_low_dip_dip30  0.01320 trivial(1)      1               
b1_mfd1_low_dip_dip45  0.03960 trivial(1)      1               
b1_mfd1_low_dip_dip60  0.01320 trivial(1)      1               
b1_mfd1_mid_dip_dip30  0.03960 trivial(1)      1               
b1_mfd1_mid_dip_dip45  0.11880 trivial(1)      1               
b1_mfd1_mid_dip_dip60  0.03960 trivial(1)      1               
b1_mfd2_high_dip_dip30 0.01360 trivial(1)      1               
b1_mfd2_high_dip_dip45 0.04080 trivial(1)      1               
b1_mfd2_high_dip_dip60 0.01360 trivial(1)      1               
b1_mfd2_low_dip_dip30  0.01360 trivial(1)      1               
b1_mfd2_low_dip_dip45  0.04080 trivial(1)      1               
b1_mfd2_low_dip_dip60  0.01360 trivial(1)      1               
b1_mfd2_mid_dip_dip30  0.04080 trivial(1)      1               
b1_mfd2_mid_dip_dip45  0.12240 trivial(1)      1               
b1_mfd2_mid_dip_dip60  0.04080 trivial(1)      1               
b1_mfd3_high_dip_dip30 0.01320 trivial(1)      1               
b1_mfd3_high_dip_dip45 0.03960 trivial(1)      1               
b1_mfd3_high_dip_dip60 0.01320 trivial(1)      1               
b1_mfd3_low_dip_dip30  0.01320 trivial(1)      1               
b1_mfd3_low_dip_dip45  0.03960 trivial(1)      1               
b1_mfd3_low_dip_dip60  0.01320 trivial(1)      1               
b1_mfd3_mid_dip_dip30  0.03960 trivial(1)      1               
b1_mfd3_mid_dip_dip45  0.11880 trivial(1)      1               
b1_mfd3_mid_dip_dip60  0.03960 trivial(1)      1               
====================== ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================== ========= ========== ==========
grp_id gsims              distances siteparams ruptparams
====== ================== ========= ========== ==========
0      '[SadighEtAl1997]' rrup      vs30       mag rake  
1      '[SadighEtAl1997]' rrup      vs30       mag rake  
2      '[SadighEtAl1997]' rrup      vs30       mag rake  
3      '[SadighEtAl1997]' rrup      vs30       mag rake  
4      '[SadighEtAl1997]' rrup      vs30       mag rake  
5      '[SadighEtAl1997]' rrup      vs30       mag rake  
6      '[SadighEtAl1997]' rrup      vs30       mag rake  
7      '[SadighEtAl1997]' rrup      vs30       mag rake  
8      '[SadighEtAl1997]' rrup      vs30       mag rake  
9      '[SadighEtAl1997]' rrup      vs30       mag rake  
10     '[SadighEtAl1997]' rrup      vs30       mag rake  
11     '[SadighEtAl1997]' rrup      vs30       mag rake  
12     '[SadighEtAl1997]' rrup      vs30       mag rake  
13     '[SadighEtAl1997]' rrup      vs30       mag rake  
14     '[SadighEtAl1997]' rrup      vs30       mag rake  
15     '[SadighEtAl1997]' rrup      vs30       mag rake  
16     '[SadighEtAl1997]' rrup      vs30       mag rake  
17     '[SadighEtAl1997]' rrup      vs30       mag rake  
18     '[SadighEtAl1997]' rrup      vs30       mag rake  
19     '[SadighEtAl1997]' rrup      vs30       mag rake  
20     '[SadighEtAl1997]' rrup      vs30       mag rake  
21     '[SadighEtAl1997]' rrup      vs30       mag rake  
22     '[SadighEtAl1997]' rrup      vs30       mag rake  
23     '[SadighEtAl1997]' rrup      vs30       mag rake  
24     '[SadighEtAl1997]' rrup      vs30       mag rake  
25     '[SadighEtAl1997]' rrup      vs30       mag rake  
26     '[SadighEtAl1997]' rrup      vs30       mag rake  
====== ================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=27, rlzs=27)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      2.00000   444          444         
2      2.00000   208          208         
4      2.00000   149          149         
6      2.00000   534          534         
8      2.00000   298          298         
10     2.00000   239          239         
12     2.00000   474          474         
14     2.00000   238          238         
16     2.00000   179          179         
18     2.00000   409          409         
20     2.00000   173          173         
22     2.00000   114          114         
24     2.00000   465          465         
26     2.00000   229          229         
28     2.00000   170          170         
30     2.00000   411          411         
32     2.00000   175          175         
34     2.00000   116          116         
36     2.00000   483          483         
38     2.00000   247          247         
40     2.00000   188          188         
42     2.00000   582          582         
44     2.00000   346          346         
46     2.00000   287          287         
48     2.00000   516          516         
50     2.00000   280          280         
52     2.00000   221          221         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed  
========= ====== ==== ============ ========= ========= ============ =======
SFLT2     3      S    384          0.00876   1.00000   384          43,827 
SFLT2     11     S    89           0.00844   1.00000   89           10,539 
SFLT2     5      S    89           0.00797   1.00000   89           11,172 
SFLT2     22     S    148          0.00767   1.00000   148          19,289 
SFLT1     0      S    60           0.00687   1.00000   60           8,736  
SFLT2     6      S    384          0.00666   1.00000   384          57,672 
SFLT2     9      S    384          0.00536   1.00000   384          71,669 
SFLT1     16     S    27           0.00522   1.00000   27           5,176  
SFLT1     24     S    132          0.00516   1.00000   132          25,602 
SFLT2     26     S    89           0.00398   1.00000   89           22,366 
SFLT2     16     S    148          0.00342   1.00000   148          43,298 
SFLT2     19     S    148          0.00339   1.00000   148          43,663 
SFLT2     18     S    384          0.00323   1.00000   384          119,031
SFLT2     15     S    384          0.00312   1.00000   384          122,891
SFLT1     20     S    99           0.00312   1.00000   99           31,770 
SFLT1     3      S    150          0.00306   1.00000   150          49,045 
SFLT1     14     S    81           0.00301   1.00000   81           26,908 
SFLT1     25     S    132          0.00238   1.00000   132          55,398 
SFLT1     19     S    99           0.00238   1.00000   99           41,611 
SFLT1     15     S    27           0.00237   1.00000   27           11,387 
========= ====== ==== ============ ========= ========= ============ =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    0.15643   54    
==== ========= ======

Duplicated sources
------------------
Found 0 unique sources and 12 duplicate sources with multiplicity 4.5: ['SFLT1' 'SFLT1' 'SFLT1' 'SFLT1' 'SFLT1' 'SFLT1' 'SFLT1' 'SFLT1' 'SFLT1'
 'SFLT2' 'SFLT2' 'SFLT2']

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.06696 0.01258 0.05483 0.11272 27     
preclassical       0.01820 0.00369 0.01283 0.02551 9      
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ ================================================ ========
task         sent                                             received
SourceReader apply_unc=51.92 KB ltmodel=5.62 KB fname=2.56 KB 97 KB   
preclassical srcs=25.66 KB params=4.62 KB srcfilter=1.96 KB   5.05 KB 
============ ================================================ ========

Slowest operations
------------------
====================== ======== ========= ======
calc_23168             time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     1.80796  0.0       27    
composite source model 0.55327  0.0       1     
total preclassical     0.16380  0.0       9     
aggregate curves       0.00287  0.0       9     
store source_info      0.00236  0.0       1     
====================== ======== ========= ======