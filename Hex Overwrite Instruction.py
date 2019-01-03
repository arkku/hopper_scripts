# Hopper Disassembler script to replace the current instruction with
# another one given as hex. On x86/x64 architectures also pads the
# instruction with NOPs as necessary.
#
# By Kimmo Kulovesi <https://arkku.com/>, 2015-2019

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
    if ins != None:
        endProc += ins.getInstructionLength()
    if endProc == adr:
        if seg.getTypeAtAddress(endProc) == Segment.TYPE_CODE:
            endProc += 1
            while seg.getTypeAtAddress(endProc) == Segment.TYPE_NEXT:
                endProc += 1
    pos = adr
    for i in range(0, len(hexStr), 2):
        byte = int(hexStr[i:i+2], 16) & 255
        #doc.log("Writing 0x%02X at address %x" % (byte, pos))
        seg.writeByte(pos, byte)
        pos += 1
    if endProc > adr:
        seg.markAsCode(adr)
        if arch in [ Instruction.ARCHITECTURE_i386, Instruction.ARCHITECTURE_X86_64 ]:
            while pos < endProc:
                # NOP
                seg.writeByte(pos, 0x90)
                seg.markAsCode(pos)
                pos += 1
    if entry != Segment.BAD_ADDRESS:
        seg.markAsProcedure(entry)
