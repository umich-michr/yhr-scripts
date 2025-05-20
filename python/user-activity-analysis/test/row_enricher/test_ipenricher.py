import pytest
from src.row_enricher.ipenricher import IpEnricher

def test_ipenricher_enrich_not_implemented():
    enricher = IpEnricher()
    with pytest.raises(NotImplementedError):
        enricher.enrich({})

def test_ipenricher_header_fields_not_implemented():
    enricher = IpEnricher()
    with pytest.raises(NotImplementedError):
        _ = enricher.header_fields