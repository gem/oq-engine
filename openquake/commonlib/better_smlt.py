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
This module rewrites the copies so that they all have the same (base)
MFD, which makes them identical, and adds after the branchset loading
each copy a chain of single-branch branchsets restoring the original MFDs
in the branch, one for each kind of MFD (and for each of the uncertainties
below). A branchset with a single source uses applyToSources="<source ID>",
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
first. Sources sharing an ID in a file and fragments of sources (colon
convention, except in mutex groups) are renamed, since applyToSources
could not select them; branch IDs with spaces are renamed too, since
applyToBranches could not refer to them. Sources with different IDs are
not converted (they are not recognized as copies of the same source).

The input files are never modified. The result is a file job.zip, in the
folder of the job.ini, with a copy of the job using the converted logic
tree, with the original file names (it replaces an existing job.zip). It
is built in 3 steps:

1. the rewritten source model files are stored in the folder `_fixed`
   next to the logic tree (the folder must not exist) and the converted
   logic tree is written next to the original one, with the suffix _mfd;
2. the converted logic tree is always checked: the original and the
   converted logic tree are compared by applying the uncertainties with
   the engine in each realization (with full enumeration of the source
   model paths): the annual occurrence rates of all the sources must be
   the same;
3. if the check is successful and the logic tree is in the folder of the
   job.ini, the folder `_fixed` is completed into a copy of the job with
   the original file names, which is zipped with oqzip.zip_job; then the
   folder `_fixed` and the converted logic tree are removed. If the check
   fails, they are left there to be inspected and there is no job.zip.

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
import shutil
import tempfile
import textwrap
import hashlib
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from contextlib import closing
import numpy
from openquake.baselib.general import duplicated, groupby
from openquake.baselib.node import striptag
from openquake.hazardlib import valid
from openquake.hazardlib.logictree import SourceModelLogicTree, branch_id
from openquake.hazardlib.source_reader import (
    modified_groups, get_bset_values, TWO24)
from openquake.commonlib import datastore, oqzip, oqvalidation, readinput

MFD_TAGS = {'truncGutenbergRichterMFD', 'incrementalMFD', 'multiMFD',
            'arbitraryMFD', 'YoungsCoppersmithMFD',
            'taperedGutenbergRichterMFD'}
UTYPE = {'truncGutenbergRichterMFD': 'abMaxMagAbsolute',
         'minMag': 'minMagGRAbsolute',
         'incrementalMFD': 'incrementalMFDAbsolute',
         'multiMFD': 'multiMFDAbsolute'}
MFD_DIR = '_fixed'  # folder with the rewritten source models
SM_TYPES = ('sourceModel', 'extendModel')
BRANCH_ID_RE = re.compile(valid.branch_id.regex)


def _read_xml(path):
    # retain comments and processing instructions when rewriting a file
    parser = ET.XMLParser(target=ET.TreeBuilder(
        insert_comments=True, insert_pis=True))
    return ET.parse(path, parser=parser).getroot()


def _write_xml(root, path):
    # use the document's namespace and wrap multiMFD arrays to 79 columns
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
                    values, width=79, initial_indent=ind + '    ',
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
        attrs = {k: v for k, v in el.attrib.items() if k != 'name'}
        geom = hashlib.md5(repr(sorted(attrs.items())).encode())
        for c in el:
            if striptag(c.tag) not in MFD_TAGS:
                geom.update(ET.tostring(c))
        self.key = (self.id, repr(sorted(group.items())), geom.hexdigest())
        self.params = self.get_params(mfd)

    def get_params(self, mfd):
        # compare the original strings, ignoring attribute order and whitespace
        if mfd is None:
            return ()
        if self.kind == 'truncGutenbergRichterMFD':
            return tuple(mfd.attrib[k] for k in
                         ('aValue', 'bValue', 'maxMag', 'minMag'))
        return tuple((striptag(el.tag), tuple(sorted(el.attrib.items())),
                      ' '.join((el.text or '').split())) for el in mfd.iter())


def _parse(path, fname):
    # read the source inventory once; identity links reuse these copies
    root = ET.parse(path).getroot()
    parents = {c: p for p in root.iter() for c in p}
    sources = (el for el in root.iter()
               if el.tag.endswith('Source') and 'id' in el.attrib)
    return [Copy(fname, pos, el, parents[el].attrib if
                 striptag(parents[el].tag) == 'sourceGroup' else {})
            for pos, el in enumerate(sources)]


def read_copies(smlt_dir, fnames):
    """
    Read all source copies in parallel, preserving file and document order.
    """
    fnames = list(fnames)
    with ProcessPoolExecutor() as pool:
        results = pool.map(_parse, [smlt_dir / f for f in fnames], fnames)
        return [cp for copies in results for cp in copies]


