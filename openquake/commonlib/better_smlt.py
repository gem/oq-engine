# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
"""
Move the MFD variants of a source model logic tree into the logic tree.

A source with the same ID and the same geometry can appear in several
source model files with different MFDs (see the warning emitted by
source_reader.check_mfd_variants); then each copy is computed separately.
A branchset whose branches load copies of the same sources differing only
in the MFDs is collapsed into a single branch loading the files of its
first branch, followed by a branchset with the original branches and
weights setting the MFDs: then the source model files of the other
branches are not needed anymore (with 100 variants the source model
files are 100 times smaller). Two branches with the same MFDs would be
duplicated, so such a branchset is not collapsed.

For the other branchsets this module rewrites the copies so that they all
have the same (base) MFD, which makes them identical, and adds after the
branchset loading each copy a chain of single-branch branchsets restoring
the original MFDs in the branch, one for each kind of MFD (and for each of
the uncertainties below). A branchset with a single source uses applyToSources="<source ID>",
otherwise it is a correlated branchset (applyToSources="*") with a
<correlated> element for each source:

- truncGutenbergRichterMFD -> abMaxMagAbsolute "a b maxMag", if they are
  different, followed by minMagGRAbsolute "minMag", if the minMag are
  different
- incrementalMFD -> incrementalMFDAbsolute
- multiMFD -> multiMFDAbsolute (the copies must have the same number of
  points)

The identical copies are then merged by the engine (see reduce_sources)
and the contexts are computed once for all the MFDs. The references to a
modified branch in the applyToBranches of the following branchsets are
replaced by the last branch of its chain. A branch without variants gets
an identity link (setting the MFD of a source to itself), so that every
branch has a chain. A source is skipped if a branchset modifying it comes
before the branchset loading it, since the absolute MFD must be applied
first. The copies of a source are recognized by their ID and geometry,
compared ignoring the formatting of the XML. Sources sharing an ID in a
file and fragments of sources (colon
convention, except in mutex groups) are renamed, since applyToSources
could not select them; branch IDs with spaces are renamed too, since
applyToBranches could not refer to them. Sources with different IDs are
not converted (they are not recognized as copies of the same source).

The input files are never modified. The result is a file job.zip, in the
folder of the job.ini, with a copy of the job using the converted logic
tree, with the original file names (it replaces an existing job.zip). It
is built in 3 steps:

1. the converted logic tree and the rewritten source model files are
   written in a temporary folder;
2. the job is zipped with them in place of the original files, leaving
   out the source model files not referenced anymore;
3. the original job and the converted one (the job extracted from the
   archive, so that a missing file is an error) are compared by applying
   the uncertainties with the engine in each realization (with full
   enumeration of the source model paths): the annual occurrence rates of
   all the sources must be the same. If the check is successful the
   archive is saved as job.zip, else it is left in job_mfd.zip to be
   inspected and job.zip is not touched.

NB: the equivalence concerns the rates of the sources, not the numerical
approximations of the calculation. With ps_grid_spacing the point sources
are collapsed into averages weighted by their rates (see calc_average in
source/point.py), so the hazard of the converted job can differ slightly
from the original one: in KOR with ps_grid_spacing=50 the hazard curves
differ by up to 1% at the lowest intensity levels, while without
ps_grid_spacing the difference is at the level of the numerical noise
(about 1E-5, like the difference between two runs of the original job with
a different number of tasks).

Use it with `oq check_input --better-smlt job.ini`.
"""
import os
import copy
import re
import tempfile
import textwrap
import hashlib
import logging
import operator
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
from contextlib import closing
from openquake.baselib.general import duplicated, groupby
from openquake.baselib.node import striptag
from openquake.baselib.parallel import Starmap
from openquake.hazardlib import valid, logictree
from openquake.hazardlib.logictree import SourceModelLogicTree, branch_id
from openquake.hazardlib.source_reader import (
    modified_groups, get_bset_values, TWO24, MFD_UNCERTAINTY)
from openquake.commonlib import datastore, oqvalidation, readinput

MFD_TAGS = {'truncGutenbergRichterMFD', 'incrementalMFD', 'multiMFD',
            'arbitraryMFD', 'YoungsCoppersmithMFD',
            'taperedGutenbergRichterMFD'}
# minMag is a pseudo-kind, see _link_copies
UTYPE = dict(MFD_UNCERTAINTY, minMag='minMagGRAbsolute')
LINE_WIDTH = 120  # maximum length of the lines of the multiMFD arrays
SM_TYPES = ('sourceModel', 'extendModel')
HASH_MASK = 2 ** 64 - 1  # the hashes of the rates are 64 bit integers
BRANCH_ID_RE = re.compile(valid.branch_id.regex)


def _read_xml(path):
    # retain comments and processing instructions when rewriting a file
    parser = ET.XMLParser(target=ET.TreeBuilder(
        insert_comments=True, insert_pis=True))
    return ET.parse(path, parser=parser).getroot()


