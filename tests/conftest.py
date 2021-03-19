from budgetplan import AssetList
import pytest


@pytest.fixture(scope="module")
def base_assetlist():
    return AssetList("test_assetlist", [])
