import logging
from typing import List

import yaml

from document import config
from document.domain import document_generator, model

with open(config.get_logging_config_file_path(), "r") as f:
    logging_config = yaml.safe_load(f.read())
    logging.config.dictConfig(logging_config)

logger = logging.getLogger(__name__)


def main() -> None:
    book_level_interleaving_test()
    verse_level_interleaving_test()


def book_level_interleaving_test() -> None:
    assembly_strategy_kind: model.AssemblyStrategyEnum = model.AssemblyStrategyEnum.book
    resource_requests: List[model.ResourceRequest] = []
    resource_requests.append(
        model.ResourceRequest(
            lang_code="en", resource_type="ulb-wa", resource_code="jud"
        )
    )
    resource_requests.append(
        model.ResourceRequest(
            lang_code="en", resource_type="tn-wa", resource_code="jud"
        )
    )
    document_request = model.DocumentRequest(
        assembly_strategy_kind=assembly_strategy_kind,
        resource_requests=resource_requests,
    )

    doc_gen = document_generator.DocumentGenerator(
        document_request, config.get_working_dir(), config.get_output_dir(),
    )
    doc_gen.run()

    logger.info("BOOK interleaving test is complete")


def verse_level_interleaving_test() -> None:
    assembly_strategy_kind: model.AssemblyStrategyEnum = model.AssemblyStrategyEnum.verse
    resource_requests: List[model.ResourceRequest] = []
    resource_requests.append(
        model.ResourceRequest(
            lang_code="en", resource_type="ulb-wa", resource_code="jud"
        )
    )
    resource_requests.append(
        model.ResourceRequest(
            lang_code="en", resource_type="tn-wa", resource_code="jud"
        )
    )
    resource_requests.append(
        model.ResourceRequest(
            lang_code="en", resource_type="tq-wa", resource_code="jud"
        )
    )
    document_request = model.DocumentRequest(
        assembly_strategy_kind=assembly_strategy_kind,
        resource_requests=resource_requests,
    )

    doc_gen = document_generator.DocumentGenerator(
        document_request, config.get_working_dir(), config.get_output_dir(),
    )
    doc_gen.run()

    logger.info("VERSE interleaving test is complete")


if __name__ == "__main__":
    main()
