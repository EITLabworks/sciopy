from unittest.mock import Mock
import struct

import numpy as np
import pytest

from sciopy.sciopy_dataclasses import (
    EITFrame,
    EitFrequencyBlock,
    EitMeasurementSetup,
)
from sciopy.usb_message_parser import (
    MessageParser,
    describe_message,
    get_data_as_matrix,
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
    device.read.side_effect = [
        bytes([0x18]),
        bytes([0x01]),
        bytes([0x83]),
        bytes([0x18]),
        b"",
    ]
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


def test_parser_allocates_buffer_for_all_frequency_settings():
    setup = EitMeasurementSetup(
        burst_count=2,
        n_el=16,
        exc_freq=[
            EitFrequencyBlock(
                f_min=1_000,
                f_max=10_000,
                f_count=10,
                f_type="lin",
            ),
            EitFrequencyBlock(
                f_min=10_000,
                f_max=100_000,
                f_count=20,
                f_type="log",
            ),
        ],
        framerate=2.0,
        amplitude=0.001,
        inj_skip=0,
        gain=1,
        adc_range=1,
    )

    parser = MessageParser(
        Mock(),
        eitsetup=setup,
    )

    assert parser.iNumFreqSettings == 30
    assert parser.iNumExcitationSettings == 16
    assert parser.iLenDataperFrame == 16 * 30 * 16
    assert len(parser.CurrentFrame.ppcData) == 16 * 30 * 16

    assert np.array_equal(
        parser.CurrentFrame.frequency_stgs,
        np.concatenate(
            [
                np.linspace(1000, 10000, 10),
                np.geomspace(10000, 100000, 20),
            ]
        ),
    )


def test_get_data_as_matrix_preserves_single_frequency_shape():
    frame = EITFrame(
        n_el=3,
        excitation_stgs=np.array(
            [
                [1, 2],
                [2, 3],
            ]
        ),
        frequency_stgs=np.array([1]),
        timestamp1=0,
        timestamp2=0,
        timestamp_pc=0,
        ppcData=np.arange(
            6,
            dtype=np.complex128,
        ),
    )

    result = get_data_as_matrix([frame])

    assert result.shape == (
        1,
        2,
        3,
    )

    assert np.array_equal(
        result[0],
        np.array(
            [
                [0, 1, 2],
                [3, 4, 5],
            ]
        ),
    )


def test_get_data_as_matrix_adds_frequency_axis_for_sweep():
    frame = EITFrame(
        n_el=3,
        excitation_stgs=np.array(
            [
                [1, 2],
                [2, 3],
            ]
        ),
        frequency_stgs=np.array([1, 2]),
        timestamp1=0,
        timestamp2=0,
        timestamp_pc=0,
        ppcData=np.arange(
            12,
            dtype=np.complex128,
        ),
    )

    result = get_data_as_matrix([frame])

    assert result.shape == (
        1,
        2,
        2,
        3,
    )

    assert np.array_equal(
        result[0, 0, 0],
        [0, 1, 2],
    )

    assert np.array_equal(
        result[0, 0, 1],
        [3, 4, 5],
    )

    assert np.array_equal(
        result[0, 1, 0],
        [6, 7, 8],
    )

    assert np.array_equal(
        result[0, 1, 1],
        [9, 10, 11],
    )


def test_parser_collects_all_frequency_rows_into_one_frame():
    setup = EitMeasurementSetup(
        burst_count=1,
        n_el=16,
        exc_freq=[
            EitFrequencyBlock(
                f_min=1_000,
                f_max=1_000,
                f_count=1,
                f_type="lin",
            ),
            EitFrequencyBlock(
                f_min=2_000,
                f_max=2_000,
                f_count=1,
                f_type="lin",
            ),
        ],
        framerate=2.0,
        amplitude=0.001,
        inj_skip=0,
        gain=1,
        adc_range=1,
    )

    parser = MessageParser(
        Mock(),
        eitsetup=setup,
    )

    def make_data_message(
        excitation_out,
        excitation_in,
        frequency_row,
    ):
        message = [
            0xB4,
            0x84,
            0x01,
            excitation_out,
            excitation_in,
        ]

        message.extend(
            frequency_row.to_bytes(
                2,
                byteorder="big",
            )
        )

        message.extend(
            struct.pack(
                ">f",
                0.0,
            )
        )

        for channel in range(16):
            value = excitation_out * 100 + frequency_row * 10 + channel

            message.extend(
                struct.pack(
                    ">f",
                    float(value),
                )
            )

            message.extend(
                struct.pack(
                    ">f",
                    float(-value),
                )
            )

        message.append(0xB4)

        return message

    message_count = 0

    for excitation_out in range(
        1,
        17,
    ):
        excitation_in = (excitation_out % 16) + 1

        for frequency_row in (
            1,
            2,
        ):
            parser.interpret_data_input(
                make_data_message(
                    excitation_out,
                    excitation_in,
                    frequency_row,
                )
            )

            message_count += 1

            if message_count < 32:
                assert len(parser.ppcData) == 0

    assert len(parser.ppcData) == 1

    frame = parser.ppcData[0]

    assert frame.excitation_stgs.shape == (
        16,
        2,
    )

    assert np.array_equal(
        frame.frequency_stgs,
        [1000, 2000],
    )

    result = get_data_as_matrix(parser.ppcData)

    assert result.shape == (
        1,
        16,
        2,
        16,
    )

    assert result[0, 0, 0, 0] == (110 - 110j)

    assert result[0, 0, 1, 0] == (120 - 120j)

    assert result[0, 15, 1, 15] == (1_635 - 1_635j)


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


@pytest.mark.parametrize("n_el", [16, 32])
def test_multiple_skips_and_frequency_blocks_parse_in_configured_order(n_el):
    setup = EitMeasurementSetup(
        1, n_el, [EitFrequencyBlock(1000, 2000, 2)], 2, 0.001, [0, 2], 1, 1
    )
    parser = MessageParser(Mock(), setup)
    expected = np.arange(n_el * 2 * 2 * n_el).reshape(n_el * 2, 2, n_el)
    index = 0
    for skip in (0, 2):
        for out in range(1, n_el + 1):
            for freq in (1, 2):
                for group in range(1, n_el // 16 + 1):
                    msg = [0xB4, 0x84, group, out, ((out + skip) % n_el) + 1]
                    msg.extend(struct.pack(">Hf", freq, 0))
                    for _ in range(16):
                        msg.extend(struct.pack(">ff", index, -index))
                        index += 1
                    msg.append(0xB4)
                    parser.interpret_data_input(msg)
    result = get_data_as_matrix(parser.ppcData)
    np.testing.assert_array_equal(result[0], expected - 1j * expected)
    assert result.shape == (1, n_el * 2, 2, n_el)
    np.testing.assert_array_equal(parser.ppcData[0].frequency_stgs, [1000, 2000])
    assert parser._completed_frames == 1


def test_measurement_read_tolerates_empty_reads_and_stops_after_saved_frame(
    monkeypatch, tmp_path
):
    setup = EitMeasurementSetup(1, 16, 1000, 2, 0.001, 0, 1, 1)
    parser = MessageParser(Mock(), setup)
    messages = []
    for out in range(1, 17):
        msg = [0xB4, 0x84, 1, out, out % 16 + 1]
        msg.extend(struct.pack(">Hf", 1, 0))
        msg.extend(struct.pack(">ff", 1, -1) * 16)
        msg.append(0xB4)
        messages.append(msg)
    parser.device_read = Mock(side_effect=[[], [1]])
    parser.parse_received_bytes = Mock(return_value=messages)
    monkeypatch.setattr("sciopy.usb_message_parser.time.sleep", lambda _: None)
    result = parser.read_usb_till_timeout(True, True, str(tmp_path) + "/")
    assert result == []
    assert parser.device_read.call_count == 2
    assert parser._completed_frames == 1
    assert len(list(tmp_path.glob("*.npz"))) == 1


def test_measurement_read_expires_when_idle(monkeypatch):
    parser = MessageParser(Mock(), EitMeasurementSetup(1, 16, 1000, 2, 0.001, 0, 1, 1))
    parser.device_read = Mock(return_value=[])
    times = iter([0, 1, 6])
    monkeypatch.setattr("sciopy.usb_message_parser.time.monotonic", lambda: next(times))
    monkeypatch.setattr("sciopy.usb_message_parser.time.sleep", lambda _: None)
    assert parser.read_usb_till_timeout() == []
    assert parser.device_read.call_count == 2


def test_command_response_keeps_immediate_timeout_with_setup():
    parser = MessageParser(Mock(), EitMeasurementSetup(1, 16, 1000, 2, 0.001, 0, 1, 1))
    parser.device_read = Mock(return_value=[])
    assert parser.read_usb_till_timeout(bStartReset=False) == []
    parser.device_read.assert_called_once()
