import os
import copy
import json
import csv
import re
from nipy import load_image
import numpy as np


def dice_coef(nii_a, nii_b):
    """
    Dice Coefficient:
        D = 2*(A == B)/(A)+(B)
    
    Input is two binary masks in the same 3D space
    NII format
    
    Output is a DICE score
    """
    
    image_a = load_image(nii_a)
    data_a = image_a.get_data()
    sum_a = np.sum(data_a)

    image_b = load_image(nii_b)
    data_b = image_b.get_data()
    sum_b = np.sum(data_b)
    
    overlap = data_a + data_b
    intersect = overlap[np.where(overlap == 2)].sum()
    
    dice = intersect / (sum_a + sum_b)
    
    return dice


def flatten(s, accepted_types=(list, tuple)):
    """flatten lists and tuples to a single list, ignore empty
    
    Parameters
    ----------
    s       :    Sequence
    accepted_types  :    Tuple (acceptable sequence types, default (list,tuple)
    
    Return
    ------
    l       :    Flat sequence
    
    Example
    -------
    flatten(('Hello',[' ',2],[' '],(),['the',[([' '])],('World')]))
    ('Hello', ' ', 2, ' ', 'the', ' ', 'World')
    """
    s_type = type(s)
    s = list(s)
    i = 0
    while i < len(s):
        while isinstance(s[i], accepted_types):
            if not s[i]:
                s.pop(i)
                i -= 1
                break
            else:
                s[i:i+1] = s[i]
        i += 1
    return s_type(s)


def list_to_str(sep=None, args=None):
    """flattened args turned to str with separator
    default separator: ''
    
    Parameters
    ----------
    sep     :    Str (separator for join)
    args    :    List or Tuple (almost any depth, may have empties)
    
    Return
    ------
    Str (sep.join(args)
    
    Example
    -------
    list_to_str(
        sep='',args=('Hello',[' ',2],[' '],(),['the',[([' '])],('World')])
        )
    'Hello 2 the World'
    """
    if sep is None:
        sep = ''
    if args is None:
        raise TypeError("Not enough arguments for str creation")
    return sep.join(str(e) for e in flatten(args))


def join_strs(sep=None, **kwargs):
    """Interface between list_to_str and Nipype function nodes
    
    Parameters
    ----------
    sep     :   Str (separator for join, default '')
    kwargs  :   Str (arguments will be joined by sep)
    
    Return
    ------
    Str (sep.join(kwargs.itervalues())
    
    Example
    -------
    join_strs(sep='_', arg0='foo', arg1='bar', arg2='baz')
    'foo_bar_baz'
    """
    # import in function for nipype
    from DINGO.utils import list_to_str
    if sep is None:
        sep = ''
    arglist = []
    for arg in kwargs.itervalues():
        arglist.append(arg)
    return list_to_str(sep=sep, args=arglist)


def split_filename(fname, special_extensions=None):
    """Split a filename into path, base filename, and extension.
    Similar to nipype.utils.filemanip.split_filename, but with other
    special extensions, and ability to change them.
    
    Parameters
    ----------
    fname               :    str - file or path name
    special_extensions  :    list
        list of extensions to split manually (several '.')
        
    Returns
    -------
    path    :    str - base path from fname
    fname   :    str - base filename, without extension
    ext     :    str - file extension from fname
    """
    # import in function for nipype
    import os
    
    default_se = ('.nii.gz', 
                  '.tar.gz',
                  '.fib.gz',
                  '.src.gz',
                  '.trk.gz',
                  '.trk.txt')
    
    if special_extensions is None:
        special_extensions = default_se
    else:
        special_extensions.extend(default_se)
                            
    path = os.path.dirname(fname)
    fname = os.path.basename(fname)

    ext = None
    for special_ext in special_extensions:
        ext_len = len(special_ext)
        if (len(fname) > ext_len) and \
           (fname[-ext_len:].lower() == special_ext.lower()):
            ext = fname[-ext_len:]
            fname = fname[:-ext_len]
            break
    if not ext:
        fname, ext = os.path.splitext(fname)

    return path, fname, ext


