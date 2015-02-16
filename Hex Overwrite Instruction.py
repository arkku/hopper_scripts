# Hopper Disassembler script to replace the current instruction with
# another one given as hex. On x86/x64 architectures also pads the
# instruction with NOPs as necessary.
#
# By Kimmo Kulovesi <http://arkku.com/>, 2015

doc = Document.getCurrentDocument()
seg = doc.getCurrentSegment()
adr = doc.getCurrentAddress()
proc = seg.getProcedureAtAddress(adr)
entry = proc.getEntryPoint() if proc != None else Segment.BAD_ADDRESS
ins = seg.getInstructionAtAddress(adr)
arch = ins.getArchitecture()

hexStr = Document.ask("Replacement instruction as hex:")
if hexStr != None:
    endProc = adr
    if seg.getTypeAtAddress(endProc) == Segment.TYPE_CODE:
        endProc += 1
        while seg.getTypeAtAddress(endProc) == Segment.TYPE_NEXT:
            endProc += 1
    pos = adr
    for i in range(0, len(hexStr), 2):
        byte = int(hexStr[i:i+2], 16) & 255
        #print("Writing 0x%02X at address %x" % (byte, pos))
        seg.writeByte(pos, byte)
        pos += 1
    if endProc > adr:
        seg.markAsCode(adr)
        if arch in [1, 2]:
            while pos < endProc:
                seg.writeByte(pos, 0x90)
                seg.markAsCode(pos)
                pos += 1
    if entry != Segment.BAD_ADDRESS:
        seg.markAsProcedure(entry)