def _write_xml(root, path):
    # use the document's namespace and wrap multiMFD arrays to LINE_WIDTH
    if root.tag.startswith('{'):
        ET.register_namespace('', root.tag[1:].split('}')[0])
    ET.register_namespace('gml', 'http://www.opengis.net/gml')
    ET.indent(root, space='    ')
    for mfd in root.iter():
        if isinstance(mfd.tag, str) and striptag(mfd.tag) == 'multiMFD':
            ind = (mfd.text or '\n    ').rsplit('\n', 1)[-1]
            for child in mfd:
                if not isinstance(child.tag, str):
                    continue
                values = ' '.join((child.text or '').split())
                child.text = ('\n' + textwrap.fill(
                    values, width=LINE_WIDTH, initial_indent=ind + '    ',
                    subsequent_indent=ind + '    ') + '\n' + ind)
    ET.ElementTree(root).write(path, encoding='utf-8', xml_declaration=True)


class BranchSet:
    def __init__(self, ordinal, el, parents):
        self.ordinal = ordinal
        self.el = el
        self.in_level = striptag(parents[el].tag) == 'logicTreeBranchingLevel'
        self.container = parents[el] if self.in_level else el
        self.parent = parents[self.container]
        self.id = el.attrib['branchSetID']
        self.utype = el.attrib['uncertaintyType']
        self.atb = el.attrib.get('applyToBranches', '').split()
        self.ats = el.attrib.get('applyToSources', '').split()
        self.branches = []
        for br in el.findall('{*}logicTreeBranch'):
            um = br.find('{*}uncertaintyModel')
            # Comments split a file list between text and child tails.
            value = (um.text or '') + ''.join(c.tail or '' for c in um)
            self.branches.append((br.attrib['branchID'], value.strip()))

    def files(self, branch_id):
        # the source model files of a branch, as written in the tree
        return (dict(self.branches)[branch_id].split()
                if self.utype in SM_TYPES else [])


def read_tree(smlt):
    # the branchsets in document order, with their insertion points
    root = _read_xml(smlt)
    parents = {c: p for p in root.iter() for c in p}
    bsets = [BranchSet(i, el, parents) for i, el in enumerate(
        root.findall('.//{*}logicTreeBranchSet'))]
    return root, bsets


def _canonical(el):
    # the content of an element, ignoring the order of the attributes and
    # the formatting, i.e. the whitespace in the texts and between elements
    return tuple((striptag(e.tag), tuple(sorted(e.attrib.items())),
                  ' '.join((e.text or '').split())) for e in el.iter())


class Copy:
    # a copy of a source in a source model file; pos is the index of the
    # source in the file (in document order), used to rename it
    def __init__(self, fname, pos, el, group):
        self.fname = fname
        self.pos = pos
        self.id = el.attrib['id']
        mfds = [c for c in el if striptag(c.tag) in MFD_TAGS]
        mfd = mfds[0] if mfds else None
        self.mfd = mfd
        self.kind = striptag(mfd.tag) if mfd is not None else None
        # the geometry, i.e. the content without the name and the MFD
        attrs = {k: v for k, v in el.attrib.items() if k != 'name'}
        geom = hashlib.md5(repr(sorted(attrs.items())).encode())
        for c in el:
            if striptag(c.tag) not in MFD_TAGS:
                geom.update(repr(_canonical(c)).encode())
        self.key = (self.id, repr(sorted(group.items())), geom.hexdigest())
        self.params = self.get_params(mfd)

    def get_params(self, mfd):
        # compare the original strings, ignoring the formatting
        if mfd is None:
            return ()
        if self.kind == 'truncGutenbergRichterMFD':
            return tuple(mfd.attrib[k] for k in
                         ('aValue', 'bValue', 'maxMag', 'minMag'))
        return _canonical(mfd)


def parse_copies(idx, path, fname):
    """
    Task reading the copies of the sources in a source model file.

    :returns: a dictionary {idx: copies}
    """
    root = ET.parse(path).getroot()
    parents = {c: p for p in root.iter() for c in p}
    sources = (el for el in root.iter()
               if el.tag.endswith('Source') and 'id' in el.attrib)
    return {idx: [Copy(fname, pos, el, parents[el].attrib if
                       striptag(parents[el].tag) == 'sourceGroup' else {})
                  for pos, el in enumerate(sources)]}


def read_copies(smlt_dir, fnames):
    """
    Read all source copies in parallel, preserving file and document order
    (the identity links reuse these copies).
    """
    allargs = [(i, smlt_dir / f, f) for i, f in enumerate(fnames)]
    bypos = Starmap(parse_copies, allargs).reduce(
        agg=lambda acc, dic: acc.update(dic) or acc, acc={})
    return [cp for i in sorted(bypos) for cp in bypos[i]]


def _group(copies, attr='key'):
    # group by (source ID, source group, geometry), or another attribute,
    # preserving document order (which determines the renamed IDs)
    return groupby(copies, operator.attrgetter(attr), sort=False)


def _has_variants(copies):
    # True if the copies are in different files with different MFDs
    return (len({cp.fname for cp in copies}) > 1 and
            len({cp.params for cp in copies}) > 1)


