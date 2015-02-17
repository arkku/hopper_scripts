# Hopper Disassembler script to insert x86/x64 instructions to return
# an integer from the current procedure. Should handle both 64-bit and
# 32-bit values. Automatically inserts function prologue if its epilogue
# remains unchanged - to avoid inserting the prologue, run this at the
# very beginning of the function so that the epilogue is overwritten.
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
    suffix = ":" if arch == 2 else " (L suffix forces 64-bit):"
    s = Document.ask("Integer value to return"+suffix)
    if s != None:
        valueSize = 4
        if s[-1] == 'L' or s[-1] == 'l':
            valueSize = 8
            s = s[:-1]
        i = int(s, 0)
        endProc = adr + 1
        while seg.getTypeAtAddress(endProc) == Segment.TYPE_NEXT:
            endProc += 1
        if (arch == 2 or valueSize < 8) and (i == 1 or i == 0):
            # xor eax, eax -> 0
            seg.writeByte(adr, 0x31)
            seg.writeByte(adr + 1, 0xC0)
            seg.markAsCode(adr)
            adr += 2
            if i == 1:
                # inc eax -> 1
                seg.writeByte(adr, 0xFF)
                seg.writeByte(adr + 1, 0xC0)
                seg.markAsCode(adr)
                adr += 2
        else:
            offset = 0
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
        if entry != Segment.BAD_ADDRESS:
            if seg.readByte(entry) == 0x55:
                if seg.readByte(entry + 1) == 0x48 and \
                        seg.readByte(entry + 2) == 0x89 and \
                        seg.readByte(entry + 3) == 0xE5:
                       # mov rsp, rbp
                       seg.writeByte(adr, 0x48)
                       seg.writeByte(adr + 1, 0x89)
                       seg.writeByte(adr + 2, 0xEC)
                       seg.markAsCode(adr)
                       adr += 3
                elif seg.readByte(entry + 1) == 0x89 and \
                        seg.readByte(entry + 2) == 0xE5:
                       # mov esp, ebp
                       seg.writeByte(adr, 0x89)
                       seg.writeByte(adr + 1, 0xEC)
                       seg.markAsCode(adr)
                       adr += 2
                # pop rbp/ebp
                seg.writeByte(adr, 0x5D)
                seg.markAsCode(adr)
                adr += 1
            elif seg.readByte(entry) == 0xC8:
                # leave
                seq.writeByte(adr, 0xC9)
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
