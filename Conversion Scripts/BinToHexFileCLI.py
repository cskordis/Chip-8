# BinToHexFileCLI version 1.1
# Author : Costas Skordis 
# January 2024
# 
# Convert binary to hexadecimal files from Source Directory, and save them into the Target Directory with the option of creating Mnemonic files.
# Origin is the start address of the intel Hex file
# ByteWidth is the number of byte pairs to be formated in the intel Hex file
#
# Requires Python 3.1.2 or newer

# Check if string is a valid hex value
def IsHex(s):
    try:
        n = int(s,16)
        if n<0:
            return False
        return True
    except ValueError:
        return False

# A generator to divide a sequence into chunks of n units.
def SplitBy(seq, n):
    while seq:
        yield seq[:n]
        seq = seq[n:]


# Function to update chip 8 display opcode DxyN with x offset
def UpdateDisplay(Data,Adjust):
    Adjust=(int(Adjust,16))
    if Adjust==0:
        return
    Dxyn=[0] * 3072
    for idx, v in enumerate(Data):
        if v[0]=='6':
            r = v[1]
            ri=int(r,16)
            Dxyn[ri]=list([idx,v[0:2],v[2:]]) 
        if v[0]=='D':
            if v[2:3]=='':
                continue
            r=v[2:3]
            ri=int(v[2:3],16)
            d=Dxyn[ri]
            if d==0:
                continue          
            i=d[0]
            v1=d[1:2][0]
            v2=d[2:3][0]
            v3=hex(int(v2,16)+Adjust).replace('0x','')
            if int(v3,16)>255:
                v3=hex(255).replace('0x','')
            v4=v1 + v3.rjust(2,'0').upper()
            Data[i]=v4
      
# Function to create hex array with update to address calls
def UpdateHex(Data,Origin,NewOrigin):
    NewOrigin = int(NewOrigin, 16)
    Origin= int(Origin, 16)
    offset=NewOrigin-Origin
    if offset==0:
        return
    for idx, v in enumerate(Data):
        hexData=Data[idx]
        op1=v[0]
        op2=v[1:]
        if op1=="1" or op1=="2" or op1=="A" or op1=="B":
            op2 = hex(offset+int(op2, 16))[2:].upper()
            v="".join([op1,op2])
            hexData=v.upper()
            Data[idx]=hexData
    
# Function to create mnemonic hex array
def CreateMnemonic(Data,NewOrigin):
    HexArray=[]
    NewOrigin = int(NewOrigin, 16)
    taa=NewOrigin
    for idx, v in enumerate(Data):
        hexAdd=hex(taa).replace('0x','')
        hexAdd=hexAdd.rjust(4,'0')
        hexAdd=hexAdd.upper()
        hexData=Data[idx]
        HexArray.append(list([hexAdd,hexData,GetOpcode(hexData)]))
        taa=taa+2
    return HexArray
            
