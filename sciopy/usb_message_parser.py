"""
Project ：quali_effects_eit_measurements
Directory: src
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
from .sciopy_dataclasses import EitMeasurementSetup

TWOPOWER24 = 16777216
TWOPOWER16 = 65536
TWOPOWER8 = 256
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


def byte_parser():
    # Return empty lists, while message is incomplete, else full usb-message as list [int[hex-format], int [hex-format], ..]
    # Initialization
    piCurrMess = []
    fMesstype = None
    iCurrLen = 0
    data = yield    # Data of dataclass Bytes
    while True:
        piCurrMess.extend(data)         # Starting Message = Message Type
                                        # Automatic conversion to integers within list
        fMesstype = data                # Save the Byte

        data = yield []                 # 2 Byte = Length of Data within message
        iCurrLen = int.from_bytes(data)
       # print(iCurrLen) #todo raus
        piCurrMess.extend(data)

        data = yield []                 # Next iCurrLen Bytes = Actual Data Bytes
        for i in range(iCurrLen):
            piCurrMess.extend(data)
            data = yield []

        if fMesstype != data:           # Last Byte != Message Type
            print(f"Current message not complete for Starting messagetype {hex(fMesstype)} and ending type {hex(data[0])}")
        piCurrMess.extend(data)
        iCurrLen = 0
        data = yield piCurrMess         # Return fully parsed message as list
        piCurrMess = []
        


#todo doku
class MessageParser:
    def __init__(self, device, eitsetup=None, devicetype="FS"):
        # General setup

        self.bCreateResultsFolder = True
        self.bPrintMessages = False
        self.iNPZSaveIndex = 1
        self.iSaveCounter = 0
        self.ppiMessages = []           # Unused
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
        self.setup= eitsetup
        self.set_measurement_setup(eitsetup)


    def set_measurement_setup(self, setup: EitMeasurementSetup):
        self.setup = setup
        if setup != None:
            self.iMaxChannelGroups = setup.n_el//16
            self.iNumExcitationSettings = setup.n_el            # todo should be independently set
            self.iNumFreqSettings = 1                           # todo
            self.iLenDataperFrame = self.iMaxChannelGroups * 16 * self.iNumExcitationSettings * self.iNumFreqSettings
            self.iMessagesperFrame = self.iMaxChannelGroups * self.iNumExcitationSettings * self.iNumFreqSettings

            # ALL needed
            self.reset_new_data_frame()


    def init_parser(self):
        self.Parser= byte_parser()
        next(self.Parser)

    def read_fs(self):
        return self.cDevice.read()

    def send_fs(self, tosend):
        self.cDevice.write(tosend)

    def read_hs(self):
        return self.cDevice.read_data_bytes(size=1024, attempt=150)

    def send_hs(self, tosend):
        self.cDevice.write_data(tosend)


    def read_usb_for_seconds(self, fTime, bSaveData=False, bDeleteDataFrame=False, sSavePath="C/"):
        if self.bCreateResultsFolder and bSaveData:
            timestr = time.strftime("%Y%m%d-%H%M%S_eit")
            path = os.path.join(sSavePath, timestr)
            os.mkdir(path)
            sSavePath = path + "/"
        messages = []
        iMessageCount= 0
        bMessageStarted = False
        timeout_count= 0
        fEndtime = time.time()+fTime
        while time.time() < fEndtime or bMessageStarted:
            buffer = self.device_read()
            if buffer:
                message = self.Parser.send(buffer)

                if len(message) > 0:
                    bMessageStarted = False
                    self.interpret_message(message, bSaveData,bDeleteDataFrame,sSavePath)
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

    def read_usb_till_timeout(self,  bSaveData=False, bDeleteDataFrame=False, sSavePath="C/"):
        messages= []
        iMessageCount = 0
        timeout_count = 0
        while True:
            buffer = self.device_read()
            if buffer:
                message= self.Parser.send(buffer)
                if len(message)>0:
                    self.interpret_message(message, bSaveData,bDeleteDataFrame,sSavePath)
                    iMessageCount += 1
                timeout_count = 0
                continue
            timeout_count += 1
            if timeout_count >= 1:
                # Break if we haven't received any data
                break

        print(f"{iMessageCount} message(s) received.")
        return self.ppcData


    def save_data_frame(self, path, dataframe):
        np.savez(path + "eitsample_{0:06d}.npz".format(self.iNPZSaveIndex),
                 #   aorta=aorta_segs[j],
                 excitation_stgs =dataframe.excitation_stgs,
                 frequency_stgs=dataframe.frequency_stgs,
                 timestamp1=dataframe.timestamp1,
                 timestamp2=dataframe.timestamp2,
                 ppcData=dataframe.ppcData)
        self.iNPZSaveIndex+=1



    # Message Interpreter Sciospec EIT
    def interpret_message(self, message, bSaveData=False, bDeleteDataFrame=False, sSavePath= "C/"):
        mess_hex = [hex(receive) for receive in message]
        if message[0] == 180:       # DATA 0XB4
            self.interpret_data_input(message, bSaveData, bDeleteDataFrame, sSavePath)
        else:
            mess_hex = [hex(receive) for receive in message]
            if self.bPrintMessages:
                if message[0] == 24:            # 0x24 Acknowledgement Message
                    try:
                        print("Message: " +str(mess_hex) +" -> "+ msg_dict[mess_hex[2]])
                    except:
                        print("Message: " +str(mess_hex) +" -> "+msg_dict["0x01"])
                else:
                    print("Unknown received message: "+str(mess_hex))

    def reset_new_data_frame(self):
        self.iInjIndex= 0
        self.iSaveCounter= 0
        self.CurrentFrame = EITFrame(channel_group=self.iMaxChannelGroups,
                                        excitation_stgs=np.zeros((self.iNumExcitationSettings, 2), dtype=int),
                                        frequency_stgs=np.zeros((self.iNumFreqSettings,), dtype=int),       # todo fill in setup freq settings
                                        timestamp1=0,
                                        timestamp2= 0,
                                        ppcData= np.zeros(self.iMaxChannelGroups * 16 * self.iNumExcitationSettings, dtype= complex))



    def interpret_data_input(self, message, bSave=False, bDeleteFrame=False, sSavePath="C/"):
        # Look after channel group and if data already started, append
        # ChannelGROUP

        # EXCITATIONSETTING
        freq_group = two_byte_to_int(message[5:7])
        if message[2] <= self.iMaxChannelGroups:# Necessary, since sometimes all four channel groups are send
            if message[2] == 1 and freq_group == 1:
                self.CurrentFrame.excitation_stgs[self.iInjIndex] = [message[3], message[4]]
                self.iInjIndex += 1
    
            # FREQUENCY ROW is set through eitsetup
            #   self.CurrentFrame.frequency_stgs = self.iNumFreqSettings
    
            #TIMESTAMP
            if self.iSaveCounter == 0:
                self.CurrentFrame.timestamp1 = four_byte_to_int(message[7:11])

            # Data Handling
            for i in range(11, 135, 8):
                data = complex(
                    four_byte_to_int(message[i: i + 4]),
                    four_byte_to_int(message[i + 4: i + 8]),
                )
                self.CurrentFrame.ppcData[self.iSaveCounter] = data
                self.iSaveCounter += 1
            if self.iSaveCounter == self.iLenDataperFrame:
                # Frame Full
                self.CurrentFrame.timestamp2 = four_byte_to_int(message[7:11])
                if bSave:
                    self.save_data_frame(sSavePath, self.CurrentFrame)
                if bDeleteFrame:
                    del self.CurrentFrame
                else:
                    self.ppcData.append(self.CurrentFrame)         
    
                self.reset_new_data_frame()
            # extract

@dataclass
class EITFrame:
    """
    This class is for parsing the whole EIT excitation stages.

    Parameters
    ----------
    start_tag : str
        has to be 'b4'
    channel_group : int
        channel group: CG=1 -> Channels 1-16, CG=2 -> Channels 17-32 up to CG=4
    excitation_stgs : List[str]
        excitation setting: [ESout, ESin]
    frequency_row : List[str]
        frequency row
    timestamp : int
        milli seconds

    end_tag : str
        has to be 'b4'
    """

    channel_group: int                      # todo weglassen
    excitation_stgs: npt.NDArray[int]      # Num Excitation Settings X 2
    frequency_stgs: npt.NDArray[int]         # List of Frequency-Sweep Settings,
    timestamp1: int  # [ms]
    timestamp2: int
    ppcData: npt.NDArray[complex]          # Channels 1-(64) all channel groups combined

    def __hex__(self):
        return hex(self.ppcData)


def make_eitframes_hex(FrameList):
    result= []
    for f in FrameList:
        result.append(hex(f.ppcData))
    return result


def get_data_as_matrix(FrameList):
    result= []
    for f in FrameList:
        L = len(f.ppcData)//len(f.excitation_stgs)
        result.append(np.reshape(f.ppcData,(len(f.excitation_stgs), L)))
    return np.array(result)


def load_eit_frames(path,names):
    # Load NPZ data into list of (EITFrame)
    pass

def load_eit_frames_into_nparray(path):
    # Loads NPZ Data into nparray of [NumFrames X Sizeof Frequency and Excitation Settings]
    pass



def four_byte_to_int(bytelist):
    return TWOPOWER24*bytelist[0] + TWOPOWER16* bytelist[1] +TWOPOWER8* bytelist[2] + bytelist[3]

def two_byte_to_int(bytelist):
    return TWOPOWER8* bytelist[0] + bytelist[1]

def bytelist_to_int(bytelist):
    r= bytelist[-1]
    for j in range(2,len(bytelist)):
        r+= bytelist[-j]* 2**((j-1)*8)
    return r


def fourbytetst(bytes_array):
    bytes_array = [int(b, 16) for b in bytes_array]
    bytes_array = bytes(bytes_array)
    s= struct.unpack("!f", bytes(bytes_array))
    return struct.unpack("!f", bytes(bytes_array))[0]

def byteintlist_to_int(bytelist):
    #faster than four bytes to int at the moment
    bytes_array = bytes(bytelist)
    return int.from_bytes(bytes_array, byteorder='big')



