import door


def test_corrupt_state_file_loads_as_unknown(tmp_path, mocker):
    state_file = tmp_path / "door_state.json"
    state_file.write_text('{"state": "op')
    mocker.patch("door.STATE_FILE", str(state_file))

    assert door.State.load().name == door.STATE_UNKNOWN