# Function to get the CHIP-8 mnemonic code 
def GetOpcode(opcode): 
    if opcode=='':
        return opcode
    if len(opcode) <4:
        opcode=opcode.rjust(4, "0")
    v0=opcode[0]
    v1=opcode[1] 
    v2=opcode[2]
    v3=opcode[3]
    v4=opcode[1:]
    v5=opcode[2:]
    v6=opcode[3:]
    
    mmnemonic = 'Data'
    if v0 == '0':
        if v1 != '0':
             mmnemonic = 'Call ' + v4
        else:
            if opcode == '00E0':
                 mmnemonic = 'Clear'
            elif opcode == '00EE':
                 mmnemonic = 'Return'
            elif opcode=='0000':
                mmnemonic = 'NoOp'
    elif v0 == '1':
         mmnemonic = "Goto " + v4    
    elif v0 == '2':
         mmnemonic = "Do " + v4     
    elif v0 == '3':
         mmnemonic = 'Skip if V'+ v1 +' = '+ v5
    elif v0 == '4':
         mmnemonic = 'Skip if not V' + v1 +' = '+ v5
    elif v0 == '5':
         mmnemonic = 'Skip if V' + v1 + ' = V' + v2
    elif v0 == '6':
         mmnemonic = 'V' + v1 +' = ' + v5
    elif v0 == '7':
         mmnemonic = 'V' + v1 +' = V'+ v1 +' + ' + v5
    elif v0 == '8':
         if v3 == '0':
             mmnemonic = 'V' + v1 + ' = V' + v2
         elif v3 == '1':
             mmnemonic = 'V' + v1 + ' or V' + v2
         elif v3 == '2':
             mmnemonic = 'V' + v1 + ' and V' + v2
         elif v3 == '3':
             mmnemonic = 'V' + v1 + ' or V' + v2
         elif v3 == '4':
             mmnemonic = 'V' + v1 + '  = V' + v1+ ' + V' + v2              
         elif v3 == '5':
             mmnemonic = 'V' + v1 + '  = V' + v1 + ' - V' + v2       
    elif v0 == '9':
         mmnemonic = 'Skip if not V' + v1 + ' = V' + v2 
    elif v0 == 'A':
         mmnemonic = 'I = ' + v4 
    elif v0 == 'B':
         mmnemonic = 'Goto ' + v4 + ' + V0'      
    elif v0 == 'C':
         mmnemonic = 'V' + v1 + ' = random and ' + v5        
    elif v0 == 'D':
         mmnemonic = 'Show ' + v3 + ' at V' + v1 + ', V' + v2      
    elif v0== 'E':
            if v5 == '9E':
             mmnemonic = 'Skip if V' + v1 + ' is key'
            elif v5 == 'A1':
             mmnemonic = 'Skip if not V' + v1 + ' is key'       
    elif v0 == 'F':
            if v5 == '00':
                mmnemonic = 'Pitch = V' + v1
            elif v5 == '07':
                mmnemonic = 'V' + v1 + ' = Time'
            elif v5 == '0A':
                mmnemonic = 'V'+ v1 + ' = Key'
            elif v5 == '15':
                mmnemonic = 'Time = V' + v1
            elif v5 == '18':
                mmnemonic = 'Tone = V' + v1
            elif v5 == '1E':
                mmnemonic = 'I = I + V' + v1
            elif v5 == '29':
                mmnemonic = 'I = Display V' + v1
            elif v5 == '33':
                mmnemonic =  'M(I)=DECML V' + v1
            elif v5 == '55':
                mmnemonic = 'M(I)=V0:V' + v1
            elif v5 == '65':
                mmnemonic = 'V0:V' + v1 + ' = M(I)'
    else:
        mmnemonic = 'Data'
    return mmnemonic

# Function to convert hex to intel Hex
def ConvertToIntelHex(DataRow,NewOrigin):    
     iHex=[]
     address = int(NewOrigin, 16)
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

def WriteFile(TargetFile,FileData,NewLine):
    f = open(TargetFile, "w")
    for data in FileData:
        if NewLine==1:
            data=data+"\n"
        f.write(data)
    f.close()  

# Write expanded mnemonics into file
def WriteMnemonic(TargetFile,HexArray,Address,Name):
  address=int(Address,16)
  p='{text0:<10}{text1:<10}{text2:30}'
  f = open(TargetFile, "w")
  f.write(Name+'\n\n')
  f.write(p.format(text0='Address',text1='Opcode',text2='Mnemonic')+'\n')
  for v in HexArray: 
      address=v[0][0:]
      opcode=v[1][0:]
      mnemonic=v[2][0:]  
      if len(opcode) <4:
           opcode=opcode.rjust(4, "0")   
      f.write(p.format(text0=address,text1=opcode,text2=mnemonic)+'\n')
  f.close()
  