def _group(copies, attr='key'):
    # group by (source ID, source group, geometry), or another attribute,
    # preserving document order (which determines the renamed IDs)
    bykey = {}
    for cp in copies:
        bykey.setdefault(getattr(cp, attr), []).append(cp)
    return bykey


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


def find_variants(bykey):
    # the groups of copies with different MFDs in different files
    variants, skipped = [], []
    for copies in bykey.values():
        if not _has_variants(copies):
            continue
        kinds = {cp.kind for cp in copies}
        src = copies[0].id
        if ':' in src:  # the logic tree sees only the base name
            skipped.append((src, 'fragment of a source (colon convention)'))
        elif len(kinds) > 1 or kinds - set(UTYPE):
            skipped.append((src, f'MFD types {sorted(map(str, kinds))}'))
        elif kinds == {'multiMFD'} and len(
                {(cp.mfd.get('kind'), cp.mfd.get('size'))
                 for cp in copies}) > 1:
            skipped.append((src, 'different kind or number of points'))
        else:
            variants.append(copies)
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


def _link(bs, parent, pairs, new_id):
    # a single-branch link; one source needs no correlated element
    bsid = f'{bs.id}_{new_id}'
    node = ET.Element(bs.el.tag, branchSetID=bsid,
                      uncertaintyType=UTYPE[pairs[0][1].kind],
                      applyToBranches=parent, applyToSources=(
                          pairs[0][0] if len(pairs) == 1 else '*'))
    branch = _sub(node, 'logicTreeBranch', branchID=new_id)
    model = _sub(branch, 'uncertaintyModel')
    for srcid, cp in pairs:
        _set_value(model if len(pairs) == 1 else
                   _sub(model, 'correlated', src=srcid), cp)
    _sub(branch, 'uncertaintyWeight').text = '1.0'
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


def _check_order(variants, bsets, carriers, renamed):
    # skip the sources modified before the branchset loading them
    ok, skipped = [], []
    for copies in variants:
        src = renamed.get(copies[0].id, copies[0].id)
        first = min(bsets[o].ordinal for cp in copies
                    for o, _ in carriers[cp.fname])
        before = [bs.id for bs in bsets[:first] if bs.utype not in SM_TYPES
                  and (not bs.ats or '*' in bs.ats or src in bs.ats or
                       src.split(':')[0] in bs.ats)]
        if before:
            skipped.append((src, f'modified before by {before}'))
        else:
            ok.append(copies)
    return ok, skipped


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
    # read the copies of the sources, rename the duplicated IDs and find
    # the MFD variants that can be converted
    carriers = {}  # file -> [(bset ordinal, branch ID)]
    for bs in bsets:
        for br_id, _ in bs.branches:
            for fname in bs.files(br_id):
                carriers.setdefault(fname, []).append((bs.ordinal, br_id))
    copies = read_copies(smlt_dir, carriers)
    renamed = rename_duplicates(copies)
    variants, skipped = find_variants(_group(copies))
    variants, skip2 = _check_order(variants, bsets, carriers, renamed)
    variants, links, identity, skip3 = complete_chains(
        variants, bsets, carriers, renamed, copies)
    return (copies, renamed, variants, links, identity,
            skipped + skip2 + skip3)


def _write_files(smlt_dir, copies, renamed, variants):
    # write the source model files with the renamed sources and the MFDs
    # normalized to the MFD of the first copy, in the folder _fixed;
    # return a dictionary file -> new file
    new_ids = {}  # file -> {position: new ID}
    for cp in copies:
        if cp.id in renamed:
            new_ids.setdefault(cp.fname, {})[cp.pos] = cp.id
    bases = {}  # file -> {position: base copy}
    for cps in variants:
        for cp in cps:
            if cp.params != cps[0].params:
                bases.setdefault(cp.fname, {})[cp.pos] = cps[0]
    renames = {}
    for fname in sorted(new_ids.keys() | bases.keys()):
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
        renames[fname] = str(Path(MFD_DIR) / fname)
        path = smlt_dir / renames[fname]
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_xml(root, path)
    return renames


def _build_chains(bsets, links, identity):
    # insert chains after the modified branchsets (or their NRML 0.4
    # levels); return the added branch IDs and the ends of the chains
    used = {br for bs in bsets for br, _ in bs.branches}
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
                new_id = f'{br_id}_mfd{n}'
                while new_id in used:
                    new_id += '_'
                used.add(new_id)
                chains.append(_link(bs, parent, bykind[kind], new_id))
                added.append(new_id)
                parent = new_id
            if parent != br_id:
                chain_end[br_id] = parent
        pos = list(bs.parent).index(bs.container) + 1
        bs.parent[pos:pos] = chains
    return added, chain_end


