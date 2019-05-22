from __future__ import unicode_literals
from builtins import (str,
                      open)

import os
import smtplib
import json
from pprint import pprint
from nipype import config

import pytest
from DINGO.base import (keep_and_move_files,
                        check_input_field,
                        check_input_fields,
                        dingo_node_factory,
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
    return fixture_ids[fixture_param[0]]


# Seems each param sent to id function, not obvious to me how to assign set id
# without the param_index, so put in the param itself.
@pytest.fixture(
    params=[
        (
            0,
            (('name', (unicode, str)),
             ('config', dict),
             ('email', dict),
             ('data_dir', (unicode, str)),
             ('steps', list),
             ('method', dict),
             (('included_ids', list), (
                ('included_imgs', list), ('included_masks', list))))
        ),
        (
            1,
            (('name', list),
             ('config', dict),
             ('email', dict),
             ('data_dir', (unicode, str)),
             ('steps', list),
             ('method', dict),
             (('included_ids', list), (
                ('included_imgs', list), ('included_masks', list))))
        ),
        (
            2,
            (('name', (unicode, str)),
             ('config', list),
             ('email', dict),
             ('data_dir', (unicode, str)),
             ('steps', list),
             ('method', dict),
             (('included_ids', list), (
                ('included_imgs', list), ('included_masks', list))))
        ),
        (
            3,
            (('config', dict),
             ('email', dict),
             ('data_dir', (unicode, str)),
             ('steps', list),
             ('method', dict),
             (('included_ids', list), (
                ('included_imgs', list), ('included_masks', list))))
        ),
        (
            4,
            (('name', (unicode, str)),
             ('email', dict),
             ('data_dir', (unicode, str)),
             ('steps', list),
             ('method', dict),
             (('included_ids', list), (
                ('included_imgs', list), ('included_masks', list))))
        ),
        (
            5,
            (('name', (unicode, str)),
             ('email', dict),
             ('data_dir', (unicode, str)),
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
        data_dir=os.getcwd(),
        included_ids=['subj1_scan1_uni1',
                      'subj1_scan1_uni2',
                      'subj1_scan2_uni1',
                      'subj2_scan1_uni1'],
        steps=['SplitIDs'],
        method=dict(SplitIDs=dict(
            inputs=dict(id_sep='_'),
            connect=dict(psid=['Setup', 'included_ids'])
            ))
    )
    param_id, input_keys_types = request.param
    # param_id = setup_inputs_idfn(request.param_index)
    expected = [ele[0] for ele in input_keys_types if isinstance(ele[0], str)]
    expected.extend([ele[0][0] for ele in input_keys_types if isinstance(ele[0], tuple)])
    temp_file = tmpdir.join('test_setup.json')
    setup_basename = os.path.basename(str(temp_file))
    with open(str(temp_file), 'w') as f:
        f.write(unicode(json.dumps(setup_dict, encoding='utf-8', indent=4)))
    return setup_dict, setup_basename, input_keys_types, expected, param_id


def test_check_input_fields(create_setup_inputs):
    setup_dict, setup_bn, input_keys_types, expected, input_id = create_setup_inputs
    test_dict = {}
    for k, v in setup_dict.items():
        if k in expected:
            test_dict.update({k: v})
    input_fields = check_input_fields(setup_bn, setup_dict, input_keys_types)
    assert input_fields == test_dict
    if 'wrong_type' in input_id and 'name' in input_id:
        pytest.raises(TypeError, check_input_fields,
                      setup_bn, setup_dict, input_keys_types)
    elif any([ele not in setup_dict.keys() for ele in expected]):
        pytest.raises(KeyError, check_input_fields,
                      setup_bn, setup_dict, input_keys_types)
