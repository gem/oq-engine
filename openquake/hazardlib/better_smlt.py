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
each copy a chain of single-branch correlated branchsets
(applyToSources="*"), one for each kind of MFD, restoring the original
MFDs in the branch:

- truncGutenbergRichterMFD -> abMaxMagAbsolute "a b maxMag" (the copies
  must have the same minMag)
- incrementalMFD -> incrementalMFDAbsolute
- multiMFD -> multiMFDAbsolute (the copies must have the same number of
  points)

The identical copies are then merged by the engine (see reduce_sources)
and the contexts are computed once for all the MFDs. The references to a
modified branch in the applyToBranches of the following branchsets are
replaced by the last branch of its chain. A source is skipped if a
branchset modifying it comes before the branchset loading it, since the
absolute MFD must be applied first. Sources sharing an ID in a file and
fragments of sources (colon convention, except in mutex groups) are
renamed, since applyToSources could not select them; branch IDs with
spaces are renamed too, since applyToBranches could not refer to them.

The rewritten source model files are stored in the folder `mfd` next to
the logic tree and the converted logic tree is written next to the
original one, with the suffix _mfd; the input files are never modified.
The converted logic tree is always checked: the original and the
converted logic tree are compared by applying the uncertainties with the
engine in each realization (with full enumeration of the source model
paths): the annual occurrence rates of all the sources must be the same.