def _rewrite_tree(bsets, renames, renamed, chain_end):
    # update only the original branchsets: newly inserted links already
    # refer to their immediate parents and must not be redirected
    for bs in bsets:
        for (br_id, _), br in zip(bs.branches,
                                  bs.el.findall('{*}logicTreeBranch')):
            br.set('branchID', br_id)
            if bs.utype in SM_TYPES:
                model = br.find('{*}uncertaintyModel')
                model.text = ' '.join(
                    renames.get(f, f) for f in bs.files(br_id))
                for child in model:
                    child.tail = None  # filenames are now all in model.text
        if bs.ats:
            bs.el.set('applyToSources', ' '.join(
                new for src in bs.ats for new in _expand(src, renamed)))
        if bs.atb:
            bs.el.set('applyToBranches', ' '.join(
                chain_end.get(br, br) for br in bs.atb))


def convert(smlt, out):
    """
    Convert the MFD variants of a source model logic tree, writing the
    new logic tree in `out` and the new source model files in the folder
    `_fixed`, which must not exist (nothing is written if there is nothing
    to convert)

    :param smlt: path to the source model logic tree
    :param out: path to the converted logic tree, in the same folder
    :returns: the IDs of the branches added to the logic tree and the
              dictionaries new ID -> old ID of the renamed sources and
              of the renamed branches
    """
    smlt, out = Path(smlt), Path(out)
    if smlt.parent.resolve() != out.parent.resolve():
        raise ValueError('The output must be in the folder of the input')
    smlt_dir = smlt.parent
    if (smlt_dir / MFD_DIR).exists():
        raise FileExistsError(f'{smlt_dir / MFD_DIR} exists already: '
                              'remove it or rename it')
    root, bsets = read_tree(smlt)
    brnames = rename_branches(bsets)
    (copies, renamed, variants, links, identity,
     skipped) = _read_variants(smlt_dir, bsets)
    for src, reason in skipped:
        logging.info('Not converted %s: %s', src, reason)
    if not variants:  # nothing to convert, nothing is written
        logging.warning('%s: no MFD variants to convert (%d skipped)',
                        smlt, len(skipped))
        return set(), {}, {}
    renames = _write_files(smlt_dir, copies, renamed, variants)
    added, chain_end = _build_chains(bsets, links, identity)
    _rewrite_tree(bsets, renames, renamed, chain_end)
    _write_xml(root, out)
    for new, old in renamed.items():
        logging.info('Renamed source %s -> %s', old, new)
    for new, old in brnames.items():
        logging.info('Renamed branch %r -> %s', old, new)
    logging.warning('%s: %d source(s) converted, %d skipped, %d file(s) '
                    'rewritten in %s, %d branchset(s) added', out,
                    len(variants), len(skipped), len(renames),
                    smlt_dir / MFD_DIR, len(added))
    return set(added), renamed, brnames


def _rates(job_ini, kw):
    # rates of the sources by (realization path, source ID)
    oq = readinput.get_oqparam(str(job_ini), kw=kw)
    # a temporary datastore, needed for the sections of multiFaultSources
    with tempfile.TemporaryDirectory() as tmp, closing(
            datastore.DataStore(os.path.join(tmp, 'check.hdf5'))) as dstore:
        dstore['oqparam'] = oq
        csm = readinput.get_composite_source_model(oq, dstore)
        return _rates_table(csm)


def _rates_table(csm):
    # the rates of the sources in each realization, uncertainties applied
    # ignore dummy branches in both trees when identifying a realization
    full = csm.full_lt
    paths = [tuple(b for b in rlz.lt_path if b != '.') for rlz in full.sm_rlzs]
    table = {}
    for sg in csm.src_groups:
        bsv = get_bset_values(full, sg)
        for trt_smrs, grp in modified_groups(sg, bsv):
            for src in grp:
                mfd = getattr(src, 'mfd', None)
                if mfd is None:
                    continue
                srcid = re.split('[!;]', src.source_id)[0]
                rates = tuple(mfd.get_annual_occurrence_rates())
                for t in trt_smrs:
                    key = (paths[t % TWO24], srcid)
                    table.setdefault(key, []).append(rates)
    return table


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