def rename_duplicates(copies):
    """
    Give a different ID to the sources sharing an ID in the same file,
    when they have MFD variants, since applyToSources could not select
    one of them: the sources with the same geometry get the same new ID
    (<ID>_<n>) in all the files, so that the copies can be merged.

    :returns: a dictionary new ID -> old ID
    """
    dupl = {srcid for _, srcid in duplicated(
        (cp.fname, cp.id) for cp in copies)}
    groups = _group(copies)
    variant = {key[0] for key, cps in groups.items() if _has_variants(cps)}
    # the fragments (colon convention) are seen by the logic tree with
    # their base name, so they are renamed too, except in mutex groups
    frags = {key[0] for key in groups if ':' in key[0] and
             "'mutex'" not in key[1]}
    dupl = (dupl | frags) & variant
    nkeys = Counter(key[0] for key in groups)
    used = {cp.id for cp in copies}
    newid, renamed = {}, {}  # (old ID, group, geometry) -> new ID
    nseg = {}  # old ID -> number of segments
    for cp in copies:
        if cp.id not in dupl:
            continue
        if cp.key not in newid:
            nseg[cp.id] = n = nseg.get(cp.id, 0) + 1
            base = cp.id.replace(':', '_')
            new = base if ':' in cp.id and nkeys[cp.id] == 1 else \
                f'{base}_{n}'
            while new in used:
                new += '_'
            used.add(new)
            newid[cp.key] = new
            renamed[new] = cp.id
        cp.id = newid[cp.key]
        cp.key = (cp.id,) + cp.key[1:]
    return renamed


def _skip_reason(copies, bsets, carriers, renamed):
    # the reason why a group of MFD variants cannot be converted, or None
    kinds = {cp.kind for cp in copies}
    src = copies[0].id
    if ':' in src:  # the logic tree sees only the base name
        return 'fragment of a source (colon convention)'
    if len(kinds) > 1 or kinds - set(UTYPE):
        return f'MFD types {sorted(map(str, kinds))}'
    if kinds == {'multiMFD'} and len({(cp.mfd.get('kind'), cp.mfd.get('size'))
                                      for cp in copies}) > 1:
        return 'different kind or number of points'
    # the absolute MFD must be applied before the other uncertainties
    old = renamed.get(src, src)
    first = min(o for cp in copies for o, _ in carriers[cp.fname])
    before = [bs.id for bs in bsets[:first] if bs.utype not in SM_TYPES
              and (not bs.ats or '*' in bs.ats or old in bs.ats or
                   old.split(':')[0] in bs.ats)]
    if before:
        return f'modified before by {before}'
    return None


def find_variants(copies, bsets, carriers, renamed):
    """
    :returns: the groups of copies of the same source (same ID, group and
              geometry) with different MFDs in different files that can be
              converted, and the list of (source ID, reason) of the others
    """
    variants, skipped = [], []
    for cps in _group(copies).values():
        if _has_variants(cps):
            reason = _skip_reason(cps, bsets, carriers, renamed)
            if reason:
                skipped.append((cps[0].id, reason))
            else:
                variants.append(cps)
    return variants, skipped


def _sub(parent, tag, **attrs):
    # create a child in the same namespace as its parent
    namespace = parent.tag.rpartition('}')[0] + '}' if \
        parent.tag.startswith('{') else ''
    return ET.SubElement(parent, namespace + tag, attrs)


def _set_value(node, cp):
    # write the absolute uncertainty using the original MFD element
    if cp.kind == 'truncGutenbergRichterMFD':
        node.text = ' '.join(cp.params[:3])
    elif cp.kind == 'minMag':  # pseudo-kind, see _link_copies
        node.text = cp.params[3]
    else:
        # Source files can use a different NRML version from the logic tree.
        mfd = _sub(node, striptag(cp.mfd.tag), **cp.mfd.attrib)
        for child in cp.mfd:
            _sub(mfd, striptag(child.tag), **child.attrib).text = child.text


def _mfd_bset(tag, bsid, parent, branches):
    # a branchset applied to the parent branch, setting the MFDs of the same
    # sources in each branch (ID, weight, [(source ID, copy)]), all copies
    # of the same kind; one source needs no correlated element
    pairs0 = branches[0][2]
    node = ET.Element(tag, branchSetID=bsid,
                      uncertaintyType=UTYPE[pairs0[0][1].kind],
                      applyToBranches=parent, applyToSources=(
                          pairs0[0][0] if len(pairs0) == 1 else '*'))
    for br_id, weight, pairs in branches:
        branch = _sub(node, 'logicTreeBranch', branchID=br_id)
        model = _sub(branch, 'uncertaintyModel')
        for srcid, cp in pairs:
            _set_value(model if len(pairs) == 1 else
                       _sub(model, 'correlated', src=srcid), cp)
        _sub(branch, 'uncertaintyWeight').text = weight
    return node


def _link(bs, parent, pairs, new_id):
    # a single-branch link
    bsid = f'{bs.id}_{new_id}'
    node = _mfd_bset(bs.el.tag, bsid, parent, [(new_id, '1.0', pairs)])
    if bs.in_level:  # NRML 0.4: one branchset per branching level
        level = ET.Element(bs.container.tag, branchingLevelID=bsid)
        level.append(node)
        return level
    return node


