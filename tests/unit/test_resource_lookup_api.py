from typing import List

from document.config import settings
from document.domain import model
from document.domain.resource import resource_factory

## Test the API:


def test_lookup_successes() -> None:
    assembly_strategy_kind: model.AssemblyStrategyEnum = (
        model.AssemblyStrategyEnum.LANGUAGE_BOOK_ORDER
    )
    resource_requests: List[model.ResourceRequest] = []
    resource_requests.append(
        model.ResourceRequest(
            lang_code="en", resource_type="ulb-wa", resource_code="gen"
        )
    )
    resource_requests.append(
        model.ResourceRequest(
            lang_code="en", resource_type="tn-wa", resource_code="gen"
        )
    )

    # NOTE # Jun 3, 2020: a couple days ago translations.json had zh tn, but now
    # it is no longer available for some reason, so let's skip this test.
    resource_requests.append(
        model.ResourceRequest(lang_code="mr", resource_type="ulb", resource_code="gen")
    )

    resource_requests.append(
        model.ResourceRequest(
            lang_code="erk-x-erakor", resource_type="reg", resource_code="eph"
        )
    )
    document_request = model.DocumentRequest(
        email_address=settings.FROM_EMAIL_ADDRESS,
        assembly_strategy_kind=assembly_strategy_kind,
        resource_requests=resource_requests,
    )

    for resource_request in document_request.resource_requests:
        resource = resource_factory(
            settings.working_dir(),
            settings.output_dir(),
            resource_request,
            document_request.resource_requests,
        )
        resource.find_location()
        assert resource.resource_url


# FIXME This fails because zh doesn't use ulb for its USFM resource
# type but 'cuv' instead, i.e., zh ulb is a special case.
# NOTE Perhaps resource_lookup should compare the requested resource
# type against those that are actually available in translations.json
# and deny the request with an
# exceptions.IncompatibleResourceTypeRequest error for an early fail.
# Preferrably the front end just wouldn't ask for things that don't
# exist in the API. In BIELHelperResourceJsonLookup we could swap the
# lang_codes, resource_types methods for ones that combine the two
# such that no malformed resource request could occur. In general we
# should probably always consider lang_code, resource_type,
# resource_code values together and never standalone.
def test_lookup_failures() -> None:
    assembly_strategy_kind: model.AssemblyStrategyEnum = (
        model.AssemblyStrategyEnum.LANGUAGE_BOOK_ORDER
    )
    resource_requests: List[model.ResourceRequest] = []
    resource_requests.append(
        model.ResourceRequest(lang_code="zh", resource_type="ulb", resource_code="jol")
    )
    document_request = model.DocumentRequest(
        email_address=settings.FROM_EMAIL_ADDRESS,
        assembly_strategy_kind=assembly_strategy_kind,
        resource_requests=resource_requests,
    )

    for resource_request in document_request.resource_requests:
        resource = resource_factory(
            settings.working_dir(),
            settings.output_dir(),
            resource_request,
            document_request.resource_requests,
        )
        resource.find_location()
        assert not resource.resource_url