def fileout_util(names=None, file_list=None, substitutions=None,
                 psep='_', nsep='.', sub_id=None, scan_id=None, uid=None):
    """Utility for sinker nodes to create container, folders, substitutions
    
    Parameters
    ----------
    names           :    list - parent folder names
    file_list       :    list - files to sink
    substitutions   :    list[tuple(str, str)
        [('str2replace', 'input_id_suffix')]
    sub_id          :    str - subject id
    scan_id         :    str - scan id
    uid             :    str - unique sequence id
    psep            :    str - prefix separator for filename 
        prefix = 'sub_id{psep}scan_id{psep}uid'
    nsep            :    str - name separator for DataSink node
        'name1{nsep}name2{nsep}'
    
    
    Returns
    -------
    container       :    str - os.path.join(sub_id,scan_id)
    out_file_list   :    list[str] prefix_suffix
    newsubs         :    list[(str, str)] - [('str2replace', 'prefix_suffix')]
    """
    # import in function for nipype
    from DINGO.utils import list_to_str, split_filename
    import os

    container = os.path.join(sub_id, scan_id)
    
    # out_file_list
    if names is not None and isinstance(names, (list, tuple, str)):
        folder = list_to_str(sep=nsep, args=(names, ''))  # extra empty=add nsep
    else:
        folder = ''
    sinkfile = ''.join((folder, '@sinkfile'))
    
    setfl = []
    if file_list is not None:
        if not isinstance(file_list, (tuple, list)):
            file_list = (file_list,)
            setfl = set().union(file_list)
            if len(setfl) != len(file_list):
                raise IndexError('file_list does not have all unique elements')
        else:
            raise TypeError('file_list is not a tuple or list')

    out_file_list = []
    for elt in setfl:
        _, newelt, _ = split_filename(elt)
        out_file_list.append(sinkfile.replace('sinkfile', newelt))

    # newsubs
    prefix = list_to_str(sep=psep, args=(sub_id, scan_id, uid))
    newsubs = []
    if substitutions is not None and isinstance(substitutions, (list, tuple)):
        for elt in substitutions:
            newsubs.append((elt[0], elt[1].replace('input_id', prefix)))
    
    return container, out_file_list, newsubs


def reverse_lookup(indict, value):
    for key in indict:
        if indict[key] == value:
            return key
    raise ValueError('Value: %s, Dict: %s' % (value, indict))


def update_dict(indict=None, **kwargs):
    """update key/value pairs dictionary with type checking
    
    Parameters
    ----------
    indict      :    Dict
    kwargs      :    Dict / key/value pairs, key=value
    
    Returns
    -------
    outdict     :    Dict (new dictionary, indict unchanged)
    
    out=update_dict(indict=d, key=value)
    """
    import copy
    if indict is None:
        outdict = dict()
    elif not isinstance(indict, dict):
        raise TypeError('indict: {} is not a dictionary'.format(indict))
    else:
        outdict = copy.deepcopy(indict)
    for k, v in kwargs.iteritems():
        if k in outdict:
            tv = type(v)
            td = type(outdict[k])
            if tv == td:
                outdict.update([(k, v)])
            else:
                raise TypeError('Type({}): {}, != Type({}): {}'
                                .format(k, tv, k, td))
        else:
            outdict.update([(k, v)])
    return outdict


def patient_scan(patientcfg, add_sequence=None, sep=None):
    """Get patient/scan id

    Parameters
    ----------
    patientcfg      :   Dict < json (patient config file with pid, scanid in top level)
    add_sequence     :   Bool (Flag to join sequence id with pid, scanid)
    sep             :   Str (separator, default '_')

    Returns
    -------
    patient_scan_id :   str (concatenated)
    """

    if "pid" in patientcfg:
        patient_id = patientcfg["pid"]
    else:
        raise KeyError("patient_config:pid")
    if "scanid" in patientcfg:
        scan_id = patientcfg["scanid"]
    else:
        raise KeyError("patient_config:scanid")
    if add_sequence is None:
        add_sequence = False
    if sep is None:
        sep = '_'
    ps_id = []
    ps_id.extend((patient_id, sep, scan_id))

    if add_sequence:  # if True, default False
        if "sequenceid" in patientcfg:
            seq_id = patientcfg["sequenceid"]
            ps_id.extend((sep, seq_id))
        else:
            raise KeyError("patient_config:sequenceid")
    patient_scan_id = "".join(ps_id)

    return patient_scan_id


