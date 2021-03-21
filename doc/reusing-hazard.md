Reusing hazard across engine versions
=====================================

The OpenQuake engine has always had the capability to reuse old hazard
calculations when performing new risk calculations, thanks to the `--hc`
command-line option. However such capability never extended across
different versions of the engine. Here we will document the reasons
for such restriction.

Reusing the GMFs
----------------

While the `--hc` option works for all kind of calculations,
`classical_risk`, `classical_damage` and `classical_bcr` calculations are
less used: what is really important is to reuse the hazard for
scenario and for event based calculations, i.e. to reuse the GMFs.

Reusing the hazard for scenario calculations is relatively straighforward:
it is enough to keep the GMFs in CSV format and to start from there by
using the `gmfs_csv` option in the job.ini. This works across versions
already. The reason why this is simple is that the logic is trivial in
this case, the engine assumes that there is a single realization and
it automatically creates a fake logic tree object.

The difficulty is for event based calculations. The details of the
*logic tree* implementation change frequently. Therefore an apparently
simple question such as "tell me which GMPE was used when computing
the ground motion field for event number 123" is actually very hard to
answer across versions. This is by far the biggest difficulty, since
the logic tree part is expected to change again and in unpredictable
ways, due to the requests of the hazard team.

This not the only difficulty. When using the ``--hc`` option the engine
has also to match the risk sites with the hazard sites; this means
that it has to match a *SiteCollection* object coming from an old version
of the engine with a SiteCollection coming from a new version of the
engine. If the SiteCollection has changed (for instance new fields have
been added) this has to be managed in some way and this is not necessarily
always possible.

Moreover there is the *events* table which associates event IDs to
realization IDs and to rupture IDs; if the form of the events table
changes across versions (for instance if new fields are added) this
is an issue. Also, if the management of the logic tree changes and
the associations are different, starting a calculation from scratch
in the new version of the engine will give different results than
reusing an old hazard calculations.

The same would happen if the *weighting algorithm* of the realizations
changed (and this happened a couple of times in the past). Moreover at
nearly each release of the engine thedoc/reusing-hazard.md details of
the algorithm used to generate the ruptures and/or the *rupture seeds
changes*, therefore again starting a calculation from scratch in the
new version of the engine would give different results than reusing an
old hazard calculations.

Another difficulty would arise if the association between asset and
hazard sites changed, causing different losses to be computed. This
has not happened intentionally, but it has happened several times
unintentionally, since there is a tricky part. Bug fixes have change
the *asset<->site association* logic several times in the past.

Reusing an old *exposure* would also also be problematic,
assuming the new exposure had more fields. Changes to the exposure
happened several time in the past, so the problem is not academic.
The solution is to not reuse old exposure and to re-import the exposure
at each risk calculation, thus paying a performance penalty.

The same can be said for *vulnerability/fragility functions*: any
change there would make reusing them across versions very hard. Notice
that such change happened few months ago already. The solution is to
not reuse old risk models and to re-parse them at each new risk
calculation, thus paying a performance penalty.

In the future, it is expected that both the site collection and the events
table will be stored differently in the datastore, in a pandas-friendly
way, for consistency with the way many other objects are stored, and
also for memory efficiency. That means that work will be needed to be
able to read both the old and the new versions of such objects. This is
actually the least of the problems mentioned until now.

The elephant in the room
------------------------

We have not talked of the biggest issue of all: the sheer size of the
GMFs dataset. Reusing the GMFs is never going to be practical if we
need to store hundreds of GB of data. The only real solution for
commercial applications would be to store a reduced set of GMFs,
corresponding to a single effective realization, small but still
reproducing with decent accurary the mean results of the full
calculation. Then the risk part of the calculation would be like a
scenario starting from a CSV file.

We could even export three CSV files for the GMFs: one for the mean
field, one for a pessimistic case and one for an optimistic case, thus
allowing the users to explore alternative hazard scenarios.

Copying with the version-dependency
-----------------------------------

The fact that old hazard cannot be reused is a minor issue for GEM people,
since we are using the git version of the engine. Here is a workflow that
works.

1. First of all, run the hazard part of the calculation on a big remote machine
   which is at version X of the code.

2. The run on the user laptop the command `oq importcalc` to dowload the remote
calculation; here is an example:
```
$ oq importcalc 41214
INFO:root:POST https://oq2.wilson.openquake.org//accounts/ajax_login/
INFO:root:GET https://oq2.wilson.openquake.org//v1/calc/41214/extract/oqparam
INFO:root:Saving /home/michele/oqdata/calc_41214.hdf5
Downloaded 58,118,085 bytes
{'checksum32': 1949258781,
 'date': '2021-03-18T15:25:11',
 'engine_version': '3.12.0-gita399903317'}
INFO:root:Imported calculation 41214 successfully
```
3. Got to version X of the code so that the risk part of the calculation
can be done locally without issues:
```bash
$ git checkout a399903317
$ oq engine --run job.ini --hc 41214
```
That's it. This guarantees consistency and reproducibility, since both
parts of the calculation are performed with the same version of the code.