def _link_copies(base, cp):
    # the copies to be written in the links to restore the MFD of cp; a
    # truncated GR needs a link for a, b, maxMag if they are different from
    # the base ones and a link for minMag (pseudo-kind) if it is different
    if cp.kind != 'truncGutenbergRichterMFD':
        return [cp]
    out = [cp] if cp.params[:3] != base.params[:3] else []
    if cp.params[3] != base.params[3]:
        mcp = copy.copy(cp)
        mcp.kind = 'minMag'
        out.append(mcp)
    return out


def _links(variants, carriers):
    # the copies with a MFD different from the base, by carrier branch
    links = {}  # (bset ordinal, branch ID) -> [(source ID, copy)]
    for copies in variants:
        base = copies[0]
        for cp in copies:
            if cp.params != base.params:
                for key in carriers[cp.fname]:
                    for lcp in _link_copies(base, cp):
                        links.setdefault(key, []).append((cp.id, lcp))
    return links


def _identity(byfile, fnames, avoid):
    # a unique, unmodified source whose MFD a link can set to itself
    for fname in fnames:
        copies = byfile.get(fname, [])
        count = Counter(cp.id for cp in copies)
        for cp in copies:
            if (count[cp.id] == 1 and ':' not in cp.id and cp.id not in avoid
                    and cp.kind in UTYPE):
                return cp
    return None


def _unsafe(copies, variants, renamed):
    # the IDs of sources in more files with different copies (the engine
    # adds the branch to their IDs, so applyToSources cannot select them)
    byid = _group(copies, 'id')
    converted = {cps[0].id for cps in variants}
    safe = {srcid for srcid, cps in byid.items()
            if len({cp.key for cp in cps}) == 1 and (
                len({cp.params for cp in cps}) == 1 or srcid in converted)}
    return (set(renamed.values()) | set(byid)) - safe


def complete_chains(variants, bsets, carriers, renamed, copies):
    """
    Every branch of a branchset with a chain must have a chain, else a
    dummy branchset would be attached to it and the following branchsets
    would not be applied below it (see attach_branches): the branches
    without MFD variants get an identity link, setting the MFD of a
    source to itself. The copies of the source in different files must be
    identical (else the engine would add the branch to its ID) and the
    source must not be modified by the branchsets before the link; for a
    sourceModel branch it must be in the files of the branch, for an
    extendModel branch it can be any source (the link does nothing if
    the source is not in the realization). If there is no such source,
    the variants carried by the branchset are not converted.

    :returns: (variants, links, identity links, skipped)
    """
    allfiles = list(carriers)
    byfile = _group(copies, 'fname')
    skipped = []
    while True:
        unsafe = _unsafe(copies, variants, renamed)
        links = _links(variants, carriers)
        identity, bad = {}, {}  # bset ordinal -> reason
        for ordinal in sorted({o for o, _ in links}):
            bs = bsets[ordinal]
            if any(b.utype not in SM_TYPES and (not b.ats or '*' in b.ats)
                   for b in bsets[:ordinal]):
                bad[ordinal] = 'all the sources are modified before it'
                continue
            if any(not BRANCH_ID_RE.match(br) for br, _ in bs.branches):
                # applyToBranches cannot refer to IDs with spaces or commas
                bad[ordinal] = 'invalid branch IDs for applyToBranches'
                continue
            # the sources modified before the link cannot be used
            avoid = unsafe | {src for b in bsets[:ordinal] for src in b.ats}
            for br_id, _ in bs.branches:
                if (ordinal, br_id) in links:
                    continue
                files = bs.files(br_id)
                if bs.utype == 'extendModel':
                    files = files + [f for f in allfiles if f not in files]
                cp = _identity(byfile, files, avoid)
                if cp is None:
                    bad[ordinal] = 'no source for an identity link'
                    break
                identity[ordinal, br_id] = [(cp.id, cp)]
        if not bad:
            return variants, links, identity, skipped
        ok = []
        for cps in variants:
            reasons = {f'{bsets[o].id}: {bad[o]}' for cp in cps
                       for o, _ in carriers[cp.fname] if o in bad}
            if reasons:
                skipped.append((cps[0].id, '; '.join(sorted(reasons))))
            else:
                ok.append(cps)
        variants = ok


def _expand(src, renamed):
    # the IDs replacing a source ID in applyToSources: its new IDs, plus
    # the new IDs of its fragments (which were selected by the base name)
    exact = [new for new, old in renamed.items() if old == src]
    frags = [new for new, old in renamed.items()
             if old != src and old.split(':')[0] == src]
    return (exact or [src]) + frags


def rename_branches(bsets):
    """
    Replace the characters not allowed by valid.branch_id (like spaces
    and commas) in the branch IDs, since applyToBranches is split on the
    spaces and could not refer to such branches.

    :returns: a dictionary new branch ID -> old branch ID
    """
    used = {br for bs in bsets for br, _ in bs.branches}
    brnames = {}
    for bs in bsets:
        for i, (br_id, value) in enumerate(bs.branches):
            if BRANCH_ID_RE.match(br_id):
                continue
            new = re.sub(r'[^\w\:\#\-\.]', '_', br_id)
            while new in used:
                new += '_'
            used.add(new)
            brnames[new] = br_id
            bs.branches[i] = (new, value)
    return brnames


