from __future__ import unicode_literals
from builtins import (str,
                      open)

import os
import smtplib
import json
from pprint import pprint
from nipype import config
from DINGO.utils import flatten

import pytest
from DINGO.base import (check_input_field,
                        check_input_fields,
                        DINGONodeFlowBase,
                        DINGOFlow,
                        DINGONode,
                        DINGO)


# Separate id_fn to determine tests by the id
def setup_inputs_idfn(fixture_param):
    fixture_ids = (
        'all_included',
        'name_wrong_type',
        'config_wrong_type',
        'no_name',
        'no_config',
        'extra_expected')
    if isinstance(fixture_param, int):
        idx = fixture_param
    else:
        idx = fixture_param[0]
    return fixture_ids[idx]


# Seems each param sent to id function, not obvious to me how to assign set id
# without the param_index, so put in the param itself.
@pytest.fixture(
    params=[
        (
            0,  # all_included
            (('name', str),
             ('config', dict),
             ('email', dict),
             ('data_dir', str),
             ('steps', list),
             ('method', dict),
             (('included_ids', list), (
                ('included_imgs', list), ('included_masks', list))))
        ),
        (
            1,  # name_wrong_type
            (('name', list),
             ('config', dict),
             ('email', dict),
             ('data_dir', str),
             ('steps', list),
             ('method', dict),
             (('included_ids', list), (
                ('included_imgs', list), ('included_masks', list))))
        ),
        (
            2,  # config_wrong_type
            (('name', str),
             ('config', list),
             ('email', dict),
             ('data_dir', str),
             ('steps', list),
             ('method', dict),
             (('included_ids', list), (
                ('included_imgs', list), ('included_masks', list))))
        ),
        (
            3,  # no_name
            (('config', dict),
             ('email', dict),
             ('data_dir', str),
             ('steps', list),
             ('method', dict),
             (('included_ids', list), (
                ('included_imgs', list), ('included_masks', list))))
        ),
        (
            4,  # no_config
            (('name', str),
             ('email', dict),
             ('data_dir', str),
             ('steps', list),
             ('method', dict),
             (('included_ids', list), (
                ('included_imgs', list), ('included_masks', list))))
        ),
        (
            5,  # extra_expected
            (('name', str),
             ('email', dict),
             ('data_dir', str),
             ('steps', list),
             ('method', dict),
             (('included_ids', list), (
                ('included_imgs', list), ('included_masks', list))),
             ('foo', list))
        )
    ],
    ids=setup_inputs_idfn
)
def create_setup_inputs(tmpdir, request):
    setup_dict = dict(
        name='foo',
        config=dict(execution=dict(
            remove_unnecessary_outputs='false'
        )),
        email=dict(server='fooserver',
                   login='foologin',
                   pw='foopw',
                   fromaddr='foofrom',
                   toaddr='footo'),
        data_dir=str(os.getcwd()),
        included_ids=['subj1_scan1_uni1',
                      'subj1_scan1_uni2',
                      'subj1_scan2_uni1',
                      'subj2_scan1_uni1'],
        included_imgs=['img1', 'img2'],
        included_masks=['mask1', 'mask2'],
        steps=[
            ['split_from_dict', 'SplitIDs'],
            ['split_from_interface', 'DINGO.workflows.utils.SplitIDs']
        ],
        method=dict(
            split_from_dict=dict(
                inputs=dict(id_sep='_'),
                connect=dict(psid=['Setup', 'included_ids'])),
            split_from_interface=dict(
                inputs=dict(id_sep='_'),
                connect=dict(psid=['Setup', 'included_ids'])),
        )
    )
    param_idx, input_keys_types = request.param
    param_id = setup_inputs_idfn(param_idx)
    expected = [ele[0] for ele in input_keys_types if isinstance(ele[0], str)]
    expected.extend([ele[0][0] for ele in input_keys_types if isinstance(ele[0], tuple)])
    print('expected: {}'.format(sorted(expected)))
    print('setup keys: {}'.format(sorted(setup_dict.keys())))
    temp_file = tmpdir.join('test_setup.json')
    setup_basename = os.path.basename(str(temp_file))
    with open(str(temp_file), 'w') as f:
        f.write(unicode(json.dumps(setup_dict, encoding='utf-8', indent=4)))
    return setup_dict, setup_basename, input_keys_types, expected, param_id


def test_check_input_field(create_setup_inputs):
    setup_dict, setup_bn, input_keys_types, _, _ = create_setup_inputs
    test_pairs = flatten(input_keys_types)
    print('test_pairs: {}'.format(test_pairs))
    keys = [ele for ele in test_pairs if test_pairs.index(ele) % 2 == 0]
    test_types = [ele for ele in test_pairs if test_pairs.index(ele) % 2 == 1]
    for i in xrange(len(keys)):
        key = keys[i]
        test_type = test_types[i]
        print('key: {}, test_type: {}'.format(
            key, test_type))
        if key not in setup_dict.keys():
            pytest.raises(KeyError, check_input_field,
                          setup_bn, setup_dict, key, test_type)
        else:
            print('real_type: {}'.format(
                  type(setup_dict[key])))
            if not isinstance(setup_dict[key], test_type):
                pytest.raises(TypeError, check_input_field,
                              setup_bn, setup_dict, key, test_type)
            else:
                try:
                    check_input_field(setup_bn, setup_dict, key, test_type)
                except Exception as err:
                    pytest.fail('Unexpected exception raised {}'.format(err))


def test_check_input_fields(create_setup_inputs):
    setup_dict, setup_bn, input_keys_types, expected, input_id = create_setup_inputs
    test_dict = {}
    for k, v in setup_dict.items():
        if k in expected:
            test_dict.update({k: v})
    if 'wrong_type' in input_id:
        pytest.raises(TypeError, check_input_fields,
                      setup_bn, setup_dict, input_keys_types)
    elif any([ele not in setup_dict.keys() for ele in expected]):
        pytest.raises(KeyError, check_input_fields,
                      setup_bn, setup_dict, input_keys_types)
    else:
        input_fields = check_input_fields(setup_bn, setup_dict, input_keys_types)
        print('test_dict')
        pprint(test_dict, indent=2)
        print('returned_input_fields')
        pprint(input_fields, indent=2)
        assert input_fields == test_dict
