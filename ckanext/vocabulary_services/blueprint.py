import ckan.lib.navl.dictization_functions as dict_fns
import ckan.logic as logic
import ckan.plugins.toolkit as toolkit
import logging

from ckan.common import request
from ckanext.vocabulary_services import helpers
from flask import Blueprint

clean_dict = logic.clean_dict
get_action = toolkit.get_action
h = toolkit.h
log = logging.getLogger(__name__)
parse_params = logic.parse_params
request = toolkit.request
tuplize_dict = logic.tuplize_dict

vocabulary_services = Blueprint('vocabulary_services', __name__, url_prefix=u'/ckan-admin')


def index():

    helpers.check_access({})

    try:
        data = {}
        errors = {}
        is_update = False
        vocab_service_id = request.args.get('id')
        if request.method == 'POST':
            data = clean_dict(dict_fns.unflatten(tuplize_dict(parse_params(
                request.form))))
            try:
                if vocab_service_id:
                    get_action('vocabulary_service_edit')({}, data)
                    h.flash_success('Vocabulary service %s updated.' % data['title'])

                    return h.redirect_to('vocabulary_services.index')
                else:
                    get_action('vocabulary_service_create')({}, data)
                    h.flash_success('Vocabulary service %s added.' % data['title'])

                # Reset the form data.
                data = {}
            except toolkit.ValidationError as e:
                log.warn(e)
                errors = e.error_dict
                log.debug(errors)

                if vocab_service_id:
                    is_update = True
                    h.flash_error('Error updating vocabulary service %s.' % data['title'])
                else:
                    h.flash_error('Error adding vocabulary service %s.' % data['title'])

        elif request.method == 'GET' and vocab_service_id:
            is_update = True
            data = get_action('get_vocabulary_service')({}, vocab_service_id)

        services = get_action('get_vocabulary_services')({}, {})

        return toolkit.render('vocabulary/index.html',
                              extra_vars={
                                  'data': data,
                                  'errors': errors,
                                  'services': services,
                                  'is_update': is_update
                              })
    except Exception as e:
        log.error(e)
        toolkit.abort(503, str(e))


def refresh(id):

    helpers.check_access({})

    service = get_action('get_vocabulary_service')({}, id)

    if service:

        data_dict = {
            'id': service.id,
            'uri': service.uri,
        }

        action = None

        if service.type == 'csiro':
            action = 'get_csiro_vocabulary_terms'
        elif service.type == 'vocprez':
            action = 'get_vocprez_vocabulary_terms'
        elif service.type == 'remote_csv':
            action = 'get_remote_csv_vocabulary_terms'

        if action:
            if get_action(action)({}, data_dict):
                get_action('update_vocabulary_service_last_processed')({}, service.id)
                h.flash_success(
                    'Terms in vocabulary refreshed. <a href="{}">View terms</a>'.format(h.url_for('vocabulary_services.terms', id=service.id)),
                    allow_html=True
                )
        else:
            h.flash_error('Vocabulary service type %s not currently implemented.' % service.type)

    return h.redirect_to('vocabulary_services.index')


def terms(id):

    helpers.check_access({})

    return toolkit.render('vocabulary/terms.html',
                          extra_vars={
                              'vocabulary_service': get_action('get_vocabulary_service')({}, id),
                              'terms': get_action('get_vocabulary_service_terms')({}, id),
                          })

def delete(id):
    """
    Delete vocabulary service.
    """
    if request.method == 'POST':
        try:
            get_action('vocabulary_service_delete')({}, id)
            h.flash_success('Vocabulary service deleted.')
        except Exception as e:
            log.error(e)
            h.flash_error('Error deleting vocabulary service.')
    else:
        h.flash_error('Can not delete vocabulary service.')

    return h.redirect_to('vocabulary_services.index')


vocabulary_services.add_url_rule(u'/vocabulary-services', methods=[u'GET', u'POST'], view_func=index)
vocabulary_services.add_url_rule(u'/vocabulary-service/refresh/<id>', view_func=refresh)
vocabulary_services.add_url_rule(u'/vocabulary-service/terms/<id>', view_func=terms)
vocabulary_services.add_url_rule(u'/vocabulary-service/delete/<id>', methods=[u'POST'], view_func=delete)
