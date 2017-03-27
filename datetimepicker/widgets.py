import json
import warnings

from functools import reduce

from django.conf import settings
from django.forms.utils import flatatt
from django.forms.widgets import DateTimeInput
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape


FORMAT_MAP = {'d': r'%d',
              'm': r'%m',
              'Y': r'%Y',
              'H': r'%H',
              'i': r'%M'}


def _py_datetime_format_to_js(format_string):
    return (format_string is not None and
            reduce(lambda format_string, args: format_string.replace(*reversed(args)),
                  FORMAT_MAP.items(),
                  format_string) or
            None)


def _js_datetime_format_to_py(format_string):
    return (format_string is not None and
            reduce(lambda format_string, args: format_string.replace(*args),
                  FORMAT_MAP.items(),
                  format_string) or
            None)


class DateTimePicker(DateTimeInput):

    def __init__(self,
                 attrs={},
                 format=None,
                 options={},
                 div_attrs={},
                 icon_attrs={}):

        # copy the dicts to avoid overriding the attribute dict
        attrs = attrs.copy()
        options = options.copy()
        div_attrs = div_attrs.copy()
        icon_attrs = icon_attrs.copy()

        # if datetime is given, convert the format to a python valid format
        datetime = attrs.get('datetime')

        # 3 possible ways to set the format
        formats = set([datetime and _js_datetime_format_to_py(datetime) or None,
                       format,
                       options.get('format')]) - {None}

        # extract the format
        if len(formats) is 0:
            format = getattr(settings, self.format_key)[0]
        elif len(formats) is 1:
            format = formats.pop()
        else:
            warnings.warn('format is set more than once', UserWarning)
        
        attrs.update({'class': ' '.join(
            set(attrs.get('class', '').split(' ') + ['form-control'])
        )})

        div_attrs.update({'class': ' '.join(
            set(div_attrs.get('class', '').split(' ') + ['input-group', 'date'])
        )})

        classes = 'glyphicon glyphicon-calendar'
        if not options.get('pickDate', True):
            classes = 'glyphicon glyphicon-time'


        icon_attrs.update({
            'class': icon_attrs.get('class', classes)
        })

        # make sure 'format' is set in the options, the if clause is used just
        # in case the format is set in the options and the attributes, but not
        # as the 'format' keyword argument
        if format:
            options.update({'format': format})
        options.update({'language': translation.get_language()})

        self.options = options
        self.div_attrs = div_attrs
        self.icon_attrs = icon_attrs

        super(DateTimePicker, self).__init__(attrs, format)


    def render(self, name, value, attrs=None, prefix='bootstrap3'):

        if value is None:
            value = ''

        input_attrs = self.build_attrs(attrs, type=self.input_type, name=name)

        if value != '':
            input_attrs.update({'value': force_text(self._format_value(value))})

        self.div_attrs.update({
            'id': '{prefix}_{field_id}'.format(
                prefix=prefix,
                field_id=input_attrs.get('id'),
            )
        })

        html = render_to_string(
            'bootstrap3_datetime/div.html',
            context={'div_attrs': flatatt(self.div_attrs),
                     'input_attrs': flatatt(input_attrs),
                     'icon_attrs': flatatt(self.icon_attrs)}
        )

        # generate a json object out of the options
        dump = json.dumps({
            **{key: val
               for key, val in self.options.items()
               if key != 'format'},
            'format': _py_datetime_format_to_js(self.options.get('format'))
        })

        js = render_to_string(
            'bootstrap3_datetime/script.html',
            context={
                'div_attrs': self.div_attrs,
                'options': dump,
            }
        )
        return html + js

    class Media:
        js = ('datetimepicker/vendor/js/jquery.min.js',
              'datetimepicker/js/jquery.datetimepicker.full.js')
        css = {'all': ('datetimepicker/css/jquery.datetimepicker.min.css',)}
