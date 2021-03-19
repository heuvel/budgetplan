def test_assetlist_new(base_assetlist):
    assert base_assetlist.name == "test_assetlist"
    assert base_assetlist == []
