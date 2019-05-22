from __future__ import division
from builtins import str
from past.utils import old_div
import os
import importlib
import copy
import json
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
    Str (sep.join(kwargs.values())
    
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
    for arg in list(kwargs.values()):
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
    for k, v in list(kwargs.items()):
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
    if not isinstance(psid, str):
        raise TypeError('{} is not a string'.format(psid))
    if not isinstance(sep, str):
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
    if isinstance(s, str):
        s = s.lower()
    if s in true:
        return True
    elif s in false:
        return False
    else:
        raise ValueError('{} cannot be converted to bool'.format(s))
    

def byteify(data, ignore_dicts=False):
    if isinstance(data, str):
        return data.encode('utf-8')
    if isinstance(data, list):
        return [byteify(item, ignore_dicts=True) for item in data]
    if isinstance(data, dict) and not ignore_dicts:
        return {
            byteify(key, ignore_dicts=True): byteify(value, ignore_dicts=True)
            for key, value in data.items()
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
