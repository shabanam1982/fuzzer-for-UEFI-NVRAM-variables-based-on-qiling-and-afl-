from .base_tainter import base_tainter
from qiling.const import *
import os
from qiling.os.uefi.utils import ptr_read64

import capstone
from capstone.x86_const import *

def SetMem_propagate_taint(ql, address, params):
    """
    Taint propagation for SetMem(). We taint or untaint the target buffer based on the taint status
    'UINT8 Value' argument.
    """
    begin = params['Buffer']
    end = begin + params['Size']
    # r8b corresponds to the 'UINT8 Value' parameter.
    Value = ql.tainters['uninitialized'].triton_ctx.registers.r8b
    taint = ql.tainters['uninitialized'].triton_ctx.isRegisterTainted(Value)
    ql.tainters['uninitialized'].set_taint_range(begin, end, taint)

def CopyMem_propagate_taint(ql, address, params):
    """
    Taint propagation for CopyMem(). The taint is copied on a byte-by-byte basis from the source
    buffer to the destination buffer.
    """
    ql.tainters['uninitialized'].copy_taint(params['Source'], params['Destination'], params['Length'])

def AllocatePool_propagate_taint(ql, address, params):
    """
    Taint propagation for AllocatePool().
    We know that all pool memory is initially uninitialized, so we taint it.
    """
    begin = ptr_read64(ql, params['Buffer'])
    end = begin + params['Size']
    ql.tainters['uninitialized'].set_taint_range(begin, end, True)

def GetVariable_propagate_taint(ql, address, params):
    """
    Taint propagation for GetVariable(). We initially assume that all NVRAM variables are fully
    initialized, so the target buffer becomes untainted.
    """
    begin = params['Data']
    if begin == 0:
        # May be NULL with a zero DataSize in order to determine the size buffer needed.
        return
        
    end = begin + ptr_read64(ql, params['DataSize'])
    ql.tainters['uninitialized'].set_taint_range(begin, end, False)

def SetVariable_propagate_taint(ql, address, params):
    """
    Taint propagation of SetVariable(). If the data that was written to NVRAM contains some tainted
    bytes, that means a potential infoleak has occurred and we can abort the process and report that.
    """
    begin = params["Data"]
    end = params["Data"] + params["DataSize"]
    if ql.tainters['uninitialized'].is_range_tainted(begin, end):
        ql.log.error(f"***")
        ql.log.error(f"Detected potential info leak in SetVariable({params})")
        ql.log.error(f"***")
        ql.os.emu_error()
        ql.os.fault_handler()

def SmmAllocatePages_propagate_taint(ql, address, params):
    """
    Taint propagation of SmmAllocatePages(). If the data that was written to NVRAM contains some tainted
    bytes, that means a potential infoleak has occurred and we can abort the process and report that.
    """
    # r8 corresponds to the 'UINTN NumberOfPages' parameter.
    NumberOfPages = ql.tainters['uninitialized'].triton_ctx.registers.r8
    if ql.tainters['uninitialized'].triton_ctx.isRegisterTainted(NumberOfPages):
        # Uninitialized value is used.
        ql.log.warn(f"An uninitialized value (0x{ql.reg.r8:x}) is used as argument NumberOfPages of SmmAllocatePages()")

    # @TODO: Are the newly allocated pages zero-initialized or not?

class uninitialized_memory_tainter(base_tainter):

    NAME = 'uninitialized'

    def enable(self):
        super().enable()

        self.ql.set_api("SetMem", SetMem_propagate_taint, QL_INTERCEPT.EXIT)
        self.ql.set_api("CopyMem", CopyMem_propagate_taint, QL_INTERCEPT.EXIT)
        self.ql.set_api("SetVariable", SetVariable_propagate_taint, QL_INTERCEPT.EXIT)
        self.ql.set_api("GetVariable", GetVariable_propagate_taint, QL_INTERCEPT.EXIT)
        self.ql.set_api("AllocatePool", AllocatePool_propagate_taint, QL_INTERCEPT.EXIT)
        self.ql.set_api("SmmAllocatePages", SmmAllocatePages_propagate_taint, QL_INTERCEPT.EXIT)

    @staticmethod
    def is_stack_pointer_decrement(inst):
        # sub rsp, x
        if inst.id == X86_INS_SUB and \
        inst.operands[0].type == capstone.CS_OP_REG and inst.operands[0].reg == X86_REG_RSP:
            assert inst.operands[1].type == capstone.CS_OP_IMM
            decrement = inst.operands[1].imm
            return True, decrement

        # add rsp, -x
        if inst.id == X86_INS_ADD and \
        inst.operands[0].type == capstone.CS_OP_REG and inst.operands[0].reg == X86_REG_RSP:
            assert inst.operands[1].type == capstone.CS_OP_IMM
            increment = inst.operands[1].imm
            if increment < 0:
                return True, -increment

        return False, 0

    def instruction_hook(self, ql, instruction):
        # We are looking for instructions which decrement the stack pointer.
        (should_taint, decrement) = self.is_stack_pointer_decrement(instruction)
        if should_taint:
            # Taint all stack memory from current rsp to new rsp.
            self.set_taint_range(ql.reg.arch_sp - decrement, ql.reg.arch_sp, True)
