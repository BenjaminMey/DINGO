from __future__ import unicode_literals
from builtins import (str,
                      open)

import os
import json
import numpy as np
from nipy.core.api import (Image,
                           AffineTransform,
                           CoordinateSystem)
from nipy.io.api import save_image

import pytest
from DINGO.utils import (dice_coef,
                         flatten,
                         list_to_str,
                         join_strs,
                         split_filename,
                         reverse_lookup,
                         update_dict,
                         patient_scan,
                         split_chpid,
                         tobool,
                         byteify,
                         json_load_byteified,
                         read_setup)


@pytest.fixture(params=[(10, 10, 11)])
def setup_nii_files(tmpdir, request):
    fname_a = tmpdir.join('a.nii.gz')
    fname_b = tmpdir.join('b.nii.gz')
    fname_c = tmpdir.join('c.nii.gz')

    input_cs = CoordinateSystem(str('ijk'))
    output_cs = CoordinateSystem(str('xyz'))
    cmap = AffineTransform(input_cs, output_cs, np.eye(4))

    dim_a, dim_b, dim_c = request.param
    data_a = np.zeros((dim_a, dim_a, dim_a), dtype=np.uint8)
    slice_a = np.ones((dim_a, dim_a), dtype=np.uint8)
    data_a[0] = slice_a
    image_a = Image(data_a, cmap)

    data_b = np.zeros((dim_b, dim_b, dim_b), dtype=np.uint8)
    slice_b = np.ones((dim_b, dim_b), dtype=np.uint8)
    data_b[1] = slice_b
    image_b = Image(data_b, cmap)

    data_c = np.zeros((dim_c, dim_c, dim_c), dtype=np.uint8)
    slice_c = np.ones((dim_c, dim_c), dtype=np.uint8)
    data_c[0] = slice_c
    image_c = Image(data_b, cmap)

    _ = save_image(image_a, fname_a)
    _ = save_image(image_b, fname_b)
    _ = save_image(image_c, fname_c)
    return fname_a, fname_b, fname_c


def test_dice_coef(setup_nii_files):
    fname_a, fname_b, fname_c = setup_nii_files
    assert dice_coef(fname_a, fname_a) == 1
    assert dice_coef(fname_a, fname_b) == 0
    assert dice_coef(fname_b, fname_b) == 1
    assert dice_coef(fname_c, fname_c) == 1
    pytest.raises(ValueError, dice_coef, fname_a, fname_c)


@pytest.fixture(
    params=[
        (['Hello', [' ', 'World']], ['Hello', ' ', 'World']),
        ((('Hello', ' '), ('World',)), ('Hello', ' ', 'World')),
        ([[('Hello',)], [([' ', 'World'],)]], ['Hello', ' ', 'World'])],
    ids=['lists', 'tuple', 'nested']
)
def setup_lists(request):
    return request.param


def test_flatten(setup_lists):
    source_list, flat_list = setup_lists
    flattened = flatten(source_list)
    assert flattened == flat_list


def test_list_to_str(setup_lists):
    source_list, flat_list = setup_lists
    assert list_to_str(sep='_', args=source_list) == '_'.join(flat_list)


def test_join_strs(setup_lists):
    source_list, flat_list = setup_lists
    assert join_strs(sep='_', kwargs=source_list) == '_'.join(flat_list)


@pytest.mark.parametrize(
    'filename, expected', [
        ('/path/foo.nii.gz', ('/path', 'foo', '.nii.gz')),
        ('foo.nii.gz', ('', 'foo', '.nii.gz')),
        ('/path/foo.trk.txt', ('/path', 'foo', '.trk.txt'))
    ],
    ids=['include_path', 'no_path', 'other_ending']
)
def test_split_filename(filename, expected):
    assert split_filename(filename) == expected


