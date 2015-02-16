# Hopper Disassembler script to insert x86/x64 instructions to return
# an integer from the current procedure. Should handle both 64-bit and
# 32-bit values, and automatically inserts pop ebp/rbp if there was an
# unreplaced push at the beginning of the procedure.
#
# By Kimmo Kulovesi <http://arkku.com/>, 2015

doc = Document.getCurrentDocument()
seg = doc.getCurrentSegment()
adr = doc.getCurrentAddress()
proc = seg.getProcedureAtAddress(adr)
entry = proc.getEntryPoint() if proc != None else Segment.BAD_ADDRESS
ins = seg.getInstructionAtAddress(adr)
arch = ins.getArchitecture()

if arch in [1, 2]:
    s = Document.ask("Integer value to return:")
    if s != None:
        i = int(s, 0)
        endProc = adr + 1
        while seg.getTypeAtAddress(endProc) == Segment.TYPE_NEXT:
            endProc += 1
        if i == 1 or i == 0:
            # xor eax, eax -> 0
            seg.writeByte(adr, 0x31)
            seg.writeByte(adr + 1, 0xC0)
            seg.markAsCode(adr)
            adr += 2
            if i == 1:
                seg.writeByte(adr, 0xFF)
                seg.writeByte(adr + 1, 0xC0)
                seg.markAsCode(adr)
                adr += 2
        else:
            offset = 0
            valueSize = 4
            valueChunk = 4
            if i > 4294967295 or i < -2147483648:
                # 64-bit value
                valueSize = 8
                if arch == 2:
                    seg.writeByte(adr, 0x48)
                    valueChunk = 8
                    offset = 1
            seg.writeByte(adr + offset, 0xB8)
            offset += 1
            for pos in range(offset, offset + valueChunk):
                seg.writeByte(adr + pos, (i & 0xFF))
                i >>= 8
            seg.markAsCode(adr)
            adr += offset + valueChunk
            if valueSize > valueChunk:
                # 64-bit value on 32-bit architecture
                seg.writeByte(adr, 0xBA)
                for pos in range(offset, offset + valueChunk):
                    seg.writeByte(adr + pos, (i & 0xFF))
                    i >>= 8
                seg.markAsCode(adr)
                adr += offset + valueChunk
        if entry != Segment.BAD_ADDRESS and seg.readByte(entry) == 0x55:
            # pop rbp
            seg.writeByte(adr, 0x5D)
            seg.markAsCode(adr)
            adr += 1
        seg.writeByte(adr, 0xC3)
        seg.markAsCode(adr)
        adr += 1
        while adr < endProc:
            seg.writeByte(adr, 0x90)
            seg.markAsCode(adr)
            adr += 1
        if entry != Segment.BAD_ADDRESS:
            seg.markAsProcedure(entry)
else:
    print("Unsupported architecture!")