def split_chpid(psid, sep):
    """Returns patient/scan/uid from input id
    
    Parameters
    ----------
    psid        :    Str (patient id, scan id, uid)
    sep         :    Str (separator of the ids)
    
    Returns
    -------
    patientid   :    Str (first or first two fields, depending on CHD presence)
    scanid      :    Str (second or third field)
    uid         :    Str (the rest)

    e.g. XXXX_YYYY_ZZZZ         ->  XXXX, YYYY, ZZZZ
         XXXX_YYYY_ZZZZ_ZZZZ    ->  XXXX, YYYY, ZZZZ_ZZZZ
         CHD_XXX_YYYY_ZZZZ      ->  CHD_XXX, YYYY, ZZZZ
         CHD_XXX_YYYY_ZZZZ_ZZZZ ->  CHD_XXX, YYYY, ZZZZ_ZZZZ
"""
    if not isinstance(psid, (str, unicode)):
        raise TypeError('{} is not a string'.format(psid))
    if not isinstance(sep, (str, unicode)):
        raise TypeError('{} is not a string'.format(sep))

    splitid = psid.split(sep)
    if splitid[0] == "CHD":
        subind = 0
        scanind = 2
        uniind = 3
    else:
        subind = 0
        scanind = 1
        uniind = 2

    subid = "_".join(splitid[subind:scanind])
    scanid = "_".join(splitid[scanind:uniind])
    uniid = "_".join(splitid[uniind:])
    return subid, scanid, uniid


def tobool(s):
    """Convert string/int true/false values to bool
    
    Parameter
    ---------
    s        :    Boolean representation 
    
    Return
    ------
    Bool    
    
    Examples
    --------
    tobool(True)    ->    True
    tobool('t')     ->    True
    tobool('YeS')   ->    True
    tobool(1)       ->    True
    """
    true = (1, '1', 't', 'true', 'y', 'yes')
    false = (0, '0', 'f', 'false', 'n', 'no')

    if isinstance(s, bool):
        return s
    if isinstance(s, (str, unicode)):
        s = s.lower()
    if s in true:
        return True
    elif s in false:
        return False
    else:
        raise ValueError('{} cannot be converted to bool'.format(s))
    
    
def add_id_subs(input_id=None, subs=None):
    """create dataout substitutions combining subs with input_id"""
    repl = []
    if input_id is not None:
        if (subs is not None) and isinstance(subs, (list, tuple)):
            for e in subs:
                if isinstance(e, tuple) and len(e) == 2 and e[1] == 'input_id':
                    newe = (e[0], input_id)
                    repl.append(newe)
                else:
                    repl.append(e)
        else:
            msg = 'create_out_subs:repl must be list or tuple of tuples'
            raise TypeError(msg)
                    
    else:
        msg = 'create_out_subs:input_id must be specified'
        raise NameError(msg)
        
    return repl
    

def byteify(data, ignore_dicts=False):
    if isinstance(data, unicode):
        return data.encode('utf-8')
    if isinstance(data, list):
        return [byteify(item, ignore_dicts=True) for item in data]
    if isinstance(data, dict) and not ignore_dicts:
        return {
            byteify(key, ignore_dicts=True): byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()
        }
    return data


def json_load_byteified(handle):
    return byteify(
        json.load(handle, object_hook=byteify), ignore_dicts=True
    )


def read_setup(setuppath):
    """Read in json config file

    Parameters
    ----------
    setuppath : str (absolute path to file)

    Returns
    -------
    config : dict < json
    """
    # import must be self-contained for use with nipype function node
    import logging
    from DINGO.utils import json_load_byteified
    logger = logging.getLogger(__name__)
    try:
        with open(setuppath) as setup_file:
            setup = json_load_byteified(setup_file)
            setup_file.close()
    except Exception:
        logger.exception("Config file could not be read: " + setuppath)
        raise
    return setup


def read_file(filename):
    """From filename, read all lines, return contents as string

    Parameters
    ----------
    filename    :   Str

    Returns
    -------
    file contents   :   Str (None if not found)
    """
    try:
        with open(filename, 'r') as f:
            from_file = f.read()
    except IOError:
        from_file = None
    return from_file