def _read_variants(smlt_dir, bsets):
    # read the copies of the sources, rename the duplicated IDs, find the
    # MFD variants that can be converted and plan the conversion: first the
    # branchsets to collapse, then the chains for the other branchsets
    carriers = {}  # file -> [(bset ordinal, branch ID)]
    for bs in bsets:
        for br_id, _ in bs.branches:
            for fname in bs.files(br_id):
                carriers.setdefault(fname, []).append((bs.ordinal, br_id))
    copies = read_copies(smlt_dir, carriers)
    renamed = rename_duplicates(copies)
    variants, skipped = find_variants(copies, bsets, carriers, renamed)
    byfile = _group(copies, 'fname')
    while True:
        rows = {}  # bset ordinal -> MFD links of each branch
        for bs in bsets:
            out = _mfd_rows(bs, byfile, variants, renamed)
            if out:
                rows[bs.ordinal] = out
        # the collapsed branchsets need no chains
        free = {f: [k for k in keys if k[0] not in rows]
                for f, keys in carriers.items()}
        ok, links, identity, skip = complete_chains(
            variants, bsets, free, renamed, copies)
        skipped += skip
        if len(ok) == len(variants):
            return copies, renamed, variants, rows, links, identity, skipped
        variants = ok  # some variants were skipped, plan again


def _write_files(smlt_dir, outdir, copies, renamed, variants, referenced):
    # write in outdir, with the same relative paths, the referenced source
    # model files with the renamed sources and the MFDs normalized to the
    # MFD of the first copy; return the number of rewritten files
    new_ids = {}  # file -> {position: new ID}
    for cp in copies:
        if cp.id in renamed:
            new_ids.setdefault(cp.fname, {})[cp.pos] = cp.id
    bases = {}  # file -> {position: base copy}
    for cps in variants:
        for cp in cps:
            if cp.params != cps[0].params:
                bases.setdefault(cp.fname, {})[cp.pos] = cps[0]
    fnames = sorted((new_ids.keys() | bases.keys()) & referenced)
    for fname in fnames:
        root = _read_xml(smlt_dir / fname)
        sources = (el for el in root.iter() if isinstance(el.tag, str)
                   and el.tag.endswith('Source') and 'id' in el.attrib)
        for pos, el in enumerate(sources):
            if pos in new_ids.get(fname, {}):
                el.set('id', new_ids[fname][pos])
            if pos in bases.get(fname, {}):
                old = next(c for c in el if isinstance(c.tag, str)
                           and striptag(c.tag) in MFD_TAGS)
                new = copy.deepcopy(bases[fname][pos].mfd)
                new.tail = old.tail
                el[list(el).index(old)] = new
        path = outdir / fname
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_xml(root, path)
    return len(fnames)


def _mfd_rows(bs, byfile, variants, renamed):
    # the links of each branch of a branchset whose branches load the same
    # sources in the same order, differing only in the MFDs of converted
    # copies: each branch sets the MFDs of its own copies, for all the kinds
    # needed by any branch; None if the branchset cannot be collapsed
    if bs.utype not in SM_TYPES or bs.in_level or len(bs.branches) < 2:
        return None
    rows = [[cp for f in bs.files(br) for cp in byfile.get(f, [])]
            for br, _ in bs.branches]
    sig = [cp.key for cp in rows[0]]
    if not sig or any([cp.key for cp in row] != sig for row in rows[1:]):
        return None
    if any(cp.id in renamed for row in rows for cp in row):
        return None
    base_of = {id(cp): cps[0] for cps in variants for cp in cps}
    out = [[] for _ in rows]
    for col in zip(*rows):
        if len({cp.params for cp in col}) == 1:
            continue  # same MFD in all the branches
        if any(id(cp) not in base_of for cp in col):
            return None  # not converted, see the skipped sources
        base = base_of[id(col[0])]
        kinds = {lcp.kind for cp in col for lcp in _link_copies(base, cp)}
        for k, cp in enumerate(col):
            for kind in sorted(kinds):
                lcp = copy.copy(cp)
                lcp.kind = kind
                out[k].append((cp.id, lcp))
    # two branches with the same MFDs would be duplicated branches
    values = {tuple((srcid, lcp.kind, lcp.params) for srcid, lcp in row)
              for row in out}
    if len(values) < len(out):
        return None
    return out if out[0] else None


def _new_id(name, used):
    # a branch (or branchset) ID not used yet
    while name in used:
        name += '_'
    used.add(name)
    return name