# Prompt message
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
    import os,sys,click
    from colorama import Fore, Back, Style, init
    
    if len(sys.argv) != 1:
        print("Usage : %s SourceDir TargetDir" % sys.argv[0],file=sys.stderr)
        raise SystemExit(1)
    
    HexFlag=1
    HexDirFlag = 0
    HexSpace=''
    iHexFlag=0
    iHexDirFlag = 0
    MnemonicFlag = 0
    Origin=''

    # Prompts

    os.system('cls')
    init(autoreset=True)
    print(f'{Fore.RED}{Style.BRIGHT}Binary To Hex File Conversion\n')
    print(f'{Fore.GREEN}{Style.BRIGHT}File Settings')
    
    SourceDir = click.prompt(f'{Fore.BLUE}Binary Source Directory', type=click.Path(exists=True), default=os.getcwd(),hide_input=False,show_choices=False,show_default=False,prompt_suffix=' <'+os.getcwd()+'> : ')
    if not SourceDir.endswith(os.sep):
        SourceDir = SourceDir + os.sep

    TargetDir = click.prompt(f'{Fore.BLUE}Target Directory', type=click.Path(exists=False), default=os.getcwd(),hide_input=False,show_choices=False,show_default=False,prompt_suffix=' <'+os.getcwd()+'> : ')
    if not TargetDir.endswith(os.sep):
        TargetDir = TargetDir + os.sep
    if click.confirm(f'{Fore.YELLOW}Do you want to include spaces between hex values ?',default='Y',show_default=False,prompt_suffix=' <Y>'):
        HexSpace=' '
    if click.confirm(f'{Fore.YELLOW}Do you want to save Hex files in a single directory as well?',default='Y',show_default=False,prompt_suffix=' <Y>'):
        HexDirFlag=1
    if click.confirm(f'{Fore.YELLOW}{Style.BRIGHT}Do you want to export to Intel Hex files ?',default='Y',show_default=False,prompt_suffix=' <Y>'):
        ByteRow=int(click.prompt(f'{Fore.YELLOW}{Style.BRIGHT}Number of Bytes per row:',default='16',type=click.Choice(['2','4','8','16','32']),hide_input=False,show_choices=False,show_default=False,prompt_suffix=' <16> : '))
        Origin=str(PromptHex(f'{Fore.YELLOW}{Style.BRIGHT}Origin start at','0000'))
        iHexFlag=1
        if click.confirm(f'{Fore.YELLOW}{Style.BRIGHT}Do you want to save Intel Hex files in a single directory as well?',default='Y',show_default=False,prompt_suffix=' <Y>'):
            iHexDirFlag=1
    if click.confirm(f'{Fore.YELLOW}{Style.BRIGHT}Do you want to export to Chip8 Mnemonic files ?',default='Y',show_default=False,prompt_suffix=' <Y>'):
        MnemonicFlag = 1
        if Origin=='':
            Origin=str(PromptHex(f'{Fore.YELLOW}{Style.BRIGHT}Origin start at','0000'))
    
    # Create directories for hex and mnemonic files
    HexDir=TargetDir + 'hex'
     
    if not os.path.exists(HexDir):
        os.makedirs(HexDir)    
    
    if iHexFlag:
        IntelHexDir=TargetDir + 'ihex'
        if not os.path.exists(IntelHexDir):
            os.makedirs(IntelHexDir)
    
    if MnemonicFlag:
        MnemonicDir=TargetDir + 'mnemonic'
        if not os.path.exists(MnemonicDir):
            os.makedirs(MnemonicDir)
             
    for file in os.listdir(SourceDir):
        if file.endswith((".bin",".BIN",".c8",".C8",".ch8",".CH8",".cos",".COS",".dat",".DAT",".st2","ST2")):
            SourceFile=os.path.join(SourceDir, file)
            SourceName=os.path.splitext(file)[0]
            AlphaName=SourceName[0]
                       
            AlphaDir=os.path.join(HexDir,AlphaName)
            if not os.path.exists(AlphaDir):
                os.makedirs(AlphaDir)    
            HexFile=os.path.join(AlphaDir,SourceName+'.hex')
            HexFileCopy=os.path.join(HexDir,SourceName+'.hex')
            
            if iHexFlag:
                AlphaDir=os.path.join(IntelHexDir,AlphaName)
                if not os.path.exists(AlphaDir):
                    os.makedirs(AlphaDir)    
                IntelHexFile=os.path.join(AlphaDir,SourceName+'.hex')
                if iHexDirFlag:
                    IntelHexFileCopy=os.path.join(IntelHexDir,SourceName+'.hex')
            
            if MnemonicFlag:
                AlphaDir=os.path.join(MnemonicDir,AlphaName)
                if not os.path.exists(AlphaDir):
                    os.makedirs(AlphaDir)    
                MnemonicFile=os.path.join(AlphaDir,SourceName+'.txt')

            Data=[]             
            with open(SourceFile,'rb') as f:
                b = f.read(2)
                while b:
                   h=b.hex()    
                   Data.append(h.upper())
                   b=f.read(2)
            DataStr=[]
            DataStr = ''.join(Data)             
            print('\n')
            if HexFlag:
                FileData=[]
                FileData.append(HexSpace.join(list(SplitBy(DataStr,2))))
                print(f'{Fore.YELLOW}Writing Hex Format File '+ HexFile)  
                WriteFile(HexFile,FileData,0)
                if HexDirFlag==1:
                    print(f'{Fore.YELLOW}Copying file '+ SourceName+' to '+HexFileCopy)
                    WriteFile(HexFileCopy,FileData,0)                     
                       
            if iHexFlag:
                print(f'{Fore.GREEN}Writing Intel Hex Format File '+ IntelHexFile)
                DataRow=[]
                DataRow.append(list(SplitBy(DataStr,ByteRow*2)))
                FileData=[]
                FileData=ConvertToIntelHex(DataRow,Origin)
                WriteFile(IntelHexFile,FileData,1)
                if iHexDirFlag==1:
                    print(f'{Fore.BLUE}Copying file '+ SourceName+' to '+IntelHexFileCopy)
                    WriteFile(IntelHexFileCopy,FileData,1)                     
 
            if MnemonicFlag:
                print(f'{Fore.GREEN}Writing Mnemonic File '+ MnemonicFile)
                FileData=[]
                FileData=CreateMnemonic(Data,Origin)
                WriteMnemonic(MnemonicFile,FileData,Origin,SourceName)