@pytest.fixture(
    params=[
        (dict(one='foo', two=2), dict(one='foo'), 'one'),
        (dict(one='foo', two=2), dict(two=2), 'two'),
        (dict(one='foo', two=2), dict(one='bar'), 'error_reverse'),
        (dict(one='foo', two=2), dict(two='bar'), 'error_both'),
    ],
    ids=['one', 'two', 'raise_reverse', 'raise_reverse_update']
)
def setup_dict(request):
    return request.param


def test_reverse_lookup(setup_dict):
    indict, dict2, expected = setup_dict
    value = dict2.values()[0]
    if 'error' in expected:
        pytest.raises(ValueError, reverse_lookup, indict, value)
    else:
        assert reverse_lookup(indict, value) == expected


def test_update_dict(setup_dict):
    indict, dict2, expected = setup_dict
    if 'error' not in expected:
        assert update_dict(indict, **dict2) == indict
    elif expected == 'error_reverse':
        test_dict = dict(one='bar', two=2)
        assert update_dict(indict, **dict2) == test_dict
    else:
        pytest.raises(TypeError, update_dict, indict, **dict2)


@pytest.fixture(
    params=[
        (dict(pid='9999', scanid='foo', sequenceid='bar'), '_', '9999_foo_bar'),
        (dict(pid='CHP_999', scanid='foo', sequenceid='bar'), '_', 'CHP_999_foo_bar')
    ],
    ids=['p_s_seq', 'chp_id']
)
def setup_ids(request):
    return request.param


def test_patient_scan(setup_ids):
    thedict, separator, expected = setup_ids
    assert patient_scan(thedict) == expected.replace(
        ''.join((separator, thedict['sequenceid'])), ''
    )
    assert patient_scan(thedict, sep=separator) == expected.replace(
        ''.join((separator, thedict['sequenceid'])), ''
    )
    assert patient_scan(thedict, add_sequence=True) == expected
    assert patient_scan(thedict, add_sequence=True, sep=separator) == expected


def test_split_chpid():
    indict, separator, thestr = setup_ids
    subid, scanid, uniid = split_chpid(thestr, separator)
    assert subid == indict['pid']
    assert scanid == indict['scanid']
    assert uniid == indict['sequenceid']


@pytest.mark.parametrize(
    'the_input, expected', [
        (1, True), ('1', True), ('t', True), ('True', True), ('Y', True), ('YeS', True),
        (0, False), ('0', False), ('F', False), ('fALse', False), ('n', False),
        ('foo', ValueError)
    ]
)
def test_tobool(the_input, expected):
    if the_input != 'foo':
        assert tobool(the_input) == expected
    else:
        pytest.raises(expected, tobool, the_input)


@pytest.fixture(
    params=[
        (dict(
            name='foo',
            included_ids=['subj1_scan1_uni1',
                          'subj1_scan1_uni2',
                          'subj1_scan2_uni1',
                          'subj2_scan1_uni1'],
            steps=['SplitIDs'],
            method=dict(SplitIDs=dict(
                inputs=dict(id_sep='_'),
                connect=dict(psid=['Setup', 'included_ids'])
                ))
        )),
        (dict(
            name='foo',
            included_ids=['subj1_scan1_uni1',
                          'subj1_scan1_uni2',
                          'subj1_scan2_uni1',
                          'subj2_scan1_uni1'],
            steps=[['SplitIDSs', 'DINGO.workflows.utils.SplitIDs']],
            method=dict(SplitIDs=dict(
                inputs=dict(id_sep='_'),
                connect=dict(psid=['Setup', 'included_ids'])
                ))
        )),
    ],
    ids=['name_only', 'name_reference']
)
def setup_nested_dicts(tmpdir, request):
    nested_dict = request.param
    temp_file = tmpdir.join('test_setup.json')
    with open(temp_file) as f:
        json.dump(nested_dict, f, encoding='utf-8', indent=4)
    return nested_dict, str(temp_file)


def test_byteify():
    pass


def test_json_load_byteified():
    pass


def test_read_setup(setup_nested_dicts):
    nested_dict, temp_setup = setup_nested_dicts
    assert read_setup(temp_setup) == nested_dict
