# HexToWavFileCLI.py Version 1.1
# 
# Author : David Beazley (http://www.dabeaz.com)
# Copyright (C) 2010
#
# Requires Python 3.1.2 or newer
#
# Updated 2022: Greg Strike (https://www.gregorystrike.com)
#
# Modified and adapted for the Cosmac ELF II by Costas Skordis April 2024
# Adapted from From kcs_encode.py and redeveloped HexToWavFileCLI.py
#
# Will ask RomFile, Source Directory, Target Directory, Leader (sec), Trailer (sec)
# Search Source Directory for all Hex text files with Hex extension add the romfile at begining of hex and convert to intel hex from wav file saving them
# in the Target Directory with an Index file representing the files converted with start and end address.
# Wav format is mono at at 22050Hz bit rate where bit 0 as 1200Hz and bit 1 as 2400Hz
# The HUG1802/HEC1802/ETI-660 computers need bit 0 as 500Hz and bit 1 as 1000Hz
# The Wav file metadata is written with the start and end address of program as Title and the name as Album
# If required Leader and Trailer will add the number in seconds of bit 1 at the begining and end of the file.
# Note: that the Hex file is in 2 byte format with a speace delimiting pairs all in one line. No line feeds allowed. 

#Takes the contents of any file and encodes it into a Kansas
#City Standard WAV file, that when played will upload data via the
#cassette tape input on various vintage home computers. See
#http://en.wikipedia.org/wiki/Kansas_City_standard

import wave
import taglib
from colorama import Fore, Back, Style, init

# A few global parameters related to the encoding as defaults

FRAMERATE = 22050      # Hz
ONES_FREQ = 2400       # Hz (per KCS)
ZERO_FREQ = 1200       # Hz (per KCS)
AMPLITUDE = 225        # Amplitude of generated square waves
CENTER    = 128        # Center point of generated waves

