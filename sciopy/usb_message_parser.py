"""
Project ：sciopy
Directory: sciopy/sciopy
File : usb_message_parser.py
Author ：Patricia Fuchs
Date ：17.11.2025 09:04
"""

import numpy as np
import time

from dataclasses import dataclass
from typing import List, Tuple, Union
import numpy.typing as npt
import os
from pandas.core.interchange import dataframe
import struct
from .sciopy_dataclasses import EitMeasurementSetup, EITFrame
from .com_util import bytesarray_to_float, byteintarray_to_float, two_byte_to_int
from datetime import datetime

# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
msg_dict = {
    "0x01": "No message inside the message buffer",
    "0x02": "Timeout: Communication-timeout (less data than expected)",
    "0x04": "Wake-Up Message: System boot ready",
    "0x11": "TCP-Socket: Valid TCP client-socket connection",
    "0x81": "Not-Acknowledge: Command has not been executed",
    "0x82": "Not-Acknowledge: Command could not be recognized",
    "0x83": "Command-Acknowledge: Command has been executed successfully",
    "0x84": "System-Ready Message: System is operational and ready to receive data",
    "0x92": "Data holdup: Measurement data could not be sent via the master interface",
}


# -------------------------------------------------------------------------------------------------------------------- #
def byte_parser():
    """
    Generator to parse each input byte by byte

    Returns:
        Empty lists, while message is incomplete, else full usb-message as list [int[hex-format], int [hex-format], ..]
    """
    # Initialization
    piCurrMess = []
    fMesstype = None
    iCurrLen = 0
    data = yield  # Data of dataclass Bytes
    while True:
        piCurrMess.extend(data)  # Starting Message = Message Type
        # Automatic conversion to integers within list
        fMesstype = data  # Save the Byte

        data = yield []  # 2 Byte = Length of Data within message
        iCurrLen = int.from_bytes(data)
        piCurrMess.extend(data)

        data = yield []  # Next iCurrLen Bytes = Actual Data Bytes
        for i in range(iCurrLen):
            piCurrMess.extend(data)
            data = yield []

        if fMesstype != data:  # Last Byte != Message Type
            print(
                f"Current message not complete for Starting messagetype {hex(fMesstype)} and ending type {hex(data[0])}"
            )
        piCurrMess.extend(data)
        iCurrLen = 0
        data = yield piCurrMess  # Return fully parsed message as list
        piCurrMess = []


# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
class MessageParser:
    """
    Parses byte wise USB messages from an Sciospec EIT Device and sorts them according to the message type
    """

    def __init__(self, device, eitsetup=None, devicetype="FS"):
        # General setup
        self.bPrintMessages = False
        self.iNPZSaveIndex = 1
        self.iSaveCounter = 0  # Unused
        self.ppcData = []
        self.iInjIndex = 0

        # Device setup
        self.cDevice = device
        self.sDevicetype = devicetype
        if self.sDevicetype == "FS":
            self.device_send = self.send_fs
            self.device_read = self.read_fs
        elif self.sDevicetype == "HS":
            self.device_send = self.send_hs
            self.device_read = self.read_hs
        self.init_parser()

        # Setup related changes
        self.CurrentFrame = None
        self.iMaxChannelGroups = 1
        self.iNumExcitationSettings = 1
        self.iNumFreqSettings = 1
        self.iLenDataperFrame = 1
        self.iMessagesperFrame = 1
        self.setup = eitsetup
        self.set_measurement_setup(eitsetup)

    # ---------------------------------------------------------------------------------------------------------------- #
    def set_measurement_setup(self, setup: EitMeasurementSetup):
        """
        Gets EIT Setup and sets up the data frame accordingly
        Args:
            setup: EITMeasurementSetup object
        """
        self.setup = setup
        if setup != None:
            self.iMaxChannelGroups = setup.n_el // 16
            self.iNumExcitationSettings = setup.n_el  # todo should be independently set
            self.iNumFreqSettings = 1  # todo
            self.iLenDataperFrame = (
                self.iMaxChannelGroups
                * 16
                * self.iNumExcitationSettings
                * self.iNumFreqSettings
            )
            self.iMessagesperFrame = (
                self.iMaxChannelGroups
                * self.iNumExcitationSettings
                * self.iNumFreqSettings
            )

            # ALL needed
            self.reset_new_data_frame()

    # ---------------------------------------------------------------------------------------------------------------- #
    def reset_new_data_frame(self):
        """
        Resets the Current EITFrame.
        """
        self.iInjIndex = 0
        self.iSaveCounter = 0
        self.CurrentFrame = EITFrame(
            n_el=self.setup.n_el,
            excitation_stgs=np.zeros((self.iNumExcitationSettings, 2), dtype=int),
            frequency_stgs=np.zeros((self.iNumFreqSettings,), dtype=int),
            # todo fill in setup freq settings
            timestamp1=0,
            timestamp2=0,
            timestamp_pc=0,
            ppcData=np.zeros(
                self.iMaxChannelGroups * 16 * self.iNumExcitationSettings, dtype=complex
            ),
        )

    # ---------------------------------------------------------------------------------------------------------------- #
    def clear_out_data(self):
        """
        Deletes saved data frames
        """
        self.ppcData = []
        self.reset_new_data_frame()

    # ---------------------------------------------------------------------------------------------------------------- #
    def init_parser(self):
        """
        Initializes the parser generator
        """
        self.Parser = byte_parser()
        next(self.Parser)

    # ---------------------------------------------------------------------------------------------------------------- #
    def read_fs(self):
        """
        Read out USB connected via FS protocol
        Returns:
            Byte read from USB
        """
        return self.cDevice.read()

    # ---------------------------------------------------------------------------------------------------------------- #
    def send_fs(self, tosend):
        """
        Sends a message over the USB connected via FS protocol
        Args:
            tosend: list/array of integers to be sent over the USB connected via FS protocol
        """
        self.cDevice.write(tosend)

    # ---------------------------------------------------------------------------------------------------------------- #
    def read_hs(self):
        """
        Read out USB connected via HS protocol
        Returns:
            Byte read from USB
        """
        return self.cDevice.read_data_bytes(size=1024, attempt=150)

    # ---------------------------------------------------------------------------------------------------------------- #
    def send_hs(self, tosend):
        """
        Sends a message over the USB connected via HS protocol
        Args:
            tosend: list/array of integers to be sent over the USB connected via HS protocol
        """
        self.cDevice.write_data(tosend)

    # ---------------------------------------------------------------------------------------------------------------- #
    def read_usb_for_seconds(
        self,
        fTime: float,
        bSaveData: bool = False,
        bDeleteDataFrame: bool = False,
        sSavePath: str = "C/",
        bStartReset: bool = True,
    ):
        """
        Reads out the USB connection for fTime seconds, regardless of whether data is received. Data bytes are parsed,
        sorted into full messages and then handled according to their Command Tag. Status or requested information is
        displayed if wished and measured EIT data is stored, deleted or returned.
        Args:
            fTime(float): time to read out usb connection (in seconds)
            bSaveData: if data should be saved
            bDeleteDataFrame: if data frame is deleted after saving data
            sSavePath: Path where the data should be saved
        Returns:
            List of received data eit frames, no Status messages are saved
        """
        if bStartReset:
            self.reset_new_data_frame()
        iMessageCount = 0
        bMessageStarted = False
        timeout_count = 0
        fEndtime = time.time() + fTime
        while time.time() < fEndtime or bMessageStarted:
            buffer = self.device_read()
            if buffer:
                message = self.Parser.send(buffer)

                if len(message) > 0:
                    bMessageStarted = False
                    self.interpret_message(
                        message, bSaveData, bDeleteDataFrame, sSavePath
                    )
                    iMessageCount += 1
                else:
                    bMessageStarted = True
                timeout_count = 0
                continue
            else:
                time.sleep(0.1)
                timeout_count += 1

            if timeout_count >= 100:
                # Break if we haven't received any data
                break
        print(f"{iMessageCount} message(s) received.")
        return self.ppcData

    # ---------------------------------------------------------------------------------------------------------------- #
    def read_usb_till_timeout(
        self,
        bSaveData: bool = False,
        bDeleteDataFrame: bool = False,
        sSavePath: str = "C/",
        bStartReset: bool = True,
    ):
        """
        Reads out the USB connection until the connections times out, so for messages received + timeout. Data bytes are parsed,
        sorted into full messages and then handled according to their Command Tag. Status or requested information is
        displayed if wished and measured EIT data is stored, deleted or returned.
        Args:
            bSaveData: if data should be saved
            bDeleteDataFrame: if data frame is deleted after saving data
            sSavePath: Path where the data should be saved
        Returns:
            List of received data eit frames, no Status messages are saved
        """
        if bStartReset:
            self.reset_new_data_frame()
        iMessageCount = 0
        timeout_count = 0
        while True:
            buffer = self.device_read()
            if buffer:
                message = self.Parser.send(buffer)
                if len(message) > 0:
                    self.interpret_message(
                        message, bSaveData, bDeleteDataFrame, sSavePath
                    )
                    iMessageCount += 1
                timeout_count = 0
                continue
            timeout_count += 1
            if timeout_count >= 1:
                # Break if we haven't received any data
                break

        print(f"{iMessageCount} message(s) received.")
        return self.ppcData

    # ---------------------------------------------------------------------------------------------------------------- #
    def interpret_message(
        self, message, bSaveData=False, bDeleteDataFrame=False, sSavePath="C/"
    ):
        """
        Message interpreter for USB messages from the Sciospec EIT Device. Status messages or requested information is
        displayed, recorded EIT data is separetely stored.
        Args:
            message: [Byte1:int, Byte2:int, ...], structured like [Command Tag, Message Length, Message Info, Command Tag]
            bSaveData: When the message is EIT data, if it should be saved
            bDeleteDataFrame: When the message is EIT data, if it should be deleted from RAM after saving
            sSavePath: When the message is EIT data, save path
        """
        if message[0] == 180:  # DATA 0XB4
            self.interpret_data_input(message, bSaveData, bDeleteDataFrame, sSavePath)
        else:
            mess_hex = [hex(receive) for receive in message]
            if self.bPrintMessages:
                if message[0] == 24:  # 0x24 Acknowledgement Message
                    try:
                        print(
                            "Message: " + str(mess_hex) + " -> " + msg_dict[mess_hex[2]]
                        )
                    except:
                        print("Message: " + str(mess_hex) + " -> " + msg_dict["0x01"])
                else:
                    print("Unknown received message: " + str(mess_hex))

    # ---------------------------------------------------------------------------------------------------------------- #
    def interpret_data_input(
        self, message, bSave=False, bDeleteFrame=False, sSavePath="C/"
    ):
        """
        Interpreter of received messages with measured data.
        Args:
            message: Received message
            bSave: If data should be saved
            bDeleteFrame: If data should be deleted from RAM after saving
            sSavePath: Save path
        """
        # EXCITATIONSETTING
        freq_group = two_byte_to_int(message[5:7])
        if (
            message[2] <= self.iMaxChannelGroups
        ):  # Necessary, since  all four channel groups are send
            if (
                message[2] == 1 and freq_group == 1
            ):  # todo or gleich 0, weil er nicht mitschreibt
                self.CurrentFrame.excitation_stgs[self.iInjIndex] = [
                    message[3],
                    message[4],
                ]
                self.iInjIndex += 1

            # FREQUENCY ROW is set through eitsetup
            # TODO input not the number of the frequency row, but all injected frequencies, beforehand
            #   self.CurrentFrame.frequency_stgs = self.iNumFreqSettings

            # TIMESTAMP
            if self.iSaveCounter == 0:
                self.CurrentFrame.timestamp1 = message[
                    7:11
                ]  # todo byteinarray_to_flaost
                self.CurrentFrame.timestamp_pc = datetime.now().timestamp()

            # Data Handling
            for i in range(11, 135, 8):
                data = complex(
                    byteintarray_to_float(message[i : i + 4]),
                    byteintarray_to_float(message[i + 4 : i + 8]),
                )
                self.CurrentFrame.ppcData[self.iSaveCounter] = data
                self.iSaveCounter += 1
            if self.iSaveCounter == self.iLenDataperFrame:
                # Frame Full
                self.CurrentFrame.timestamp2 = byteintarray_to_float(message[7:11])
                if bSave:
                    save_data_frame(sSavePath, self.CurrentFrame, self.iNPZSaveIndex)
                    self.iNPZSaveIndex += 1
                if bDeleteFrame:
                    del self.CurrentFrame
                else:
                    self.ppcData.append(self.CurrentFrame)
                self.reset_new_data_frame()


# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
def make_eitframes_hex(FrameList):
    # todo, not working
    result = []
    for f in FrameList:
        result.append(hex(f.ppcData))
    return result


# -------------------------------------------------------------------------------------------------------------------- #
def make_results_folder(bCreateResultsFolder: bool, bSaveData: bool, sSavePath: str):
    """
    Creates a new data results folder, if data should be saved. Then stores the path in the class
    Args:
        bCreateResultsFolder: If folder shall be created
        bSaveData(bool): If data should be saved, folder is only created if data should be saved
        sSavePath(str): Path where the folder should be created
    """
    if bSaveData and bCreateResultsFolder:
        timestr = time.strftime("%Y%m%d-%H%M%S_eit")
        path = os.path.join(sSavePath, timestr)
        os.mkdir(path)
        return path + "/"
    else:
        return sSavePath


# -------------------------------------------------------------------------------------------------------------------- #
def get_data_as_matrix(FrameList):
    """
    List of EITFrames to be reshaped into matrix of [Number frames, num injection settings, n_el]
    Args:
        FrameList: List of EITFrames to be reshaped into matrix

    Returns:
            np.array of eit data of shape [Number frames, num injection settings, n_el]
    """
    result = []
    for f in FrameList:
        L = len(f.ppcData) // len(f.excitation_stgs)
        result.append(np.reshape(f.ppcData, (len(f.excitation_stgs), L)))
    return np.array(result)


