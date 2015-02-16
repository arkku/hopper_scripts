# Hopper Disassembler script to insert hexadecimal values at the current
# cursor position. Makes it quicker to change, e.g., a 0x00 to 0x01 within
# an instruction: place the cursor at the 0x00 position and type 01 as the
# value to insert...
#
# By Kimmo Kulovesi <http://arkku.com/>, 2015

doc = Document.getCurrentDocument()
seg = doc.getCurrentSegment()
adr = doc.getCurrentAddress()
proc = seg.getProcedureAtAddress(adr)
entry = proc.getEntryPoint() if proc != None else Segment.BAD_ADDRESS
col = doc.getCurrentColumn() - 17 # magic number to skip the address column
col = (col / 2) if col >= 0 else 0

hexStr = Document.ask("Enter hexadecimal value to insert:")
if hexStr != None:
    originalType = seg.getTypeAtAddress(adr)
    pos = adr + col
    for i in range(0, len(hexStr), 2):
        byte = int(hexStr[i:i+2], 16) & 255
        #print("Writing 0x%02X at address %x" % (byte, pos))
        seg.writeByte(pos, byte)
        pos += 1
    if originalType == Segment.TYPE_CODE:
        seg.markAsCode(adr)
    if entry != Segment.BAD_ADDRESS:
        seg.markAsProcedure(entry)
