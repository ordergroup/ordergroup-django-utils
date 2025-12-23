from decimal import Decimal

import six
from django.conf import settings
from django.template import Library
from django.utils.safestring import mark_safe

try:
    from og_django_utils.utils.images import FileObjectExtended
except ImportError:
    use_filebrowser = False
else:
    use_filebrowser = getattr(settings, 'PROGRESSIVE_IMAGES_FILEBROWSER', False)


register = Library()


def get_image_variation(image, variation, webp=False):
    if not use_filebrowser:
        return getattr(image, variation)
    if not hasattr(image, 'path'):
        return image
    image = FileObjectExtended(image.path)
    if hasattr(image, 'version_generate'):
        try:
            image = image.version_generate(variation, webp=webp)
        except FileNotFoundError:
            return ''
    return image


def prepare_tag_context(image, variation=None, min_variation='min', sm_variation=None, always_load=False, loader=False, default_image='', **kwargs):
    data_params = []
    webp_enabled = kwargs.get('webp_enabled')
    for param_name, value in six.iteritems(kwargs):
        if param_name.startswith('data_'):
            param_name = param_name.replace('_', '-')
            if type(value) not in [int, float, Decimal]:
                value = f'"{value}"'
            data_params.append(f'{param_name}={mark_safe(value)}')

    full_image = image if not variation else get_image_variation(image, variation, webp=webp_enabled)
    full_image_url = full_image.url if full_image else default_image or ''
    data_params.append(f'data-progressive="{full_image_url}"')

    medium_image = None if not sm_variation else get_image_variation(image, sm_variation, webp=webp_enabled)
    if medium_image:
        data_params.append(f'data-progressive-sm="{medium_image.url}"')

    data_params = ' '.join(data_params)
    thumb_image = get_image_variation(image, min_variation, webp=webp_enabled)
    thumb_image_url = thumb_image.url if thumb_image else default_image or ''
    return {
        'thumb_image': thumb_image_url,
        'always_load_class': 'progressive--always-load' if always_load else '',
        'loader_class': 'img-loader' if loader else '',
        'data_params': data_params
    }


@register.simple_tag(takes_context=True)
def render_progressive_as_bg(context, image, variation=None, classes='', min_variation='min', sm_variation=None,
                             always_load=False, **kwargs):
    kwargs['webp_enabled'] = context.get('webp_user')
    tag_context = prepare_tag_context(image, variation, min_variation, sm_variation, always_load, **kwargs)

    html_tag = r'''<div class="progressive__bg progressive--not-loaded {} {}" style="background-image: url('{}')" {}></div>'''.format(
        tag_context['always_load_class'], classes, tag_context['thumb_image'], tag_context['data_params']
    )
    return mark_safe(html_tag)


@register.simple_tag(takes_context=True)
def render_progressive(context, image, variation=None, classes='', min_variation='min', sm_variation=None,
                       always_load=False, wrapper_classes='', loader=False, progressbar=False, **kwargs):
    kwargs['webp_enabled'] = context.get('webp_user')
    tag_context = prepare_tag_context(image, variation, min_variation, sm_variation, always_load, loader, **kwargs)
    progressbar_tag = r'''
    <div class="progress-bar"><div class="progress-loader" id="progress-loader"></div></div>
    '''
    loader_tag = r'''
    <svg class="svg-spinner" viewBox="0 0 50 50">
          <circle class="path" cx="25" cy="25" r="20" fill="none" stroke-width="5"></circle>
    </svg>
    '''
    loader_context = loader_tag if loader else ''
    progress = progressbar_tag if progressbar else ''
    html_tag = r'''
    <figure class="progressive {}">
        {}{}
        <img class="progressive__img progressive--not-loaded {} {} {}" src="{}" {}>
        </img>
    </figure>'''.format(
        wrapper_classes, loader_context, progress, tag_context['loader_class'], tag_context['always_load_class'], classes,
        tag_context['thumb_image'], tag_context['data_params']
    )
    return mark_safe(html_tag)