# Create a single square wave cycle of a given frequency
def make_square_wave(freq,framerate):
    n = int(framerate/freq/2)
    return bytearray([CENTER-AMPLITUDE//2])*n + \
           bytearray([CENTER+AMPLITUDE//2])*n

# Function to convert Hexadecimal to Binary
def HexToBin(hex_string):
  binary_string = ''.join(['{0:04b}'.format(int(d, 16)) for d in hex_string])  
  return binary_string

# Check if string is a valid hex value
def IsHex(s):
    try:
        n = int(s,16)
        print(n)
        if n<0:
            return False
        return True
    except ValueError:
        return False

# Calculate parity using XOR 
def parity(x):
    parity = 0
    while x:
        parity ^= x & 1
        x >>= 1
    return parity
# Take a single byte value as binary and turn it into a bytearray representing
# the associated waveform along with the required start and parity bits.
def encode_byte(byteval):
 
    binval=HexToBin(byteval)
    s = binval
    b = bytearray()
    b.extend(map(ord, s))
    # The start bit (0)
    encoded = bytearray(zero_pulse)
    # 8 data bits
    for bit in b:
        if (bit==49):
            encoded.extend(one_pulse)
        else:
            encoded.extend(zero_pulse)
    # Add parity bit
    encoded.extend(zero_pulse if (parity(int(byteval,16))) else one_pulse)
    return encoded

# A generator to divide a sequence into chunks of n units.
def SplitBy(seq, n):
    while seq:
        yield seq[:n]
        seq = seq[n:]

# Function to convert hex to intel Hex
def ConvertToIntelHex(DataRow,Origin):    
     iHex=[]
     address = int(Origin, 16)
     recordtype='00'
     trailer=':00000001FF'
     for v in DataRow:
         for v1 in v:
             v2=list(SplitBy(v1, 2))
             chksum=0
             bytecount=0
             for h in v2:
                 bytecount=bytecount+1
                 chksum=chksum+int(h, 16)
             
             bytecount=hex(bytecount).replace('0x','')
             bytecount=bytecount.rjust(2,'0')
 
             hexAdd=hex(address).replace('0x','')
             hexAdd=hexAdd.rjust(4,'0')
             hexAdd1=hexAdd[:2]
             hexAdd2=hexAdd[2:]

             chksum=chksum + int(bytecount,16) + int(hexAdd1,16) + int(hexAdd2,16) + int(recordtype,16)
             chksum=hex(chksum).replace('x','')
             chksum=int("0100",16)-int(chksum[-2:],16)
             chksum=hex(chksum).replace('x','')[-2:].rjust(2,'0')
             data=':' + bytecount + hexAdd + recordtype + ''.join(v2)+chksum
             iHex.append(data.upper())
             address=address + int(bytecount,16)
     iHex.append(trailer)
     return iHex
 
# Write a WAV file with encoded data. leader and trailer specify the
# number of seconds of carrier signal to encode before and after the data
def write_wav(filename,data,leader,trailer):  
    w = wave.open(filename,"wb")
    w.setnchannels(1)
    w.setsampwidth(1)
    w.setframerate(FRAMERATE)

    # Write the leader
    if leader:
        for x in range(leader):
            w.writeframes(one_pulse*(int(FRAMERATE/len(one_pulse))))
 
    # Encode the actual data
    for byteval in data:
        if byteval!='':
            w.writeframes(encode_byte(byteval))
  
    # Write the trailer
    if trailer:
        for x in range(trailer):
            w.writeframes(one_pulse*(int(FRAMERATE/len(one_pulse))))
    w.close()

# Write file
def write_file(TargetFile,FileData,NewLine):
    f = open(TargetFile, "w")
    for data in FileData:
        if NewLine==1:
            data=data+"\n"
        f.write(data)
    f.close()  

# Write tag
def write_tag(filename,text1,text2):
    with taglib.File(filename) as file:    
        file.tags["ALBUM"] = [text1]
        file.tags["TITLE"] = [text2]
        file.save()

def PromptHex(prompt, default=None):
    if default!='':
        prompt=prompt+' <'+str(default)+'> :'   
    while True:     
        resp=input(prompt).upper()
        if len(resp)==0 and default!='':
            resp=default
        resp=str(resp)   
        if not IsHex(resp):
                print('Invalid entry. Please enter valid hexidecimal values')
        else:
            break
    return resp
    
if __name__ == '__main__':
    import os,sys
    import click
    from pathlib import Path
    
   
    if len(sys.argv) != 1:
        print("Usage : %s" % sys.argv[0],file=sys.stderr)
        raise SystemExit(1)
  
    iHexFlag=0
    iHexDirFlag=0
    WavFileFlag=0
    StudioRom=0
    os.system('cls')
    init(autoreset=True)
    print(f'{Fore.RED}{Style.BRIGHT}Hexadecimal To Kansas City Standard Wav File Conversion\n')
    print(f'{Fore.YELLOW}{Style.BRIGHT}Kansas City Standard Settings')
    if click.confirm(f'{Fore.YELLOW}Do you want to export wav files?',default='Y'):
        ONES_FREQ = int(click.prompt(f'{Fore.YELLOW}Bit 1 Frequency Hz' ,default=str(ONES_FREQ), type=click.Choice(['300','500','600','1000','1200','2400','4800','9600']),hide_input=False,show_choices=False,show_default=False,prompt_suffix=' <'+str(ONES_FREQ)+'> :'))
        ZERO_FREQ = int(click.prompt(f'{Fore.YELLOW}Bit 0 Frequency Hz' ,default=str(ZERO_FREQ), type=click.Choice(['300','500','600','1200','2400','4800','9600']),hide_input=False,show_choices=False,show_default=False,prompt_suffix=' <'+str(ZERO_FREQ)+'> :'))
        FRAMERATE = int(click.prompt(f'{Fore.YELLOW}Framerate Hz' ,default=str(FRAMERATE), type=click.Choice(['4800','9600','11025','22050','44100','48000']),hide_input=False,show_choices=False,show_default=False,prompt_suffix=' <'+str(FRAMERATE)+'> :'))
        AMPLITUDE = int(click.prompt(f'{Fore.YELLOW}Amplitude' ,default=str(AMPLITUDE), type=click.IntRange(0, 255),hide_input=False,show_default=False,prompt_suffix=' <'+str(AMPLITUDE)+'> :'))
        Leader = int(click.prompt(f'{Fore.YELLOW}Leader in seconds' ,default=2,type=click.IntRange(0, 60),hide_input=False,show_default=False,prompt_suffix=' <2> :'))
        Trailer = int(click.prompt(f'{Fore.YELLOW}Trailer in seconds',default=0,type=click.IntRange(0, 60),hide_input=False,show_default=False,prompt_suffix=' <0> :'))
        WavFileFlag=1
        
        # Create the wave patterns that encode 1s and 0s
        one_pulse  = make_square_wave(ONES_FREQ,FRAMERATE)
        zero_pulse = make_square_wave(ZERO_FREQ,FRAMERATE)
   
    print('\n')
    print(f'{Fore.GREEN}{Style.BRIGHT}File Settings')
    SourceDir = click.prompt(f'{Fore.GREEN}Hexadecimal Source Directory', type=click.Path(exists=True), default=os.getcwd(),hide_input=False,show_choices=False,show_default=False,prompt_suffix=' <'+os.getcwd()+'> : ')
    if not SourceDir.endswith(os.sep):
        SourceDir = SourceDir + os.sep

    TargetDir = click.prompt(f'{Fore.GREEN}Export Target Directory', type=click.Path(exists=False), default=os.getcwd(),hide_input=False,show_choices=False,show_default=False,prompt_suffix=' <'+os.getcwd()+'> : ')
    if not TargetDir.endswith(os.sep):
        TargetDir = TargetDir + os.sep

    RomFile = click.prompt(f'{Fore.GREEN}Rom File', type=click.Path(exists=False),default='.',hide_input=False,show_choices=False,show_default=False)
    
    if RomFile=='.':
        RomFile=''   
    elif not os.path.isfile(RomFile):
        print(f'{Fore.WHITE}{Back.RED}{Style.BRIGHT}Rom file '+RomFile+' does not exist. Proceeding without rom file')
        RomFile='' 

    if RomFile!='':
        if click.confirm(f'{Fore.GREEN}Is this a RCA Studio rom File?',default='n'):
            StudioRom=1
        else:
            StudioRom=0

    print('\n')
    print(f'{Fore.MAGENTA}{Style.BRIGHT}Hexadecimal Settings')
    if click.confirm(f'{Fore.MAGENTA}Do you want to export to Intel Hex files ?',default='Y'):
        
        ByteRow=int(click.prompt(f'{Fore.MAGENTA}Number of Bytes per row:',default='16',type=click.Choice(['2','4','8','16','32']),hide_input=False,show_choices=False,show_default=False,prompt_suffix=' <16> : '))
        Origin=str(PromptHex(f'{Fore.MAGENTA}Origin start at','0000'))
        iHexFlag=1
        if click.confirm(f'{Fore.MAGENTA}Do you want to save hex files in one directory as well ?',default='Y'):
            iHexDirFlag=1
   
    if not iHexFlag:
        Origin=str(PromptHex(f'{Fore.MAGENTA}Origin start at','0000'))

    # Create new directories if they don't exist
    if WavFileFlag:
        WavDir = os.path.join(TargetDir, 'wav')
        if not os.path.exists(WavDir):
            os.makedirs(WavDir)
        IndexDir=os.path.join(WavDir, 'Index')
        if not os.path.exists(IndexDir):
            os.makedirs(IndexDir)
        IndexFile=os.path.join(IndexDir, 'Index.txt')
        index=open(IndexFile,"w")
    
    if iHexFlag:
        IntelHexDir=os.path.join(TargetDir, 'ihex')
        if not os.path.exists(IntelHexDir):
            os.makedirs(IntelHexDir)    
        
    RomDataStr=[]
    if os.path.isfile(RomFile):
        obj = open(RomFile,"r")
        RomDataStr = obj.read().split(' ')
        print(f'{Fore.BLUE}ROM File')
        print(RomDataStr)

    for path in Path(SourceDir).glob('*.hex'):
        SourceFile=os.path.join(SourceDir, path)
        FileName=os.path.splitext(path.name)[0]
        AlphaName=FileName[0]
               
        if WavFileFlag:
            AlphaDir=os.path.join(WavDir,AlphaName)
            if not os.path.exists(AlphaDir):
                os.makedirs(AlphaDir)    
            TargetFile=os.path.join(AlphaDir, FileName+'.wav')
        
        if iHexFlag:
            AlphaDir=os.path.join(IntelHexDir,AlphaName)
            if not os.path.exists(AlphaDir):
                os.makedirs(AlphaDir) 
            
            IntelHexFile=os.path.join(AlphaDir,FileName+'.hex')
            if iHexDirFlag:
                IntelHexFileCopy=os.path.join(IntelHexDir,FileName+'.hex')
         
        obj = open(SourceFile,"r")
        
        Data = obj.read().split(' ')
       
        if StudioRom==1:
            # Only take Rom from 0000 to 03FF and append software from 0200 onwards
            Data = RomDataStr[:1024] + Data[256:]
        else:
            ##Data = RomDataStr[:1536] + Data
            Data=RomDataStr+Data
        
        DataLen=len(Data)
        pages=str(-(-DataLen // 256))
        Address1=hex(int(Origin,16)).replace('x','').upper()
        Address1=Address1.rjust(4,'0')
        Address2=hex(DataLen+int(Origin,16)-1).replace('x','')
        Address2=Address2.upper()
        if len(Address2)>4:
            Address2=Address2[1:]
        Address2=str(Address2.upper()).zfill(4)
        Address=Address1+' - '+Address2+' ('+ pages +')'
        
        if WavFileFlag:
            print('\n')
            print(f'{Fore.LIGHTMAGENTA_EX}Creating wav file '+ TargetFile)
            write_wav(TargetFile,Data,Leader,Trailer)
            FName=Path(TargetFile).resolve().stem
            # Format and create index file
            f='{text1:.<70}{text2:15}'
            print(f.format(text1=FName,text2=Address))
            index.write(f.format(text1=FName,text2=Address)+'\n')
            write_tag(TargetFile,FName,Address)
                    
        if iHexFlag:
            DataStr = ''.join(Data)
            DataRow=[]
            DataRow.append(list(SplitBy(DataStr,ByteRow*2)))
            FileData=[]
            FileData=ConvertToIntelHex(DataRow,Origin)
            print(f'{Fore.GREEN}Writing Intel Hex Format File '+ IntelHexFile)   
            write_file(IntelHexFile,FileData,1)
            if iHexDirFlag:
                print(f'{Fore.YELLOW}Copying file '+ FileName+' to '+IntelHexFileCopy)
                write_file(IntelHexFileCopy,FileData,1)             
if WavFileFlag:
    index.close()