def _collapse(bsets, rows, used):
    """
    Replace each branchset whose branches load copies of the same sources,
    differing only in the MFDs, with a single branch loading the files of
    the first branch, followed by a branchset with the original branches
    and weights setting the MFDs; the further kinds of MFD (i.e. minMag)
    are set by single-branch links below each branch. Then the files of
    the other branches are not needed anymore.

    :param rows: bset ordinal -> MFD links of each branch (see _mfd_rows)
    :param used: the branch IDs already used
    :returns: the added branch IDs and the ends of the chains
    """
    added, chain_end = [], {}
    for bs in bsets:
        if bs.ordinal not in rows:
            continue
        brels = bs.el.findall('{*}logicTreeBranch')
        weights = [br.find('{*}uncertaintyWeight').text.strip()
                   for br in brels]
        br_ids = [br for br, _ in bs.branches]
        base_id = _new_id(f'{br_ids[0]}_base', used)
        for br in brels[1:]:
            bs.el.remove(br)
        brels[0].find('{*}uncertaintyWeight').text = '1.0'
        bs.branches = [(base_id, bs.branches[0][1])]
        added.append(base_id)
        bykind = [groupby(row, key=lambda pair: pair[1].kind)
                  for row in rows[bs.ordinal]]
        kinds = sorted(bykind[0])
        nodes = [_mfd_bset(bs.el.tag, _new_id(f'{bs.id}_mfd', used), base_id,
                           [(br, w, bk[kinds[0]])
                            for br, w, bk in zip(br_ids, weights, bykind)])]
        for br, bk in zip(br_ids, bykind):
            parent = br
            for n, kind in enumerate(kinds[1:], 2):
                link_id = _new_id(f'{br}_mfd{n}', used)
                nodes.append(_link(bs, parent, bk[kind], link_id))
                added.append(link_id)
                parent = link_id
            if parent != br:
                chain_end[br] = parent
        pos = list(bs.parent).index(bs.container) + 1
        bs.parent[pos:pos] = nodes
    return added, chain_end


def _build_chains(bsets, links, identity, used):
    # insert chains after the modified branchsets (or their NRML 0.4
    # levels); return the added branch IDs and the ends of the chains
    chain_end, added = {}, []
    for bs in bsets:
        chains = []
        for br_id, _ in bs.branches:
            parent = br_id
            pairs = links.get((bs.ordinal, br_id)) or identity.get(
                (bs.ordinal, br_id), [])
            # one correlated link for each kind of MFD
            bykind = groupby(sorted(pairs, key=lambda pair: pair[0]),
                             key=lambda pair: pair[1].kind)
            for n, kind in enumerate(sorted(bykind), 1):
                new_id = _new_id(f'{br_id}_mfd{n}', used)
                chains.append(_link(bs, parent, bykind[kind], new_id))
                added.append(new_id)
                parent = new_id
            if parent != br_id:
                chain_end[br_id] = parent
        pos = list(bs.parent).index(bs.container) + 1
        bs.parent[pos:pos] = chains
    return added, chain_end


def _rewrite_tree(bsets, renamed, chain_end):
    # update only the original branchsets: newly inserted links already
    # refer to their immediate parents and must not be redirected
    for bs in bsets:
        for (br_id, _), br in zip(bs.branches,
                                  bs.el.findall('{*}logicTreeBranch')):
            br.set('branchID', br_id)
            if bs.utype in SM_TYPES:
                model = br.find('{*}uncertaintyModel')
                model.text = ' '.join(bs.files(br_id))
                for child in model:
                    child.tail = None  # filenames are now all in model.text
        if bs.ats:
            bs.el.set('applyToSources', ' '.join(
                new for src in bs.ats for new in _expand(src, renamed)))
        if bs.atb:
            bs.el.set('applyToBranches', ' '.join(
                chain_end.get(br, br) for br in bs.atb))


def convert(smlt, outdir):
    """
    Convert the MFD variants of a source model logic tree, writing in
    `outdir` the converted logic tree, with the name of the original one,
    and the rewritten source model files, with their relative paths
    (nothing is written if there is nothing to convert)

    :param smlt: path to the source model logic tree
    :param outdir: path to the output folder
    :returns: the IDs of the branches added to the logic tree and the
              dictionaries new ID -> old ID of the renamed sources and
              of the renamed branches
    """
    smlt, outdir = Path(smlt), Path(outdir)
    smlt_dir = smlt.parent
    root, bsets = read_tree(smlt)
    brnames = rename_branches(bsets)
    (copies, renamed, variants, rows, links, identity,
     skipped) = _read_variants(smlt_dir, bsets)
    for src, reason in skipped:
        logging.info('Not converted %s: %s', src, reason)
    if not variants:  # nothing to convert, nothing is written
        logging.warning('%s: no MFD variants to convert (%d skipped)',
                        smlt, len(skipped))
        return set(), {}, {}
    outdir.mkdir(parents=True, exist_ok=True)
    used = {br for bs in bsets for br, _ in bs.branches}
    added, chain_end = _collapse(bsets, rows, used)
    added2, chain_end2 = _build_chains(bsets, links, identity, used)
    added += added2
    chain_end.update(chain_end2)
    referenced = {f for bs in bsets for br, _ in bs.branches
                  for f in bs.files(br)}
    nfiles = _write_files(smlt_dir, outdir, copies, renamed, variants,
                          referenced)
    _rewrite_tree(bsets, renamed, chain_end)
    _write_xml(root, outdir / smlt.name)
    for new, old in renamed.items():
        logging.info('Renamed source %s -> %s', old, new)
    for new, old in brnames.items():
        logging.info('Renamed branch %r -> %s', old, new)
    logging.warning('%s: %d source(s) converted, %d skipped, %d branchset(s) '
                    'collapsed, %d file(s) rewritten, %d branch(es) added',
                    smlt, len(variants), len(skipped), len(rows), nfiles,
                    len(added))
    return set(added), renamed, brnames