Use it with `oq check_input --better-smlt job.ini`.
"""
import os
import re
import tempfile
import textwrap
import hashlib
import logging
import configparser
import xml.etree.ElementTree as ET
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

MFD_TAGS = {'truncGutenbergRichterMFD', 'incrementalMFD', 'multiMFD',
            'arbitraryMFD', 'YoungsCoppersmithMFD',
            'taperedGutenbergRichterMFD'}
UTYPE = {'truncGutenbergRichterMFD': 'abMaxMagAbsolute',
         'incrementalMFD': 'incrementalMFDAbsolute',
         'multiMFD': 'multiMFDAbsolute'}
SM_TYPES = ('sourceModel', 'extendModel')
BRANCH_ID_RE = re.compile(r'^[\w\:\#_\-\.]+$')  # as in valid.branch_id
BSET_RE = re.compile(r'<((?:\w+:)?)logicTreeBranchSet\b.*?'
                     r'</\1logicTreeBranchSet>', re.S)


def _tag(el):
    return el.tag.split('}')[-1]


class BranchSet:
    def __init__(self, ordinal, el, span, prefix, in_level=False):
        self.ordinal = ordinal
        self.in_level = in_level  # inside a logicTreeBranchingLevel
        self.id = el.attrib['branchSetID']
        self.utype = el.attrib['uncertaintyType']
        self.atb = el.attrib.get('applyToBranches', '').split()
        self.ats = el.attrib.get('applyToSources', '').split()
        self.span = span  # (start, end) in the text of the logic tree
        self.prefix = prefix  # namespace prefix, like 'ns0:'
        self.branches = []  # pairs (branchID, uncertaintyModel text)
        for br in el.iter():
            if _tag(br) == 'logicTreeBranch':
                [um] = [c for c in br if _tag(c) == 'uncertaintyModel']
                self.branches.append((br.attrib['branchID'],
                                      (um.text or '').strip()))

    def files(self, branch_id):
        # the source model files of a branch, as written in the tree
        if self.utype not in SM_TYPES:
            return []
        return dict(self.branches)[branch_id].split()


def read_tree(smlt):
    # the branchsets in order, with their spans in the text
    text = smlt.read_text(encoding='utf-8')
    root = ET.parse(smlt).getroot()
    parent = {c: p for p in root.iter() for c in p}
    elems = [el for el in root.iter() if _tag(el) == 'logicTreeBranchSet']
    spans = list(BSET_RE.finditer(text))
    if len(spans) != len(elems):
        raise ValueError(f'Cannot locate the branchsets in {smlt}')
    bsets = [BranchSet(i, el, m.span(), m.group(1),
                       _tag(parent[el]) == 'logicTreeBranchingLevel')
             for i, (el, m) in enumerate(zip(elems, spans))]
    return text, bsets


SRC_RE = re.compile(  # NB: like id= "x" or id='x'
    r'<(?:\w+:)?\w+Source\b[^>]*?\bid\s*=\s*["\']([^"\']*)["\']')


class Copy:
    # a copy of a source in a source model file; pos is the index of the
    # source in the file (in document order), used to rename it
    def __init__(self, fname, pos, el, group):
        self.fname = fname
        self.pos = pos
        self.id = el.attrib['id']
        mfds = [c for c in el if _tag(c) in MFD_TAGS]
        mfd = mfds[0] if mfds else None
        self.kind = _tag(mfd) if mfd is not None else None
        attrs = {k: v for k, v in el.attrib.items() if k != 'name'}
        geom = hashlib.md5(repr(sorted(attrs.items())).encode())
        for c in el:
            if _tag(c) not in MFD_TAGS:
                geom.update(ET.tostring(c))
        self.key = (self.id, repr(sorted(group.items())), geom.hexdigest())
        self.params = self.get_params(mfd)

    def get_params(self, mfd):
        # the MFD parameters as strings, as written in the file
        if self.kind == 'truncGutenbergRichterMFD':
            a = mfd.attrib
            return (a['aValue'], a['bValue'], a['maxMag'], a['minMag'])
        elif self.kind == 'incrementalMFD':
            [rates] = [c for c in mfd if _tag(c) == 'occurRates']
            return (mfd.attrib['minMag'], mfd.attrib['binWidth'],
                    ' '.join(rates.text.split()))
        elif self.kind == 'multiMFD':
            # kind, number of points and arrays of parameters
            return (mfd.attrib['kind'], mfd.attrib['size'],
                    tuple((_tag(c), ' '.join((c.text or '').split()))
                          for c in mfd))
        elif mfd is not None:
            return (hashlib.md5(ET.tostring(mfd)).hexdigest(),)
        return ()


def _ids(path):
    # the source IDs in a file, quickly
    return set(SRC_RE.findall(path.read_text(encoding='utf-8')))


def _parse(path, fname, ids):
    # the copies of the sources with the given IDs in a file
    root = ET.parse(path).getroot()
    parent = {c: p for p in root.iter() for c in p}
    copies, pos = [], 0
    for el in root.iter():
        if 'id' in el.attrib and _tag(el).endswith('Source'):
            if ids is None or el.attrib['id'] in ids:
                grp = parent.get(el)
                attrs = grp.attrib if grp is not None and _tag(grp) == \
                    'sourceGroup' else {}
                copies.append(Copy(fname, pos, el, attrs))
            pos += 1
    return copies


def read_copies(smlt_dir, fnames):
    """
    :returns: the copies of the sources appearing in more files, in
              document order, and their IDs; the files are read in parallel
    """
    fnames = list(fnames)
    paths = [smlt_dir / fname for fname in fnames]
    with ProcessPoolExecutor() as pool:
        idsets = list(pool.map(_ids, paths))
        count = {}
        for ids in idsets:
            for srcid in ids:
                count[srcid] = count.get(srcid, 0) + 1
        multi = {srcid for srcid, n in count.items() if n > 1}
        args = [(path, fname, ids & multi) for path, fname, ids in
                zip(paths, fnames, idsets) if ids & multi]
        results = pool.map(_parse, *zip(*args)) if args else []
        return [cp for copies in results for cp in copies], multi


def _group(copies):
    # the copies grouped by (source ID, source group, geometry)
    bykey = {}
    for cp in copies:
        bykey.setdefault(cp.key, []).append(cp)
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
    count = {}
    for cp in copies:
        count[cp.fname, cp.id] = count.get((cp.fname, cp.id), 0) + 1
    dupl = {srcid for (_, srcid), n in count.items() if n > 1}
    groups = _group(copies)
    variant = {key[0] for key, cps in groups.items() if _has_variants(cps)}
    # the fragments (colon convention) are seen by the logic tree with
    # their base name, so they are renamed too, except in mutex groups
    frags = {key[0] for key in groups if ':' in key[0] and
             "'mutex'" not in key[1]}
    dupl = (dupl | frags) & variant
    nkeys = {}
    for key in groups:
        nkeys[key[0]] = nkeys.get(key[0], 0) + 1
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


def _rename_ids(text, new_ids):
    # replace the IDs of the sources of a file, given by position,
    # in a single pass over the text
    pieces, last = [], 0
    for pos, m in enumerate(SRC_RE.finditer(text)):
        if pos in new_ids:
            pieces.append(text[last:m.start(1)])
            pieces.append(new_ids[pos])
            last = m.end(1)
    pieces.append(text[last:])
    return ''.join(pieces)


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
        elif kinds == {'truncGutenbergRichterMFD'} and len(
                {cp.params[3] for cp in copies}) > 1:
            skipped.append((src, 'different minMag'))
        elif kinds == {'multiMFD'} and len(
                {cp.params[:2] for cp in copies}) > 1:
            skipped.append((src, 'different kind or number of points'))
        else:
            variants.append(copies)
    return variants, skipped


END_RE = re.compile(r'</(?:\w+:)?\w+Source>')
LEVEL_END_RE = re.compile(r'</(?:\w+:)?logicTreeBranchingLevel>')


def _new_body(body, base):
    # the text of a source with the MFD parameters of the base copy
    if base.kind == 'multiMFD':
        m = re.search(r'<(\w+:)?multiMFD\b.*?</\1?multiMFD>', body, re.S)
        # the indentation of the line of the multiMFD element
        start = body.rfind('\n', 0, m.start()) + 1
        ind = re.match(r'[ \t]*', body[start:]).group(0)
        return (body[:m.start()] +
                _multi(m.group(1) or '', base.params, ind) + body[m.end():])
    elif base.kind == 'truncGutenbergRichterMFD':
        a, b, mmax, _ = base.params
        for name, val in (('aValue', a), ('bValue', b), ('maxMag', mmax)):
            body = re.sub(r'\b%s="[^"]*"' % name, f'{name}="{val}"', body,
                          count=1)
    else:
        mmin, width, rates = base.params
        body = re.sub(r'(<(?:\w+:)?incrementalMFD\b[^>]*?)minMag="[^"]*"',
                      r'\g<1>minMag="%s"' % mmin, body, count=1)
        body = re.sub(r'(<(?:\w+:)?incrementalMFD\b[^>]*?)binWidth="[^"]*"',
                      r'\g<1>binWidth="%s"' % width, body, count=1)
        body = re.sub(r'(<(?:\w+:)?occurRates>).*?(</(?:\w+:)?occurRates>)',
                      r'\g<1>%s\g<2>' % rates, body, count=1, flags=re.S)
    return body


def _set_mfds(text, bases):
    # replace the MFDs of the sources given by position with the MFDs of
    # their base copies, in a single pass over the text
    pieces, last = [], 0
    for pos, m in enumerate(SRC_RE.finditer(text)):
        if pos in bases:
            stop = END_RE.search(text, m.end()).end()
            pieces.append(text[last:m.start()])
            pieces.append(_new_body(text[m.start():stop], bases[pos]))
            last = stop
    pieces.append(text[last:])
    return ''.join(pieces)


def _multi(prefix, params, indent=''):
    # a multiMFD element with the given parameters, one array per line,
    # wrapped to avoid lines longer than 79 characters; the first line is
    # not indented, since the caller writes it after its own indentation
    p, ind = prefix, indent
    kind, size, arrays = params
    lines = [f'<{p}multiMFD kind="{kind}" size="{size}">']
    for tag, text in arrays:
        lines.append(f'{ind}    <{p}{tag}>')
        lines.extend(textwrap.wrap(
            text, width=79, initial_indent=ind + ' ' * 8,
            subsequent_indent=ind + ' ' * 8))
        lines.append(f'{ind}    </{p}{tag}>')
    lines.append(f'{ind}</{p}multiMFD>')
    return '\n'.join(lines)


def _value(prefix, cp, indent=''):
    # the MFD of a copy, as written in an uncertaintyModel; indent is the
    # indentation of the element containing the value
    p = prefix
    if cp.kind == 'truncGutenbergRichterMFD':
        return '%s %s %s' % cp.params[:3]
    elif cp.kind == 'multiMFD':
        ind = indent + ' ' * 4
        return f'\n{ind}' + _multi(p, cp.params, ind) + f'\n{indent}'
    mmin, width, rates = cp.params
    return (f'<{p}incrementalMFD minMag="{mmin}" binWidth="{width}">'
            f'<{p}occurRates>{rates}</{p}occurRates></{p}incrementalMFD>')


def _link(prefix, bsid, parent, pairs, branch_id, indent, level=False):
    # a single-branch correlated branchset setting the MFDs of the given
    # sources, all with the same kind of MFD; with level=True it is
    # wrapped in a logicTreeBranchingLevel (NRML 0.4)
    p, ind = prefix, indent
    if level:
        bset = _link(prefix, bsid, parent, pairs, branch_id, indent)
        return (f'\n{ind}<{p}logicTreeBranchingLevel branchingLevelID='
                f'"{bsid}">{bset}\n{ind}</{p}logicTreeBranchingLevel>')
    cind = ind + ' ' * 12  # indentation of the correlated elements
    rows = ''.join(f'\n{cind}<{p}correlated src="{src_id}">'
                   f'{_value(p, cp, cind)}</{p}correlated>'
                   for src_id, cp in pairs)
    return (f'\n{ind}<{p}logicTreeBranchSet branchSetID="{bsid}" '
            f'uncertaintyType="{UTYPE[pairs[0][1].kind]}"\n{ind}    '
            f'applyToBranches="{parent}" applyToSources="*">\n'
            f'{ind}    <{p}logicTreeBranch branchID="{branch_id}">\n'
            f'{ind}        <{p}uncertaintyModel>{rows}\n'
            f'{ind}        </{p}uncertaintyModel>\n'
            f'{ind}        <{p}uncertaintyWeight>1.0'
            f'</{p}uncertaintyWeight>\n'
            f'{ind}    </{p}logicTreeBranch>\n'
            f'{ind}</{p}logicTreeBranchSet>')


def _replace_files(bset_text, branch_id, renames):
    # replace the file names in the uncertaintyModel of a branch
    m = re.search(r'<(?:\w+:)?logicTreeBranch\b[^>]*?'
                  r'branchID\s*=\s*["\']%s["\'][^>]*>'
                  r'(.*?)</(?:\w+:)?logicTreeBranch>' % re.escape(branch_id),
                  bset_text, re.S)
    body = m.group(1)
    for old, new in renames.items():
        # NB: a file name can be next to the tags, as in <tag>name</tag>
        body = re.sub(r'(?<![^\s>])%s(?![^\s<])' % re.escape(old), new,
                      body)
    return bset_text[:m.start(1)] + body + bset_text[m.end(1):]


def _links(variants, carriers):
    # the copies with a MFD different from the base, by carrier branch
    links = {}  # (bset ordinal, branch ID) -> [(source ID, copy)]
    for copies in variants:
        base = copies[0]
        for cp in copies:
            if cp.params != base.params:
                for key in carriers[cp.fname]:
                    links.setdefault(key, []).append((cp.id, cp))
    return links


def _identity(smlt_dir, fnames, avoid, newids):
    # a source of the files with a MFD that a link can set to itself;
    # newids are the IDs after renaming, by (file, position)
    for fname in fnames:
        path = smlt_dir / fname
        ids = [newids.get((fname, pos), srcid) for pos, srcid in
               enumerate(SRC_RE.findall(path.read_text(encoding='utf-8')))]
        count = {}
        for srcid in ids:
            count[srcid] = count.get(srcid, 0) + 1
        ok = {pos for pos, srcid in enumerate(ids) if count[srcid] == 1
              and ':' not in srcid and srcid not in avoid}
        if not ok:
            continue
        for cp in _parse(path, fname, None):
            if cp.pos in ok and cp.kind in UTYPE:
                cp.id = ids[cp.pos]
                return cp
    return None


def _unsafe(copies, variants, multi, renamed):
    # the IDs of sources in more files with different copies (the engine
    # adds the branch to their IDs, so applyToSources cannot select them)
    byid = {}
    for cp in copies:
        byid.setdefault(cp.id, []).append(cp)
    converted = {cps[0].id for cps in variants}
    safe = {srcid for srcid, cps in byid.items()
            if len({cp.key for cp in cps}) == 1 and (
                len({cp.params for cp in cps}) == 1 or srcid in converted)}
    return (set(multi) | set(renamed.values()) | set(byid)) - safe


def complete_chains(variants, bsets, carriers, smlt_dir, renamed, multi,
                    copies):
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
    newids = {(cp.fname, cp.pos): cp.id for cp in copies}
    skipped = []
    while True:
        unsafe = _unsafe(copies, variants, multi, renamed)
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
                cp = _identity(smlt_dir, files, avoid, newids)
                if cp is None:
                    bad[ordinal] = 'no source for an identity link'
                    break
                identity[ordinal, br_id] = [(cp.id, cp)]
        if not bad:
            return variants, links, identity, skipped
        ok = []
        for copies in variants:
            reasons = {f'{bsets[o].id}: {bad[o]}' for cp in copies
                       for o, _ in carriers[cp.fname] if o in bad}
            if reasons:
                skipped.append((copies[0].id, '; '.join(sorted(reasons))))
            else:
                ok.append(copies)
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
    copies, multi = read_copies(smlt_dir, carriers)
    renamed = rename_duplicates(copies)
    variants, skipped = find_variants(_group(copies))
    variants, skip2 = _check_order(variants, bsets, carriers, renamed)
    variants, links, identity, skip3 = complete_chains(
        variants, bsets, carriers, smlt_dir, renamed, multi, copies)
    return (carriers, copies, renamed, variants, links, identity,
            skipped + skip2 + skip3)


def _write_files(smlt_dir, copies, renamed, variants):
    # write the source model files with the renamed sources and the MFDs
    # normalized to the MFD of the first copy, in the folder mfd;
    # return a dictionary file -> new file
    texts = {}  # file -> new text
    new_ids = {}  # file -> {position: new ID}
    for cp in copies:
        if cp.id in renamed:
            new_ids.setdefault(cp.fname, {})[cp.pos] = cp.id
    for fname in sorted(new_ids):
        texts[fname] = _rename_ids(
            (smlt_dir / fname).read_text(encoding='utf-8'), new_ids[fname])
    bases = {}  # file -> {position: base copy}
    for cps in variants:
        for cp in cps:
            if cp.params != cps[0].params:
                bases.setdefault(cp.fname, {})[cp.pos] = cps[0]
    for fname, dic in bases.items():
        if fname not in texts:
            texts[fname] = (smlt_dir / fname).read_text(encoding='utf-8')
        texts[fname] = _set_mfds(texts[fname], dic)
    renames = {fname: str(Path('mfd') / fname) for fname in texts}
    for fname, txt in texts.items():
        path = smlt_dir / renames[fname]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(txt, encoding='utf-8')
    return renames


def _build_chains(text, bsets, links, identity):
    # build the chains, to be inserted after the branchsets of the
    # modified branches; return (added branch IDs, chain ends, inserts)
    used = {br for bs in bsets for br, _ in bs.branches}
    chain_end, added, inserts = {}, [], {}
    for bs in bsets:
        line_start = text.rfind('\n', 0, bs.span[0]) + 1
        indent = re.match(r'[ \t]*', text[line_start:bs.span[0]]).group(0)
        chains = []
        for br_id, _ in bs.branches:
            parent = br_id
            pairs = links.get((bs.ordinal, br_id)) or identity.get(
                (bs.ordinal, br_id), [])
            # one correlated link for each kind of MFD
            bykind = {}
            for src_id, cp in sorted(pairs, key=lambda pair: pair[0]):
                bykind.setdefault(cp.kind, []).append((src_id, cp))
            for n, kind in enumerate(sorted(bykind), 1):
                new_id = f'{br_id}_mfd{n}'
                while new_id in used:
                    new_id += '_'
                used.add(new_id)
                chains.append(_link(bs.prefix, f'{bs.id}_{new_id}', parent,
                                    bykind[kind], new_id, indent,
                                    bs.in_level))
                added.append(new_id)
                parent = new_id
            if parent != br_id:
                chain_end[br_id] = parent
        inserts[bs.ordinal] = ''.join(chains)
    return added, chain_end, inserts


def _rewrite_tree(text, bsets, brnames, renames, renamed, chain_end,
                  inserts):
    # rewrite the logic tree, from the end to keep the spans valid
    for bs in reversed(bsets):
        start, end = bs.span
        btext = text[start:end]
        for new, old in brnames.items():
            btext = re.sub(r'(branchID\s*=\s*["\'])%s(["\'])'
                           % re.escape(old), r'\g<1>%s\g<2>' % new, btext)
        for br_id, _ in bs.branches:
            rn = {f: renames[f] for f in bs.files(br_id) if f in renames}
            if rn:
                btext = _replace_files(btext, br_id, rn)
        new = ' '.join(' '.join(_expand(src, renamed)) for src in bs.ats)
        if new != ' '.join(bs.ats):
            btext = re.sub(r'applyToSources\s*=\s*["\'][^"\']*["\']',
                           f'applyToSources="{new}"', btext, count=1)
        if any(br in chain_end for br in bs.atb):
            new = ' '.join(chain_end.get(br, br) for br in bs.atb)
            btext = re.sub(r'applyToBranches\s*=\s*["\'][^"\']*["\']',
                           f'applyToBranches="{new}"', btext, count=1)
        # NB: a branchset in a branching level is followed by the levels
        # of its chains, since a level can contain a single branchset
        tail = text[end:]
        pos = LEVEL_END_RE.search(tail).end() if bs.in_level else 0
        text = (text[:start] + btext + tail[:pos] + inserts[bs.ordinal] +
                tail[pos:])
    return text


def convert(smlt, out):
    """
    Convert the MFD variants of a source model logic tree, writing the
    new logic tree in `out` and the new source model files in the folder
    `mfd` (nothing is written if there is nothing to convert)

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
    text, bsets = read_tree(smlt)
    brnames = rename_branches(bsets)
    (carriers, copies, renamed, variants, links, identity,
     skipped) = _read_variants(smlt_dir, bsets)
    for src, reason in skipped:
        logging.info('Not converted %s: %s', src, reason)
    if not variants:  # nothing to convert, nothing is written
        logging.warning('%s: no MFD variants to convert (%d skipped)',
                        smlt, len(skipped))
        return set(), {}, {}
    renames = _write_files(smlt_dir, copies, renamed, variants)
    added, chain_end, inserts = _build_chains(text, bsets, links, identity)
    out.write_text(_rewrite_tree(text, bsets, brnames, renames, renamed,
                                 chain_end, inserts), encoding='utf-8')
    for new, old in renamed.items():
        logging.info('Renamed source %s -> %s', old, new)
    for new, old in brnames.items():
        logging.info('Renamed branch %r -> %s', old, new)
    logging.warning('%s: %d source(s) converted, %d skipped, %d file(s) '
                    'rewritten in %s, %d branchset(s) added', out,
                    len(variants), len(skipped), len(renames),
                    smlt_dir / 'mfd', len(added))
    return set(added), renamed, brnames