def read_list_by_lines(filename):
    """From filename, read all lines, return lines as list without newline

    Parameters
    ----------
    filename    :   Str

    Returns
    -------
    file_contents   :   List
    """
    from_file = read_file(filename)
    id_list = from_file.split('\n')

    n_blank_lines = id_list.count('')
    for _ in xrange(0, n_blank_lines):
        id_list.remove('')
    return id_list


def read_ind_stats_file(filename):
    """Given a dsi_studio stats file, return list of [key, value] pairs

    Parameters
    ----------
    filename    :   Str

    Returns
    -------
    Labeled stats   :   List[ [Name, Value], ... ]
    """
    ind_data_list = read_list_by_lines(filename)
    ind_data_list = [ele.strip().replace(' ', '_') for ele in ind_data_list]
    ind_data_list = map(lambda x: x.split('\t'), ind_data_list)
    return ind_data_list


def read_ind_stats_from_dir(directory, file_list, pattern):
    """Find first(only) file in directory matching pattern, return its data
    as a list of pairs. If not found returns None.
    """
    ind_data_list = None
    for afile in file_list:
        if re.search(pattern, afile):
            ind_data_list = read_ind_stats_file(os.path.join(directory, afile))
            # only one with one individual per folder so break loop and return early
            break
    return ind_data_list


def update_dict_from_list(data_dict, data_list, primary, secondary_list):
    """With List[ [secondarykey, value] ],
    update dict { primary_secondarykey: value }"""
    for secondary in secondary_list:
        key2update = '_'.join((primary, secondary))

        for pair in data_list:
            if secondary in pair[0]:
                data_dict.update({key2update: pair[1]})


def collate_tract_stats(file_lists, ids, category, tracts, stats, directory, fileout_bn):
    """Write CSV id_category, tract_stat to fileout_bn.
    When tract not found, values will be ''

    Parameters
    ----------
    file_lists  :   List[List[Str]] (list of lists of tract statistics files)
    ids         :   List[Str] (list of id strs matching file_lists index)
    category    :   Str or List[Str] (if Str, apply to all ids,
        if List[Str], apply to id with matching index)
    tracts      :   List[Str] (tracts for which to get statistics)
    stats       :   List[Str] (stats to get for each tract)
    directory   :   Str (directory to which to write file)
    fileout_bn  :   Str (basename of file to write)

    Outputs
    -------
    collated_stats_file :   os.path.abspath(fileout_bn) WILL OVERWRITE"""
    if category is not None:
        if isinstance(category, str):
            ids_cat = ('_'.join((anid, category)) for anid in ids)
        if isinstance(category, (list, tuple)):
            ids_cat = ('_'.join((ids[i], category[i])) for i in xrange(len(ids)))
    else:
        ids_cat = ids
    ts_fixed = [ts.replace(' ', '_') for ts in stats]
    tract_tsf = ['_'.join((t, tsf)) for t in tracts for tsf in ts_fixed]
    fieldnames = ['id']
    fieldnames.extend(tract_tsf)

    base_dict = {ttsf: None for ttsf in tract_tsf}
    data = [dict(id=anid, **base_dict) for anid in ids_cat]

    for idx in xrange(len(ids)):
        files = file_lists[idx]
        for afile in files:
            # file vs tract check
            tract_data = read_ind_stats_file(afile)
            if tract_data is not None:
                update_dict_from_list(data[idx], tract_data, t, ts_fixed)

    write_group_file(base_dir, fileout_bn, fieldnames, data)


def write_group_file(out_dir, fileout_bn, fn, data):
    """Write list of dicts as fileout_bn to out_dir

    Parameters
    ----------
    out_dir     :   Str (directory which to write file)
    fileout_bn  :   Str (basename of file to write)
    fn          :   List (fieldnames / column headers)
    data        :   List[Dict] (each dict a source for a row)

    Writes
    ------
    out_file    :   CSV (will overwrite)
    """
    out_file = os.path.join(out_dir, fileout_bn)
    with open(out_file, 'wb') as f:
        w = csv.DictWriter(f, fieldnames=fn)
        w.writeheader()
        [w.writerow(row) for row in data]