def _digest(srcid, rates):
    # a 64 bit hash of the source ID and of the (magnitude, rate) pairs
    # rounded to 10 significant digits, so that rates equal within the
    # tolerance have the same hash
    text = srcid + ',' + ','.join('%.9e %.9e' % pair for pair in rates)
    return int.from_bytes(hashlib.blake2b(
        text.encode(), digest_size=8).digest(), 'little')


def _add(acc, table, normkey=None):
    # add a table (count, sum of the hashes) to acc, normalizing the keys
    for key, (n, h) in table.items():
        if normkey:
            key = normkey(key)
        m, g = acc.get(key, (0, 0))
        acc[key] = (m + n, (g + h) & HASH_MASK)
    return acc


def rates_table(sources, bset_values, paths, renamed, detail):
    """
    Task computing the hashes of the rates of a block of sources.

    :param sources: a block of sources of the same group
    :param bset_values: the uncertainties to apply, see get_bset_values
    :param paths: the realization paths, by ordinal
    :param renamed: a dictionary new source ID -> original source ID
    :param detail: None or a set of realization paths
    :returns: a dictionary realization path -> (number of rates, sum of
              the hashes of the source IDs and rates), with the
              uncertainties applied, or (realization path, source ID) ->
              (number, sum) for the paths in `detail`; the sum does not
              depend on the order, so the tables of the blocks can be merged
    """
    table = {}
    for trt_smrs, grp in modified_groups(sources, bset_values):
        for src in grp:
            mfd = getattr(src, 'mfd', None)
            if mfd is None:
                continue
            srcid = re.split('[!;]', src.source_id)[0]
            srcid = renamed.get(srcid, srcid)
            h = _digest(srcid, mfd.get_annual_occurrence_rates())
            for t in trt_smrs:
                key = paths[t % TWO24]
                if detail is not None:
                    if key not in detail:
                        continue
                    key = (key, srcid)
                n, s = table.get(key, (0, 0))
                table[key] = (n + 1, (s + h) & HASH_MASK)
    return table


