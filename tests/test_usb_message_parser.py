from unittest.mock import Mock

import numpy as np

from sciopy.sciopy_dataclasses import EITFrame
from sciopy.usb_message_parser import (
    MessageParser,
    describe_message,
    load_eit_frames,
    save_data_frame,
)


def test_parser_accepts_a_message_split_across_reads():
    parser = MessageParser(Mock(), devicetype="FS")

    assert parser.parse_received_bytes(bytes([0x18, 0x01])) == []
    assert parser.parse_received_bytes(bytes([0x83, 0x18])) == [
        [0x18, 0x01, 0x83, 0x18]
    ]


def test_parser_extracts_multiple_messages_from_one_hs_block():
    parser = MessageParser(Mock(), devicetype="HS")
    block = bytes([0x18, 0x01, 0x83, 0x18, 0x18, 0x01, 0x84, 0x18])

    assert parser.parse_received_bytes(block) == [
        [0x18, 0x01, 0x83, 0x18],
        [0x18, 0x01, 0x84, 0x18],
    ]


def test_parser_rejects_mismatched_message_tags():
    parser = MessageParser(Mock(), devicetype="FS")

    try:
        parser.parse_received_bytes(bytes([0x18, 0x01, 0x83, 0x19]))
    except ValueError as error:
        assert "Invalid message framing" in str(error)
    else:
        raise AssertionError("Parser accepted mismatched message tags")


def test_status_read_does_not_require_measurement_setup():
    device = Mock()
    device.read.side_effect = [bytes([0x18]), bytes([0x01]), bytes([0x83]), bytes([0x18]), b""]
    parser = MessageParser(device, devicetype="FS")

    assert parser.read_usb_till_timeout() == []


def test_manual_command_information_describes_acknowledgement():
    assert describe_message([0x18, 0x01, 0x83, 0x18]) == (
        "Acknowledge / General System Message (0x18): "
        "Command-Acknowledge: Command has been executed successfully"
    )


def test_manual_command_information_describes_setup_option():
    assert describe_message([0xB1, 0x03, 0x02, 0x00, 0x04, 0xB1]) == (
        "Get Measurement Setup (0xB1) – Burst Count: 02 00 04"
    )


def test_parser_prints_command_information_instead_of_message_count(capsys):
    parser = MessageParser(Mock(), devicetype="FS")
    parser.bPrintMessages = True

    parser.interpret_message([0xD1, 0x02, 0x01, 0x19, 0xD1])

    output = capsys.readouterr().out
    assert output == "Get Device Info (0xD1): 01 19\n"
    assert "message(s) received" not in output


def test_acknowledgement_is_labelled_with_its_pending_command(capsys):
    parser = MessageParser(Mock(), devicetype="FS")
    parser.bPrintMessages = True
    parser.set_pending_command([0xB0, 0x03, 0x02, 0x00, 0x04, 0xB0])

    parser.interpret_message([0x18, 0x01, 0x83, 0x18])

    output = capsys.readouterr().out
    assert "Set Measurement Setup (0xB0) – Burst Count" in output
    assert "Command-Acknowledge: Command has been executed successfully" in output
    assert parser.pending_command is None


def test_saved_eit_frame_round_trips_and_ignores_other_files(tmp_path):
    frame = EITFrame(
        n_el=16,
        excitation_stgs=np.array([[1, 2]]),
        frequency_stgs=np.array([125_000]),
        timestamp1=1.0,
        timestamp2=2.0,
        timestamp_pc=3.0,
        ppcData=np.array([1 + 2j]),
    )
    save_data_frame(f"{tmp_path}/", frame, 1)
    (tmp_path / "notes.txt").write_text("ignored", encoding="utf-8")

    loaded = load_eit_frames(tmp_path)

    assert len(loaded) == 1
    assert loaded[0].n_el == 16
    assert np.array_equal(loaded[0].ppcData, frame.ppcData)