# -------------------------------------------------------------------------------------------------------------------- #
def save_data_frame(path: str, dataframe: EITFrame, iNPZSaveIndex: int):
    """
    Saves a single EIT frame in a npz-file. Based on the EITframe class. Saves it at self.NPZSaveIndex
    Args:
        path: Where to save the EIT frame
        dataframe: EITFrame to be saved
        iNPZSaveIndex: Index of the EIT frame to be saved
    """
    np.savez(
        path + "eitsample_{0:06d}.npz".format(iNPZSaveIndex),
        n_el=dataframe.n_el,
        excitation_stgs=dataframe.excitation_stgs,
        frequency_stgs=dataframe.frequency_stgs,
        timestamp1=dataframe.timestamp1,
        timestamp2=dataframe.timestamp2,
        timestamp_pc=dataframe.timestamp_pc,
        ppcData=dataframe.ppcData,
    )


# -------------------------------------------------------------------------------------------------------------------- #
def load_eit_frames(path):
    """
    Loads NPZ eit frames and stores them in a list of EITFrame
    Args:
        path: Path of the NPZ eit frames

    Returns:
        List of EITFrame
    """
    loaded = []
    files = os.listdir(path)
    files = sorted(files)
    for f in files:
        l = np.load(os.path.join(path, f), allow_pickle=True)
        e = EITFrame(
            n_el=l["n_el"],
            excitation_stgs=l["excitation_stgs"],
            frequency_stgs=l["frequency_stgs"],
            timestamp1=l["timestamp1"],
            timestamp2=l["timestamp2"],
            timestamp_pc=l["timestamp_pc"],
            ppcData=l["ppcData"],
        )
        loaded.append(e)
    return loaded


# -------------------------------------------------------------------------------------------------------------------- #
def load_eit_frames_into_nparray(path):
    """
    Load NPZ eit frames, retrieves the complex data and stores it in a numpy array.
    Args:
        path: Path of the NPZ eit frames

    Returns: np.array(ppcData)
    """
    loaded = load_eit_frames(path)
    l = []
    for frame in loaded:
        l.append(frame.ppcData)
    return np.array(l)
