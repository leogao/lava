import pytz
import yaml
import re
from dateutil import parser
from django import template
from django.conf import settings
from collections import OrderedDict
from django.utils.safestring import mark_safe
from lava_scheduler_app.models import TestJob
from lava_scheduler_app.dbutils import load_devicetype_template


register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def udecode(obj):
    # Sometime we do have unicode string: they have been already decoded, so we
    # should not do anything.
    # The only way to test for unicode string in both python2 and 3, is to test
    # for the bytes type.
    if not isinstance(obj, bytes):
        return obj
    try:
        return obj.decode("utf-8", errors="replace")
    except AttributeError:
        return obj


# Compile it only once
action_id_regexp = re.compile(r'^start: ([\d.]+) [\w_-]+ ')


@register.assignment_tag
def get_action_id(string):
    try:
        return action_id_regexp.match(string).group(1).replace('.', '-')
    except (TypeError, AttributeError, IndexError):
        return ''


@register.filter
def replace_dots(string):
    return string.replace('.', '-')


@register.assignment_tag()
def assign_setting(value):
    """Returns the value of the setting"""
    if hasattr(settings, value):
        return getattr(settings, value)


def _get_pipeline_data(pipeline, levels):
    """
    Recursive check on the pipeline description dictionary
    """
    for action in pipeline:
        levels[action['level']] = {
            'name': action['name'],
            'description': action['description'],
            'summary': action['summary'],
            'timeout': action['timeout'],
        }
        if 'url' in action:
            levels[action['level']].update({'url': action['url']})
        if 'pipeline' in action:
            _get_pipeline_data(action['pipeline'], levels)


@register.assignment_tag()
def get_pipeline_sections(pipeline):
    """
    Just a top level view of the pipeline sections
    """
    sections = []
    for action in pipeline:
        if 'section' in action:
            sections.append({action['section']: action['level']})
    return sections


@register.assignment_tag()
def get_pipeline_levels(pipeline):
    """
    Retrieve the full set of action levels in this pipeline.
    """
    levels = OrderedDict()
    _get_pipeline_data(pipeline, levels)
    return levels


@register.assignment_tag()
def parse_timestamp(time_str):
    """
    Convert the pipeline log timestamp into datetime
    :param time_str: timestamp generated by the log handler
       of the form 2015-10-13T08:21:48.646202
    :return: datetime.datetime object or None
    """
    try:
        retval = parser.parse(time_str, ignoretz=True)
    except (AttributeError, TypeError):
        return None
    return pytz.utc.localize(retval)


@register.assignment_tag()
def logging_levels(request):
    levels = ['info', 'warning', 'exception']
    if 'info' in request.GET and request.GET['info'] == 'off':
        del levels[levels.index('info')]
    if 'debug' in request.GET and request.GET['debug'] == 'on':
        levels.append('debug')
    if 'warning' in request.GET and request.GET['warning'] == 'off':
        del levels[levels.index('warning')]
        del levels[levels.index('exception')]
    return levels


@register.filter()
def dump_exception(entry):
    data = [entry['exception']]
    if 'debug' in entry:
        data.append(entry['debug'])
    return yaml.dump(data)


@register.filter()
def deploy_methods(device_type, methods):
    data = load_devicetype_template(device_type)
    if not data or 'actions' not in data or methods not in data['actions']:
        return []
    methods = data['actions'][methods]['methods']
    if isinstance(methods, dict):
        return methods.keys()
    return [methods]


@register.assignment_tag()
def device_type_timeouts(device_type):
    data = load_devicetype_template(device_type)
    if not data or 'timeouts' not in data:
        return None
    return data['timeouts']


@register.filter()
def result_url(result_dict, job_id):
    if not isinstance(result_dict, dict):
        return None
    if 'test_definition' in result_dict:
        testdef = result_dict['test_definition']
        testcase = None
        for key, _ in result_dict.items():
            if key == 'test_definition':
                continue
            testcase = key
            break
        # 8125/singlenode-intermediate/tar-tgz
        return mark_safe('/results/%s/%s/%s' % (
            job_id, testdef, testcase
        ))
    elif len(result_dict.keys()) == 1:
        # action based result
        testdef = 'lava'
        if isinstance(result_dict.values()[0], OrderedDict):
            testcase = result_dict.keys()[0]
            return mark_safe('/results/%s/%s/%s' % (
                job_id, testdef, testcase
            ))
    else:
        return None


@register.assignment_tag()
def result_name(result_dict):
    if not isinstance(result_dict, dict):
        return None
    testcase = None
    testresult = None
    if 'test_definition' in result_dict:
        testdef = result_dict['test_definition']
        for key, value in result_dict.items():
            if key == 'test_definition':
                continue
            testcase = key
            testresult = value
            break
        # 8125/singlenode-intermediate/tar-tgz
        return mark_safe('%s - %s - %s' % (
            testdef, testcase, testresult
        ))
    elif len(result_dict.keys()) == 1:
        # action based result
        testdef = 'lava'
        if isinstance(result_dict.values()[0], OrderedDict):
            testcase = result_dict.keys()[0]
            if 'success' in result_dict.values()[0]:
                testresult = 'pass'
            if 'status' in result_dict.values()[0]:
                testresult = 'pass'  # FIXME
            # 8125/singlenode-intermediate/tar-tgz
            return mark_safe('%s - %s - %s' % (
                testdef, testcase, testresult
            ))
    else:
        return None


@register.filter()
def markup_metadata(key, value):
    if 'target.device_type' in key:
        return mark_safe("<a href='/scheduler/device_type/%s'>%s</a>" % (value, value))
    elif 'target.hostname' in key:
        return mark_safe("<a href='/scheduler/device/%s'>%s</a>" % (value, value))
    elif 'definition.repository' in key and value.startswith('http'):
        return mark_safe("<a href='%s'>%s</a>" % (value, value))
    else:
        return value


@register.assignment_tag
def can_view(record, user):
    try:
        return record.can_view(user)
    except:
        return False


@register.filter()
def split_definition(data):
    # preserve comments
    # rstrip() gets rid of the empty new line.
    return data.rstrip().split('\n')


@register.filter()
def level_replace(level):
    return level.replace('.', '-')


@register.filter()
def sort_items(items):
    return sorted(items)


@register.filter()
def replace_python_unicode(data):
    return data.replace('!!python/unicode ', '')