def _blocks(src_groups):
    # split the source groups in blocks of sources (keeping the atomic
    # groups whole), about Starmap.CT blocks in total
    size = max(1, sum(len(sg) for sg in src_groups) // Starmap.CT)
    for sg in src_groups:
        step = max(1, len(sg)) if sg.atomic else size
        for start in range(0, len(sg), step):
            block = copy.copy(sg)
            block.sources = sg.sources[start:start + step]
            yield block


def _rates(job_ini, kw, renamed, detail=None):
    """
    :returns: the hashes of the rates of the sources, see rates_table,
              and the number of warnings about the MFD variants; the rates
              are computed in parallel
    """
    warnings = []

    class Handler(logging.Handler):
        def emit(self, record):
            if 'appear multiple times' in record.getMessage():
                warnings.append(record)
    handler = Handler()
    logging.getLogger().addHandler(handler)
    oq = readinput.get_oqparam(str(job_ini), kw=kw)
    # a temporary datastore, needed for the sections of the
    # multiFaultSources, which must exist while computing the rates
    with tempfile.TemporaryDirectory() as tmp, closing(
            datastore.DataStore(os.path.join(tmp, 'c.hdf5'))) as dstore:
        dstore['oqparam'] = oq
        try:
            csm = readinput.get_composite_source_model(oq, dstore)
        finally:
            logging.getLogger().removeHandler(handler)
        full = csm.full_lt
        # ignore the dummy branches when identifying a realization
        paths = [tuple(b for b in rlz.lt_path if b != '.')
                 for rlz in full.sm_rlzs]
        allargs = [(block, get_bset_values(full, block), paths, renamed,
                    detail) for block in _blocks(csm.src_groups)]
        del csm
        table = Starmap(rates_table, allargs).reduce(agg=_add, acc={})
    return table, len(warnings)


def _trivial_gsim_lt(smlt, path):
    # one GMPE per TRT: enumerate only the source model paths
    root = ET.Element('nrml', xmlns='http://openquake.org/xmlns/nrml/0.5')
    tree = _sub(root, 'logicTree', logicTreeID='lt1')
    trts = sorted(SourceModelLogicTree(str(smlt)).tectonic_region_types)
    for i, trt in enumerate(trts):
        bs = _sub(tree, 'logicTreeBranchSet', branchSetID=f'bs{i}',
                  uncertaintyType='gmpeModel', applyToTectonicRegionType=trt)
        br = _sub(bs, 'logicTreeBranch', branchID=f'b{i}')
        _sub(br, 'uncertaintyModel').text = 'BooreAtkinson2008'
        _sub(br, 'uncertaintyWeight').text = '1.0'
    _write_xml(root, path)


def check(job_ini, conv_ini, added, renamed, smlt, brnames):
    """
    Compare the rates of all the sources in all the realizations of the
    original job and of the converted one (the job.ini extracted from the
    archive, so that a missing file is an error); the rates are computed
    in parallel and compared by hash, see _digest, one hash per
    realization; the sources are compared only in the realizations with
    different hashes, to report them
    """
    # NB: strict=false, so that the original logic tree can have invalid
    # branch IDs (the engine replaces their spaces with underscores)
    full = {'number_of_logic_tree_samples': '0', 'strict': 'false',
            'max_potential_paths': '100000000'}
    # the GMPEs are irrelevant for the rates, so a trivial GMPE logic
    # tree is used, written next to the job, since paths must be relative
    gsim_lt = job_ini.parent / '_check_gmmLT.xml'
    full['gsim_logic_tree_file'] = gsim_lt.name
    try:
        _trivial_gsim_lt(smlt, gsim_lt)
        _trivial_gsim_lt(smlt, conv_ini.parent / gsim_lt.name)
        # the renamed sources are hashed with their original IDs
        orig, warn_orig = _rates(job_ini, full, {})
        conv, warn_conv = _rates(conv_ini, full, renamed)
        # remove the added branches from the converted paths (the dummy
        # branches were removed in _rates) and restore the original
        # branch IDs
        paths = {path: tuple(branch_id(brnames.get(b, b)) for b in path
                             if b not in added) for path in conv}
        conv = _add({}, conv, paths.get)
        bad = {path for path in set(orig) | set(conv)
               if orig.get(path) != conv.get(path)}
        logging.warning('Checked %d realizations, %d source rates: %d '
                        'realization(s) different', len(orig),
                        sum(n for n, _ in orig.values()), len(bad))
        if bad:  # find the sources with different rates
            orig, _ = _rates(job_ini, full, {}, bad)
            conv, _ = _rates(conv_ini, full, renamed,
                             {path for path in paths if paths[path] in bad})
            conv = _add({}, conv, lambda key: (paths[key[0]], key[1]))
            srcs = [key for key in set(orig) | set(conv)
                    if orig.get(key) != conv.get(key)]
            for key in sorted(srcs, key=str)[:10]:
                logging.error('Different rates for %s', key)
    finally:
        gsim_lt.unlink(missing_ok=True)
    logging.warning('MFD variants warning: %d in the original, %d in the '
                    'converted logic tree', warn_orig, warn_conv)
    return not bad


def make_zip(job_ini, smlt, convdir, archive):
    """
    Zip a copy of the job using the converted logic tree, with the
    original file names: the converted logic tree and the rewritten source
    models in `convdir` replace the original ones, and the source models
    not referenced anymore by the converted logic tree are left out.

    :param job_ini: path to the original job.ini file
    :param smlt: path to the original logic tree
    :param convdir: folder with the converted logic tree and the
                    rewritten source models (see convert)
    :param archive: path to the zip file to write
    """
    # do not validate to avoid permissions errors on the export_dir
    oq = oqvalidation.OqParam(**readinput.get_params(str(job_ini)))
    info = logictree.collect_info(str(smlt))
    old = {os.path.normpath(f) for f in info.smpaths + info.h5paths}
    src = {}  # path in the job -> file to zip
    for f in readinput.get_input_files(oq):
        path = os.path.normpath(f)
        if path not in old:
            src[path] = path
    src[os.path.normpath(smlt)] = convdir / smlt.name
    _, bsets = read_tree(convdir / smlt.name)
    for bs in bsets:
        for br, _ in bs.branches:
            for f in bs.files(br):
                path = os.path.normpath(smlt.parent / f)
                new = convdir / f
                src[path] = new if new.exists() else path
                h5 = os.path.splitext(path)[0] + '.hdf5'
                if os.path.exists(h5):
                    src[h5] = h5
    # the paths in the archive are relative to the common folder
    prefix = os.path.commonpath([os.path.dirname(p) for p in src])
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED,
                         allowZip64=True) as z:
        for path, fname in sorted(src.items()):
            z.write(fname, Path(os.path.relpath(path, prefix)).as_posix())


def main(job_ini):
    """
    Convert the source model logic tree of the given job, zip the job with
    the converted logic tree (with the original file names) and check it:
    if the check is successful the archive is saved as job.zip, in the
    folder of the job.ini, else as job_mfd.zip, to be inspected.

    :param job_ini: path to a job.ini file
    :returns: True if the converted logic tree is equivalent to the
              original one (or if there is nothing to convert)
    """
    job_ini = Path(job_ini).resolve()
    inputs = readinput.get_params(job_ini)['inputs']
    if 'source_model_logic_tree' not in inputs:
        raise ValueError(f'{job_ini}: missing source_model_logic_tree_file')
    smlt = Path(inputs['source_model_logic_tree']).resolve()
    archive = job_ini.parent / 'job_mfd.zip'
    with tempfile.TemporaryDirectory() as tmp:
        convdir = Path(tmp) / 'converted'
        added, renamed, brnames = convert(smlt, convdir)
        if not added:  # nothing converted, nothing to check
            return True
        make_zip(job_ini, smlt, convdir, archive)
        [conv_ini] = [f for f in readinput.extract_from_zip(
            archive, targetdir=os.path.join(tmp, 'job'))
            if Path(f).name == job_ini.name]
        ok = check(job_ini, Path(conv_ini), added, renamed, smlt, brnames)
    if ok:
        archive = archive.replace(archive.with_name('job.zip'))
        logging.warning('Wrote %s', archive)
    else:
        logging.error('The converted job is in %s', archive)
    return ok