def _rates(job_ini, kw):
    # rates of the sources by (realization path, source ID)
    from openquake.commonlib import readinput
    from openquake.commonlib.datastore import DataStore
    oq = readinput.get_oqparam(str(job_ini), kw=kw)
    # a temporary datastore, needed for the sections of multiFaultSources
    with tempfile.TemporaryDirectory() as tmp:
        dstore = DataStore(os.path.join(tmp, 'check.hdf5'))
        dstore['oqparam'] = oq
        try:
            csm = readinput.get_composite_source_model(oq, dstore)
            return _rates_table(csm)
        finally:
            dstore.close()


def _rates_table(csm):
    # the rates of the sources in each realization, uncertainties applied
    from openquake.hazardlib.source_reader import (
        modified_groups, get_bset_values, TWO24)
    full = csm.full_lt
    paths = [tuple(rlz.lt_path) for rlz in full.sm_rlzs]
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
    # a GMPE logic tree with a single GMPE per tectonic region type, so
    # that the full enumeration involves only the source model paths
    from xml.sax.saxutils import quoteattr
    from openquake.hazardlib.logictree import SourceModelLogicTree
    trts = sorted(SourceModelLogicTree(str(smlt)).tectonic_region_types)
    bsets = ''.join(
        f'<logicTreeBranchSet uncertaintyType="gmpeModel" '
        f'branchSetID="bs{i}" applyToTectonicRegionType={quoteattr(trt)}>'
        f'<logicTreeBranch branchID="b{i}"><uncertaintyModel>'
        f'BooreAtkinson2008</uncertaintyModel><uncertaintyWeight>1.0'
        f'</uncertaintyWeight></logicTreeBranch></logicTreeBranchSet>\n'
        for i, trt in enumerate(trts))
    path.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n<nrml xmlns='
        '"http://openquake.org/xmlns/nrml/0.5">\n<logicTree logicTreeID='
        f'"lt1">\n{bsets}</logicTree>\n</nrml>\n', encoding='utf-8')


