# Hopper Disassembler script to insert x86/x64 instructions to return
# an integer from the current procedure. Should handle both 64-bit and
# 32-bit values. Automatically inserts function epilogue if its prologue
# remains unchanged - to avoid inserting the epilogue, run this at the
# very beginning of the function so that the prologue is overwritten.
#
# Currently this only supports the basic `push rbp`, `mov rbp, rsp`
# prologue - if you need to restore other registers, or if `rbp` isn't
# used to store `rsp`, you need to handle that manually. (However,
# if you just return immediately, this is not a problem.)
#
# By Kimmo Kulovesi <https://arkku.com/>, 2015-2019

doc = Document.getCurrentDocument()
seg = doc.getCurrentSegment()
adr = doc.getCurrentAddress()
proc = seg.getProcedureAtAddress(adr)
entry = proc.getEntryPoint() if proc != None else Segment.BAD_ADDRESS
ins = seg.getInstructionAtAddress(adr)
arch = ins.getArchitecture()

if arch in [ Instruction.ARCHITECTURE_i386, Instruction.ARCHITECTURE_X86_64 ]:
    suffix = ":" if arch == Instruction.ARCHITECTURE_X86_64 else " (L suffix forces 64-bit):"
    s = Document.ask("Integer value to return"+suffix)
    if s != None:
        valueSize = 4
        if s[-1] == 'L' or s[-1] == 'l':
            # Force 64-bit with L suffix
            valueSize = 8
            s = s[:-1]
        i = int(s, 0)
        endProc = adr + 1

        # Find the end of the procedure
        while seg.getTypeAtAddress(endProc) == Segment.TYPE_NEXT:
            endProc += 1
        if (arch == Instruction.ARCHITECTURE_X86_64 or valueSize < 8) and (i == 1 or i == 0):
            # Values 0 and 1 are handled as special cases
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
            # Try to identify function prologue
            if seg.readByte(entry) == 0x55:
                # P: push rbp/ebp
                if seg.readByte(entry + 1) == 0x48 and \
                        seg.readByte(entry + 2) == 0x89 and \
                        seg.readByte(entry + 3) == 0xE5:
                        # P: mov rbp, rsp
                        # E: mov rsp, rbp:
                       seg.writeByte(adr, 0x48)
                       seg.writeByte(adr + 1, 0x89)
                       seg.writeByte(adr + 2, 0xEC)
                       seg.markAsCode(adr)
                       adr += 3
                elif seg.readByte(entry + 1) == 0x89 and \
                        seg.readByte(entry + 2) == 0xE5:
                        # P: mov ebp, esp
                        # E: mov esp, ebp:
                       seg.writeByte(adr, 0x89)
                       seg.writeByte(adr + 1, 0xEC)
                       seg.markAsCode(adr)
                       adr += 2
                # E: pop rbp/ebp:
                seg.writeByte(adr, 0x5D)
                seg.markAsCode(adr)
                adr += 1
            elif seg.readByte(entry) == 0xC8:
                # P: enter
                # E: leave:
                seq.writeByte(adr, 0xC9)
                seg.markAsCode(adr)
                adr += 1

        # ret:
        seg.writeByte(adr, 0xC3)
        seg.markAsCode(adr)
        adr += 1

        while adr < endProc:
            # NOP the old code
            seg.writeByte(adr, 0x90)
            seg.markAsCode(adr)
            adr += 1

        if entry != Segment.BAD_ADDRESS:
            seg.markAsProcedure(entry)
else:
    doc.log("Unsupported architecture!")
