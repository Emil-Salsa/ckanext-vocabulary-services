import logging

from ckan.plugins.toolkit import get_action
from ckanext.vocabulary_services.model import VocabularyService, VocabularyServiceTerm
from ckanext.vocabulary_services import helpers, validator
from datetime import datetime

log = logging.getLogger(__name__)


def vocabulary_service_last_processed(context, id):

    helpers.check_access(context)

    vocabulary_service = VocabularyService.get(id)

    if vocabulary_service:
        vocabulary_service.date_last_processed = datetime.utcnow()
        vocabulary_service.save()


def update_vocabulary_terms(context, data_dict):

    helpers.check_access(context)

    id = data_dict.get('id', None)
    uri = data_dict.get('uri', None)
    service_type = data_dict.get('type', None)

    if id and uri and service_type:
        try:
            if service_type == 'csiro':
                if get_action('get_csiro_vocabulary_terms')(context, data_dict):
                    get_action('update_vocabulary_service_last_processed')(context, id)
                    log.info('Terms in vocabulary refreshed')
            elif service_type == 'vocprez':
                if get_action('get_vocprez_vocabulary_terms')(context, data_dict):
                    get_action('update_vocabulary_service_last_processed')(context, id)
                    log.info('Terms in vocabulary refreshed')
            elif service_type == 'remote_csv':
                if get_action('remote_csv_vocabulary_terms')(context, data_dict):
                    get_action('update_vocabulary_service_last_processed')(context, id)
                    log.info('Terms in vocabulary refreshed')
            else:
                log.error('Vocabulary service type %s not currently implemented.' % service_type)

        except Exception as e:
            log.error(str(e))


def vocabulary_service_edit(context, data_dict):
    """
    Edit vocabulary service.
    """
    helpers.check_access(context)

    # Load vocabulary service.
    vocabulary_service = VocabularyService.get(data_dict['id'])

    # Validate the form values.
    validator.validate_vocabulary_service(context, data_dict, True)

    try:
        if vocabulary_service:
            for key in data_dict:
                setattr(vocabulary_service, key, data_dict[key])

            vocabulary_service.save()
    except Exception as e:
        log.error(str(e))
        raise Exception('Error updating vocabulary service.')

def vocabulary_service_delete(context, id):
    """
    Delete vocabulary service and its term.
    """
    helpers.check_access(context)

    try:
        # Remove terms.
        terms = get_action('get_vocabulary_service_terms')({}, id)

        for term in terms:
            term.delete()
            term.commit()

        vocabulary_service = VocabularyService.get(id)
        vocabulary_service.delete()
        vocabulary_service.commit()
    except Exception as e:
        log.error(e)
        raise Exception("Error deleting vocabulary service.")