def check(job_ini, out, added, renamed, smlt, brnames):
    """
    Compare the rates of all the sources in all the realizations
    """
    from openquake.hazardlib.logictree import branch_id
    import numpy
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

    # remove the added branches and the dummy branches from the paths and
    # restore the original IDs of the renamed sources
    normed = {}
    for (path, srcid), rates in conv.items():
        key = (tuple(branch_id(brnames.get(b, b)) for b in path
                     if b not in added and b != '.'),
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


def main(job_ini):
    """
    Convert the source model logic tree of the given job and check it.

    :param job_ini: path to a job.ini file
    :returns: True if the converted logic tree is equivalent to the
              original one (or if there is nothing to convert)
    """
    job_ini = Path(job_ini)
    cfg = configparser.ConfigParser(inline_comment_prefixes=('#',))
    cfg.read(job_ini)
    fnames = [v for sec in cfg.sections() for k, v in cfg.items(sec)
              if k == 'source_model_logic_tree_file']
    if not fnames:
        raise ValueError(f'{job_ini}: missing source_model_logic_tree_file')
    smlt = job_ini.parent / fnames[0].strip()
    out = smlt.with_name(smlt.stem + '_mfd' + smlt.suffix)
    added, renamed, brnames = convert(smlt, out)
    if not added:  # nothing converted, nothing to check
        return True
    try:
        return check(job_ini, out, added, renamed, smlt, brnames)
    finally:
        (job_ini.parent / '_check_gmmLT.xml').unlink(missing_ok=True)