def check(job_ini, out, added, renamed, smlt, brnames):
    """
    Compare the rates of all the sources in all the realizations
    """
    warnings = []

    class Handler(logging.Handler):
        def emit(self, record):
            msg = record.getMessage()
            if 'appear multiple times' in msg:
                warnings.append(msg)
    handler = Handler()
    logging.getLogger().addHandler(handler)
    # NB: strict=false, so that the original logic tree can have invalid
    # branch IDs (the engine replaces their spaces with underscores)
    full = {'number_of_logic_tree_samples': '0', 'strict': 'false',
            'max_potential_paths': '100000000'}
    # the GMPEs are irrelevant for the rates, so a trivial GMPE logic
    # tree is used, written next to the job, since paths must be relative
    gsim_lt = job_ini.parent / '_check_gmmLT.xml'
    _trivial_gsim_lt(smlt, gsim_lt)
    full['gsim_logic_tree_file'] = gsim_lt.name
    relpath = os.path.relpath(out.resolve(), job_ini.parent.resolve())
    try:
        orig = _rates(job_ini, full)
        nwarn = len(warnings)
        conv = _rates(job_ini, dict(full,
                                    source_model_logic_tree_file=relpath))
    finally:
        logging.getLogger().removeHandler(handler)

    # remove the added branches from the paths and restore the original
    # IDs of the renamed sources (dummy branches were removed above)
    normed = {}
    for (path, srcid), rates in conv.items():
        key = (tuple(branch_id(brnames.get(b, b)) for b in path
                     if b not in added),
               renamed.get(srcid, srcid))
        normed.setdefault(key, []).extend(rates)
    conv = normed
    bad = []
    for key in set(orig) | set(conv):
        a, b = sorted(orig.get(key, [])), sorted(conv.get(key, []))
        if len(a) != len(b) or any(
                len(x) != len(y) or not numpy.allclose(x, y, rtol=1e-10)
                for x, y in zip(a, b)):
            bad.append(key)
    npaths = len({k[0] for k in orig})
    logging.warning('Checked %d realizations, %d (realization, source) '
                    'pairs: %d different', npaths, len(orig), len(bad))
    for key in sorted(bad, key=str)[:10]:
        logging.error('Different rates for %s', key)
    logging.warning('MFD variants warning: %d in the original, %d in the '
                    'converted logic tree', nwarn, len(warnings) - nwarn)
    return not bad


def make_zip(job_ini, smlt, out):
    """
    Complete the folder `_fixed`, which contains the rewritten source models,
    into a copy of the job where all the files have the original names:
    the converted logic tree is saved with the name of the original one
    and the other files of the job are linked (or copied) there; then zip
    it in the file job.zip, in the folder of the job and remove the folder
    `_fixed` and the converted logic tree. It works only if the logic tree is
    in the same folder of the job.ini, else nothing is removed.

    :param job_ini: path to the original job.ini file
    :param smlt: path to the original logic tree
    :param out: path to the converted logic tree
    :returns: the path to the zip file, or None
    """
    job_ini, smlt = Path(job_ini).resolve(), Path(smlt).resolve()
    jobdir = job_ini.parent
    if smlt.parent != jobdir:
        logging.warning('%s is not in the folder of %s: no job.zip',
                        smlt, job_ini)
        return
    pkg = jobdir / MFD_DIR
    # the converted tree refers to rewritten files as _fixed/<file>
    renames = {f'{MFD_DIR}/{f.relative_to(pkg).as_posix()}':
               f.relative_to(pkg).as_posix() for f in pkg.rglob('*')
               if f.is_file()}
    root, bsets = read_tree(out)
    _rewrite_tree(bsets, renames, {}, {})
    _write_xml(root, pkg / smlt.name)
    shutil.copy(job_ini, pkg / job_ini.name)
    # do not validate to avoid permissions errors on the export_dir
    oq = oqvalidation.OqParam(**readinput.get_params(str(job_ini)))
    for f in readinput.get_input_files(oq):
        dest = pkg / Path(f).resolve().relative_to(jobdir)
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.link(f, dest)
            except OSError:  # different file systems
                shutil.copy2(f, dest)
    archive = jobdir / 'job.zip'
    archive.unlink(missing_ok=True)  # zip_job refuses to overwrite
    oqzip.zip_job(str(pkg / job_ini.name), str(archive), log=logging.debug)
    logging.warning('Wrote %s', archive)
    shutil.rmtree(pkg)
    Path(out).unlink()
    return archive


def main(job_ini):
    """
    Convert the source model logic tree of the given job and check it;
    if the check is successful, write a job.zip file with the job using
    the converted logic tree (with the original file names).

    :param job_ini: path to a job.ini file
    :returns: True if the converted logic tree is equivalent to the
              original one (or if there is nothing to convert)
    """
    job_ini = Path(job_ini)
    inputs = readinput.get_params(job_ini)['inputs']
    if 'source_model_logic_tree' not in inputs:
        raise ValueError(f'{job_ini}: missing source_model_logic_tree_file')
    smlt = Path(inputs['source_model_logic_tree'])
    out = smlt.with_name(smlt.stem + '_mfd' + smlt.suffix)
    added, renamed, brnames = convert(smlt, out)
    if not added:  # nothing converted, nothing to check
        return True
    try:
        ok = check(job_ini, out, added, renamed, smlt, brnames)
    finally:
        (job_ini.parent / '_check_gmmLT.xml').unlink(missing_ok=True)
    if ok:
        make_zip(job_ini, smlt, out)
    return ok
